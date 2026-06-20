"""
security.py

Minimal but real input-validation guardrails for the image upload path.
This is intentionally simple -- no API keys or secrets are needed for this
pipeline since it runs entirely on local/open models and local JSON data --
but the upload path is still the main attack surface, so it gets validated.
"""

from io import BytesIO

from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class InvalidImageError(ValueError):
    pass


def validate_and_load_image(raw_bytes: bytes) -> Image.Image:
    """
    Validate an uploaded image's size and format, and return a decoded PIL
    image. Raises InvalidImageError on any failure -- callers should catch
    this and return a clean error to the user rather than a stack trace.
    """
    if not raw_bytes:
        raise InvalidImageError("No image data received.")

    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise InvalidImageError(
            f"Image is too large ({len(raw_bytes) / 1_000_000:.1f} MB). "
            f"Maximum allowed is {MAX_UPLOAD_BYTES / 1_000_000:.0f} MB."
        )

    try:
        image = Image.open(BytesIO(raw_bytes))
        image.verify()  # checks for corrupt/truncated data
        # re-open after verify() since verify() closes the file pointer
        image = Image.open(BytesIO(raw_bytes))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError("File could not be read as a valid image.") from exc

    if image.format not in ALLOWED_FORMATS:
        raise InvalidImageError(
            f"Unsupported image format '{image.format}'. Allowed: {', '.join(ALLOWED_FORMATS)}."
        )

    return image.convert("RGB")
