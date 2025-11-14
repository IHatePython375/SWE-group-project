-- Blackjack Game Database Schema
-- Compatible with PostgreSQL

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'player' CHECK (role IN ('player', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_banned BOOLEAN DEFAULT FALSE,
    total_games_played INT DEFAULT 0
);

CREATE INDEX idx_username ON users(username);
CREATE INDEX idx_email ON users(email);

-- ============================================
-- USER PROFILES TABLE
-- ============================================
CREATE TABLE user_profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    display_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(255),
    total_winnings DECIMAL(10, 2) DEFAULT 0.00,
    total_losses DECIMAL(10, 2) DEFAULT 0.00,
    highest_balance DECIMAL(10, 2) DEFAULT 1000.00,
    longest_win_streak INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================
-- GAME SESSIONS TABLE
-- ============================================
CREATE TABLE game_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    game_mode VARCHAR(20) NOT NULL CHECK (game_mode IN ('tournament', 'freeplay')),
    starting_money DECIMAL(10, 2) DEFAULT 1000.00,
    current_money DECIMAL(10, 2) NOT NULL,
    rounds_completed INT DEFAULT 0,
    max_rounds INT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_user_status ON game_sessions(user_id, status);

-- ============================================
-- GAME STATES TABLE (for saving mid-round)
-- ============================================
CREATE TABLE game_states (
    state_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL,
    round_number INT NOT NULL,
    player_hand JSON NOT NULL,
    dealer_hand JSON NOT NULL,
    deck_state JSON NOT NULL,
    current_bet DECIMAL(10, 2) NOT NULL,
    game_phase VARCHAR(20) NOT NULL CHECK (game_phase IN ('betting', 'player_turn', 'dealer_turn', 'complete')),
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_gs_session ON game_states(session_id);

-- ============================================
-- GAME ROUNDS TABLE (individual hand history)
-- ============================================
CREATE TABLE game_rounds (
    round_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL,
    round_number INT NOT NULL,
    bet_amount DECIMAL(10, 2) NOT NULL,
    player_hand JSON NOT NULL,
    dealer_hand JSON NOT NULL,
    player_score INT NOT NULL,
    dealer_score INT NOT NULL,
    result VARCHAR(20) NOT NULL CHECK (result IN ('win', 'loss', 'push', 'blackjack', 'bust')),
    winnings DECIMAL(10, 2) NOT NULL,
    balance_after DECIMAL(10, 2) NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_session_round ON game_rounds(session_id, round_number);

-- ============================================
-- LEADERBOARD TABLE
-- ============================================
CREATE TABLE leaderboard (
    leaderboard_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    session_id INT NOT NULL,
    final_money DECIMAL(10, 2) NOT NULL,
    rounds_completed INT NOT NULL,
    profit DECIMAL(10, 2) NOT NULL,
    rank INT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_lb_final_money ON leaderboard(final_money DESC);
CREATE INDEX idx_lb_user ON leaderboard(user_id);

-- ============================================
-- FRIENDSHIPS TABLE
-- ============================================
CREATE TABLE friendships (
    friendship_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    friend_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'blocked')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (friend_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE (user_id, friend_id),
    CHECK (user_id != friend_id)
);

CREATE INDEX idx_f_user_status ON friendships(user_id, status);
CREATE INDEX idx_f_friend_status ON friendships(friend_id, status);

-- ============================================
-- MESSAGES TABLE
-- ============================================
CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message_text TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_m_receiver_read ON messages(receiver_id, is_read);
CREATE INDEX idx_m_conversation ON messages(sender_id, receiver_id, sent_at);

-- ============================================
-- ADMIN LOGS TABLE
-- ============================================
CREATE TABLE admin_logs (
    log_id SERIAL PRIMARY KEY,
    admin_id INT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    target_user_id INT,
    description TEXT,
    details JSON,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (target_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE INDEX idx_al_admin_time ON admin_logs(admin_id, performed_at);
CREATE INDEX idx_al_action_type ON admin_logs(action_type);

-- ============================================
-- GAME SETTINGS TABLE (for admin configuration)
-- ============================================
CREATE TABLE game_settings (
    setting_id SERIAL PRIMARY KEY,
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value VARCHAR(255) NOT NULL,
    description TEXT,
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ============================================
-- Insert Default Game Settings
-- ============================================
INSERT INTO game_settings (setting_key, setting_value, description) VALUES
('starting_money', '1000', 'Default starting money for players'),
('tournament_rounds', '10', 'Number of rounds in tournament mode'),
('blackjack_payout', '1.5', 'Payout multiplier for blackjack'),
('min_bet', '10', 'Minimum bet amount'),
('max_bet', '500', 'Maximum bet amount');

-- ============================================
-- Create Views for Common Queries
-- ============================================

-- Top 10 Leaderboard View
CREATE VIEW top_leaderboard AS
SELECT 
    l.leaderboard_id,
    u.username,
    l.final_money,
    l.profit,
    l.rounds_completed,
    l.recorded_at,
    RANK() OVER (ORDER BY l.final_money DESC) as rank
FROM leaderboard l
JOIN users u ON l.user_id = u.user_id
ORDER BY l.final_money DESC
LIMIT 10;

-- User Statistics View
CREATE VIEW user_statistics AS
SELECT 
    u.user_id,
    u.username,
    up.total_winnings,
    up.total_losses,
    up.highest_balance,
    u.total_games_played,
    COUNT(DISTINCT gs.session_id) as total_sessions,
    COUNT(DISTINCT CASE WHEN gr.result = 'win' THEN gr.round_id END) as rounds_won,
    COUNT(DISTINCT CASE WHEN gr.result = 'loss' THEN gr.round_id END) as rounds_lost,
    ROUND(
        COUNT(DISTINCT CASE WHEN gr.result = 'win' THEN gr.round_id END) * 100.0 / 
        NULLIF(COUNT(DISTINCT gr.round_id), 0), 2
    ) as win_percentage
FROM users u
LEFT JOIN user_profiles up ON u.user_id = up.user_id
LEFT JOIN game_sessions gs ON u.user_id = gs.user_id
LEFT JOIN game_rounds gr ON gs.session_id = gr.session_id
GROUP BY u.user_id, u.username, up.total_winnings, up.total_losses, up.highest_balance, u.total_games_played;

-- Active Friends View
CREATE VIEW active_friends AS
SELECT 
    f.friendship_id,
    f.user_id,
    u1.username as user_name,
    f.friend_id,
    u2.username as friend_name,
    f.created_at
FROM friendships f
JOIN users u1 ON f.user_id = u1.user_id
JOIN users u2 ON f.friend_id = u2.user_id
WHERE f.status = 'accepted';