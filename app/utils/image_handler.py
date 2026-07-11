import os
import uuid
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file_obj, subfolder: str, max_size: tuple = (1200, 800)) -> str | None:
    """Save and optionally resize an uploaded image. Returns the filename."""
    if not file_obj or not allowed_file(file_obj.filename):
        return None

    ext = file_obj.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(upload_path, exist_ok=True)
    filepath = os.path.join(upload_path, filename)

    img = Image.open(file_obj)
    img.thumbnail(max_size, Image.LANCZOS)
    img.save(filepath, optimize=True, quality=85)

    return f"uploads/{subfolder}/{filename}"


def delete_image(filepath: str):
    if filepath and not filepath.endswith("default_avatar.png"):
        full = os.path.join(current_app.config["UPLOAD_FOLDER"], "..", filepath)
        if os.path.exists(full):
            os.remove(full)
