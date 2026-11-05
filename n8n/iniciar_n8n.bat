@echo off
title n8n Local

REM ============================================================
REM RUTAS PERMITIDAS PARA READ/WRITE FILES FROM DISK
REM Igual que tu .bat, mas C:\videos-youtube\publicar para la cola de videos
REM ============================================================

set "N8N_RESTRICT_FILE_ACCESS_TO=C:\automatic;C:\piensarapido;C:\minecraft;C:\videos-youtube\publicar"
set "NODES_EXCLUDE=[]"

echo.
echo ==========================================
echo       INICIANDO N8N LOCAL
echo ==========================================
echo Rutas permitidas:
echo   - C:\automatic
echo   - C:\piensarapido
echo   - C:\minecraft
echo   - C:\videos-youtube\publicar
echo.
echo Nodos excluidos: %NODES_EXCLUDE%
echo ==========================================
echo.

REM Mini panel of the channels (bottom-right corner): coverage, queue and next video
start "" "C:\Users\david\AppData\Local\Programs\Python\Python313\pythonw.exe" "C:\videos-youtube\publicar\panel\panel.pyw"

n8n start

pause
