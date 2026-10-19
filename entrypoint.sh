#!/bin/sh
set -eu

# A API so inicia quando todas as revisoes do banco estiverem aplicadas.
echo "Aplicando migracoes Alembic..."
alembic upgrade head

echo "Iniciando TaskFlow API..."
exec "$@"
