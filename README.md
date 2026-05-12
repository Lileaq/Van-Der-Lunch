# Van Der Lunch
API for food delivery service

---



### 1. Install Dependencies
Ensure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 2. Database Setup
* Open your MySQL/MariaDB administration tool (e.g., phpMyAdmin).
* Import and execute the SQL queries found in **`create_database.txt`** to generate the schema and initial data.

### 3. Environment Configuration
Create a file named **`.env`** in the root directory and add your connection string:
```env
DATABASE_URL=mysql+asyncmy://Dutch:password123@localhost/van-der-data
```

### 4. Run the API
Start the development server using Uvicorn:
```bash
uvicorn main:app --reload
```

---

## Access Points

Once the server is running, you can access the following:

* **Main API URL:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Interactive Documentation (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
