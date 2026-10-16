@echo off
title PANDATEC Product Upload Checker
echo.
echo PANDATEC Product Upload Checker
echo --------------------------------
echo.
echo Open the new product folder in File Explorer, click the address bar,
echo copy the folder address, and paste it below.
echo Example: C:\Products\batch_2026-10-14
echo.
set /p BATCH_FOLDER=New product folder address: 
if "%BATCH_FOLDER%"=="" goto missing
echo.
python "%~dp0convert_products.py" "%BATCH_FOLDER%"
echo.
echo Finished. Read validation_report.txt in the batch folder.
pause
exit /b

:missing
echo No folder address was entered. Please run this file again.
pause
