from flask import Blueprint, send_file, request
import qrcode
import zipfile
import io
import os
from PIL import Image, ImageDraw
from db import db

qr_bp = Blueprint("qr", __name__)

TEMPLATE_PNG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "template", "template.png"))
TEMPLATE_JPEG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "template", "template.jpeg"))

_cached_template = None
_cached_box = None

def get_resources():
    global _cached_template, _cached_box
    
    if _cached_template is None:
        if os.path.exists(TEMPLATE_PNG_PATH):
            _cached_template = Image.open(TEMPLATE_PNG_PATH).convert("RGB")
            _cached_box = (272, 920, 752, 1400) # Centered white frame box for 1024x1536
        elif os.path.exists(TEMPLATE_JPEG_PATH):
            _cached_template = Image.open(TEMPLATE_JPEG_PATH).convert("RGB")
            _cached_box = (395, 939, 907, 1451)
        else:
            raise FileNotFoundError("Buildora template image not found.")
        
    return _cached_template, _cached_box

def make_gatepass_turbo(token: str, template_img, box) -> bytes:
    img = template_img.copy()
    box_x, box_y = box[0], box[1]
    box_w = box[2] - box[0]
    box_h = box[3] - box[1]

    # Maximize QR code size to fill white frame nicely (450px inside 480px box)
    qr_size = 450
    qr_img = qrcode.make(token, border=1).convert("RGB")
    qr_final = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)

    paste_x = box_x + (box_w - qr_size) // 2
    paste_y = box_y + (box_h - qr_size) // 2
    img.paste(qr_final, (paste_x, paste_y))

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85, optimize=True)
    return out.getvalue()

@qr_bp.route("/qr-codes", methods=["GET"])
def generate_qr():
    try:
        participants = db.fetch_all()
        if not participants: return "No participants found in database.", 404

        participants.sort(key=lambda x: (str(x.get("branch", "General")).lower(), str(x.get("participant_name", x.get("student_name", ""))).lower()))

        template_img, box = get_resources()
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            from concurrent.futures import ThreadPoolExecutor
            
            def process_participant(p):
                token = p.get("token")
                name = p.get("participant_name") or p.get("student_name")
                branch = p.get("branch") or p.get("Branch", "Buildora")
                if not token or not name: return None
                
                pass_bytes = make_gatepass_turbo(token, template_img, box)
                
                safe_branch = "".join(c if c.isalnum() or c in " _-" else "_" for c in str(branch)).strip().lower().replace(" ", "_")
                safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip().lower().replace(" ", "_")
                
                return f"buildora_passes/{safe_branch}/{safe_name}.jpg", pass_bytes

            with ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(process_participant, participants)
                for res in results:
                    if res:
                        zf.writestr(res[0], res[1])

        memory_file.seek(0)
        response = send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='buildora_2026_passes.zip')
        response.headers['Content-Length'] = memory_file.getbuffer().nbytes
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@qr_bp.route("/qr-single", methods=["GET"])
def generate_single_qr():
    token = request.args.get("token")
    if not token: return "Missing token", 400

    try:
        template_img, box = get_resources()
        pass_bytes = make_gatepass_turbo(token, template_img, box)
        return send_file(
            io.BytesIO(pass_bytes),
            mimetype='image/png',
            as_attachment=True,
            download_name=f"buildora_pass_{token}.png"
        )
    except Exception as e:
        return str(e), 500