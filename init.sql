-- Initialize the database schema

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    status INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, guild_id)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_guild_id ON users(guild_id);

-- Sample data for testing (optional - uncomment to use)
-- INSERT INTO users (user_id, guild_id, status)
-- VALUES (123456789012345678, 987654321098765432, 2)
-- ON CONFLICT (user_id, guild_id) DO NOTHING;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to bot user
GRANT SELECT, INSERT, UPDATE, DELETE ON users TO bot_user;
GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO bot_user;
