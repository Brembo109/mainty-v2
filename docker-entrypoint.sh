#!/bin/bash
set -e

echo "Building Tailwind CSS..."
tailwindcss -i static/src/main.css -o static/dist/main.css --minify

echo "Waiting for database..."
until pg_isready -h "${POSTGRES_HOST:-db}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-mainty}"; do
    echo "  ... still waiting"
    sleep 1
done
echo "Database ready."

echo "Running migrations..."
python manage.py migrate --noinput

if [ "${DJANGO_SETTINGS_MODULE}" = "mainty.settings.production" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

exec "$@"
