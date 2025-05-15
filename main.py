from app import app  # noqa: F401
import os

if __name__ == "__main__":
    # Aumenta i timeout per Werkzeug in modalità di sviluppo
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    app.run(host='0.0.0.0', 
            port=5000, 
            debug=True, 
            threaded=True)
