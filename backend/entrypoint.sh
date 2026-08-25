#!/bin/sh
set -eu

alembic upgrade head

if [ "${AUTO_SEED:-false}" = "true" ]; then
  python -m app.database.seed
fi

exec "$@"

