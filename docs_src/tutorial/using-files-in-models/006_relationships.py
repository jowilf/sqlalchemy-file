from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_file import FileField

Base = declarative_base()


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField)

    article_id = Column(Integer, ForeignKey("article.id"))


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, autoincrement=True, primary_key=True)
    title = Column(String(100), unique=True)

    attachments = relationship(Attachment, cascade="all, delete-orphan")
