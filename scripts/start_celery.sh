#!/bin/bash

echo "=== Cleaning up existing Celery processes ==="

# Kill all existing Celery processes
echo "Stopping all Celery processes..."
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true
pkill -f "celery.*flower" 2>/dev/null || true

# Wait for processes to terminate
sleep 3

# Check if any Celery processes are still running
REMAINING=$(pgrep -f "celery.*worker" | wc -l)
if [ $REMAINING -gt 0 ]; then
    echo "Force killing remaining Celery processes..."
    pkill -9 -f "celery.*worker" 2>/dev/null || true
    sleep 2
fi

# Clean up any leftover PID files
rm -f /tmp/celery_*.pid 2>/dev/null || true

# Start Celery worker for pipeline tasks
echo "Starting Celery worker for pipeline tasks..."
celery -A app.tasks.worker.celery_app worker \
    --loglevel=info \
    --queues=pipeline,steps \
    --concurrency=4 \
    --hostname=pipeline-worker@%h \
    --detach \
    --pidfile=/tmp/celery_pipeline_worker.pid \
    --logfile=/tmp/celery_pipeline_worker.log

# Start Celery beat scheduler (if you have scheduled pipelines)
echo "Starting Celery beat scheduler..."
celery -A app.tasks.worker.celery_app beat \
    --loglevel=info \
    --detach \
    --pidfile=/tmp/celery_beat.pid \
    --logfile=/tmp/celery_beat.log

# Start Flower monitoring (optional)
echo "Starting Flower monitoring..."
celery -A app.tasks.worker.celery_app flower \
    --port=5555 \
    --detach \
    --pidfile=/tmp/celery_flower.pid \
    --logfile=/tmp/celery_flower.log

echo "All Celery services started successfully!"
echo "Flower monitoring available at http://localhost:5555"
