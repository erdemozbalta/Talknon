import os
from app import create_app
from app.extensions import socketio

application = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = application.config.get('DEBUG', False)
    print(f"\n[*] Talknon baslatiliyor (Port: {port}, Debug: {debug})...")
    print(f"[*] Tarayicida acin: http://localhost:{port}")
    print("[*] Durdurmak icin: Ctrl+C\n")
    socketio.run(application, host='0.0.0.0', port=port, debug=debug)
