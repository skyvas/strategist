-- =============================================================================
-- Restaurant Table Management & Waitlist Schema (15-Table Constraint)
-- Target Database: PostgreSQL
-- =============================================================================

CREATE TYPE table_status AS ENUM ('AVAILABLE', 'CALLED', 'OCCUPIED', 'DIRTY');
CREATE TYPE queue_status AS ENUM ('WAITING', 'CALLED', 'SEATED', 'CANCELLED', 'EXPIRED');

-- 15 Physical Dining Tables
CREATE TABLE IF NOT EXISTS tables (
    table_number INT PRIMARY KEY,
    capacity INT NOT NULL,
    status table_status NOT NULL DEFAULT 'AVAILABLE',
    current_party_id INT NULL,
    seated_at TIMESTAMP WITH TIME ZONE NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Active & Historical Queue Entries
CREATE TABLE IF NOT EXISTS queue_entries (
    id SERIAL PRIMARY KEY,
    ticket_uuid VARCHAR(64) UNIQUE NOT NULL,
    guest_name VARCHAR(100) NOT NULL,
    party_size INT NOT NULL,
    phone_number VARCHAR(30) NOT NULL,
    status queue_status NOT NULL DEFAULT 'WAITING',
    assigned_table_number INT NULL REFERENCES tables(table_number),
    joined_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    called_at TIMESTAMP WITH TIME ZONE NULL,
    reminder_sent_at TIMESTAMP WITH TIME ZONE NULL,
    seated_at TIMESTAMP WITH TIME ZONE NULL,
    completed_at TIMESTAMP WITH TIME ZONE NULL
);

-- Event Audit Log
CREATE TABLE IF NOT EXISTS queue_audit_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    ticket_id INT NULL REFERENCES queue_entries(id),
    table_number INT NULL REFERENCES tables(table_number),
    payload JSONB NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Pre-seed 15 physical dining tables with defined seat capacities:
-- Tables 1–6: 2-Tops (Capacity: 2)
-- Tables 7–12: 4-Tops (Capacity: 4)
-- Tables 13–15: 6-Tops (Capacity: 6)
INSERT INTO tables (table_number, capacity, status)
VALUES
    (1, 2, 'AVAILABLE'),
    (2, 2, 'AVAILABLE'),
    (3, 2, 'AVAILABLE'),
    (4, 2, 'AVAILABLE'),
    (5, 2, 'AVAILABLE'),
    (6, 2, 'AVAILABLE'),
    (7, 4, 'AVAILABLE'),
    (8, 4, 'AVAILABLE'),
    (9, 4, 'AVAILABLE'),
    (10, 4, 'AVAILABLE'),
    (11, 4, 'AVAILABLE'),
    (12, 4, 'AVAILABLE'),
    (13, 6, 'AVAILABLE'),
    (14, 6, 'AVAILABLE'),
    (15, 6, 'AVAILABLE')
ON CONFLICT (table_number) DO NOTHING;
