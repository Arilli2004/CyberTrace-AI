-- ─────────────────────────────────────────────────────────────────────────────
-- CyberTrace AI — PostgreSQL Database Schema
-- ─────────────────────────────────────────────────────────────────────────────

-- ─── Extensions ──────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search

-- ─── Enums ───────────────────────────────────────────────────────────────────
CREATE TYPE user_role AS ENUM ('admin', 'investigator', 'analyst', 'viewer');
CREATE TYPE case_status AS ENUM ('new', 'evidence_uploaded', 'parsing', 'analysis', 'completed', 'archived');
CREATE TYPE evidence_type AS ENUM ('evtx', 'log', 'csv', 'json', 'xml');
CREATE TYPE severity_level AS ENUM ('low', 'medium', 'high', 'critical');

-- ─── Users ───────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            user_role DEFAULT 'investigator',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ
);
CREATE INDEX idx_users_email ON users(email);

-- ─── Cases ───────────────────────────────────────────────────────────────────
CREATE TABLE cases (
    id                  SERIAL PRIMARY KEY,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    investigator_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status              case_status DEFAULT 'new',
    priority            VARCHAR(20) DEFAULT 'medium',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ
);
CREATE INDEX idx_cases_investigator ON cases(investigator_id);
CREATE INDEX idx_cases_status ON cases(status);

-- ─── Evidence ────────────────────────────────────────────────────────────────
CREATE TABLE evidence (
    id                  SERIAL PRIMARY KEY,
    case_id             INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    filename            VARCHAR(500) NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    sha256              VARCHAR(64) NOT NULL,
    file_type           evidence_type NOT NULL,
    size                BIGINT NOT NULL,
    file_path           VARCHAR(500) NOT NULL,
    is_parsed           BOOLEAN DEFAULT FALSE,
    parse_status        VARCHAR(50) DEFAULT 'pending',
    event_count         INTEGER DEFAULT 0,
    uploaded_at         TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_evidence_case ON evidence(case_id);
CREATE INDEX idx_evidence_sha256 ON evidence(sha256);

-- ─── Events ──────────────────────────────────────────────────────────────────
CREATE TABLE events (
    id                  SERIAL PRIMARY KEY,
    evidence_id         INTEGER NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    timestamp           TIMESTAMPTZ NOT NULL,
    source              VARCHAR(100),
    event_type          VARCHAR(100),
    event_id            VARCHAR(50),
    "user"              VARCHAR(100),
    host                VARCHAR(100),
    ip_address          VARCHAR(45),
    process             VARCHAR(255),
    severity            severity_level DEFAULT 'low',
    description         TEXT,
    raw_data            JSONB,
    is_suspicious       BOOLEAN DEFAULT FALSE,
    confidence_score    FLOAT DEFAULT 0.0,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_events_evidence ON events(evidence_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_user ON events("user");
CREATE INDEX idx_events_host ON events(host);
CREATE INDEX idx_events_severity ON events(severity);
CREATE INDEX idx_events_suspicious ON events(is_suspicious);
CREATE INDEX idx_events_raw_data ON events USING GIN(raw_data);

-- ─── Alerts ──────────────────────────────────────────────────────────────────
CREATE TABLE alerts (
    id                  SERIAL PRIMARY KEY,
    event_id            INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    severity            severity_level NOT NULL,
    confidence          FLOAT DEFAULT 0.0,
    rule_name           VARCHAR(100),
    is_acknowledged     BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_alerts_event ON alerts(event_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);

-- ─── AI Reports ──────────────────────────────────────────────────────────────
CREATE TABLE ai_reports (
    id                  SERIAL PRIMARY KEY,
    case_id             INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    summary             TEXT,
    root_cause          TEXT,
    risk_level          VARCHAR(20),
    recommendations     JSONB,
    suspicious_activities JSONB,
    report_path         VARCHAR(500),
    generated_at        TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ai_reports_case ON ai_reports(case_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- End of Schema
-- ─────────────────────────────────────────────────────────────────────────────
