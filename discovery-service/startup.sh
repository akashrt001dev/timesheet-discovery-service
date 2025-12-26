#!/bin/bash

# Discovery Service (Eureka) - Startup Script

# PID file for tracking the running process
PID_FILE="/tmp/eureka-discovery-service.pid"

# Function to display usage
show_usage() {
    echo "Usage: $0 {start|stop|build|restart|status|logs|health}"
    echo ""
    echo "Commands:"
    echo "  start         - Start the service (default)"
    echo "  stop          - Stop the running service"
    echo "  build         - Build and start the service (install dependencies)"
    echo "  restart       - Restart the service"
    echo "  status        - Check if service is running"
    echo "  logs          - Show last 30 lines of logs"
    echo "  logs follow   - Follow logs in real-time (Ctrl+C to exit)"
    echo "  health        - Check service health endpoint"
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

# Function to show logs (last 30 lines)
show_logs() {
    echo "=========================================="
    echo "Last 30 lines of service output"
    echo "=========================================="
    
    # Try to find docker container logs if running in docker
    if command -v docker &> /dev/null; then
        CONTAINER_ID=$(docker ps -q -f "ancestor=eureka-discovery-service" 2>/dev/null)
        if [ -n "$CONTAINER_ID" ]; then
            docker logs --tail 30 $CONTAINER_ID
            return 0
        fi
    fi
    
    # Fallback to system logs if available
    if [ -f /var/log/eureka-discovery-service.log ]; then
        tail -30 /var/log/eureka-discovery-service.log
    else
        echo "No logs found. Service may not be running."
        echo "Try running: sudo ./startup.sh logs follow"
    fi
}

# Function to follow logs in real-time
follow_logs() {
    echo "=========================================="
    echo "Following service logs (Press Ctrl+C to stop)"
    echo "=========================================="
    
    # Try docker logs if available
    if command -v docker &> /dev/null; then
        CONTAINER_ID=$(docker ps -q -f "ancestor=eureka-discovery-service" 2>/dev/null)
        if [ -n "$CONTAINER_ID" ]; then
            docker logs -f --tail 50 $CONTAINER_ID
            return 0
        fi
    fi
    
    # Fallback to system logs
    if [ -f /var/log/eureka-discovery-service.log ]; then
        tail -f /var/log/eureka-discovery-service.log
    else
        echo "Error: Could not find service logs"
        echo "Make sure service is running: sudo ./startup.sh status"
    fi
}

# Function to check service health
check_health() {
    echo "=========================================="
    echo "Checking Service Health"
    echo "=========================================="
    
    # Load .env to get the port
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
        PORT=${SERVER_PORT:-8761}
        HOST=${SERVER_HOST:-0.0.0.0}
    else
        PORT=8761
        HOST=127.0.0.1
    fi
    
    # Check health endpoint
    echo "Checking http://$HOST:$PORT/health..."
    
    RESPONSE=$(curl -s -w "\n%{http_code}" http://$HOST:$PORT/health 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Service is HEALTHY (HTTP $HTTP_CODE)"
        echo ""
        echo "Response:"
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    else
        echo "❌ Service is UNHEALTHY (HTTP $HTTP_CODE)"
        echo "Response: $BODY"
        return 1
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
    logs)
        if [ "$2" = "follow" ]; then
            follow_logs
        else
            show_logs
        fi
        ;;
    health)
        check_health
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
