import os
import qrcode
from flask import current_app

def generate_qr_code(cafe_slug, base_url=None):
\
\
\
\
\
\
\
\
\

    if not base_url:
        base_url = 'http://localhost:5000'

    url = f"{base_url}/cafe/{cafe_slug}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1a1a2e", back_color="white")

    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
    qr_dir = os.path.join(upload_folder, 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)

    filename = f"qr_{cafe_slug}.png"
    filepath = os.path.join(qr_dir, filename)
    img.save(filepath)

    relative_path = f"uploads/qrcodes/{filename}"
    return relative_path
