from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_file import ImageField
from sqlalchemy_file.processors import ThumbnailGenerator

Base = declarative_base()


class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, autoincrement=True, primary_key=True)
    title = Column(String(100), unique=True)
    cover = Column(ImageField(processors=[ThumbnailGenerator()]))
