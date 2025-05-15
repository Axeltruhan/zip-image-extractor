@echo off
if "%~1"=="" (
    echo Utilizzo: process_zip.bat percorso/al/file.zip
    echo.
    echo Esempio: process_zip.bat C:\Download\mio_archivio.zip
    goto :eof
)

echo Elaborazione del file ZIP: %1
python zip_processor_local.py %*
echo.
echo Elaborazione completata.
pause