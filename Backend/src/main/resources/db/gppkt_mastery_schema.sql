-- GPPKT weakness + mastery tables (also created via JPA ddl-auto=update)
CREATE TABLE IF NOT EXISTS user_weakness_summary (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    weak_kcs TEXT,
    n_weak INTEGER DEFAULT 0,
    weakest_5 TEXT NOT NULL,
    related_kcs TEXT
);

CREATE TABLE IF NOT EXISTS user_kc_mastery (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    kc_name VARCHAR(255) NOT NULL,
    mastery DOUBLE PRECISION NOT NULL,
    n_attempts INTEGER DEFAULT 0,
    is_weak BOOLEAN DEFAULT FALSE,
    rank INTEGER,
    UNIQUE (user_id, kc_name)
);

CREATE INDEX IF NOT EXISTS idx_user_kc_mastery_user ON user_kc_mastery (user_id);
