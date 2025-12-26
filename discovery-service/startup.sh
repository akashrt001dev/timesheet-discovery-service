#!/bin/bash

# Discovery Service (Eureka) - Startup Script

# PID file for tracking the running process
PID_FILE="/tmp/eureka-discovery-service.pid"

# Function to display usage
show_usage() {
    echo "Usage: $0 {start|stop|build|restart|status}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the service (default)"
    echo "  stop     - Stop the running service"
    echo "  build    - Build and start the service (install dependencies)"
    echo "  restart  - Restart the service"
    echo "  status   - Check if service is running"
}

# Function to start the service
start_service() {
    echo "=========================================="
    echo "Starting Eureka Discovery Service"
    echo "=========================================="

    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is not installed"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "Error: .env file not found"
        exit 1
    fi

    # Load environment variables
    export $(cat .env | grep -v '^#' | xargs)

    # Start the server with auto-reload enabled
    echo ""
    echo "Starting server on http://$EUREKA_INSTANCE_HOSTNAME:$SERVER_PORT"
    echo "=========================================="
    echo "Auto-reload is enabled - changes will be reloaded automatically"
    echo "=========================================="
    echo ""

    # Run in background and save PID
    uvicorn app.main:app --host $SERVER_HOST --port $SERVER_PORT --reload &
    echo $! > $PID_FILE

    wait
}

# Function to build and start
build_and_start() {
    echo "=========================================="
    echo "Building Eureka Discovery Service"
    echo "=========================================="

    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is not installed"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "Error: .env file not found"
        exit 1
    fi

    # Install dependencies
    echo ""
    echo "Installing dependencies..."

    # Check if pip is installed, if not install it
    if ! command -v pip3 &> /dev/null; then
        echo "pip3 not found. Installing pip..."
        python3 -m ensurepip --upgrade || {
            echo "Error: Failed to install pip via ensurepip"
            echo "Attempting alternative installation method..."
            sudo apt-get update && sudo apt-get install -y python3-pip || {
                echo "Error: Failed to install pip3"
                exit 1
            }
        }
    fi

    # Install requirements
    pip3 install -r requirements.txt

    # Check if installation was successful
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi

    # Start the service
    start_service
}

# Function to stop the service
stop_service() {
    echo "=========================================="
    echo "Stopping Eureka Discovery Service"
    echo "=========================================="

    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping process $PID..."
            kill $PID
            sleep 2
            # Force kill if still running
            if kill -0 $PID 2>/dev/null; then
                echo "Force stopping process $PID..."
                kill -9 $PID
            fi
            rm $PID_FILE
            echo "Service stopped successfully"
        else
            echo "Service is not running (PID $PID not found)"
            rm $PID_FILE
        fi
    else
        echo "Service is not running"
        # Try to find and kill any uvicorn process
        pkill -f "uvicorn app.main:app" || true
    fi

    echo "=========================================="
}

# Function to check status
check_status() {
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            echo "Service is running (PID: $PID)"
            return 0
        else
            echo "Service is not running (stale PID file)"
            rm $PID_FILE
            return 1
        fi
    else
        if pgrep -f "uvicorn app.main:app" > /dev/null; then
            echo "Service is running (detected by process search)"
            return 0
        else
            echo "Service is not running"
            return 1
        fi
    fi
}

# Main command handler
COMMAND=${1:-start}

case $COMMAND in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    build)
        build_and_start
        ;;
    restart)
        stop_service
        sleep 1
        start_service
        ;;
    status)
        check_status
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo ""
        show_usage
        exit 1
        ;;
esac
