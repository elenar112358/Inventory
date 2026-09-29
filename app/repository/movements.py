from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, exists, func, case
from sqlalchemy.orm import Session

from app.enums import DocTypes
from app.models import Product, Site, Batch, Document
from app.schemas import MovementsRequest, MovementsResponse, ProductsAverageStock, ProductSKUStock


def get_product_by_sku(db: Session, product_sku: str) -> Product | None:
    query = select(Product).where(Product.sku == product_sku)

    return db.scalars(query).first()

def get_site_by_name(db: Session, site_name: str) -> Site | None:
    query = select(Site).where(Site.name == site_name)

    return db.scalars(query).first()

def get_batch_by_number(db: Session, product_id: UUID, batch_number: str) -> Batch | None:
    query = select(Batch).where(
        Batch.product_id == product_id,
        Batch.number == batch_number,
    )

    return db.scalars(query).first()

def document_exists(db: Session, number: str) -> bool:
    query = select(exists().where(Document.number == number))

    return db.scalar(query)

def post_receipt(
        db: Session,
        document_date: date,
        number: str,
        document_type: DocTypes,
        batch_id: UUID,
        site_id: UUID,
        quantity: Decimal,
    ) -> Document:

    document = Document(
        document_date=document_date,
        number=number,
        document_type=document_type,
        batch_id=batch_id,
        site_id=site_id,
        quantity=quantity,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document

def get_product_quantity(db: Session, product_id: UUID) -> Decimal:
    query = (
        select(func.coalesce(func.sum(Document.quantity), 0))
        .join(Batch, Document.batch_id == Batch.id)
        .where(Batch.product_id == product_id)
    )

    return Decimal(db.scalar(query))

def get_product_quantity_by_site(db: Session, product_id: UUID, site_id: UUID) -> Decimal:
    query = (
        select(func.coalesce(func.sum(Document.quantity), 0))
        .join(Batch, Document.batch_id == Batch.id)
        .where(
            Batch.product_id == product_id,
            Document.site_id == site_id,
        )
    )

    return Decimal(db.scalar(query))

def get_FEFO_batches(db: Session, product_id: UUID, site_id: UUID, quantity: Decimal) -> dict[UUID, Decimal]:
    query = (
        select(
            Batch.id,
            func.coalesce(func.sum(Document.quantity), 0).label("available_count"),
        )
        .join(Batch, Document.batch_id == Batch.id)
        .where(
            Batch.product_id == product_id,
            Document.site_id == site_id,
        )
        .group_by(Batch.id, Batch.expiry_date)
        .having(func.coalesce(func.sum(Document.quantity), 0) > 0)
        .order_by(Batch.expiry_date.asc().nulls_last())
    )

    remaining = quantity
    res: dict[UUID, Decimal] = {}

    for batch_id, available_count in db.execute(query):
        if remaining <= 0:
            break

        take = min(available_count, remaining)
        res[batch_id] = take
        remaining -= take

    return res

def post_consume(
        db: Session,
        document_date: date,
        number: str,
        document_type: DocTypes,
        batches: dict[UUID, Decimal],
        site_id: UUID,
    ) -> list[UUID]:

    list_id = []
    for batch_id, batch_quantity in batches.items():
        document = Document(
            document_date=document_date,
            number=number,
            document_type=document_type,
            batch_id=batch_id,
            site_id=site_id,
            quantity=-batch_quantity,
        )

        db.add(document)
        list_id.append(document.id)

    db.commit()

    return list_id

def get_batch_quantity_by_site(db: Session, batch_id: UUID, site_id: UUID) -> Decimal:
    query = (
        select(func.coalesce(func.sum(Document.quantity), 0))
        .join(Batch, Document.batch_id == Batch.id)
        .where(
            Batch.id == batch_id,
            Document.site_id == site_id,
        )
    )

    return Decimal(db.scalar(query))

def get_total_movements(db: Session, query_params: MovementsRequest) -> int:
    query = (
        select(func.count(Document.id))
        .select_from(Document)
        .join(Document.site)
        .join(Document.batch)
        .join(Batch.product)
    )

    if query_params.product_sku is not None:
        query = query.where(Product.sku == query_params.product_sku)

    if query_params.site_name is not None:
        query = query.where(Site.name == query_params.site_name)

    if query_params.document_type is not None:
        query = query.where(Document.document_type == query_params.document_type)

    if query_params.date_from is not None:
        query = query.where(Document.document_date >= query_params.date_from)

    if query_params.date_to is not None:
        query = query.where(Document.document_date <= query_params.date_to)

    return db.scalar(query) or 0

def get_movements(db: Session, query_params: MovementsRequest) -> list[MovementsResponse]:
    query = (
        select(
            Product.sku.label("product_sku"),
            Site.name.label("site_name"),
            Document.document_type.label("document_type"),
            Document.quantity.label("quantity"),
        )
        .join(Document.site)
        .join(Document.batch)
        .join(Batch.product)
    )

    if query_params.product_sku is not None:
        query = query.where(Product.sku == query_params.product_sku)

    if query_params.site_name is not None:
        query = query.where(Site.name == query_params.site_name)

    if query_params.document_type is not None:
        query = query.where(Document.document_type == query_params.document_type)

    if query_params.date_from is not None:
        query = query.where(Document.document_date >= query_params.date_from)

    if query_params.date_to is not None:
        query = query.where(Document.document_date <= query_params.date_to)

    query = (
        query
        .order_by(Document.document_date.asc(), Document.id.asc())
        .limit(query_params.limit)
        .offset(query_params.offset)
    )

    return [MovementsResponse(**document) for document in db.execute(query).mappings().all()]


def get_stock_balance(db: Session, average_date_ago: date) -> list[ProductsAverageStock]:
    ...

def get_product_stock_balance(db: Session, product_id: UUID) -> list[ProductSKUStock]:
    ...




