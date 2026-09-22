@echo off
setlocal
cd /d "%~dp0"

echo Instaluje zaleznosci (opencv-python, numpy, scipy, flask)...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Blad instalacji zaleznosci. Sprawdz, czy Python i pip sa zainstalowane i w PATH.
    pause
    exit /b 1
)

echo.
echo Uruchamiam dashboard (http://localhost:5050)...
python app.py
if errorlevel 1 (
    echo.
    echo Dashboard zakonczyl sie bledem - zobacz komunikat powyzej.
)

pause
