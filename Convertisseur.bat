@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"

if not exist "%PY%" goto install
"%PY%" -c "import flask, pymupdf, PIL, pillow_heif, pdf2docx, openpyxl, pptx, faster_whisper, yt_dlp, pysubs2, segno, barcode, zxingcpp" 1>nul 2>nul || goto install
goto run

:install
echo.
echo  Convertisseur - installation des composants (premiere utilisation, quelques minutes)...
echo  Convertisseur - installing components (first launch, a few minutes)...
echo.
if not exist "%PY%" (
  where py >nul 2>nul && (py -3 -m venv .venv) || (python -m venv .venv)
)
if not exist "%PY%" (
  echo  Python 3 est introuvable. Installez-le depuis https://www.python.org puis relancez ce fichier.
  echo  Python 3 was not found. Install it from https://www.python.org, then run this file again.
  pause
  exit /b 1
)
"%PY%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo  L'installation a echoue. Verifiez votre connexion Internet puis relancez.
  echo  The installation failed. Check your Internet connection, then try again.
  pause
  exit /b 1
)

:run
start "" ".venv\Scripts\pythonw.exe" "%~dp0app.py"
endlocal
