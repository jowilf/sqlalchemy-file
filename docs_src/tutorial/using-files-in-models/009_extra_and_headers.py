from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy_file.types import FileField

Base = declarative_base()


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(
        FileField(
            extra={
                "acl": "private",
                "dummy_key": "dummy_value",
                "meta_data": {"key1": "value1", "key2": "value2"},
            },
            headers={
                "Access-Control-Allow-Origin": "http://test.com",
                "Custom-Key": "xxxxxxx",
            },
        )
    )
