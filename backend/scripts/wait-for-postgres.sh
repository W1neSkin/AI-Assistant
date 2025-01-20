#!/bin/sh
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

# Maximum number of attempts
max_attempts=30
attempt=1

echo "Waiting for PostgreSQL to be ready..."
echo "Host: $host"
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'SELECT 1;' > /dev/null 2>&1; do
  # Try to get more specific error information
  error_msg=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB" 2>&1 || true)
  
  >&2 echo "Attempt $attempt of $max_attempts: PostgreSQL is unavailable - sleeping"
  >&2 echo "Error details: $error_msg"
  
  # Check if postgres is accepting connections
  if nc -z "$host" 5432 2>/dev/null; then
    echo "Port 5432 is open, but connection failed"
  else
    echo "Port 5432 is not accessible yet"
  fi

  sleep 1
  attempt=$(( attempt + 1 ))
  if [ $attempt -gt $max_attempts ]; then
    >&2 echo "ERROR: Could not connect to PostgreSQL after $max_attempts attempts"
    >&2 echo "Last error: $error_msg"
    >&2 echo "Please check:"
    >&2 echo "1. PostgreSQL container is running (docker ps)"
    >&2 echo "2. Database credentials are correct"
    >&2 echo "3. Database $POSTGRES_DB exists"
    >&2 echo "4. Network connectivity between containers"
    exit 1
  fi
done

>&2 echo "PostgreSQL is up and accepting connections"
>&2 echo "Database $POSTGRES_DB is ready"
>&2 echo "Executing command: $cmd"
exec $cmd 