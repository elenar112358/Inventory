from typing import Generator

from app.database import SessionLocal
from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session