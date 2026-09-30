from sqlalchemy import select

from app.models import Product, Batch
from app.repository import movements as movements_repository


def test_post_receipts(db_session, client, receipt_movement):
    product = (
        db_session.query(Product)
        .filter(Product.sku == "SPA-0001")
        .first()
    )

    # batch = movements_repository.get_batch_by_number(
    #     db_session,
    #     product_id=product.id,
    #     batch_number="B-0002",
    # )

    # print("REPOSITORY BATCH:", batch)

    # batch = db_session.query(Batch).filter(
    #     Batch.number == "B-0002"
    # ).first()

    # query = select(Batch).where(
    #     Batch.product_id == product.id,
    #     Batch.number == "B-0002",
    # )
    #
    # batch = db_session.scalars(query).first()

    batch = db_session.scalars(
        select(Batch).where(
            Batch.product_id == product.id
        )
    ).first()

    print("BATCH:", batch)

    print(Batch.__table__.c.product_id.type)
    print(type(Batch.__table__.c.product_id.type))

    print(Product.__table__.c.id.type)
    print(type(Product.__table__.c.id.type))

    query = select(Batch).where(
        Batch.product_id == product.id
    )

    print(query)
    print(query.compile().params)

    # print("Product.id:", product.id, type(product.id))
    # print("Batch.product_id:", batch.product_id, type(batch.product_id))
    # print("Equal:", batch.product_id == product.id)
    #
    # print("Product.id column:", Product.__table__.c.id.type)
    # print("Batch.product_id column:", Batch.__table__.c.product_id.type)
    #
    # print(
    #     db_session.scalars(
    #         select(Batch).where(Batch.product_id == product.id)
    #     ).all()
    # )

    response = client.post(
        "/api/movements",
        params=receipt_movement.model_dump(),
    )

    # assert response.status_code == 200, response.text

