#!/bin/bash
echo "AI Operating System Status:"
echo "=========================="
ps aux | grep -E "(main.py|browser_server.py|system_operations_server.py|communication_server.py|ide_integration_server.py|github_actions_server.py|voice_ui_server.py)" | grep -v grep
