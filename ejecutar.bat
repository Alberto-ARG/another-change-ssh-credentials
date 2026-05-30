@echo off
REM Lanza la GUI del gestor de credenciales con doble clic.
REM Usa pythonw (Python sin consola) para no dejar una ventana negra de fondo.
REM 'start' lanza la GUI desacoplada y este .bat cierra su consola enseguida.
start "" pythonw "%~dp0app.py"
