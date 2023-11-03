from typing import List

from libcloud.storage.types import (
    ObjectDoesNotExistError,
)
from sqlalchemy_file.exceptions import ValidationError
from sqlalchemy_file.helpers import LOCAL_STORAGE_DRIVER_NAME
from sqlalchemy_file.storage import StorageManager
from sqlmodel import Session, select
from starlette.responses import (
    FileResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)

from fastapi import Depends, FastAPI, Path

from .depends import get_session
from .models import Category, CategoryOut, category_form, init_db
from .storage import init_storage

app = FastAPI(
    title="Azure Blob storage Example",
    on_startup=[init_db, init_storage],
    debug=True,
)


@app.get("/categories", response_model=List[CategoryOut])
async def get_all(session: Session = Depends(get_session)):
    return session.execute(select(Category)).scalars().all()


@app.get("/categories/{id}", response_model=CategoryOut)
async def get_one(id: int = Path(...), session: Session = Depends(get_session)):
    category = session.get(Category, id)
    if category is not None:
        return category
    return JSONResponse({"detail": "Not found"}, status_code=404)


@app.post("/categories", response_model=CategoryOut)
async def create_new(
    category: Category = Depends(category_form), session: Session = Depends(get_session)
):
    try:
        session.add(category)
        session.commit()
        session.refresh(category)
        return category
    except ValidationError as e:
        return JSONResponse({"error": {"key": e.key, "msg": e.msg}}, status_code=422)


@app.get("/medias/{storage}/{file_id}", response_class=FileResponse)
async def serve_files(storage: str = Path(...), file_id: str = Path(...)):
    try:
        file = StorageManager.get_file(f"{storage}/{file_id}")
        if file.object.driver.name == LOCAL_STORAGE_DRIVER_NAME:
            """If file is stored in local storage, just return a
            FileResponse with the fill full path."""
            return FileResponse(
                file.get_cdn_url(), media_type=file.content_type, filename=file.filename
            )
        elif file.get_cdn_url() is not None:  # noqa: RET505
            """If file has public url, redirect to this url"""
            return RedirectResponse(file.get_cdn_url())
        else:
            """Otherwise, return a streaming response"""
            return StreamingResponse(
                file.object.as_stream(),
                media_type=file.content_type,
                headers={"Content-Disposition": f"attachment;filename={file.filename}"},
            )
    except ObjectDoesNotExistError:
        return JSONResponse({"detail": "Not found"}, status_code=404)
