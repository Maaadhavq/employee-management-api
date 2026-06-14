# Employee Management REST API - Week 3

This is my Week 3 submission for the Employee Management API. For this week, I successfully migrated the data storage from a local JSON file to a real PostgreSQL database using SQLAlchemy.

## What's Included
* **FastAPI Backend**: The core API endpoints for creating, reading, updating, and deleting employees.
* **PostgreSQL Integration**: The API now connects to a PostgreSQL database. It automatically creates the necessary tables (`employees` and `departments`) when the server starts.
* **Validation**: It still uses Pydantic to ensure all data (like emails and salaries) is valid before touching the database.
* **Database Scripts**: You can find my raw SQL schema, seed data, and example queries in the `db/` folder.
* **ER Diagram**: I've included an Entity-Relationship diagram in the `docs/` folder showing how the tables connect.

## How to Run It

1. **Install Dependencies**
   Make sure you are in the project directory and run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL**
   * Make sure you have PostgreSQL running locally (port 5432).
   * Create a database named `employee_db`.
   * Rename the `.env.example` file to `.env` and put your database password inside it.

3. **Start the Server**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Test the API**
   Once the server is running, open your browser and go to:
   [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   
   The Swagger UI will let you test out all the endpoints! The server will automatically create the tables and add some starting data (like Ada Lovelace and Grace Hopper) the first time you boot it up.
