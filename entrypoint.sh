#!/bin/bash

# Apply database migrations
python /app/webhook_dialogflow/manage.py migrate

# Collect static files
python /app/webhook_dialogflow/manage.py collectstatic --noinput

# Start Gunicorn server
cd /app/webhook_dialogflow
exec gunicorn webhook_dialogflow.wsgi:application --bind 0.0.0.0:8000