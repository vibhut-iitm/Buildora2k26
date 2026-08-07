import sys
import os
import importlib.util

backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

app_path = os.path.join(backend_dir, "app.py")
spec = importlib.util.spec_from_file_location("backend_app_module", app_path)
backend_app_module = importlib.util.module_from_spec(spec)
sys.modules["backend_app_module"] = backend_app_module
spec.loader.exec_module(backend_app_module)

app = backend_app_module.app

if __name__ == "__main__":
    app.run()
