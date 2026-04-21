from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReviewCreate(BaseModel):
    user_id: int
    restaurant_id: int
    stars: int = Field(ge=1, le=5)
    review_text: Optional[str] = None