"""Tests for image magic byte validation and size enforcement."""

import base64

from app.services.image_utils import validate_and_decode_image


def test_valid_jpeg_magic_bytes():
    """Verify valid JPEG header validation."""
    # JPEG header \xff\xd8\xff\xe0
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100
    b64 = "data:image/jpeg;base64," + base64.b64encode(jpeg_bytes).decode("ascii")

    is_valid, mime, raw = validate_and_decode_image(b64)
    assert is_valid is True
    assert mime == "image/jpeg"
    assert raw == jpeg_bytes


def test_valid_png_magic_bytes():
    """Verify valid PNG header validation."""
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    b64 = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")

    is_valid, mime, raw = validate_and_decode_image(b64)
    assert is_valid is True
    assert mime == "image/png"


def test_spoofed_image_extension_rejected():
    """Verify file disguised as image is rejected if magic bytes do not match."""
    fake_exe = b"MZ\x90\x00" + b"\x00" * 50
    b64 = "data:image/jpeg;base64," + base64.b64encode(fake_exe).decode("ascii")

    is_valid, msg, raw = validate_and_decode_image(b64)
    assert is_valid is False
    assert "Unsupported image type" in msg


def test_oversized_image_rejected():
    """Verify images exceeding 300 KB are rejected."""
    oversized_bytes = b"\xff\xd8\xff\xe0" + (b"A" * 320_000)
    b64 = "data:image/jpeg;base64," + base64.b64encode(oversized_bytes).decode("ascii")

    is_valid, msg, raw = validate_and_decode_image(b64)
    assert is_valid is False
    assert "exceeds maximum size limit" in msg
