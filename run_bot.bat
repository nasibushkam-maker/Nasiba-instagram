@echo off
title Nasiba Instagram Bot
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo       Instagram Video Downloader Bot ишга тушмоқда...
echo ========================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ХАТОЛИК] Виртуал муҳит (venv) топилмади!
    pause
    exit /b
)

venv\Scripts\python.exe main.py

pause
