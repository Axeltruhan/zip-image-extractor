#!/usr/bin/env python3
"""
ZIP Processor - Versione GUI
-----------------------------
Interfaccia grafica per processare file ZIP e separare i contenuti
per tipo di media (immagini, audio, video e altri) in file ZIP separati.

Requisiti:
- Python 3.x
- tkinter (pre-installato con Python)
- python-magic (opzionale, per una classificazione migliore)

Uso:
  python zip_processor_gui.py
"""

import os
import sys
import zipfile
import shutil
import tempfile
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("AVVISO: python-magic non installato. Classificazione basata solo su estensioni file.")
    print("Per una classificazione migliore, installa python-magic con: pip install python-magic")
    print("Su Windows potrebbe essere necessario installare anche il binario 'magic': https://github.com/ahupp/python-magic#dependencies")

# Categorie di file supportate
FILE_EXTENSIONS = {
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'],
    'audio': ['.mp3', '.wav', '.ogg', '.aac', '.flac', '.aiff', '.wma', '.m4a'],
    'video': ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.webm', '.flv', '.3gp', '.m4v'],
    'others': []  # Tutti gli altri
}

# MIME types per una classificazione migliore quando magic è disponibile
FILE_MIME_TYPES = {
    'images': ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/tiff', 'image/svg+xml'],
    'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/x-wav', 'audio/mp3', 'audio/aac', 'audio/flac', 'audio/x-aiff'],
    'video': ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/x-ms-wmv', 'video/x-matroska', 'video/webm', 'video/3gpp'],
    'others': []  # Tutti gli altri
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
        except Exception:
            pass  # Fall back to extension check
    
    # Fallback to extension check
    file_ext = os.path.splitext(file_path)[1].lower()
    for category, extensions in FILE_EXTENSIONS.items():
        if file_ext in extensions:
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

class ZipProcessorApp(tk.Tk):
    """Interfaccia grafica per l'elaborazione di file ZIP"""
    
    def __init__(self):
        super().__init__()
        self.title("ZIP Processor - Separatore File Multimediali")
        self.geometry("800x600")
        self.minsize(600, 500)
        
        self.processing_thread = None
        self.cancelled = False
        
        self.create_widgets()
        self.create_menu()
        self.center_window()
        
    def create_widgets(self):
        """Crea i widget dell'interfaccia"""
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="ZIP Processor", font=("Arial", 18, "bold")).pack(side=tk.LEFT)
        
        # Descrizione
        desc_frame = ttk.LabelFrame(self.main_frame, text="Descrizione", padding=10)
        desc_frame.pack(fill=tk.X, pady=5)
        
        desc_text = ("Questo programma elabora file ZIP e separa i contenuti per tipo di media "
                    "(immagini, audio, video, altro) in file ZIP separati. "
                    "Seleziona un file ZIP per iniziare.")
        ttk.Label(desc_frame, text=desc_text, wraplength=750).pack(fill=tk.X)
        
        # File selection
        file_frame = ttk.LabelFrame(self.main_frame, text="Selezione File", padding=10)
        file_frame.pack(fill=tk.X, pady=5)
        
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill=tk.X)
        
        self.file_path_var = tk.StringVar()
        ttk.Label(input_frame, text="File ZIP:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(input_frame, textvariable=self.file_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(input_frame, text="Sfoglia...", command=self.browse_file).pack(side=tk.LEFT)
        
        # Output dir selection
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.output_dir_var = tk.StringVar()
        ttk.Label(output_frame, text="Cartella output:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="Sfoglia...", command=self.browse_output_dir).pack(side=tk.LEFT)
        
        # Advanced options
        options_frame = ttk.LabelFrame(self.main_frame, text="Opzioni", padding=10)
        options_frame.pack(fill=tk.X, pady=5)
        
        # Checkboxes for options
        options_inner = ttk.Frame(options_frame)
        options_inner.pack(fill=tk.X)
        
        self.open_after_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_inner, text="Apri cartella dopo elaborazione", variable=self.open_after_var).pack(side=tk.LEFT, padx=(0, 20))
        
        # Progress section
        progress_frame = ttk.LabelFrame(self.main_frame, text="Avanzamento", padding=10)
        progress_frame.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="In attesa di selezione file")
        ttk.Label(progress_frame, textvariable=self.status_var).pack(fill=tk.X, pady=(0, 5))
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Details textbox
        self.log_text = tk.Text(progress_frame, height=8, width=50, state=tk.DISABLED, wrap=tk.WORD, 
                                font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for text
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.process_btn = ttk.Button(button_frame, text="Elabora File ZIP", command=self.process_file)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_btn = ttk.Button(button_frame, text="Annulla", command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT)
        
        ttk.Button(button_frame, text="Esci", command=self.quit).pack(side=tk.RIGHT)
        
    def create_menu(self):
        """Crea il menu dell'applicazione"""
        menubar = tk.Menu(self)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Seleziona File ZIP...", command=self.browse_file)
        file_menu.add_command(label="Elabora File", command=self.process_file)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Aiuto", command=self.show_help)
        help_menu.add_command(label="Informazioni", command=self.show_about)
        menubar.add_cascade(label="Aiuto", menu=help_menu)
        
        self.config(menu=menubar)
    
    def center_window(self):
        """Centra la finestra nello schermo"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def browse_file(self):
        """Apre il file dialog per selezionare un file ZIP"""
        file_path = filedialog.askopenfilename(
            title="Seleziona file ZIP",
            filetypes=[("File ZIP", "*.zip"), ("Tutti i file", "*.*")]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            
            # Auto-set output directory to same directory as the file
            output_dir = os.path.dirname(file_path)
            self.output_dir_var.set(output_dir)
            
            self.status_var.set(f"File selezionato: {os.path.basename(file_path)}")
    
    def browse_output_dir(self):
        """Apre il file dialog per selezionare una directory di output"""
        output_dir = filedialog.askdirectory(title="Seleziona directory di output")
        
        if output_dir:
            self.output_dir_var.set(output_dir)
    
    def process_file(self):
        """Avvia l'elaborazione del file ZIP in un thread separato"""
        zip_file_path = self.file_path_var.get()
        
        if not zip_file_path:
            messagebox.showerror("Errore", "Nessun file selezionato.")
            return
        
        if not os.path.exists(zip_file_path):
            messagebox.showerror("Errore", f"File non trovato: {zip_file_path}")
            return
        
        if not zipfile.is_zipfile(zip_file_path):
            messagebox.showerror("Errore", f"Il file non è un file ZIP valido: {zip_file_path}")
            return
        
        output_dir = self.output_dir_var.get()
        if not output_dir:
            output_dir = os.path.dirname(zip_file_path)
            self.output_dir_var.set(output_dir)
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError:
                messagebox.showerror("Errore", f"Impossibile creare la directory: {output_dir}")
                return
        
        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Reset progress
        self.progress_var.set(0)
        self.status_var.set("Avvio elaborazione...")
        
        # Update UI
        self.process_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.cancelled = False
        
        # Start processing in a separate thread
        self.processing_thread = threading.Thread(
            target=self.processing_task,
            args=(zip_file_path, output_dir)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def processing_task(self, zip_file_path, output_dir):
        """Task eseguito in un thread separato per elaborare il file ZIP"""
        start_time = time.time()
        try:
            self.log(f"Inizio elaborazione di: {zip_file_path}")
            self.update_status("Apertura e verifica file ZIP...")
            
            # Verify the ZIP file
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                # Get file count for progress reporting
                files_info = zip_ref.infolist()
                file_count = len(files_info)
                self.log(f"Il file ZIP contiene {file_count} file.")
            
            # Use temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                if self.cancelled:
                    self.log("Operazione annullata dall'utente")
                    self.update_status("Operazione annullata")
                    self.complete_processing(False)
                    return
                
                extract_dir = os.path.join(temp_dir, 'extracted')
                os.makedirs(extract_dir, exist_ok=True)
                
                # Phase 1: Extract files
                self.update_status("Estrazione dei file...")
                self.progress_var.set(0)
                
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    for i, file_info in enumerate(files_info):
                        if self.cancelled:
                            break
                        
                        try:
                            zip_ref.extract(file_info, extract_dir)
                        except Exception as e:
                            self.log(f"Errore durante l'estrazione di {file_info.filename}: {e}")
                            continue
                        
                        # Update progress
                        progress_percent = (i + 1) / file_count * 30  # First 30% of progress
                        self.progress_var.set(progress_percent)
                        
                        if i % 10 == 0 or i == file_count - 1:
                            self.update_status(f"Estrazione file {i+1}/{file_count}...")
                
                if self.cancelled:
                    self.log("Operazione annullata dall'utente")
                    self.update_status("Operazione annullata")
                    self.complete_processing(False)
                    return
                
                # Phase 2: Categorize files
                self.update_status("Analisi e categorizzazione dei file...")
                
                categorized_files = {
                    'images': [],
                    'audio': [],
                    'video': []
                }
                
                # Build a list of all files for progress reporting
                file_list = []
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, extract_dir)
                        file_list.append((file_path, rel_path))
                
                # Process each file
                for i, (file_path, rel_path) in enumerate(file_list):
                    if self.cancelled:
                        break
                    
                    # Skip hidden files
                    if os.path.basename(file_path).startswith('.'):
                        continue
                    
                    # Categorize file
                    category = get_file_category(file_path)
                    # Assicurati che il tipo esista nel dizionario (immagini, audio, video)
                    if category in categorized_files:
                        # Usa solo il nome del file invece del percorso relativo
                        file_name = os.path.basename(file_path)
                        categorized_files[category].append((file_path, file_name))
                    # Se il tipo è 'others' o non è riconosciuto, salta questo file
                    
                    # Update progress (30-60%)
                    progress_percent = 30 + (i + 1) / len(file_list) * 30
                    self.progress_var.set(progress_percent)
                    
                    if i % 10 == 0 or i == len(file_list) - 1:
                        self.update_status(f"Analisi file {i+1}/{len(file_list)}...")
                
                if self.cancelled:
                    self.log("Operazione annullata dall'utente")
                    self.update_status("Operazione annullata")
                    self.complete_processing(False)
                    return
                
                # Log categorization results
                for category, files in categorized_files.items():
                    self.log(f"File {category}: {len(files)}")
                
                # Phase 3: Create ZIP files for each category
                results = {}
                category_count = sum(1 for cat, files in categorized_files.items() if files)
                processed_cats = 0
                
                for category, files in categorized_files.items():
                    if self.cancelled:
                        break
                    
                    if files:
                        output_zip_path = os.path.join(output_dir, f"{category}.zip")
                        self.update_status(f"Creazione {category}.zip con {len(files)} file...")
                        self.log(f"Creazione {category}.zip con {len(files)} file...")
                        
                        try:
                            with zipfile.ZipFile(output_zip_path, 'w') as zipf:
                                for i, (file_path, rel_path) in enumerate(files):
                                    if self.cancelled:
                                        break
                                    
                                    if os.path.exists(file_path) and os.path.isfile(file_path):
                                        zipf.write(file_path, rel_path)
                                    
                                    # Update progress within this category (60-100%)
                                    cat_progress = (i + 1) / len(files)
                                    cat_progress_total = 60 + (processed_cats + cat_progress) / category_count * 40
                                    self.progress_var.set(cat_progress_total)
                                    
                                    if i % 20 == 0 or i == len(files) - 1:
                                        self.update_status(f"Aggiunta file a {category}.zip: {i+1}/{len(files)}...")
                            
                            # Store result info
                            size_bytes = os.path.getsize(output_zip_path)
                            results[category] = {
                                'path': output_zip_path,
                                'count': len(files),
                                'size': format_file_size(size_bytes)
                            }
                            
                            self.log(f"Completato {category}.zip: {format_file_size(size_bytes)}")
                        except Exception as e:
                            self.log(f"Errore durante la creazione di {category}.zip: {e}")
                            results[category] = {
                                'path': None,
                                'count': len(files),
                                'size': '0 B',
                                'error': str(e)
                            }
                    else:
                        results[category] = {
                            'path': None,
                            'count': 0,
                            'size': '0 B'
                        }
                    
                    processed_cats += 1
            
            # Calculate total time
            end_time = time.time()
            total_time = end_time - start_time
            total_minutes = total_time / 60
            
            # Final report
            if not self.cancelled:
                self.log("\n" + "="*50)
                self.log(f"ELABORAZIONE COMPLETATA IN {total_minutes:.2f} MINUTI")
                self.log("="*50)
                self.log(f"File sorgente: {os.path.basename(zip_file_path)}")
                self.log(f"Directory output: {output_dir}")
                self.log("-"*50)
                self.log("File risultanti:")
                
                for category in ['images', 'audio', 'video', 'others']:
                    if category in results and results[category]['count'] > 0:
                        self.log(f"- {category.upper()}: {results[category]['count']} file ({results[category]['size']})")
                        if results[category]['path']:
                            self.log(f"  Salvato in: {results[category]['path']}")
                
                self.progress_var.set(100)
                self.update_status("Elaborazione completata con successo!")
                
                # If checkbox is selected, open output directory
                if self.open_after_var.get():
                    self.open_output_directory(output_dir)
                
                # Show completion message
                messagebox.showinfo("Completato", 
                                   f"Elaborazione completata in {total_minutes:.2f} minuti.\n"
                                   f"I file risultanti sono disponibili in:\n{output_dir}")
            
            self.complete_processing(True)
            
        except Exception as e:
            self.log(f"ERRORE: {e}")
            self.update_status(f"Errore: {e}")
            messagebox.showerror("Errore", f"Si è verificato un errore durante l'elaborazione: {e}")
            self.complete_processing(False)
    
    def cancel_processing(self):
        """Annulla l'operazione in corso"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.cancelled = True
            self.update_status("Annullamento in corso...")
            self.cancel_btn.config(state=tk.DISABLED)
    
    def complete_processing(self, success):
        """Completa l'elaborazione e ripristina l'interfaccia"""
        self.process_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        
        if success and not self.cancelled:
            self.progress_var.set(100)
        elif self.cancelled:
            self.update_status("Operazione annullata")
    
    def update_status(self, message):
        """Aggiorna il messaggio di stato"""
        self.status_var.set(message)
        self.update_idletasks()
    
    def log(self, message):
        """Aggiunge un messaggio al log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.update_idletasks()
    
    def open_output_directory(self, directory):
        """Apre la directory dei risultati nell'esplora file"""
        try:
            if sys.platform == 'win32':
                os.startfile(directory)
            elif sys.platform == 'darwin':  # macOS
                os.system(f'open "{directory}"')
            else:  # Linux/Unix
                os.system(f'xdg-open "{directory}"')
        except Exception as e:
            self.log(f"Impossibile aprire la directory: {e}")
    
    def show_help(self):
        """Mostra la finestra di aiuto"""
        help_text = """
        ZIP Processor - Aiuto
        
        Questo programma ti permette di processare file ZIP e separare i contenuti
        per tipo di media (immagini, audio, video, altro) in file ZIP separati.
        
        Come utilizzare il programma:
        
        1. Clicca su "Sfoglia" per selezionare un file ZIP da processare
        2. Opzionalmente, scegli una directory di output differente
        3. Clicca su "Elabora File ZIP" per avviare l'elaborazione
        4. Attendi che l'elaborazione sia completata
        5. I file risultanti saranno disponibili nella directory di output
        
        Tipi di file supportati:
        
        - Immagini: JPG, PNG, GIF, BMP, WebP, SVG, ecc.
        - Audio: MP3, WAV, OGG, AAC, FLAC, ecc.
        - Video: MP4, AVI, MOV, WMV, MKV, WebM, ecc.
        - Altri: tutti gli altri tipi di file
        """
        messagebox.showinfo("Aiuto", help_text)
    
    def show_about(self):
        """Mostra la finestra di informazioni"""
        about_text = """
        ZIP Processor v1.0
        
        Questa applicazione consente di elaborare file ZIP
        e separare i contenuti per tipo di media.
        
        Sviluppato con Python e Tkinter.
        
        © 2025 - Tutti i diritti riservati
        """
        messagebox.showinfo("Informazioni", about_text)

def main():
    """Funzione principale"""
    app = ZipProcessorApp()
    app.mainloop()

if __name__ == "__main__":
    main()