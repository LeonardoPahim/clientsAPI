from sqlalchemy import Column, Integer
from app.core.database import Base

class Product(Base):
    __tablename__ = "products_ref"
    id = Column(Integer, primary_key=True, index=True, autoincrement=False)