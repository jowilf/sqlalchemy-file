from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_file import FileField

Base = declarative_base()


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField)


engine = create_engine(
    "sqlite:///example.db", connect_args={"check_same_thread": False}
)
Base.metadata.create_all(engine)
