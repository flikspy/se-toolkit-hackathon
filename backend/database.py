from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Production: PostgreSQL via DATABASE_URL
# Local dev: SQLite fallback if no DATABASE_URL set
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./grocery.db")

# SQLite needs different connect_args than PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
