#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        use_cloud BOOLEAN DEFAULT FALSE,
        enable_document_search BOOLEAN DEFAULT FALSE,
        handle_urls BOOLEAN DEFAULT FALSE,
        check_db BOOLEAN DEFAULT FALSE
    );
    -- Add other table creation statements here

    -- Insert initial data
    INSERT INTO users (username, hashed_password, use_cloud)
    VALUES ('admin', '\$2b\$12\$dBWYvhpifGC2vW09dXjT/.lJkIP0O0EpLZYRc2QWuqnfblsBcm/ra', TRUE)
    ON CONFLICT (username) DO NOTHING;

    -- Add other INSERT statements here
EOSQL

# You can add other shell commands here if needed. 