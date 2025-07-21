from archives.utils import generate_qr_image

def test_generate_qr_image_returns_file_like_object():
    qr_file = generate_qr_image("https://example.com")
    assert hasattr(qr_file, "read")

def test_generate_qr_image_output_is_png():
    qr_file = generate_qr_image("https://example.org")
    data = qr_file.read()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
