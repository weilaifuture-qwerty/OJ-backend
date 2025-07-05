#!/bin/bash

echo "Starting Dramatiq worker for judge tasks..."

# Activate virtual environment
source oj_env/bin/activate

# Start dramatiq worker
echo "Running: python manage.py rundramatiq"
python manage.py rundramatiq