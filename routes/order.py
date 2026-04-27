import polyline
import requests
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Union
from database_configuration import get_db, Restaurant, FoodItem, Order, OrderItem, OrderStatus, User, \
    Courier
from datetime import datetime,timezone
from logger import logger
from routes.user import get_current_user
from schemas import OrderCreate, ItemInOrder, CreateOrderResponse, RegularSuccessResponse, OrderListResponse, \
    OrderStatusDetailedResponse

router = APIRouter(
    prefix="/order",
    tags=["order"]
)


def is_restaurant_open(opening_hours_list):
    now = datetime.now(timezone.utc)
    current_day = now.weekday()
    current_minutes = now.hour * 60 + now.minute

    for oh in opening_hours_list:
        if oh.day_of_week == current_day:
            if oh.is_closed:
                return False
            return oh.open_from_minute <= current_minutes <= oh.close_to_minute

    return False

@router.post("/create",
    summary="Create new order",
    description="Validates items, checks restaurant availability and calculates price",
    status_code=201,
    response_model=CreateOrderResponse,
    responses={
        201: {"description": "Order created in cart status"},
        400: {"description": "Items from different restaurants"},
        403: {"description": "Restaurant is closed"},
        409: {"description": "User location missing or too far"},
        500: {"description": "Create order failed"}
    })
async def create_order(
        data : OrderCreate,
        db: AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user)
):
    logger.info("Hit /create create new order")


    try:

        # do not allow empty order
        if len(data.order_items) == 0:
            raise HTTPException(status_code=404, detail="Empty order")



        #check if items available and from the same restaurant
        food_items_ids = [i.food_id for i in data.order_items]
        query = select(FoodItem).where(
            and_(
                FoodItem.availability == True,
                FoodItem.id.in_(food_items_ids)
            ))
        result = await db.execute(query)
        food_items = result.scalars().all()

        # not available or do not exist
        if len(data.order_items) != len(food_items):
            logger.info(f"create review failed")
            raise HTTPException(status_code=404, detail="Food items not found")

        # check if from the same restaurant
        restaurant_id = {item.restaurant_id for item in food_items}
        if len(restaurant_id) > 1:
            raise HTTPException(
                status_code=400,
                detail="All items in one order must come from the same restaurant"
            )

        quantity_map = {item.food_id: item.quantity for item in data.order_items}
        #calculate the price
        price = 0
        for item in food_items:
            quantity = quantity_map.get(item.id, 0)
            price += item.base_price * quantity

        # ORDER ROUTE LOGIC
        # check if user localisation is correct (exists and not too far)
        query = select(User).where(User.id == user["id"])
        result = await db.execute(query)
        user_data = result.scalars().first()

        if user_data.lat == None or user_data.lng == None:
            raise HTTPException(status_code=409, detail="User has no localisation specified")


        query = select(Restaurant)\
            .options(selectinload(Restaurant.opening_hours_list))\
            .where(Restaurant.id == food_items[0].restaurant_id,)
        result = await db.execute(query)
        restaurant = result.scalars().first()

        # check if restaurant open
        if not is_restaurant_open(restaurant.opening_hours_list):
            raise HTTPException(
                status_code=403,
                detail="Restaurant is currently closed. Orders are not accepted."
            )

        # check if in area
        if abs(float(restaurant.lat) - float(user_data.lat)) > 0.5 or abs(float(restaurant.lng) - float(user_data.lng)) > 0.5:
            raise HTTPException(status_code=409, detail="User too far away from restaurant")

        # ask the api for a route and save it for later use
        url = f'http://router.project-osrm.org/route/v1/driving/{restaurant.lng},{restaurant.lat};{user_data.lng},{user_data.lat}?overview=full&geometries=polyline'
        response = requests.get(url).json()
        route = response['routes'][0]['geometry']
        delivery_time = response['routes'][0]['duration']


        # create order in a cart state
        new_order = Order(
            user_id=user["id"],
            restaurant_id=food_items[0].restaurant_id,
            status=OrderStatus.cart,
            total_price=price,
            route=route,
            delivery_time=delivery_time
        )
        db.add(new_order)
        await db.flush()

        # create order items
        for item in food_items:
            new_order_item = OrderItem(
                order_id = new_order.id,
                food_item_id = item.id,
                quantity = quantity_map.get(item.id, 0)
            )
            db.add(new_order_item)

        await db.commit()
        await db.refresh(new_order)
        return {"msg": "Order created successfully", "order_id": new_order.id}

    except Exception as e:
        logger.info(f"Create order failed : {e}")
        raise HTTPException(status_code=500, detail="Create order failed")


@router.post(
    "/add-to-cart/{cart_id}",
    summary="Add items to existing cart",
    description="Increments quantity of existing items or adds new items to an active cart.",
    response_model=RegularSuccessResponse,
    responses={
        404: {"description": "Cart not found or not in 'cart' status"},
        500: {"description": "Add item to cart failed"}})
async def add_to_cart(
    cart_id: int,
    order_items : list[ItemInOrder],
    db: AsyncSession = Depends(get_db),
):
    try:
        # get cart data
        query = select(Order).where(Order.id == cart_id)
        result = await db.execute(query)
        cart = result.scalars().first()

        #no cart
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # chceck if in cart stage
        if cart.status.value != "cart":
            raise HTTPException(status_code=404, detail="Cart not in cart status anymore")

        query = select(Restaurant).options(selectinload(Restaurant.opening_hours_list)).where(
            Restaurant.id == cart.restaurant_id)
        response = await db.execute(query)
        restaurant = response.scalars().first()
        if not is_restaurant_open(restaurant.opening_hours_list):
            raise HTTPException(
                status_code=403,
                detail="Restaurant is currently closed. Orders are not accepted."
            )

        # get new food data from db
        food_ids = [item.food_id for item in order_items]
        food_query = select(FoodItem).where(FoodItem.id.in_(food_ids))
        food_result = await db.execute(food_query)
        food_items_db = food_result.scalars().all()

        # bad food data - wrong id
        if len(food_items_db) != len(set(food_ids)):
            raise HTTPException(status_code=404, detail="One or more food items not found")

        # check if items are correct
        for item in food_items_db:
            if item.restaurant_id != cart.restaurant_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Item is from a different restaurant"
                )
            if not item.availability:
                raise HTTPException(status_code=400, detail=f"Item {item.name} is currently unavailable")

        #if already in cart increment that order_items quantity
        query = select(OrderItem).where(
            and_(
                OrderItem.food_item_id.in_(food_ids),
                OrderItem.order_id == cart_id
            )
        )
        result = await db.execute(query)
        food_in_cart = result.scalars().all()

        # info maps
        food_in_cart_map = {item.food_item_id: item for item in food_in_cart}
        request_quantity_map = {item.food_id: item.quantity for item in order_items}
        food_prices = {item.id: item.base_price for item in food_items_db}

        added_price = 0

        for food in food_ids:
            quantity = request_quantity_map[food]
            price = food_prices[food]

            if food in food_in_cart_map:
                food_in_cart_map[food].quantity += quantity
            else:
                new_item = OrderItem(
                    order_id=cart_id,
                    food_item_id=food,
                    quantity=quantity
                )
                db.add(new_item)

            added_price += price * quantity

        cart.total_price += added_price

        await db.commit()
        await db.refresh(cart)


        return {"msg" : "Cart updated"}


    except Exception as e:
        logger.info(f"Add item to cart failed : {e}")
        raise HTTPException(status_code=500, detail="Add item to cart failed")


@router.post(
    "/pay/{cart_id}",
    summary="Pay for order",
    description="Changes order status from 'cart' to 'paid'",
    response_model=RegularSuccessResponse,
    responses={
        500: {"description": "Pay for order failed"},
        403: {"description": "This order does not belong to this user"}
    }
)
async def pay(
        cart_id : int,
        db :AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user)
):
    logger.info("Hit /pay")
    try:
        query = select(Order).where(Order.id == cart_id)
        result = await db.execute(query)
        order = result.scalars().first()

        if order.user_id != user["id"]:
            raise HTTPException(status_code=403, detail="This order does not belong to this user")

        order.status = OrderStatus.paid

        await db.commit()
        await db.refresh(order)

        # assign a courier, if no courier available create a new one


        return {"msg" : f"Order {cart_id} paid"}
    except Exception as e:
        logger.info(f"Pay for order failed : {e}")
        raise HTTPException(status_code=500, detail="Pay for order failed")


@router.get(
    "/history",
    summary="User order history",
    description="Returns all completed or canceled orders for the logged-in user.",
    response_model=OrderListResponse,
    responses={
        500: {"description": "Get user order history failed"},
        404: {"description": "No user order history"}
    }
)
async def order_history(
        db :AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user)
):
    try:
        query = select(Order).where(
            and_(
                Order.user_id == user["id"],
                or_(
                    Order.status == OrderStatus.completed,
                    Order.status == OrderStatus.canceled
                )
            )
        )
        result = await db.execute(query)
        history = result.scalars().all()

        if len(history) == 0:
            raise HTTPException(status_code=404, detail="No user order history")

        return {"orders" : history}
    except Exception as e:
        logger.info(f"Get user order history failed : {e}")
        raise HTTPException(status_code=500, detail="Get user order history failed")


@router.get("/active",
    summary="Active orders",
    description="Returns all orders that are currently in progress (from cart to on the way).",
    response_model=OrderListResponse,
    responses={
        500: {"description": "Get user active orders failed"},
        404: {"description": "No active orders for this user"}
    }
    )
async def order_history(
        db :AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user)
):
    try:
        query = select(Order).where(
            and_(
                Order.user_id == user["id"],
                or_(
                    Order.status == OrderStatus.cart,
                    Order.status == OrderStatus.not_paid,
                    Order.status == OrderStatus.paid,
                    Order.status == OrderStatus.preparing,
                    Order.status == OrderStatus.on_the_way,
                )
            )
        )
        result = await db.execute(query)
        actives = result.scalars().all()

        if len(actives) == 0:
            raise HTTPException(status_code=404, detail="No active orders for this user")

        return {"orders" : actives}
    except Exception as e:
        logger.info(f"order history failed : {e}")
        raise HTTPException(status_code=500, detail="Get user active orders failed")


@router.get(
    "/status/{order_id}",
    summary="Track order and courier",
    description="""
    Provides real-time-like status updates. 
    If the courier is 'on the way', it calculates their current GPS position based on the elapsed time and the OSRM route.
    """,
    response_model=Union[OrderStatusDetailedResponse,RegularSuccessResponse],
    responses={
        500 : {"description": "Get order status failed"},
        404 : {"description": "Order does not exist"},
        403 : {"description": "This order does not belong to this user"}
    }
)
async def order_status(
    order_id : int,
    db :AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    logger.info("Hit /status")
    try:

        now = datetime.now(timezone.utc)
        # get order data
        query = select(Order).where(Order.id == order_id)
        result = await db.execute(query)
        order = result.scalars().first()

        if not order:
            raise HTTPException(status_code=404, detail="Order does not exist")
        #check if order belongs to the user
        if order.user_id != user["id"]:
            raise HTTPException(status_code=403, detail="This order does not belong to this user")


        if order.status == OrderStatus.cart:
            return {"msg" : "order in cart state"}

        update_time = order.updated_at.replace(tzinfo=timezone.utc)
        seconds_since_update = (now - update_time).total_seconds()

        # time passed -> order completed
        if order.status == OrderStatus.on_the_way and seconds_since_update >= order.delivery_time:
            order.status = OrderStatus.completed
            query = select(Courier).where(Courier.current_order_id == order_id)
            result = await db.execute(query)
            courier = result.scalars().first()
            if courier:
                courier.current_order_id = None

            await db.commit()
            return {"msg" : "your order has been delivered"}


        # preparing or on the way already
        status_changed = False
        logger.info("sprawdzamy")
        if order.status == OrderStatus.paid:
            logger.info("zapłacony")
            if seconds_since_update < 60:
                logger.info("mniej niż 60 -> preparing")
                order.status = OrderStatus.preparing
            else:
                order.status = OrderStatus.on_the_way
                logger.info("wićej niż 60 -> on the way")
            status_changed = True

        elif order.status == OrderStatus.preparing:
            if seconds_since_update >= 60:
                logger.info("preparowany już z minutę wiec --> on the way")
                order.status = OrderStatus.on_the_way
                status_changed = True


        if status_changed:
            logger.info(f"teraz będą zmiany {order.status}")
            await db.commit()
            await db.refresh(order)

            now = datetime.now(timezone.utc)
            update_time = order.updated_at.replace(tzinfo=timezone.utc)
            seconds_since_update = (now - update_time).total_seconds()
            logger.info(f"zmiany powinny iść {order.status}")

        logger.info(f"tera mamy {order.status} " )

        if order.status == OrderStatus.on_the_way:
            logger.info("jedzie do nas")
            # compute where the courier should be
            route = polyline.decode(order.route)
            progres = (now - update_time).total_seconds() / order.delivery_time
            logger.info(str((now - update_time).total_seconds()) + " seconds")
            index = int(progres * (len(route) - 1))
            logger.info(str(index) + " out of " + str(len(route)-1))
            courier_position = route[index]

            #update the courier info
            query = select(Courier).where(Courier.current_order_id == order_id)
            result = await db.execute(query)
            courier = result.scalars().first()

            if not courier:
                #assign a courier
                query = select(Courier).where(Courier.current_order_id == None)
                result = await db.execute(query)
                empty_courier = result.scalars().first()

                if not empty_courier:
                    courier = Courier(name=f"Kurier #{order_id + 100}", current_order_id=order.id)
                    await db.add(courier)

            await db.commit()
            # await db.refresh(courier)

            return {
                "msg" : "courier on the way",
                "status" : order.status,
                "courier_position" : courier_position,
                "courier_name" : courier.name,
                "progress": f"{int(progres * 100)}%"
            }

        # return {"status" : order.status}
    except Exception as e:
        logger.info(f"Get order status failed : {e}")
        raise HTTPException(status_code=500, detail="Get order status failed")