-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    use_cloud BOOLEAN DEFAULT FALSE,
    enable_document_search BOOLEAN DEFAULT FALSE,
    handle_urls BOOLEAN DEFAULT FALSE,
    check_db BOOLEAN DEFAULT FALSE
);

-- Add any other table creation statements here.  Make sure to use
-- "CREATE TABLE IF NOT EXISTS" to ensure idempotency.

-- Insert initial data (e.g., an admin user)
-- IMPORTANT: Use a secure, hashed password in a real application!
-- This is just an example.
INSERT INTO users (username, hashed_password, use_cloud)
VALUES ('admin', '$2b$12$dBWYvhpifGC2vW09dXjT/.lJkIP0O0EpLZYRc2QWuqnfblsBcm/ra', TRUE)  -- Replace with a real hash
ON CONFLICT (username) DO NOTHING; -- Important for idempotency!

-- Add other INSERT statements for any other initial data you need. 