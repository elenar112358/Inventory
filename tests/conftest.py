from typing import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base
from app.dependency import get_db
from app.enums import DocTypes
from app.main import app
from app.schemas import MovementsPost

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
)


def get_test_db() -> Generator[Session, None, None]:
    with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = get_test_db

@pytest.fixture()
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(test_engine)

    sql = Path("tests/test_data_maker.sql").read_text(encoding="utf-8")
    with test_engine.begin() as conn:
        conn.connection.executescript(sql)

    yield
    Base.metadata.drop_all(test_engine)

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    with TestSessionLocal() as session:
        yield session

@pytest.fixture
def receipt_movement() -> MovementsPost:
    movement_request = MovementsPost(
        document_date="2026-09-01",
        document_number="REC-2026-0004",
        document_type=DocTypes.RECEIPT,
        product_sku="SPA-0001",
        quantity=20.0,
        site_name="Склад филиала",
        batch_number="B-0002",
    )

    return movement_request


"""
class MovementsPost(BaseModel):
    document_date: date
    document_number: str = Field(max_length=20)
    document_type: DocTypes

    product_sku: str = Field(max_length=20)
    quantity: Decimal

    site_name: str = Field(max_length=30)
    batch_number: str | None = Field(default=None, max_length=20)
"""
