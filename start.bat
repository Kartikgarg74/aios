@echo off
echo Starting AI Operating System...
cd /d "%~dp0"
start python main.py
start python browser_server.py
start python system_operations_server.py
start python communication_server.py
start python ide_integration_server.py
start python github_actions_server.py
start python voice_ui_server.py
echo All servers started. Check logs for details.
pause
