from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependency import get_db
from app.schemas import (
    MovementsPost,
    MovementsPostResponse,
    MovementsRequest,
    MovementsQueryResponse,
    ProductsStock, ProductSKUStock, ProductsForecastRequest, ProductsForecastResponse, AlertsResponse,
)
from app.service import movements as movements_service

from app.enums import DocTypes

router = APIRouter()

"""
Реализовать эндпоинт POST /api/movements: принимает запись движения товара (дата,
SKU, объект, тип операции receipt / consume / writeoff / return / correction, количество,
партия, номер документа), сохраняет её в БД и возвращает идентификатор записи и
пересчитанный остаток по позиции и объекту.
"""

@router.post(
    "/movements",
    response_model=MovementsPostResponse,
    summary="Запись движения товара"
)
def add_movements(
        movement: Annotated[MovementsPost, Query()],
        db: Session = Depends(get_db)
):
    res = None

    match movement.document_type:
        case DocTypes.RECEIPT:
            res = movements_service.post_receipt(db, movement)
        case DocTypes.CONSUME:
            res = movements_service.post_consume(db, movement)
        case DocTypes.WRITEOFF:
            res = movements_service.post_writeoff(db, movement)
        case DocTypes.RETURN:
            res = movements_service.post_return(db, movement)
        case DocTypes.CORRECTION:
            res = movements_service.post_correction(db, movement)

    return res

"""
GET /api/movements — список движений с фильтрами по SKU, объекту, типу
операции и периоду и с пагинацией (limit, offset, total).
"""

@router.get(
    "/movements",
    response_model=MovementsQueryResponse,
    summary="Cписок движений товаров с фильтрами по SKU, складу, типу операции и периоду"
)
def get_movements(
        query_params: Annotated[MovementsRequest, Query()],
        db: Session = Depends(get_db)
):
    return movements_service.get_movements(db, query_params)

"""
Реализовать GET /api/stock — текущие остатки по позициям и объектам. Остаток
вычисляется из движений и партий, а не хранится отдельным изменяемым полем. В
ответе: остаток, средний расход в день за 90 дней, запас в днях и ближайший срок
годности.
"""

@router.get(
    "/stock",
    response_model=list[ProductsStock],
    summary="Текущие остатки по товарам и складам"
)
def get_stock(
        db: Session = Depends(get_db)
):
    return movements_service.get_stock(db)

"""
Реализовать GET /api/stock/{sku} — детализация по позиции: остатки по объектам и по
партиям со сроками годности, ценами поступления и номерами накладных.
"""

@router.get(
    "/stock/{sku}",
    response_model=list[ProductSKUStock],
    summary="Текущие остатки товара по складам и партиям"
)
def get_stock_by_sku(
        sku: str,
        db: Session = Depends(get_db),
):
    return movements_service.get_stock_by_sku(db, sku)

"""
Реализовать POST /api/forecast — расчёт потребности: на вход SKU, объект, горизонт в
днях или месяцах и страховой запас в днях; на выход прогнозный расход, текущий
остаток, поставки в пути, страховой запас, точка заказа, рекомендуемый объём закупки,
ориентировочная стоимость, рекомендуемая дата заказа и блок explanation с исходными
данными, формулами и допущениями. Рекомендуемый объём округляется вверх до
кратности упаковки и минимальной партии поставщика.
"""

@router.get(
    "/forecast",
    response_model=ProductsForecastResponse,
    summary="Прогноз потребности в товарах"
)
def get_forecast(
        query_params: Annotated[ProductsForecastRequest, Query()],
        db: Session = Depends(get_db),
):
    return movements_service.get_forecast(db, query_params)

"""
    Реализовать GET /api/alerts — предупреждения по складу: 
    - риск дефицита (запаса меньше, чем срок поставки), 
    - приближение срока годности партии и отсутствие движения по позиции. 
    У каждого предупреждения — уровень важности и показатели, на которых оно построено.
"""

@router.get(
    "/alerts",
    response_model=AlertsResponse,
    summary="Предупреждения по складу"
)
def get_forecast(
        db: Session = Depends(get_db),
):
    return movements_service.get_alerts(db)


