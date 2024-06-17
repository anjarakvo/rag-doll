### Backend (Fast API)

The backend of this project is built using [FastAPI](https://fastapi.tiangolo.com/), a modern and high-performance web framework for building APIs with Python 3.12.3. The backend communicates with a PostgreSQL database to manage and store application data. The PostgreSQL database is initialized with predefined scripts located in the ./postgres/docker-entrypoint-initdb.d directory, ensuring that the database schema and initial data are set up automatically. Additionally, a PgAdmin4 service is provided to offer a user-friendly interface for managing the PostgreSQL database. PgAdmin4 is configured to run on port 5050 and can be accessed using the default credentials specified in the environment variables.