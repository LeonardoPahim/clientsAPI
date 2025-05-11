import uuid
from sqlalchemy import Column, String, Table, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

client_favorite_products_table = Table(
    'client_favorite_products', Base.metadata,
    Column('client_id', UUID(as_uuid=True), ForeignKey('clients.id', ondelete="CASCADE"), primary_key=True),
    Column('product_ref_id', Integer, ForeignKey('products_ref.id', ondelete="CASCADE"), primary_key=True)
)

class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

    favorite_products = relationship(
        "Product",
        secondary=client_favorite_products_table,
        collection_class=set,
        lazy="selectin"
    )