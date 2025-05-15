import os
import logging
import uuid
import zipfile
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from werkzeug.utils import secure_filename
from utils import process_zip_file, process_zip_file_async, get_process_status, cleanup_temp_files, format_file_size

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Configurazione per file di grandi dimensioni
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10 GB
app.config['UPLOAD_TIMEOUT'] = 3600  # 1 ora in secondi

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = '/tmp/zip_processor'
ALLOWED_EXTENSIONS = {'zip'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Clean any leftover temporary files
    cleanup_temp_files()
    return render_template('index_3d.html')

@app.route('/old')
def old_index():
    """Versione precedente della home page"""
    return render_template('index.html')

@app.route('/download-app')
def download_app():
    """Pagina 3D per il download dell'applicazione"""
    return render_template('download.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check if a file was included in the request
        if 'file' not in request.files:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'No file part'}), 400
            flash('No file part', 'danger')
            return redirect(url_for('index'))
        
        file = request.files['file']
        
        # Check if the user submitted an empty form
        if not file or not file.filename:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'No file selected'}), 400
            flash('No file selected', 'danger')
            return redirect(url_for('index'))
        
        # Check if the file is allowed
        if allowed_file(file.filename):
            # Generate a unique session ID for this upload
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            
            # Create a unique folder for this upload session
            session_folder = os.path.join(UPLOAD_FOLDER, session_id)
            os.makedirs(session_folder, exist_ok=True)
            
            # Save the uploaded file
            filename = secure_filename(file.filename)
            file_path = os.path.join(session_folder, filename)
            
            try:
                # Salvataggio del file con gestione degli errori migliorata
                try:
                    file.save(file_path)
                except Exception as save_error:
                    logger.error(f"Error saving uploaded file: {save_error}")
                    error_msg = f"Impossibile salvare il file caricato: {str(save_error)}"
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'error': error_msg}), 500
                    flash(error_msg, 'danger')
                    return redirect(url_for('index'))
                
                # Verifica che il file esista e non sia vuoto
                if not os.path.exists(file_path):
                    error_msg = "File caricato non trovato nel server. Riprova."
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'error': error_msg}), 500
                    flash(error_msg, 'danger')
                    return redirect(url_for('index'))
                
                if os.path.getsize(file_path) == 0:
                    error_msg = "Il file caricato è vuoto. Verifica il contenuto del file ZIP."
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'error': error_msg}), 400 
                    flash(error_msg, 'danger')
                    return redirect(url_for('index'))
                
                # Verifica che sia un file ZIP valido
                if not zipfile.is_zipfile(file_path):
                    error_msg = "Il file caricato non è un file ZIP valido o è danneggiato."
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'error': error_msg}), 400
                    flash(error_msg, 'danger')
                    return redirect(url_for('index'))
                
                # Processa il file ZIP in modo asincrono per i file di grandi dimensioni
                file_size = os.path.getsize(file_path)
                is_large_file = file_size > 50 * 1024 * 1024  # 50 MB
                
                if is_large_file:
                    logger.info(f"Avvio elaborazione asincrona per file grande: {file.filename} ({format_file_size(file_size)})")
                    # Avvia l'elaborazione in background
                    process_zip_file_async(file_path, session_folder, session_id)
                    
                    # Se è una richiesta AJAX, restituisci un JSON con URL di reindirizzamento
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'message': 'Caricamento completato, elaborazione avviata', 
                            'redirect': url_for('progress')
                        })
                    
                    # Altrimenti reindirizza normalmente
                    return redirect(url_for('progress'))
                else:
                    # Per file più piccoli, continua con l'elaborazione sincrona
                    logger.info(f"Avvio elaborazione sincrona: {file.filename}")
                    results = process_zip_file(file_path, session_folder, session_id)
                    logger.info("Elaborazione ZIP completata con successo")
                    
                    # Store the results in the session
                    session['results'] = results
                    
                    # Se è una richiesta AJAX, restituisci un JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'message': 'Elaborazione completata con successo', 
                            'redirect': url_for('result')
                        })
                    
                    # Altrimenti reindirizza normalmente
                    return redirect(url_for('result'))
                    
            except zipfile.BadZipFile:
                logger.error("Invalid ZIP file format")
                error_msg = 'Il file caricato non è un file ZIP valido o è danneggiato'
                cleanup_temp_files(session_id)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': error_msg}), 400
                
                flash(error_msg, 'danger')
                return redirect(url_for('index'))
                
            except ValueError as ve:
                logger.error(f"Validation error: {ve}")
                error_msg = str(ve)
                cleanup_temp_files(session_id)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': error_msg}), 400
                
                flash(error_msg, 'danger')
                return redirect(url_for('index'))
                
            except Exception as e:
                logger.error(f"Error processing file: {e}")
                error_msg = f'Errore durante l\'elaborazione del file: {str(e)}'
                cleanup_temp_files(session_id)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': error_msg}), 500
                
                flash(error_msg, 'danger')
                return redirect(url_for('index'))
        else:
            error_msg = 'Solo i file ZIP sono supportati'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': error_msg}), 400
            
            flash(error_msg, 'warning')
            return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        error_msg = 'Si è verificato un errore imprevisto durante il caricamento del file. Riprova.'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error_msg}), 500
        
        flash(error_msg, 'danger')
        return redirect(url_for('index'))

@app.route('/progress')
def progress():
    """Pagina di monitoraggio dell'avanzamento per file di grandi dimensioni"""
    if 'session_id' not in session:
        flash('Nessun file in elaborazione. Carica un file ZIP.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('progress.html', session_id=session['session_id'])

@app.route('/api/status/<session_id>')
def get_status(session_id):
    """API per ottenere lo stato di avanzamento di un'elaborazione"""
    if 'session_id' not in session or session['session_id'] != session_id:
        return jsonify({'error': 'Invalid session ID'}), 403
    
    status = get_process_status(session_id)
    
    # Se l'elaborazione è completata e ci sono risultati, li mettiamo nella sessione
    if status.get('status') == 'completed' and 'result' in status:
        session['results'] = status['result']
    
    return jsonify(status)

@app.route('/result')
def result():
    """Mostra i risultati dell'elaborazione completata"""
    if 'results' not in session:
        # Verifica se c'è un'elaborazione in corso
        if 'session_id' in session:
            status = get_process_status(session['session_id'])
            if status.get('status') == 'completed' and 'result' in status:
                session['results'] = status['result']
            else:
                # Reindirizza alla pagina di avanzamento se l'elaborazione è ancora in corso
                return redirect(url_for('progress'))
        else:
            flash('Nessun file elaborato. Carica un file ZIP.', 'warning')
            return redirect(url_for('index'))
    
    return render_template('result.html', results=session['results'])

@app.route('/download/<file_type>')
def download(file_type):
    if 'session_id' not in session or 'results' not in session:
        flash('No processed files found. Please upload a ZIP file first.', 'warning')
        return redirect(url_for('index'))
    
    session_id = session['session_id']
    results = session['results']
    
    # Check if the requested file type is valid
    if file_type not in results or not results[file_type]['path']:
        flash(f'No {file_type} file available for download', 'warning')
        return redirect(url_for('result'))
    
    file_path = results[file_type]['path']
    
    # Check if the file exists
    if not os.path.exists(file_path):
        flash(f'File not found: {file_type}', 'danger')
        return redirect(url_for('result'))
    
    # Return the file for download
    return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

@app.route('/cleanup')
def cleanup():
    if 'session_id' in session:
        cleanup_temp_files(session['session_id'])
        session.pop('session_id', None)
        session.pop('results', None)
    
    flash('Temporary files have been cleaned up', 'success')
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    flash('An internal server error occurred. Please try again.', 'danger')
    return redirect(url_for('index'))
