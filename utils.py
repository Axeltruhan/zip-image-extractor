import os
import shutil
import zipfile
import logging
import magic
import json
import time
from pathlib import Path
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Base temporary directory
UPLOAD_FOLDER = '/tmp/zip_processor'

# Storage per i progressi di elaborazione
process_status = {}

# File type categories - Lista ESTESA
FILE_TYPES = {
    'images': [
        'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 
        'image/tiff', 'image/svg+xml', 'image/vnd.microsoft.icon', 'image/x-icon',
        'image/heic', 'image/heif', 'image/avif', 'image/x-adobe-dng', 'image/x-canon-cr2',
        'image/x-nikon-nef', 'image/x-olympus-orf', 'image/x-sony-arw', 'image/x-sony-sr2'
    ],
    'audio': [
        'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/x-wav', 'audio/mp3', 'audio/aac',
        'audio/flac', 'audio/x-aiff', 'audio/basic', 'audio/ac3', 'audio/x-ms-wma',
        'audio/amr', 'audio/midi', 'audio/x-midi', 'audio/opus', 'audio/x-ape',
        'audio/mp4', 'audio/x-m4a', 'audio/mp4a-latm', 'audio/vnd.dts', 'audio/vnd.rn-realaudio'
    ],
    'video': [
        'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/x-ms-wmv',
        'video/x-matroska', 'video/webm', 'video/3gpp', 'video/mp2t', 'video/mpeg', 'video/x-flv',
        'video/x-m4v', 'video/mxf', 'video/ogg', 'video/x-ogm', 'video/vnd.rn-realvideo',
        'video/MP2T', 'video/x-ms-asf', 'video/divx', 'video/vnd.dlna.mpeg-tts'
    ]
}

# Supporto mediante estensioni di file (fallback se il tipo MIME non funziona)
FILE_EXTENSIONS = {
    'images': [
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.svg', 
        '.ico', '.raw', '.cr2', '.nef', '.orf', '.sr2', '.heic', '.heif', '.avif'
    ],
    'audio': [
        '.mp3', '.wav', '.ogg', '.aac', '.flac', '.aiff', '.wma', '.m4a', 
        '.aac', '.ac3', '.amr', '.mid', '.midi', '.ape', '.opus', '.alac'
    ],
    'video': [
        '.mp4', '.avi', '.mov', '.wmv', '.mkv', '.webm', '.flv', '.3gp', '.m4v', 
        '.mpg', '.mpeg', '.mxf', '.ogv', '.rm', '.rmvb', '.vob', '.divx', '.3g2', '.ts', '.mts'
    ]
}

def get_file_type(file_path):
    """Determine the type of a file using python-magic and fallback to file extension"""
    try:
        # Prima prova con il tipo MIME
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        
        # Verifica se il tipo MIME è nelle liste conosciute
        for category, mime_types in FILE_TYPES.items():
            if mime_type in mime_types:
                return category
                
        # Verifica per prefisso del MIME type (es. image/*)
        if mime_type.startswith('image/'):
            return 'images'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type.startswith('video/'):
            return 'video'
        
        # Se il MIME type non ha funzionato, verifica l'estensione del file
        file_ext = os.path.splitext(file_path)[1].lower()
        for category, extensions in FILE_EXTENSIONS.items():
            if file_ext in extensions:
                logger.debug(f"File {file_path} classificato per estensione: {category} (ext: {file_ext})")
                return category
        
        logger.debug(f"File {file_path} non classificato come media. MIME: {mime_type}, Estensione: {file_ext}")
        # Non categorizzato - non verrà incluso nei risultati
        return None
    except Exception as e:
        logger.error(f"Error determining file type for {file_path}: {e}")
        # Se c'è un errore con magic, prova almeno con l'estensione
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            for category, extensions in FILE_EXTENSIONS.items():
                if file_ext in extensions:
                    logger.debug(f"Fallback: File {file_path} classificato per estensione: {category}")
                    return category
        except Exception as ex:
            logger.error(f"Fallback failed for {file_path}: {ex}")
            
        # Non categorizzato - non verrà incluso nei risultati
        return None

def update_process_status(session_id, status, progress=0, message=""):
    """Aggiorna lo stato di elaborazione per un determinato session_id"""
    process_status[session_id] = {
        'status': status,
        'progress': progress,
        'message': message,
        'timestamp': time.time()
    }
    logger.debug(f"Status update for {session_id}: {status} - {progress}% - {message}")

def get_process_status(session_id):
    """Ottiene lo stato di elaborazione corrente per un session_id"""
    if session_id in process_status:
        return process_status[session_id]
    return {'status': 'unknown', 'progress': 0, 'message': 'Stato sconosciuto'}

def process_zip_file_async(zip_file_path, session_folder, session_id):
    """
    Versione asincrona della funzione process_zip_file
    """
    thread = Thread(target=_process_zip_file_thread, args=(zip_file_path, session_folder, session_id))
    thread.daemon = True
    thread.start()
    return {
        'status': 'processing',
        'session_id': session_id,
        'message': 'Elaborazione avviata. Puoi seguire lo stato sulla pagina.'
    }

def _process_zip_file_thread(zip_file_path, session_folder, session_id):
    """
    Thread worker per processare file ZIP di grandi dimensioni
    """
    try:
        result = process_zip_file(zip_file_path, session_folder, session_id)
        # Aggiorna lo stato con i risultati
        process_status[session_id]['result'] = result
        process_status[session_id]['status'] = 'completed'
        process_status[session_id]['progress'] = 100
        process_status[session_id]['message'] = 'Elaborazione completata con successo'
    except Exception as e:
        logger.error(f"Error in process_zip_file_thread: {e}")
        process_status[session_id]['status'] = 'error'
        process_status[session_id]['message'] = f'Errore: {str(e)}'
        # Re-raise per debug
        raise

def process_zip_file(zip_file_path, session_folder, session_id=None):
    """
    Process a ZIP file, categorize its contents, and create ZIP files for each category
    Returns a dictionary with information about the processed files
    """
    if session_id:
        update_process_status(session_id, 'initializing', 0, 'Inizializzazione elaborazione')
    
    logger.debug(f"Processing zip file: {zip_file_path}")
    
    # Verify the file exists and is a valid ZIP
    if not os.path.exists(zip_file_path):
        if session_id:
            update_process_status(session_id, 'error', 0, 'File ZIP non trovato')
        raise FileNotFoundError(f"ZIP file not found: {zip_file_path}")
    
    if not zipfile.is_zipfile(zip_file_path):
        if session_id:
            update_process_status(session_id, 'error', 0, 'File ZIP non valido o danneggiato')
        raise zipfile.BadZipFile("The file is not a valid ZIP archive")
    
    # Create extraction directory
    extract_dir = os.path.join(session_folder, 'extracted')
    os.makedirs(extract_dir, exist_ok=True)
    
    result = {}
    
    try:
        if session_id:
            update_process_status(session_id, 'extracting', 5, 'Estrazione archivio ZIP in corso...')
        
        # Extract the ZIP file - ottenere prima il conteggio dei file
        file_count = 0
        zip_size = os.path.getsize(zip_file_path)
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            file_count = len(zip_ref.infolist())
            if session_id:
                update_process_status(session_id, 'extracting', 10, 
                                    f'Estrazione di {file_count} file ({format_file_size(zip_size)})')
            zip_ref.extractall(extract_dir)
        
        if session_id:
            update_process_status(session_id, 'analyzing', 30, 'Analisi e categorizzazione dei file...')
        
        # Categorize files - rimuovi 'others' per non creare questo file ZIP
        categorized_files = {
            'images': [],
            'audio': [],
            'video': []
        }
        
        # Check if any files were extracted
        files_found = False
        processed_count = 0
        
        # Walk through the extracted directory and categorize files
        for root, _, files in os.walk(extract_dir):
            for file in files:
                files_found = True
                file_path = os.path.join(root, file)
                # Usa solo il nome del file senza la struttura delle cartelle
                file_name = os.path.basename(file_path)
                
                # Skip hidden files
                if os.path.basename(file_path).startswith('.'):
                    continue
                
                # Aggiorna progresso categorizzazione (30-70%)
                processed_count += 1
                if session_id and file_count > 0 and processed_count % max(1, file_count // 20) == 0:
                    progress = 30 + int(40 * (processed_count / file_count))
                    update_process_status(session_id, 'analyzing', progress, 
                                        f'Classificazione file {processed_count}/{file_count}')
                
                try:
                    # Categorize the file
                    file_type = get_file_type(file_path)
                    # Assicurati che il tipo esista nel dizionario (immagini, audio, video)
                    if file_type in categorized_files:
                        categorized_files[file_type].append((file_path, file_name))
                    # Se il tipo è 'others' o non è riconosciuto, salta questo file
                except Exception as e:
                    logger.warning(f"Error categorizing file {file_path}: {e}")
                    # Non aggiungiamo più file alla categoria 'others'
        
        if not files_found:
            if session_id:
                update_process_status(session_id, 'error', 0, 'Il file ZIP non contiene nessun file')
            raise ValueError("The ZIP file doesn't contain any files")
        
        if session_id:
            update_process_status(session_id, 'packaging', 70, 'Creazione archivi per tipologia di media...')
        
        # Create ZIP files for each category
        category_count = len([c for c, f in categorized_files.items() if f])
        processed_categories = 0
        
        for category, files in categorized_files.items():
                
            if files:
                processed_categories += 1
                if session_id:
                    category_progress = 70 + int((processed_categories / max(1, category_count)) * 25)
                    update_process_status(session_id, 'packaging', category_progress, 
                                        f'Creazione archivio {category}.zip ({len(files)} file)')
                                        
                # Create a ZIP file for this category
                output_zip_path = os.path.join(session_folder, f'{category}.zip')
                
                try:
                    with zipfile.ZipFile(output_zip_path, 'w') as zipf:
                        file_processed = 0
                        for file_path, file_name in files:
                            if os.path.exists(file_path) and os.path.isfile(file_path):
                                # Usa solo il nome del file per evitare di riprodurre la struttura delle cartelle
                                zipf.write(file_path, file_name)
                            else:
                                logger.warning(f"Skipping non-existent file: {file_path}")
                            
                            file_processed += 1
                            if session_id and file_processed % max(1, len(files) // 10) == 0:
                                progress = 70 + int((processed_categories / max(1, category_count)) * 25)
                                message = f'Aggiunta file a {category}.zip: {file_processed}/{len(files)}'
                                update_process_status(session_id, 'packaging', progress, message)
                    
                    # Calculate the file size in a readable format
                    size_bytes = os.path.getsize(output_zip_path)
                    size_display = format_file_size(size_bytes)
                    
                    result[category] = {
                        'path': output_zip_path,
                        'count': len(files),
                        'size': size_display
                    }
                except Exception as e:
                    logger.error(f"Error creating ZIP for {category}: {e}")
                    result[category] = {
                        'path': None,
                        'count': len(files),
                        'size': '0 B',
                        'error': str(e)
                    }
            else:
                result[category] = {
                    'path': None,
                    'count': 0,
                    'size': '0 B'
                }
        
        # Add the source zip info
        source_size = os.path.getsize(zip_file_path)
        result['source'] = {
            'path': zip_file_path,
            'name': os.path.basename(zip_file_path),
            'size': format_file_size(source_size)
        }
        
        if session_id:
            update_process_status(session_id, 'finishing', 95, 'Completamento elaborazione...')
        
        logger.debug(f"Finished processing: {zip_file_path}")
        
        if session_id:
            update_process_status(session_id, 'completed', 100, 'Elaborazione completata con successo')
        
        return result
        
    except Exception as e:
        logger.error(f"Error in process_zip_file: {e}")
        # Clean up extraction directory on error
        if os.path.exists(extract_dir):
            try:
                shutil.rmtree(extract_dir)
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up extraction directory: {cleanup_error}")
        
        # Aggiorna stato in caso di errore
        if session_id:
            update_process_status(session_id, 'error', 0, f'Errore: {str(e)}')
        
        # Re-raise the exception to be handled by the caller
        raise

def format_file_size(size_bytes):
    """Format file size in a human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def cleanup_temp_files(session_id=None):
    """Clean up temporary files for a specific session or all if session_id is None"""
    if session_id:
        # Clean up only the specified session
        session_folder = os.path.join(UPLOAD_FOLDER, session_id)
        if os.path.exists(session_folder):
            shutil.rmtree(session_folder)
            logger.debug(f"Cleaned up session folder: {session_folder}")
    else:
        # Clean up all folders older than 1 hour (function not implemented for simplicity)
        # In a production environment, you would want to implement this with a timestamp check
        pass
