@echo off
cd /d "%~dp0"
echo.
echo  Michelle's Recipe Admin Server
echo  --------------------------------
echo  Make sure Chrome is closed (or run copy_profile.py first)
echo.
python server.py
pause
