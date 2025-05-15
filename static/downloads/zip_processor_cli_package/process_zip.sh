#!/bin/bash

if [ -z "$1" ]; then
    echo "Utilizzo: ./process_zip.sh percorso/al/file.zip"
    echo
    echo "Esempio: ./process_zip.sh ~/Download/mio_archivio.zip"
    exit 1
fi

echo "Elaborazione del file ZIP: $1"
python3 zip_processor_local.py "$@"
echo
echo "Elaborazione completata."