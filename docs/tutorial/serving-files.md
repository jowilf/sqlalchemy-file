# Serving Files

## With FastApi
```Python
@app.get("/medias/{storage}/{file_id}", response_class=FileResponse)
def serving_files(storage: str = Path(...), file_id: str = Path(...)):
    try:
        file = StorageManager.get_file(f"{storage}/{file_id}")
        if isinstance(file.object.driver, LocalStorageDriver):
            """If file is stored in local storage, just return a
            FileResponse with the fill full path."""
            return FileResponse(
                file.get_cdn_url(), media_type=file.content_type, filename=file.filename
            )
        elif file.get_cdn_url() is not None:
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
```
See Full example [here]()

## With Flask
```Python
@app.route("/medias/<storage>/<file_id>")
def serving_files(storage, file_id):
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
        elif file.get_cdn_url() is not None:
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
```
See Full example [here]()
