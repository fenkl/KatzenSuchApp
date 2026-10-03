#!/bin/bash
# KatzenSuchApp Local LAN Startup Script
# Für Tests mit PC als Server im LAN
# IP: 192.168.2.13, API Port: 5000

PROJECT_DIR="/home/cesco/PycharmProjects/KatzenSuchApp"
cd "$PROJECT_DIR"

# Environment check
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

echo "=========================================="
echo "KatzenSuchApp - Local LAN Startup"
echo "IP: 192.168.2.13"
echo "API Port: 5000"
echo "Flet UI Port: 8080"
echo "=========================================="

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "WARNING: .env.local nicht gefunden, nutze .env"
fi

# Function to start API
start_api() {
    echo "Starting FastAPI on http://192.168.2.13:5000"
    source .venv/bin/activate
    uvicorn api.main:app --host 0.0.0.0 --port 5000 --reload &
    API_PID=$!
    echo $API_PID > /tmp/katzensuchapp_api.pid
    echo "API PID: $API_PID"
}

# Function to start Scraper
start_scraper() {
    echo "Starting Scraper Orchestrator"
    source .venv/bin/activate
    python3 -m modules.services.orchestrator &
    SCRAPER_PID=$!
    echo $SCRAPER_PID > /tmp/katzensuchapp_scraper.pid
    echo "Scraper PID: $SCRAPER_PID"
}

# Function to start Flet UI
start_ui() {
    echo "Starting Flet UI on http://192.168.2.13:8080"
    source .venv/bin/activate
    # Use PYTHONPATH to ensure imports work
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    flet run flet_app/main.py --web --host 0.0.0.0 --port 8080 &
    UI_PID=$!
    echo $UI_PID > /tmp/katzensuchapp_ui.pid
    echo "UI PID: $UI_PID"
}

# Cleanup function
cleanup() {
    echo "Stopping all services..."
    [ -f /tmp/katzensuchapp_api.pid ] && kill $(cat /tmp/katzensuchapp_api.pid) 2>/dev/null
    [ -f /tmp/katzensuchapp_scraper.pid ] && kill $(cat /tmp/katzensuchapp_scraper.pid) 2>/dev/null
    [ -f /tmp/katzensuchapp_ui.pid ] && kill $(cat /tmp/katzensuchapp_ui.pid) 2>/dev/null
    rm -f /tmp/katzensuchapp_*.pid
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start services based on argument
case "${1:-all}" in
    api)
        start_api
        ;;
    scraper)
        start_scraper
        ;;
    ui)
        start_ui
        ;;
    all)
        start_api
        sleep 3
        start_scraper
        sleep 2
        start_ui
        echo ""
        echo "All services started!"
        echo "API: http://192.168.2.13:5000/docs"
        echo "UI:  http://192.168.2.13:8080"
        echo ""
        echo "Press Ctrl+C to stop all services"
        wait
        ;;
    stop)
        cleanup
        ;;
    *)
        echo "Usage: $0 [api|scraper|ui|all|stop]"
        echo "  api     - Start only FastAPI"
        echo "  scraper - Start only scraper"
        echo "  ui      - Start only Flet UI"
        echo "  all     - Start all services (default)"
        echo "  stop    - Stop all services"
        exit 1
        ;;
esac
