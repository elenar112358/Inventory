from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.enums import DocTypes

"""
принимает запись движения товара (дата,
SKU, объект, тип операции receipt / consume / writeoff / return / correction, количество,
партия, номер документа), сохраняет её в БД и возвращает идентификатор записи и
пересчитанный остаток по позиции и объекту.

"""

class MovementsPost(BaseModel):
    document_date: date
    document_number: str = Field(max_length=20)
    document_type: DocTypes

    product_sku: str = Field(max_length=20)
    product_name: str = Field(max_length=100)

    site_name: str = Field(max_length=30)

    quantity: Decimal
    price: Decimal

    batch_date: date
    batch_number: str = Field(max_length=20)
    expiry_date: date | None


    @field_validator('price')
    @classmethod
    def validate_price(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError('Цена должна быть неотрицательной')

        return value.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @field_validator('document_date')
    @classmethod
    def validate_document_date(cls, value: date) -> date:
        if value > datetime.now(timezone.utc).date():
            raise ValueError('Дата документа не может быть в будущем')

        return value

    @field_validator('batch_date')
    @classmethod
    def validate_batch_date(cls, value: date) -> date:
        if value > datetime.now(timezone.utc).date():
            raise ValueError('Дата партии не может быть в будущем')

        return value

    @model_validator(mode="after")
    def validate_quantity(self):
        if self.document_type == DocTypes.CORRECTION:
            if self.quantity < 0:
                raise ValueError('Количество должно быть положительным')
            else:
                raise ValueError('Количество должно быть неотрицательным')

        self.quantity = self.quantity.quantize(
            Decimal("0.001"),
            rounding=ROUND_HALF_UP,
        )

        return self

"""
Добавить проверки: неизвестный SKU или объект — 404; 
количество меньше или равно нулю для receipt и consume — 422; 
расход больше доступного остатка — 422 с указанием доступного количества; 
дата операции в будущем — 422; 
повторная загрузка того же номера документа — 409.
"""

class MovementsPostResponse(BaseModel):
    id: UUID
    title: str = Field(max_length=255)
    product_quantity: Decimal
    site_quantity: Decimal


class MovementsRequest(BaseModel):
    product_sku: str | None = Field(max_length=20)
    site_name: str | None = Field(max_length=30)
    document_type: DocTypes | None = None
    date_from: date | None = None
    date_to: date | None = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)

    @model_validator(mode="after")
    def check_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("Дата начала запроса не может быть больше даты окончания запроса")
        return self


class MovementsResponse(BaseModel):
    product_sku: str | None = Field(max_length=20)
    site_name: str | None = Field(max_length=30)
    document_type: DocTypes | None = None
    quantity: Decimal


class MovementsQueryResponse(BaseModel):
    movements: list[MovementsResponse] = []
    date_from: date | None = None
    date_to: date | None = None
    limit: int
    offset: int
    total: int


class ProductsStock(BaseModel):
    product_sku: str
    site_name: str
    balance: Decimal
    average_consume: Decimal
    stock_in_days: int
    expiry_date: date | None = None

    """
    Реализовать GET /api/stock — текущие остатки по позициям и объектам. Остаток
    вычисляется из движений и партий, а не хранится отдельным изменяемым полем. В
    ответе: остаток, средний расход в день за 90 дней, запас в днях и ближайший срок
    годности. balance, average daily consumption over 90 days, stock in days, and nearest expiration date
    """


class ProductSKUStock(BaseModel):
    site_name: str
    batch_date: date
    batch_number: str
    expiry_date: date
    balance: Decimal
    price: Decimal

    """
    Реализовать GET /api/stock/{sku} — детализация по позиции: остатки по объектам и по
    партиям со сроками годности, ценами поступления и номерами накладных.
    """


class ProductsForecastRequest(BaseModel):
    product_sku: str = Field(max_length=20)
    site_name: str = Field(max_length=30)
    days: int = Field(90, ge=1, le=200)
    days_safety_stock: int = Field(90, ge=1, le=200)

    """
    Реализовать POST /api/forecast — расчёт потребности: на вход SKU, объект, горизонт в
    днях или месяцах и страховой запас в днях; на выход прогнозный расход, текущий
    остаток, поставки в пути, страховой запас, точка заказа, рекомендуемый объём закупки,
    ориентировочная стоимость, рекомендуемая дата заказа и блок explanation с исходными
    данными, формулами и допущениями. Рекомендуемый объём округляется вверх до
    кратности упаковки и минимальной партии поставщика.
    """


class ForecastExplanation(BaseModel):
    data_used: list[Decimal]
    formulas: list[Decimal]
    assumptions: list[str]
    as_of: date


class Warnings(BaseModel):
    level: str
    message: str


class ProductsForecastResponse(BaseModel):
    product_sku: str
    name: str
    unit: str
    location: str
    period: dict[str, date | int]
    avg_daily_consumption: Decimal
    forecast_demand: Decimal
    current_stock: Decimal
    incoming_qty: Decimal
    safety_stock: Decimal
    reorder_point: Decimal
    recommended_purchase_qty: Decimal
    unit_price: Decimal
    estimated_cost: Decimal
    recommended_order_date: date
    stockout_date: date
    explanation: ForecastExplanation
    warnings: list[Warnings]


z = {
    "sku": "OIL-001",
    "name": "Массажное масло базовое (миндаль)",
    "unit": "л",
    "location": "MS-01",
    "period": {"from": "2026-10-01", "to": "2026-12-31", "days": 92},
    "avg_daily_consumption": 1.362,
    "forecast_demand": 125.3,
    "current_stock": 50.39,
    "incoming_qty": 20.0,
    "safety_stock": 19.07,
    "reorder_point": 28.6,
    "recommended_purchase_qty": 75.0,
    "unit_price": 1259.05,
    "estimated_cost": 94428.75,
    "recommended_order_date": "2026-10-25",
    "stockout_date": "2026-11-01",
    "explanation": {
        "data_used": [
            "Движение товара за последние 90 дней",
            "Остатки по партиям на 15.09.2026",
            "Открытые заказы к поставке в периоде"
        ],
        "formulas": [
            "средний расход/день = расход за 90 дн. ÷ 90",
            "прогноз = средний расход/день × дней в периоде",
            "объём = прогноз + страховой запас − остаток − поставки в пути"
        ],
        "assumptions": ["Цена принята на уровне последней закупки."],
        "as_of": "2026-09-15"
    },
    "warnings": [
        {"level": "warning", "message": "Остаток ниже точки заказа"}
    ]
}

class AlertsResponse(BaseModel):
    warnings: list[Warnings]

    """
    Реализовать GET /api/alerts — предупреждения по складу: 
    - риск дефицита (запаса меньше, чем срок поставки), 
    - приближение срока годности партии и отсутствие движения по позиции. 
    У каждого предупреждения — уровень важности и показатели, на которых оно построено.
    """