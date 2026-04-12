#!/bin/sh

echo "Waiting for Redis..."
until python -c "import redis; redis.from_url('${BLOG_REDIS_URL:-redis://redis:6379/0}').ping()" 2>/dev/null; do
    sleep 1
done
echo "Redis is ready!"

python3 manage.py migrate --noinput
python3 manage.py collectstatics --noinput
python3 manage.py compilemessages || true

if ["${BLOG_SEED_DB}" = "true"]; then
    echo "Seeding db.."
    python3 manage.py seed
fi

exec "$@"