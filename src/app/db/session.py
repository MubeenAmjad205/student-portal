# File: app/db/session.py
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker

# 1️⃣ Load env and validate
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# 2️⃣ Create one Engine at import time, with pooling and pre-ping
engine = create_engine(
    DATABASE_URL,
    pool_size=10,            # max persistent connections
    max_overflow=20,         # extra connections beyond pool_size
    pool_pre_ping=True,      # test connections before using
    pool_recycle=1800,       # recycle connections older than 30m
    pool_timeout=30,         # wait up to 30s for a free connection
    connect_args={"sslmode": "require"},
    # echo=True,            # <-- turn on for SQL logging in dev
)

# 3️⃣ Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    expire_on_commit=False,
)

# 4️⃣ Create tables (call this at app startup)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 5️⃣ FastAPI dependency: open a Session for each request, always close it
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
