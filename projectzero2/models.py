from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, String

Base = declarative_base()


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, index=True, nullable=False)
    titulo = Column(Text)
    precio = Column(Text)
    stock = Column(Text)
    raw = Column(Text)
