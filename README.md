# ZIP Media Separator

Un'applicazione per separare file all'interno di un archivio ZIP in base al tipo di media (immagini, audio, video e altro).

## Descrizione

ZIP Media Separator è un'applicazione che consente di analizzare un file ZIP ed estrarre i suoi contenuti in file ZIP separati per categoria:

- **images.zip**: Contiene tutte le immagini (jpg, png, gif, bmp, webp, svg, ecc.)
- **audio.zip**: Contiene tutti i file audio (mp3, wav, ogg, aac, flac, ecc.)
- **video.zip**: Contiene tutti i file video (mp4, avi, mov, wmv, mkv, webm, ecc.)
- **others.zip**: Contiene tutti gli altri tipi di file

## Versioni Disponibili

L'applicazione è disponibile in due versioni:

### 1. Versione Web

Una applicazione web basata su Flask che consente di caricare file ZIP e scaricare i file ZIP risultanti. Tuttavia, questa versione è limitata alle dimensioni del file supportate dal server web.

Per avviare la versione web:

```bash
python main.py
```

### 2. Versione Desktop - Linea di Comando

Uno script Python da eseguire in locale che processa i file ZIP direttamente sul tuo computer. Questa versione è ideale per file di grandi dimensioni.

Uso:

```bash
python zip_processor_local.py percorso/al/file.zip
```

Opzioni:

- `-o`, `--output-dir`: Directory in cui salvare i file ZIP risultanti
- `-v`, `--verbose`: Mostra output dettagliato

### 3. Versione Desktop - Interfaccia Grafica

Un'applicazione desktop con interfaccia grafica facile da usare, per processare i file ZIP localmente con un'interfaccia user-friendly.

Per avviarla:

```bash
python zip_processor_gui.py
```

## Requisiti

- Python 3.6 o superiore
- Librerie Python:
  - `flask`: Per la versione web
  - `python-magic`: Per una migliore classificazione dei file (opzionale)
  - `tkinter`: Per la versione GUI (pre-installato con Python)

## Installazione

1. Clona o scarica il repository
2. Installa le dipendenze necessarie:

```bash
pip install flask python-magic
```

Per Windows, potrebbe essere necessario installare anche il binario 'magic':
[Istruzioni per Windows](https://github.com/ahupp/python-magic#dependencies)

## Limitazioni Note

- L'interfaccia web è limitata alle dimensioni di upload consentite dal server
- La classificazione dei file è più accurata con la libreria `python-magic` installata
- Alcuni tipi di file possono essere classificati in modo errato in base alla sola estensione

## Licenza

Questo progetto è distribuito con licenza MIT.