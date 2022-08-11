from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_file import FileField
from sqlalchemy_file.validators import ContentTypeValidator, SizeValidator

Base = declarative_base()


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(
        FileField(
            validators=[
                SizeValidator("500k"),
                ContentTypeValidator(["text/plain", "text/csv"]),
            ]
        )
    )
