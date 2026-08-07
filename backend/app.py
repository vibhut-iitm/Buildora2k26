import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.verify import verify_bp
from routes.generate import generate_bp
from routes.qr_generator import qr_bp
from routes.upload_csv import upload_bp
from config import FRONTEND_URL
from routes.admin import admin_bp

FRONTEND_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

app = Flask(__name__, static_folder=FRONTEND_FOLDER, static_url_path="")
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Register API Blueprints
app.register_blueprint(verify_bp)
app.register_blueprint(generate_bp)
app.register_blueprint(qr_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(admin_bp)

# Static Frontend Route Handlers
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_FOLDER, "index.html")

@app.route("/login")
def serve_login():
    if os.path.exists(os.path.join(FRONTEND_FOLDER, "login.html")):
        return send_from_directory(FRONTEND_FOLDER, "login.html")
    return send_from_directory(FRONTEND_FOLDER, "index.html")

@app.route("/dashboard")
def serve_dashboard():
    if os.path.exists(os.path.join(FRONTEND_FOLDER, "dashboard.html")):
        return send_from_directory(FRONTEND_FOLDER, "dashboard.html")
    return send_from_directory(FRONTEND_FOLDER, "index.html")

@app.route("/scan")
def serve_scan():
    if os.path.exists(os.path.join(FRONTEND_FOLDER, "scan.html")):
        return send_from_directory(FRONTEND_FOLDER, "scan.html")
    return send_from_directory(FRONTEND_FOLDER, "index.html")

@app.errorhandler(404)
def handle_404(e):
    # Check if request path matches a static file in frontend directory
    from flask import request
    req_path = request.path.lstrip("/")
    target = os.path.join(FRONTEND_FOLDER, req_path)
    if req_path and os.path.isfile(target):
        return send_from_directory(FRONTEND_FOLDER, req_path)
    if req_path and os.path.isfile(f"{target}.html"):
        return send_from_directory(FRONTEND_FOLDER, f"{req_path}.html")
    return send_from_directory(FRONTEND_FOLDER, "index.html")

if __name__ == "__main__":
    app.run(debug=True, port=8000)
