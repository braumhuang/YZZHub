@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 (
    echo [ERROR] Cannot enter the project directory.
    echo Please move the project to a writable local folder.
    pause
    exit /b 1
)

set "BUILD_LOG=%CD%\build_win.log"
set "STEP_LOG=%TEMP%\YZZHub_build_step_%RANDOM%.log"
> "%BUILD_LOG%" echo YZZ Hub Windows build log
>> "%BUILD_LOG%" echo Project: %CD%
>> "%BUILD_LOG%" echo Started: %DATE% %TIME%

echo ============================================================
echo YZZ Hub Windows build
echo Log: %BUILD_LOG%
echo ============================================================

call :main
set "BUILD_RESULT=%ERRORLEVEL%"

if exist "%STEP_LOG%" del /q "%STEP_LOG%" >nul 2>&1
echo.
if "%BUILD_RESULT%"=="0" (
    echo [SUCCESS] Build completed.
    echo Output: %CD%\dist\YZZ Hub.exe
) else (
    echo [FAILED] Build stopped with exit code %BUILD_RESULT%.
    echo Please review the error shown above and the log file:
    echo %BUILD_LOG%
)
echo.
echo Press any key to close this window...
pause >nul
exit /b %BUILD_RESULT%


:main
rem Prefer project-local environments in this order: .venv, then venv.
rem Only use PY or system Python when neither local environment exists.
if exist ".venv\Scripts\python.exe" goto use_dotvenv
if exist "venv\Scripts\python.exe" goto use_venv
if defined PY goto use_py_override
set "PY=python"
set "PY_SOURCE=system Python from PATH"
goto python_selected

:use_dotvenv
set "PY=%CD%\.venv\Scripts\python.exe"
set "PY_SOURCE=project .venv"
goto python_selected

:use_venv
set "PY=%CD%\venv\Scripts\python.exe"
set "PY_SOURCE=project venv"
goto python_selected

:use_py_override
set "PY_SOURCE=PY environment variable"

:python_selected
echo [INFO] Python source: %PY_SOURCE%
echo [INFO] Python command: %PY%
"%PY%" --version > "%STEP_LOG%" 2>&1
set "STEP_RC=%ERRORLEVEL%"
type "%STEP_LOG%"
type "%STEP_LOG%" >> "%BUILD_LOG%"
if not "%STEP_RC%"=="0" (
    echo [ERROR] Cannot start the selected Python interpreter: %PY%
    echo Check Python installation and PATH. >> "%BUILD_LOG%"
    exit /b 1
)

"%PY%" -c "import sys; print('.'.join(str(x) for x in sys.version_info[:3]))" > "%STEP_LOG%" 2>&1
set "STEP_RC=%ERRORLEVEL%"
if not "%STEP_RC%"=="0" (
    type "%STEP_LOG%"
    type "%STEP_LOG%" >> "%BUILD_LOG%"
    echo [ERROR] Cannot read the Python version.
    exit /b 1
)
set /p PY_VERSION=<"%STEP_LOG%"
"%PY%" -c "import sys; print(sys.version_info.minor)" > "%STEP_LOG%" 2>&1
set "STEP_RC=%ERRORLEVEL%"
if not "%STEP_RC%"=="0" (
    type "%STEP_LOG%"
    type "%STEP_LOG%" >> "%BUILD_LOG%"
    echo [ERROR] Cannot detect the Python minor version.
    exit /b 1
)
set /p PY_MINOR=<"%STEP_LOG%"
"%PY%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8, 5) else 1)" > "%STEP_LOG%" 2>&1
set "STEP_RC=%ERRORLEVEL%"
if not "%STEP_RC%"=="0" (
    echo [ERROR] Python 3.8.5 or later is required. Detected: %PY_VERSION%.
    echo Detected Python: %PY_VERSION% >> "%BUILD_LOG%"
    exit /b 1
)
echo [INFO] Detected Python %PY_VERSION%.
echo Detected Python: %PY_VERSION% >> "%BUILD_LOG%"

if "%PY_MINOR%"=="8" goto python38
if %PY_MINOR% GTR 8 (
    echo [NOTICE] Python 3.9+ does not support Windows 7.
    echo [NOTICE] This executable is intended for Windows 8.1 or later.
    echo Python 3.9+ selected: Windows 8.1+ target. >> "%BUILD_LOG%"
)
goto install_pip

:python38
echo [NOTICE] Python 3.8 selected: using the Win7-oriented dependency tooling.
echo Python 3.8 selected: Win7-oriented build path. >> "%BUILD_LOG%"

:install_pip
echo.
echo [1/6] Preparing pip...
if "%PY_MINOR%"=="8" (
    "%PY%" -m pip install --upgrade "pip<25" > "%STEP_LOG%" 2>&1
) else (
    "%PY%" -m pip install --upgrade pip > "%STEP_LOG%" 2>&1
)
set "STEP_RC=%ERRORLEVEL%"
type "%STEP_LOG%"
type "%STEP_LOG%" >> "%BUILD_LOG%"
if not "%STEP_RC%"=="0" (
    echo [ERROR] pip upgrade failed. See build_win.log.
    exit /b 1
)

 echo.
echo [2/6] Installing application dependencies...
"%PY%" -m pip install -r requirements.txt > "%STEP_LOG%" 2>&1
set "STEP_RC=%ERRORLEVEL%"
type "%STEP_LOG%"
type "%STEP_LOG%" >> "%BUILD_LOG%"
if not "%STEP_RC%"=="0" (
    echo [ERROR] Dependency installation failed. See build_win.log.
    exit /b 1
)

"%PY%" -c "import sys, certifi; from PyQt5 import QtCore, QtGui, QtWidgets; PYQT_VERSION_STR=QtCore.PYQT_VERSION_STR; assert sys.version_info >= (3,8,5); assert PYQT_VERSION_STR == '5.15.11', 'PyQt5 must be 5.15.11'; assert certifi.where(), 'certifi CA bundle missing'; print('PyQt5', PYQT_VERSION_STR, '| certifi OK | Qt GUI imports OK')" > "%STEP_LOG%" 2>&1
set "STEP_RC=%ERRORLEVEL%"
type "%STEP_LOG%"
type "%STEP_LOG%" >> "%BUILD_LOG%"
if not "%STEP_RC%"=="0" (
    echo [ERROR] Runtime dependency verification failed. See build_win.log.
    exit /b 1
)

if "%PY_MINOR%"=="8" goto install_pyinstaller38
goto install_pyinstaller_modern

:install_pyinstaller38
echo.
echo [3/6] Installing Win7-oriented packaging tools for Python 3.8...
"%PY%" -m pip install --upgrade --force-reinstall "pyinstaller==4.10" "pyinstaller-hooks-contrib==2022.15" > "%STEP_LOG%" 2>&1
goto check_pyinstaller

:install_pyinstaller_modern
echo.
echo [3/6] Installing packaging tools for modern Windows...
"%PY%" -m pip install --upgrade "pyinstaller>=5.13.2,<7" > "%STEP_LOG%" 2>&1

:check_pyinstaller
set "STEP_RC=%ERRORLEVEL%"
type "%STEP_LOG%"
type "%STEP_LOG%" >> "%BUILD_LOG%"
if not "%STEP_RC%"=="0" (
    echo [ERROR] PyInstaller installation failed. See build_win.log.
    exit /b 1
)

"%PY%" -c "from yzzhub import APP_VERSION; print(APP_VERSION)" > "%STEP_LOG%" 2>&1
set "STEP_RC=%ERRORLEVEL%"
if not "%STEP_RC%"=="0" (
    type "%STEP_LOG%"
    type "%STEP_LOG%" >> "%BUILD_LOG%"
    echo [ERROR] Cannot read APP_VERSION from yzzhub.
    exit /b 1
)
set /p APP_VERSION=<"%STEP_LOG%"
if not defined APP_VERSION (
    echo [ERROR] APP_VERSION from yzzhub is empty.
    exit /b 1
)
echo APP_VERSION: %APP_VERSION% >> "%BUILD_LOG%"
echo.
echo [4/6] Synchronizing application version: %APP_VERSION%
"%PY%" tools\sync_version.py "%APP_VERSION%" > "%STEP_LOG%" 2>&1
set "STEP_RC=%ERRORLEVEL%"
type "%STEP_LOG%"
type "%STEP_LOG%" >> "%BUILD_LOG%"
if not "%STEP_RC%"=="0" (
    echo [ERROR] Version synchronization failed. See build_win.log.
    exit /b 1
)

if exist "dist\YZZ Hub.exe" del /f /q "dist\YZZ Hub.exe"
if exist "build\YZZ Hub" rmdir /s /q "build\YZZ Hub"
if not exist "YZZ Hub.spec" (
    echo [ERROR] YZZ Hub.spec is missing. The spec file pins the
    echo [ERROR] Win7-compatible VC++ runtime and is required for the build.
    exit /b 1
)
if not exist "dist" mkdir "dist"

echo.
echo [5/6] Building one-file Windows executable...
rem The spec file replaces the command line options: --onefile --windowed
rem --name --icon --version-file --add-data are defined inside "YZZ Hub.spec".
rem It also pins msvcp140*.dll / vcruntime140*.dll to the copies shipped in
rem the PyQt5 wheel (PyQt5\Qt5\bin), so building on a machine with a newer
rem system VC++ runtime (e.g. GitHub Actions runners) cannot leak runtime
rem DLLs that require a newer Universal CRT than Windows 7 provides.
"%PY%" -m PyInstaller --noconfirm --clean --distpath "dist" --workpath "build" "YZZ Hub.spec" > "%STEP_LOG%" 2>&1
set "STEP_RC=%ERRORLEVEL%"
type "%STEP_LOG%"
type "%STEP_LOG%" >> "%BUILD_LOG%"
if not "%STEP_RC%"=="0" (
    echo [ERROR] PyInstaller build failed. See build_win.log.
    exit /b 1
)

if not exist "dist\YZZ Hub.exe" (
    echo [ERROR] Build finished without dist\YZZ Hub.exe.
    exit /b 1
)
if not exist "build\YZZ Hub\warn-YZZ Hub.txt" (
    echo [ERROR] PyInstaller warning report is missing.
    exit /b 1
)
rem PyInstaller's warn file may list optional Qt integrations; their absence
rem is not a build failure. Required PyQt5/certifi imports were checked above;
rem PyInstaller itself must exit successfully and produce the EXE.
echo [INFO] PyInstaller warning report saved to build\YZZ Hub\warn-YZZ Hub.txt
echo [INFO] Optional integration warnings are informational, not fatal.
echo PyInstaller warning report: build\YZZ Hub\warn-YZZ Hub.txt >> "%BUILD_LOG%"
echo Optional integration warnings are informational. >> "%BUILD_LOG%"

echo.
echo [6/6] Verifying output...
for %%F in ("dist\YZZ Hub.exe") do echo Output: %%~fF ^(%%~zF bytes^)
echo Python source: %PY_SOURCE%
echo [SUCCESS] YZZ Hub v%APP_VERSION% Windows one-file build completed.
if "%PY_MINOR%"=="8" (
    echo Target: Windows 7 SP1 and later ^(Win7 compatibility still requires testing^).
) else (
    echo Target: Windows 8.1 and later.
)
>> "%BUILD_LOG%" echo Build succeeded: YZZ Hub v%APP_VERSION%
exit /b 0
