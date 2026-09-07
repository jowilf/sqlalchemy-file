import contextlib
import os

from flask_sqlalchemy import SQLAlchemy
from libcloud.storage.drivers.local import LocalStorageDriver
from libcloud.storage.providers import get_driver
from libcloud.storage.types import (
    ContainerAlreadyExistsError,
    ObjectDoesNotExistError,
    Provider,
)
from sqlalchemy_file import FileField, ImageField
from sqlalchemy_file.exceptions import ValidationError
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.validators import ContentTypeValidator, SizeValidator

from flask import Flask, abort, render_template, request, send_file

db = SQLAlchemy(engine_options={"echo": True})
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:////tmp/example.db?check_same_thread=False"
)
db.init_app(app)


class Book(db.Model):
    __tablename__ = "books"
    isbn = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    cover = db.Column(
        ImageField(
            upload_storage="images",
            thumbnail_size=(50, 50),
            validators=[SizeValidator("1M")],
        )
    )
    document = db.Column(
        FileField(
            upload_storage="documents",
            validators=[
                SizeValidator("5M"),
                ContentTypeValidator(
                    allowed_content_types=[
                        "application/pdf",
                        "application/msword",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ]
                ),
            ],
        )
    )


@app.route("/", methods=("GET", "POST"))
def index():
    error = None
    if request.method == "POST":
        try:
            book = Book(
                author=request.form["author"],
                title=request.form["title"],
            )
            if "cover" in request.files and request.files["cover"].filename != "":
                book.cover = request.files["cover"]
            if "document" in request.files and request.files["document"].filename != "":
                book.document = request.files["document"]
            db.session.add(book)
            db.session.commit()
        except ValidationError as err:
            error = err
            db.session.rollback()
    return render_template(
        "index.html", books=Book.query.all(), form=request.form, error=error
    )


@app.route("/medias/<storage>/<file_id>")
def serve_files(storage, file_id):
    try:
        file = StorageManager.get_file(f"{storage}/{file_id}")
        if isinstance(file.object.driver, LocalStorageDriver):
            """If file is stored in local storage, just return a
            FileResponse with the fill full path."""
            return send_file(
                file.get_cdn_url(),
                mimetype=file.content_type,
                download_name=file.filename,
            )
        elif file.get_cdn_url() is not None:  # noqa: RET505
            """If file has public url, redirect to this url"""
            return app.redirect(file.get_cdn_url())
        else:
            """Otherwise, return a streaming response"""
            return app.response_class(
                file.object.as_stream(),
                mimetype=file.content_type,
                headers={"Content-Disposition": f"attachment;filename={file.filename}"},
            )
    except ObjectDoesNotExistError:
        abort(404)


if __name__ == "__main__":
    os.makedirs("./upload_dir", 0o777, exist_ok=True)
    driver = get_driver(Provider.LOCAL)("./upload_dir")

    """
    Or with MinIO:

    cls = get_driver(Provider.MINIO)
    driver = cls("minioadmin", "minioadmin", secure=False, host="127.0.0.1", port=9000)
    """

    with contextlib.suppress(ContainerAlreadyExistsError):
        driver.create_container(container_name="images")

    with contextlib.suppress(ContainerAlreadyExistsError):
        driver.create_container(container_name="documents")

    StorageManager.add_storage("images", driver.get_container(container_name="images"))
    StorageManager.add_storage(
        "documents", driver.get_container(container_name="documents")
    )

    with app.app_context():
        db.create_all()
    app.run(debug=True)
