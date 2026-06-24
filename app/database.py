from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    if os.environ.get("VERCEL"):
        DB_URL = "sqlite:////tmp/app.db"
    else:
        DB_URL = "sqlite:///./app.db"

connect_args = {}
if DB_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
