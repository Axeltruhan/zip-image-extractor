#!/usr/bin/env python3
"""
ZIP Processor - Versione Desktop Locale
---------------------------------------
Questo script processa file ZIP locali e separa i contenuti per tipo di media
(immagini, audio, video e altri) in file ZIP separati.

Uso:
  python zip_processor_local.py percorso/al/file.zip

Il risultato sarà nella stessa cartella del file originale, con i seguenti file:
- images.zip - Tutte le immagini
- audio.zip - Tutti i file audio
- video.zip - Tutti i file video
- others.zip - Altri tipi di file
"""

import os
import sys
import zipfile
import shutil
import tempfile
import time
import argparse
import logging
from pathlib import Path

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("AVVISO: python-magic non installato. Classificazione basata solo su estensioni file.")
    print("Per una classificazione migliore, installa python-magic con: pip install python-magic")
    print("Su Windows potrebbe essere necessario installare anche il binario 'magic': https://github.com/ahupp/python-magic#dependencies")
    print()

# Configura logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ZipProcessor")

# Categorie di file supportate - Lista ESTESA
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

# MIME types per una classificazione migliore quando magic è disponibile - Lista ESTESA
FILE_MIME_TYPES = {
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

def get_file_category(file_path):
    """Determina la categoria di un file in base all'estensione e/o al tipo MIME"""
    # Check by mime type first if available
    if MAGIC_AVAILABLE:
        try:
            import magic  # Import dentro la funzione se disponibile
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(file_path)
            
            # Check against known MIME types
            for category, mime_types in FILE_MIME_TYPES.items():
                if mime_type in mime_types:
                    return category
                    
            # Check for prefix matches (es. image/*)
            if mime_type.startswith('image/'):
                return 'images'
            elif mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type.startswith('video/'):
                return 'video'
                
            # Il MIME type non ha identificato il file, prova con l'estensione
            file_ext = os.path.splitext(file_path)[1].lower()
            for category, extensions in FILE_EXTENSIONS.items():
                if file_ext in extensions:
                    logger.debug(f"File {os.path.basename(file_path)} classificato per estensione '{file_ext}' come {category} (MIME: {mime_type})")
                    return category
                    
            logger.debug(f"File {os.path.basename(file_path)} non classificato come media. MIME: {mime_type}, Estensione: {file_ext}")
            # Non categorizzato - non verrà incluso nei risultati
            return None
            
        except Exception as e:
            logger.warning(f"Errore nella determinazione del MIME type per {file_path}: {e}")
            # Fallback a verifica per estensione in caso di errore magic
    
    # Fallback to extension check
    file_ext = os.path.splitext(file_path)[1].lower()
    for category, extensions in FILE_EXTENSIONS.items():
        if file_ext in extensions:
            logger.debug(f"File {os.path.basename(file_path)} classificato per estensione '{file_ext}' come {category}")
            return category
    
    # Non categorizzato - non verrà incluso nei risultati
    return None

def format_file_size(size_bytes):
    """Formatta la dimensione del file in modo leggibile"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def format_time(seconds):
    """Formatta il tempo in modo leggibile"""
    if seconds < 60:
        return f"{seconds:.1f} secondi"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minuti"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} ore"

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """Stampa una barra di avanzamento nel terminale"""
    percent = "{0:.1f}".format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total: 
        print()

def process_zip_file(zip_file_path, output_dir=None):
    """
    Processa un file ZIP e crea ZIP separati per ogni categoria di media
    
    Args:
        zip_file_path: Percorso al file ZIP da processare
        output_dir: Directory di output (se None, usa la stessa del file ZIP)
    
    Returns:
        Un dizionario con i risultati dell'elaborazione
    """
    start_time = time.time()
    logger.info(f"Inizio elaborazione di: {zip_file_path}")
    
    # Verify the file exists and is a valid ZIP
    if not os.path.exists(zip_file_path):
        logger.error(f"File non trovato: {zip_file_path}")
        return None
    
    if not zipfile.is_zipfile(zip_file_path):
        logger.error(f"File non valido o non è un file ZIP: {zip_file_path}")
        return None
    
    # Determine output directory
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(zip_file_path))
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        # Open and get info about the ZIP
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Get file count and total size for progress reporting
            files_info = zip_ref.infolist()
            file_count = len(files_info)
            
            logger.info(f"Estrazione di {file_count} file...")
            
            # Extract files with progress
            for i, file_info in enumerate(files_info):
                zip_ref.extract(file_info, extract_dir)
                print_progress_bar(i + 1, file_count, prefix='Estrazione:', 
                                  suffix=f'File {i+1}/{file_count}', length=40)
        
        extraction_time = time.time()
        logger.info(f"Estrazione completata in {format_time(extraction_time - start_time)}")
        
        # Categorize files - rimuovi 'others' per non creare questo file ZIP
        categorized_files = {
            'images': [],
            'audio': [],
            'video': []
        }
        
        logger.info("Preparazione elenco file...")
        file_list = []
        
        # Build a list of all files
        for root, _, files in os.walk(extract_dir):
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                # Usa solo il nome del file, senza struttura delle cartelle
                file_name = os.path.basename(file_path)
                file_list.append((file_path, file_name))
        
        total_files = len(file_list)
        logger.info(f"Trovati {total_files} file da analizzare")
        
        # Analisi in 3 fasi separate per garantire analisi completa
        # Fase 1: Individua tutti i file video
        logger.info("Fase 1: Ricerca file video...")
        files_processed = 0
        for file_path, file_name in file_list:
            # Verifica specifica per video
            try:
                # Check by extension and MIME type
                if get_file_category(file_path) == 'video':
                    categorized_files['video'].append((file_path, file_name))
            except Exception as e:
                logger.warning(f"Errore nell'analisi del file {file_name}: {e}")
                
            # Progress for phase 1
            files_processed += 1
            if files_processed % 20 == 0 or files_processed == total_files:
                print_progress_bar(files_processed, total_files, 
                                  prefix='Ricerca video:', 
                                  suffix=f'File {files_processed}/{total_files}', 
                                  length=40)
        
        # Fase 2: Individua tutti i file audio
        logger.info(f"Fase 2: Ricerca file audio... (trovati {len(categorized_files['video'])} video)")
        files_processed = 0
        for file_path, file_name in file_list:
            # Verifica specifica per audio
            try:
                if get_file_category(file_path) == 'audio':
                    categorized_files['audio'].append((file_path, file_name))
            except Exception as e:
                logger.warning(f"Errore nell'analisi del file {file_name}: {e}")
                
            # Progress for phase 2
            files_processed += 1
            if files_processed % 20 == 0 or files_processed == total_files:
                print_progress_bar(files_processed, total_files, 
                                  prefix='Ricerca audio:', 
                                  suffix=f'File {files_processed}/{total_files}', 
                                  length=40)
        
        # Fase 3: Individua tutti i file immagine
        logger.info(f"Fase 3: Ricerca immagini... (trovati {len(categorized_files['audio'])} audio)")
        files_processed = 0
        for file_path, file_name in file_list:
            # Verifica specifica per immagini
            try:
                if get_file_category(file_path) == 'images':
                    categorized_files['images'].append((file_path, file_name))
            except Exception as e:
                logger.warning(f"Errore nell'analisi del file {file_name}: {e}")
            
            # Progress for phase 3
            files_processed += 1
            if files_processed % 20 == 0 or files_processed == total_files:
                print_progress_bar(files_processed, total_files, 
                                  prefix='Ricerca immagini:', 
                                  suffix=f'File {files_processed}/{total_files}', 
                                  length=40)
        
        categorization_time = time.time()
        logger.info(f"Categorizzazione completata in {format_time(categorization_time - extraction_time)}")
        
        # Summary of categorization
        for category, files in categorized_files.items():
            logger.info(f"File {category}: {len(files)}")
        
        # Create ZIP files for each category
        results = {}
        for category, files in categorized_files.items():
                
            if files:
                output_zip_path = os.path.join(output_dir, f"{category}.zip")
                logger.info(f"Creazione {category}.zip con {len(files)} file...")
                
                with zipfile.ZipFile(output_zip_path, 'w') as zipf:
                    for i, (file_path, file_name) in enumerate(files):
                        if os.path.exists(file_path) and os.path.isfile(file_path):
                            # Usa solo il nome del file per evitare di riprodurre la struttura delle cartelle
                            zipf.write(file_path, file_name)
                        
                        # Show progress
                        print_progress_bar(i + 1, len(files), prefix=f'Creazione {category}.zip:', 
                                          suffix=f'File {i+1}/{len(files)}', length=40)
                
                # Store result info
                size_bytes = os.path.getsize(output_zip_path)
                results[category] = {
                    'path': output_zip_path,
                    'count': len(files),
                    'size': format_file_size(size_bytes)
                }
            else:
                results[category] = {
                    'path': None,
                    'count': 0,
                    'size': '0 B'
                }
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Add source file info
    source_size = os.path.getsize(zip_file_path)
    results['source'] = {
        'path': zip_file_path,
        'name': os.path.basename(zip_file_path),
        'size': format_file_size(source_size)
    }
    
    # Print summary
    print("\n" + "="*70)
    print(f"RIEPILOGO ELABORAZIONE: {os.path.basename(zip_file_path)}")
    print("="*70)
    print(f"Tempo totale di elaborazione: {format_time(total_time)}")
    print(f"File sorgente: {results['source']['name']} ({results['source']['size']})")
    print("-"*70)
    print("File risultanti:")
    
    for category in ['images', 'audio', 'video']:
        if results[category]['count'] > 0:
            print(f"- {category.upper()}: {results[category]['count']} file ({results[category]['size']})")
            print(f"  Salvato in: {results[category]['path']}")
    
    # Mostra gli 'others' solo nel conteggio ma non come output
    if results['others']['count'] > 0:
        print(f"- OTHERS: {results['others']['count']} file (non inclusi nei risultati)")
    
    print("="*70)
    
    logger.info(f"Elaborazione completata in {format_time(total_time)}")
    return results

def main():
    """Funzione principale per l'esecuzione da riga di comando"""
    parser = argparse.ArgumentParser(description='Processa file ZIP e separa i contenuti per tipo di media.')
    parser.add_argument('zip_file', help='Percorso al file ZIP da processare')
    parser.add_argument('-o', '--output-dir', help='Directory in cui salvare i file ZIP risultanti')
    parser.add_argument('-v', '--verbose', action='store_true', help='Mostra output dettagliato')
    
    args = parser.parse_args()
    
    # Set verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Process the ZIP file
    process_zip_file(args.zip_file, args.output_dir)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperazione interrotta dall'utente.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione: {e}")
        sys.exit(1)