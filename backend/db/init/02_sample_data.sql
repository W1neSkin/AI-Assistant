-- Function to generate random date within last year
CREATE OR REPLACE FUNCTION random_date(start_date timestamp with time zone, end_date timestamp with time zone)
RETURNS timestamp with time zone AS $$
BEGIN
    RETURN start_date + (random() * EXTRACT(EPOCH FROM (end_date - start_date)) * INTERVAL '1 second');
END;
$$ LANGUAGE plpgsql;

-- Clear existing data
TRUNCATE clients, addresses, subscriptions, subscription_charges CASCADE;

-- Insert 100 clients
WITH client_data AS (
    SELECT 
        i as customer_id,
        (ARRAY['John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Emma', 'William', 'Olivia'])[floor(random()*10+1)] || ' ' || 
        chr(floor(65+random()*26)::int) || '.' as first_name,
        (ARRAY['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez'])[floor(random()*10+1)] as last_name,
        CASE WHEN random() < 0.8 THEN 'residential' ELSE 'business' END as customer_type,
        (ARRAY['standard', 'premium', 'vip'])[floor(random()*3+1)] as customer_group,
        random_date(CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 year') as created_at
    FROM generate_series(1, 100) i
)
INSERT INTO clients (customer_id, first_name, last_name, customer_type, customer_group, created_at)
SELECT * FROM client_data;

-- Insert addresses (90 unique addresses for 100 clients - 10% share addresses)
WITH address_data AS (
    SELECT 
        (ARRAY['Main St', 'Oak Ave', 'Maple Rd', 'Cedar Ln', 'Pine St', 'Elm Dr', 'Park Ave', 'Lake St', 'River Rd', 'Hill St'])[floor(random()*10+1)] as street,
        floor(random()*1000+1)::int as house,
        (ARRAY['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'])[floor(random()*10+1)] as city,
        floor(random()*90000+10000)::text as zip,
        floor(random()*100+1)::int as customer_id,
        random_date(CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 year') as created_at
    FROM generate_series(1, 90) i
)
INSERT INTO addresses (
    street,
    house,
    city,
    zip,
    customer_id,
    created_at
)
SELECT * FROM address_data;

-- Assign shared addresses to remaining 10 clients
INSERT INTO addresses (street, house, city, zip, customer_id, created_at)
SELECT 
    shared_addresses.street,
    shared_addresses.house,
    shared_addresses.city,
    shared_addresses.zip,
    c.customer_id,
    random_date(CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 year') as created_at
FROM clients c
LEFT JOIN addresses a ON c.customer_id = a.customer_id
CROSS JOIN (
    SELECT * FROM addresses ORDER BY random() LIMIT 10
) shared_addresses
WHERE a.address_id IS NULL;

-- Insert 10 subscriptions per client
WITH subscription_data AS (
    SELECT 
        row_number() OVER () as subscription_id,
        c.customer_id,
        (ARRAY['Basic', 'Standard', 'Premium', 'Business', 'Enterprise'])[floor(random()*5+1)] as rateplan,
        random_date(CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 year')::date as creation_date,
        a.address_id as installation_address_id,
        random_date(CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 year') as created_at
    FROM clients c
    CROSS JOIN generate_series(1, 10)
    JOIN addresses a ON c.customer_id = a.customer_id
)
INSERT INTO subscriptions (subscription_id, customer_id, rateplan, creation_date, installation_address_id, created_at)
SELECT * FROM subscription_data;

-- Insert 5 charges per subscription
WITH charge_data AS (
    SELECT 
        row_number() OVER () as charge_id,
        s.subscription_id,
        random_date(CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 year') as charge_datetime,
        (ARRAY['Monthly Fee', 'Usage Fee', 'Service Fee', 'Additional Services', 'One-time Charge'])[floor(random()*5+1)] as charge_name,
        (random() * 99.9 + 0.1)::numeric(10,2) as charge_amount,
        random_date(CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 year') as created_at
    FROM subscriptions s
    CROSS JOIN generate_series(1, 5)
)
INSERT INTO subscription_charges (charge_id, subscription_id, charge_datetime, charge_name, charge_amount, created_at)
SELECT * FROM charge_data; 