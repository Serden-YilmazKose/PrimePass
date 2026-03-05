-- populate_manual.sql
-- Run with: docker exec -i primepass-db mysql -u root -ppass < populate_manual.sql

-- ========== USER DATABASE ==========
USE user_db;

-- Insert demo user (password: password123)
INSERT INTO USERS (id, name, email, password_hash, status, created_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'demo_user',
    'demo@primepass.com',
    'scrypt:32768:8:1$t7CQvI2fFqW5e3tW$c2f7e1f8a0e5c3a7d8b4a2f1e6d9c8b7a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0',
    'active',
    NOW()
);

-- ========== EVENT DATABASE ==========
USE event_db;

-- Event 1: Nordic Music Festival
INSERT INTO EVENT (title, venue, city, description, starts_at, ends_at, status)
VALUES (
    'Nordic Music Festival',
    'Central Park Arena',
    'Helsinki',
    'A full-day outdoor music festival featuring Nordic artists.',
    '2026-06-15 12:00:00',
    '2026-06-15 23:00:00',
    'active'
);
SET @event1_id = LAST_INSERT_ID();

-- Event 2: Arctic Tech Summit
INSERT INTO EVENT (title, venue, city, description, starts_at, ends_at, status)
VALUES (
    'Arctic Tech Summit',
    'Oulu Congress Center',
    'Oulu',
    'A two-day technology conference focused on AI and cloud computing.',
    '2026-09-10 09:00:00',
    '2026-09-11 17:00:00',
    'active'
);
SET @event2_id = LAST_INSERT_ID();

-- ========== TICKET DATABASE ==========
USE ticket_db;

-- Tickets for event 1
INSERT INTO TICKET (event_id, name, price, capacity, remaining)
VALUES (@event1_id, 'Standard', 59.90, 300, 300),
       (@event1_id, 'VIP', 129.90, 50, 50);

-- Tickets for event 2
INSERT INTO TICKET (event_id, name, price, capacity, remaining)
VALUES (@event2_id, 'Early Bird', 199.00, 100, 100),
       (@event2_id, 'Regular', 299.00, 200, 200),
       (@event2_id, 'Student', 99.00, 75, 75);