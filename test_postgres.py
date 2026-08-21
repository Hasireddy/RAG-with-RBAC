from sqlalchemy import create_engine, text

DATABASE_URL = (
    "postgresql+psycopg://"
    "rag_user:rag_password@localhost:5432/rag_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

with engine.connect() as connection:
    result = connection.execute(
        text("SELECT current_database(), current_user")
    )

    row = result.fetchone()

    print("Database:", row[0])
    print("User:", row[1])