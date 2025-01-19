-- Create tables
CREATE TABLE clients (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    customer_type VARCHAR(50) NOT NULL,
    customer_group VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE addresses (
    address_id SERIAL PRIMARY KEY,
    zip VARCHAR(20) NOT NULL,
    city VARCHAR(100) NOT NULL,
    street VARCHAR(200) NOT NULL,
    house INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES clients(customer_id) ON DELETE CASCADE
);

CREATE TABLE subscriptions (
    subscription_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    rateplan VARCHAR(100) NOT NULL,
    creation_date DATE NOT NULL,
    installation_address_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES clients(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (installation_address_id) REFERENCES addresses(address_id) ON DELETE CASCADE
);

CREATE TABLE subscription_charges (
    charge_id SERIAL PRIMARY KEY,
    charge_datetime TIMESTAMP NOT NULL,
    charge_name VARCHAR(200) NOT NULL,
    charge_amount INTEGER NOT NULL,
    subscription_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_clients_customer_type ON clients(customer_type);
CREATE INDEX idx_clients_customer_group ON clients(customer_group);
CREATE INDEX idx_addresses_customer_id ON addresses(customer_id);
CREATE INDEX idx_subscriptions_customer_id ON subscriptions(customer_id);
CREATE INDEX idx_subscription_charges_subscription_id ON subscription_charges(subscription_id); 