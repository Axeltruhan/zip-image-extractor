ZIP MEDIA SEPARATOR - Versione a Riga di Comando
=============================================

Questo pacchetto contiene l'applicazione ZIP Media Separator a riga di comando (CLI).

REQUISITI:
----------
- Python 3.6 o superiore
- python-magic (opzionale, per una classificazione migliore)

INSTALLAZIONE:
-------------
1. Assicurati di avere Python 3.6 o superiore installato

   Se non hai Python installato, segui queste istruzioni:
   
   Vai al sito ufficiale:
   👉 https://www.python.org/downloads/

   Clicca su Download Python 3.x.x (la versione più recente).

   Molto importante: nella schermata di installazione, spunta la casella
   ✅ "Add Python to PATH"
   prima di cliccare su "Install Now".

2. (Opzionale) Installa python-magic per una migliore classificazione dei file:
   pip install python-magic

   Per Windows potrebbe essere necessario installare anche il binario 'magic'
   Vedi: https://github.com/ahupp/python-magic#dependencies

ESECUZIONE:
-----------
1. Da terminale/prompt dei comandi:
   python zip_processor_local.py percorso/al/file.zip [opzioni]

   Esempio:
   python zip_processor_local.py mio_archivio.zip -o cartella_output

   Opzioni:
   -o, --output-dir   Directory di output (opzionale)
   -v, --verbose      Output dettagliato (opzionale)

2. In alternativa, usa gli script di avvio rapido:
   
   Windows:
   process_zip.bat percorso/al/file.zip
   
   MacOS/Linux:
   ./process_zip.sh percorso/al/file.zip

RISOLUZIONE PROBLEMI:
--------------------
- Se ricevi errori relativi a percorsi, assicurati di utilizzare le virgolette se i percorsi contengono spazi:
  python zip_processor_local.py "percorso con spazi/mio_archivio.zip"
  
- Se l'applicazione è lenta, prova a installare python-magic per migliorare le prestazioni

Per assistenza: support@zipprocessor.example.com (esempio)