@echo off
REM Production Validation Script for Windows

echo.
echo 🔍 MAYA SOC Enterprise - Production Validation
echo =============================================="
echo.

REM Check Docker
echo 1️⃣  Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not installed
    exit /b 1
)
echo ✓ Docker ready
echo.

REM Check Docker Compose
echo 2️⃣  Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not installed
    exit /b 1
)
echo ✓ Docker Compose ready
echo.

REM Check Python
echo 3️⃣  Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not installed
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% ready
echo.

REM Check .env file
echo 4️⃣  Validating .env...
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo ⚠️  UPDATE .env with production values before deploying!
)
echo ✓ .env file exists
echo.

REM Check files
echo 5️⃣  Validating project structure...
set MISSING=0
for %%F in (
    "backend\Dockerfile"
    "backend\requirements.txt"
    "backend\app\main.py"
    "backend\app\core\config.py"
    "docker-compose.yml"
    ".env"
    ".env.example"
) do (
    if not exist %%F (
        echo ❌ Missing: %%F
        set MISSING=1
    )
)

if %MISSING%==0 (
    echo ✓ All required files present
) else (
    exit /b 1
)
echo.

REM Check Python syntax
echo 6️⃣  Checking Python syntax...
cd backend
python -m py_compile app\main.py app\core\config.py app\core\security.py ^
    app\core\event_bus.py app\models\event.py app\models\incident.py ^
    app\api\v1\endpoints.py >nul 2>&1

if errorlevel 1 (
    echo ❌ Python syntax errors found
    cd ..
    exit /b 1
)
cd ..
echo ✓ Python syntax valid
echo.

REM Validate docker-compose
echo 7️⃣  Validating docker-compose.yml...
docker-compose config >nul 2>&1
if errorlevel 1 (
    echo ❌ docker-compose.yml is invalid
    exit /b 1
)
echo ✓ docker-compose.yml valid
echo.

echo ✅ PRODUCTION VALIDATION PASSED
echo.
echo Ready to deploy. Run:
echo   docker-compose up --build
echo.
echo Then test:
echo   curl http://localhost:8000/health
echo.
