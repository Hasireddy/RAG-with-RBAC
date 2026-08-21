from sqlalchemy import create_engine, text

DATABASE_URL = (
    "postgresql+psycopg://"
    "rag_user:rag_password@127.0.0.1:5433/rag_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

with engine.connect() as connection:
    row = connection.execute(
        text("""
            SELECT
                version(),
                current_database(),
                current_user,
                inet_server_addr(),
                inet_server_port()
        """)
    ).fetchone()

    print("Version:", row[0])
    print("Database:", row[1])
    print("User:", row[2])
    print("Server address:", row[3])
    print("Server port:", row[4])

    vector = connection.execute(
        text("""
            SELECT
                name,
                default_version,
                installed_version
            FROM pg_available_extensions
            WHERE name = 'vector'
        """)
    ).fetchall()

    print("Vector:", vector)