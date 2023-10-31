from typing import Optional, Union

from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy_file import File, ImageField
from sqlalchemy_file.validators import SizeValidator
from sqlmodel import Field, SQLModel

from fastapi import File as FormFile
from fastapi import Form, UploadFile

from .db import engine


class Thumbnail(BaseModel):
    path: str
    url: Optional[str]


class FileInfo(BaseModel):
    filename: str
    content_type: str
    path: str
    url: Optional[str]
    thumbnail: Thumbnail


class CategoryBase(SQLModel):
    id: Optional[int] = Field(None, primary_key=True)
    name: str = Field(None, min_length=3, max_length=100)


class Category(CategoryBase, table=True):
    image: Union[File, UploadFile, None] = Field(
        sa_column=Column(
            ImageField(
                upload_storage="category",
                thumbnail_size=(200, 200),
                validators=[SizeValidator(max_size="1M")],
            )
        )
    )


class CategoryOut(CategoryBase):
    image: Optional[FileInfo]


def category_form(
    name: str = Form(..., min_length=3),
    image: Optional[UploadFile] = FormFile(None),
) -> Category:
    return Category(name=name, image=image)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
