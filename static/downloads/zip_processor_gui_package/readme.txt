ZIP MEDIA SEPARATOR - Versione GUI
==================================

Questo pacchetto contiene l'applicazione ZIP Media Separator con interfaccia grafica (GUI).

REQUISITI:
----------
- Python 3.6 o superiore
- tkinter (pre-installato con Python)
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
1. Doppio click su "start_gui.bat" (Windows) o "start_gui.sh" (MacOS/Linux)
   
   OPPURE
   
2. Da terminale/prompt dei comandi:
   python zip_processor_gui.py

UTILIZZO:
---------
1. Avvia l'applicazione
2. Clicca "Sfoglia" per selezionare un file ZIP
3. Seleziona una cartella di destinazione (opzionale)
4. Clicca "Elabora File ZIP"
5. Attendi il completamento dell'elaborazione
6. I file ZIP risultanti saranno disponibili nella cartella di output

RISOLUZIONE PROBLEMI:
--------------------
- Se ricevi errori relativi a tkinter, assicurati che sia installato con Python
- Se l'applicazione è lenta, prova a installare python-magic per migliorare le prestazioni

Per assistenza: support@zipprocessor.example.com (esempio)