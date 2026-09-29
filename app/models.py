import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Date, Enum, Numeric, String, ForeignKey, UniqueConstraint

from app.database import Base
from app.enums import DocTypes


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    sku: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    batches: Mapped[list["Batch"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    batch_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )

    product: Mapped["Product"] = relationship(
        back_populates="batches"
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("product_id", "number", name="uq_batches_product_id_number"),
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    document_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
    )

    document_type: Mapped[DocTypes] = mapped_column(
        Enum(DocTypes, name="document_type_enum"),
        nullable=False,
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="CASCADE"),
        nullable=False,
    )

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="RESTRICT"),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )

    batch: Mapped["Batch"] = relationship(
        back_populates="documents"
    )

    site: Mapped["Site"] = relationship(
        back_populates="documents"
    )


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="site",
        cascade="save-update, merge",
        passive_deletes=True,
    )

