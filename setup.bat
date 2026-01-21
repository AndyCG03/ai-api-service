@echo off
echo ========================================
echo Setup de AI API Service
echo ========================================
echo.

echo [1/5] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo Error al crear entorno virtual
    pause
    exit /b 1
)

echo [2/5] Activando entorno virtual...
call venv\Scripts\activate.bat

echo [3/5] Actualizando pip...
python -m pip install --upgrade pip

echo [4/5] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error al instalar dependencias
    pause
    exit /b 1
)

echo [5/5] Copiando archivo de configuracion...
if not exist .env (
    copy .env.example .env
    echo Archivo .env creado. Por favor, editalo con tu configuracion.
) else (
    echo El archivo .env ya existe.
)

echo.
echo ========================================
echo Setup completado exitosamente!
echo ========================================
echo.
echo Para ejecutar la API:
echo   1. Activa el entorno: venv\Scripts\activate
echo   2. Ejecuta: python app/main.py
echo.
pause
