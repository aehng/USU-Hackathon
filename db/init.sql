-- db/init.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    raw_transcript TEXT,
    symptoms TEXT[],
    severity INTEGER CHECK (severity >= 1 AND severity <= 10),
    potential_triggers TEXT[],
    mood VARCHAR(50),
    body_location TEXT[],
    time_context VARCHAR(100),
    notes TEXT,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE correlations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    symptom VARCHAR(255),
    trigger VARCHAR(255),
    correlation_score FLOAT,
    sample_size INTEGER,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE insights_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    insights_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    entry_count_at_computation INTEGER
);

CREATE INDEX idx_entries_user_id ON entries(user_id);
CREATE INDEX idx_entries_logged_at ON entries(logged_at);
CREATE INDEX idx_entries_symptoms ON entries USING GIN (symptoms);
CREATE INDEX idx_entries_potential_triggers ON entries USING GIN (potential_triggers);

CREATE TABLE trigger_taxonomy (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    raw_trigger VARCHAR(255),
    root_cause VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT _user_raw_trigger_uc UNIQUE (user_id, raw_trigger)
);

CREATE INDEX idx_trigger_taxonomy_user_id ON trigger_taxonomy(user_id);
CREATE INDEX idx_trigger_taxonomy_raw_trigger ON trigger_taxonomy(raw_trigger);
CREATE INDEX idx_trigger_taxonomy_root_cause ON trigger_taxonomy(root_cause);

-- Insert demo user
INSERT INTO users (id) VALUES ('00000000-0000-0000-0000-000000000001');
