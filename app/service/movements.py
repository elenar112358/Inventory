from fastapi import HTTPException
from sqlalchemy.orm import Session

from uuid import UUID
from decimal import Decimal

from app.schemas import (
    MovementsPost,
    MovementsPostResponse,
    MovementsRequest,
    MovementsResponse,
    ProductsStock,
    ProductSKUStock,
    ProductsForecastRequest,
    ProductsForecastResponse,
    AlertsResponse,
)

from app.repository import movements as movements_repository


def get_movements_objects(db: Session, movement: MovementsPost):
    product = movements_repository.get_product_by_sku(
        db,
        product_sku=movement.product_sku,
    )
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f'Товар с sku = "{movement.product_sku}" не найден'
        )

    site = movements_repository.get_site_by_name(
        db,
        site_name=movement.site_name,
    )
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f'Склад "{movement.site_name}" не найден'
        )

    if movement.batch_number is None:
        return product, site

    batch = movements_repository.get_batch_by_number(
        db,
        product_id=product.id,
        batch_number=movement.batch_number,
    )
    if not batch:
        raise HTTPException(
            status_code=404,
            detail=f'Партия "{movement.batch_number}" для товара с sku = "{movement.product_sku}" не найдена'
        )

    return product, site, batch

def post_receipt(db: Session, movement: MovementsPost) -> MovementsPostResponse:
    product, site, batch = get_movements_objects(db, movement)

    document = movements_repository.post_receipt(
        db,
        document_date=movement.document_date,
        number=movement.document_number,
        document_type=movement.document_type,
        batch_id=batch.id,
        site_id=site.id,
        quantity=movement.quantity,
    )

    product_quantity = movements_repository.get_product_quantity(
        db,
        product_id=product.id,
    )

    site_quantity = movements_repository.get_product_quantity_by_site(
        db,
        product_id=product.id,
        site_id=site.id,
    )

    return MovementsPostResponse(
        list_id=[document.id],
        product_quantity=product_quantity,
        site_quantity=site_quantity,
    )

def post_consume(db: Session, movement: MovementsPost) -> MovementsPostResponse:
    product, site = get_movements_objects(db, movement)

    site_quantity = movements_repository.get_product_quantity_by_site(
        db,
        product_id=product.id,
        site_id=site.id,
    )

    if site_quantity < movement.quantity:
        raise HTTPException(
            status_code=422,
            detail=(
                f'Для товара с sku = "{movement.product_sku}" требуется '
                f'{movement.quantity}{product.unit}, доступно {site_quantity}{product.unit}'
            ),
        )

    batches: dict[UUID, Decimal] = movements_repository.get_FEFO_batches(
        db,
        product_id=product.id,
        site_id=site.id,
        quantity=movement.quantity,
    )

    docs_id = movements_repository.post_consume(
        db,
        document_date=movement.document_date,
        number=movement.document_number,
        document_type=movement.document_type,
        batches=batches,
        site_id=site.id,
    )

    product_quantity = movements_repository.get_product_quantity(
        db,
        product_id=product.id,
    )

    site_quantity = movements_repository.get_product_quantity_by_site(
        db,
        product_id=product.id,
        site_id=site.id,
    )

    return MovementsPostResponse(
        list_id=docs_id,
        product_quantity=product_quantity,
        site_quantity=site_quantity,
    )

def post_writeoff(db: Session, movement: MovementsPost) -> MovementsPostResponse:
    product, site, batch = get_movements_objects(db, movement)

    batch_quantity = movements_repository.get_batch_quantity_by_site(
        db,
        product_id=product.id,
        batch_id=batch.id,
        site_id=site.id,
    )

    if batch_quantity < movement.quantity:
        raise HTTPException(
            status_code=422,
            detail=(
                f'Для товара с sku = "{movement.product_sku}" партии "{batch.number}" требуется '
                f'{movement.quantity}{product.unit}, доступно {batch_quantity}{product.unit}'
            ),
        )

    docs_id = movements_repository.post_consume(
        db,
        document_date=movement.document_date,
        number=movement.document_number,
        document_type=movement.document_type,
        batches={batch.id: movement.quantity},
        site_id=site.id,
    )

    product_quantity = movements_repository.get_product_quantity(
        db,
        product_id=product.id,
    )

    site_quantity = movements_repository.get_product_quantity_by_site(
        db,
        product_id=product.id,
        site_id=site.id,
    )

    return MovementsPostResponse(
        list_id=docs_id,
        product_quantity=product_quantity,
        site_quantity=site_quantity,
    )

def post_return(db: Session, movement: MovementsPost) -> MovementsPostResponse:
    product, site, batch = get_movements_objects(db, movement)

    document = movements_repository.post_receipt(
        db,
        document_date=movement.document_date,
        number=movement.document_number,
        document_type=movement.document_type,
        batch_id=batch.id,
        site_id=site.id,
        quantity=movement.quantity,
    )

    product_quantity = movements_repository.get_product_quantity(
        db,
        product_id=product.id,
    )

    site_quantity = movements_repository.get_product_quantity_by_site(
        db,
        product_id=product.id,
        site_id=site.id,
    )

    return MovementsPostResponse(
        list_id=[document.id],
        product_quantity=product_quantity,
        site_quantity=site_quantity,
    )

def post_correction(db: Session, movement: MovementsPost) -> MovementsPostResponse:
    product, site, batch = get_movements_objects(db, movement)

    batch_quantity = movements_repository.get_batch_quantity_by_site(
        db,
        product_id=product.id,
        batch_id=batch.id,
        site_id=site.id,
    )

    docs_id = []

    if batch_quantity < movement.quantity:
        document = movements_repository.post_receipt(
            db,
            document_date=movement.document_date,
            number=movement.document_number,
            document_type=movement.document_type,
            batch_id=batch.id,
            site_id=site.id,
            quantity=movement.quantity - batch_quantity,
        )
        docs_id = [document.id]

    elif batch_quantity > movement.quantity:
        docs_id = movements_repository.post_consume(
            db,
            document_date=movement.document_date,
            number=movement.document_number,
            document_type=movement.document_type,
            batches={batch.id: batch_quantity - movement.quantity},
            site_id=site.id,
        )

    product_quantity = movements_repository.get_product_quantity(
        db,
        product_id=product.id,
    )

    site_quantity = movements_repository.get_product_quantity_by_site(
        db,
        product_id=product.id,
        site_id=site.id,
    )

    return MovementsPostResponse(
        list_id=docs_id,
        product_quantity=product_quantity,
        site_quantity=site_quantity,
    )

def get_movements(db: Session, query_params: MovementsRequest) -> MovementsResponse:
    ...

def get_stock(db: Session) -> ProductsStock:
    ...

def get_stock_by_sku(db: Session, sku: str) -> ProductSKUStock:
    ...

def get_forecast(db: Session, query_params: ProductsForecastRequest) -> ProductsForecastResponse:
    ...

def get_alerts(db: Session) -> AlertsResponse:
    ...


