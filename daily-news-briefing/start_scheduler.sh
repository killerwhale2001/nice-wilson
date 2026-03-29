#!/bin/bash
# Usage: ./start_scheduler.sh [start|stop|status]
#   start  — run scheduler in background (default if no argument given)
#   stop   — stop the running scheduler
#   status — check if scheduler is running

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/scheduler.pid"
LOG_FILE="$SCRIPT_DIR/logs/scheduler.log"

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Scheduler is already running (PID $(cat "$PID_FILE"))"
        exit 1
    fi

    cd "$SCRIPT_DIR"
    source ~/.zshrc 2>/dev/null || true

    mkdir -p logs
    nohup python3 scheduler.py >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Scheduler started (PID $(cat "$PID_FILE")). Logs: $LOG_FILE"
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "No PID file found — scheduler may not be running."
        exit 1
    fi
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        echo "Scheduler stopped (PID $PID)."
    else
        echo "Process $PID not found — removing stale PID file."
        rm -f "$PID_FILE"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Scheduler is running (PID $(cat "$PID_FILE"))."
    else
        echo "Scheduler is not running."
    fi
}

case "${1:-start}" in
    start)  start ;;
    stop)   stop ;;
    status) status ;;
    *)      echo "Usage: $0 [start|stop|status]" ;;
esac
