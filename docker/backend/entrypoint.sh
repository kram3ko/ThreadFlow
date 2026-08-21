#!/bin/sh
set -eu

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

python manage.py collectstatic --noinput --clear
python manage.py migrate --noinput
python manage.py ensure_storage_bucket
python manage.py seed_demo
exec uvicorn config.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --proxy-headers \
    --forwarded-allow-ips "*" \
    --ws-ping-interval "${WS_HEARTBEAT_INTERVAL_SECONDS:-20}"
