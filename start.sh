#!/bin/bash
echo "Starting AI Operating System..."
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):$(dirname "$(pwd)")"
source .venv/bin/activate
nohup ./.venv/bin/uvicorn gpt_oss_mcp_server.main_mcp_server:mcp --host 0.0.0.0 --port 9000 > uvicorn.log 2>&1 &
sleep 5
echo "All servers started. Check logs for details."}]}}}}]}}}
