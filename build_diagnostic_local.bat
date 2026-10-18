@echo off
title DrawMotion Diagnostic Local Build
echo ========================================================
echo   Building DrawMotion Diagnostic Build Locally (v1.7.8)
echo ========================================================

:: Run Nuitka Standalone Compilation
venv\Scripts\python.exe -m nuitka ^
  --standalone ^
  --plugin-enable=pyside6 ^
  --include-qt-plugins=sensible,multimedia,imageformats,iconengines ^
  --assume-yes-for-downloads ^
  --windows-icon-from-ico="resources/branding/ICO/DrawMotion.ico" ^
  --windows-console-mode=force ^
  --include-package=components ^
  --include-package=core ^
  --include-package=advanced_features ^
  --include-package=graphics ^
  --include-package=services ^
  --include-package=asset_library ^
  --include-package=utils ^
  --include-package=models ^
  --include-data-dir="resources=resources" ^
  --include-data-dir="bin=bin" ^
  --include-data-dir="assets=assets" ^
  --include-data-dir="core/security_engine/bin=core/security_engine/bin" ^
  --include-data-dir="docs=docs" ^
  --nofollow-import-to=scipy ^
  --output-dir="dist_local" ^
  --output-filename="DrawMotion" ^
  main.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Nuitka build failed with code %ERRORLEVEL%.
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo   Copying Debug_DrawMotion.bat into distribution folder
echo ========================================================

if exist "dist_local\main.dist" (
    copy /Y "build_assets\Debug_DrawMotion.bat" "dist_local\main.dist\Debug_DrawMotion.bat"
    echo Diagnostic runner ready at: dist_local\main.dist\Debug_DrawMotion.bat
)
if exist "dist_local\DrawMotion.dist" (
    copy /Y "build_assets\Debug_DrawMotion.bat" "dist_local\DrawMotion.dist\Debug_DrawMotion.bat"
    echo Diagnostic runner ready at: dist_local\DrawMotion.dist\Debug_DrawMotion.bat
)

echo.
echo ========================================================
echo   LOCAL BUILD SUCCESSFUL!
echo ========================================================
