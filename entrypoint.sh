#!/bin/bash

# Apply Alembic migrations from migrations dir
alembic upgrade head

# Run your application
exec "$@"
