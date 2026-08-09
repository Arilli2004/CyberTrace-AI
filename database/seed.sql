-- ─────────────────────────────────────────────────────────────────────────────
-- CyberTrace AI — Seed Data
-- ─────────────────────────────────────────────────────────────────────────────

-- Default admin user (password: Admin@123)
INSERT INTO users (name, email, password_hash, role) VALUES
('Admin User', 'admin@cybertrace.ai', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'admin'),
('John Investigator', 'investigator@cybertrace.ai', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'investigator')
ON CONFLICT (email) DO NOTHING;

-- Sample cases
INSERT INTO cases (title, description, investigator_id, status, priority) VALUES
('Ransomware Investigation - ACME Corp', 'Suspected ransomware attack on ACME Corp servers on July 28, 2026', 2, 'analysis', 'critical'),
('Data Exfiltration - Finance Dept', 'Unusual large data transfers from finance department workstations', 2, 'evidence_uploaded', 'high'),
('Unauthorized Access - HR Systems', 'Multiple failed login attempts followed by successful access to HR database', 2, 'new', 'medium')
ON CONFLICT DO NOTHING;
