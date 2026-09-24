@echo off
title Space Debris AI Tracker - Local Server
echo ========================================================
echo   AEROSPACE AI // Space Debris Tracker & Collision Sim
echo ========================================================
echo.
echo Starting local web server on port 8080...
echo.
echo Access URL: http://localhost:8080
echo.
start http://localhost:8080
python -m http.server 8080
pause
