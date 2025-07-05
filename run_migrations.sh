#!/bin/bash

# Run migrations for the homework app

echo "Creating and applying migrations..."

# Create migrations for homework app
python manage.py makemigrations homework

# Show what will be migrated
python manage.py showmigrations homework

# Apply migrations
python manage.py migrate

echo "Migrations complete!"