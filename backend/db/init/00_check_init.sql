\connect customerdb;

-- Create table to track initialization status
CREATE TABLE IF NOT EXISTS db_init_status (
    init_id SERIAL PRIMARY KEY,
    init_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    init_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL
);

-- Function to check if specific initialization was done
CREATE OR REPLACE FUNCTION check_init(init_name VARCHAR) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM db_init_status 
        WHERE init_type = init_name 
        AND status = 'completed'
    );
END;
$$ LANGUAGE plpgsql; 