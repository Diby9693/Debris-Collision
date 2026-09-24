@echo off
title Space Debris AI Tracker - Public Live Link Tunnel
echo ========================================================
echo   GENERATING PUBLIC LIVE HTTPS LINK VIA SECURE TUNNEL
echo ========================================================
echo.
echo Make sure the local server (START_APP.bat) is running on port 8080!
echo Connecting to secure tunnel...
echo.
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=15 -R 80:localhost:8080 nokey@localhost.run
pause
