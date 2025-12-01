import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
from contextlib import contextmanager

class DatabaseHelper:
    """
    Database helper class for Blackjack game
    Handles all database operations
    """
    
    def __init__(self, host='localhost', port=5432, database='blackjack_db', 
                 user='your_user', password='your_password', 
                 minconn=1, maxconn=20):
        #initialize connection pool
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn,
            maxconn,
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        )
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Context manager for database cursors"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    

    # USER OPERATIONS

    
    def create_user(self, username, email, password_hash, role='player'):
        """Create a new user"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id
            """, (username, email, password_hash, role))
            
            user_id = cursor.fetchone()['user_id']
            
            # Create user profile
            cursor.execute("""
                INSERT INTO user_profiles (user_id)
                VALUES (%s)
            """, (user_id,))
            
            return user_id
    
    def get_user_by_username(self, username):
        """Get user by username"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM users WHERE username = %s
            """, (username,))
            return cursor.fetchone()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM users WHERE user_id = %s
            """, (user_id,))
            return cursor.fetchone()
    
    def update_last_login(self, user_id):
        """Update user's last login timestamp"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (user_id,))
    
    def ban_user(self, user_id, admin_id):
        """Ban a user (admin only)"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE users SET is_banned = TRUE WHERE user_id = %s
            """, (user_id,))
            
            # Log admin action
            self.log_admin_action(admin_id, 'ban_user', user_id, 
                                'User banned by admin')
    
    def get_user_profile(self, user_id):
        """Get user profile with statistics"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT u.*, up.* 
                FROM users u
                LEFT JOIN user_profiles up ON u.user_id = up.user_id
                WHERE u.user_id = %s
            """, (user_id,))
            return cursor.fetchone()
    

    # GAME SESSION OPERATIONS

    
    def create_game_session(self, user_id, game_mode, starting_money=1000, max_rounds=None):
        """Create a new game session"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO game_sessions 
                (user_id, game_mode, starting_money, current_money, max_rounds)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING session_id
            """, (user_id, game_mode, starting_money, starting_money, max_rounds))
            
            return cursor.fetchone()['session_id']
    
    def get_active_session(self, user_id):
        """Get user's active game session"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM game_sessions
                WHERE user_id = %s AND status = 'active'
                ORDER BY started_at DESC
                LIMIT 1
            """, (user_id,))
            return cursor.fetchone()
    
    def update_session(self, session_id, current_money, rounds_completed):
        """Update game session"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE game_sessions
                SET current_money = %s, rounds_completed = %s
                WHERE session_id = %s
            """, (current_money, rounds_completed, session_id))
    
    def complete_session(self, session_id):
        """Mark session as completed"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE game_sessions
                SET status = 'completed', ended_at = CURRENT_TIMESTAMP
                WHERE session_id = %s
            """, (session_id,))
    

    # GAME STATE OPERATIONS (Save/Load)

    
    def save_game_state(self, session_id, round_number, player_hand, dealer_hand, 
                       deck_state, current_bet, game_phase):
        """Save current game state"""
        with self.get_cursor() as cursor:
            # Delete old save for this session
            cursor.execute("""
                DELETE FROM game_states WHERE session_id = %s
            """, (session_id,))
            
            # Insert new save
            cursor.execute("""
                INSERT INTO game_states 
                (session_id, round_number, player_hand, dealer_hand, 
                 deck_state, current_bet, game_phase)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING state_id
            """, (session_id, round_number, json.dumps(player_hand), 
                  json.dumps(dealer_hand), json.dumps(deck_state), 
                  current_bet, game_phase))
            
            return cursor.fetchone()['state_id']
    
    def load_game_state(self, session_id):
        """Load saved game state"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM game_states
                WHERE session_id = %s
                ORDER BY saved_at DESC
                LIMIT 1
            """, (session_id,))
            
            state = cursor.fetchone()
            if state:
                # Check if already parsed (postgres returns JSON as dict/list)
                if isinstance(state['player_hand'], str):
                    state['player_hand'] = json.loads(state['player_hand'])
                if isinstance(state['dealer_hand'], str):
                    state['dealer_hand'] = json.loads(state['dealer_hand'])
                if isinstance(state['deck_state'], str):
                    state['deck_state'] = json.loads(state['deck_state'])
            
            return state
    
    def delete_game_state(self, session_id):
        """Delete saved game state"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM game_states WHERE session_id = %s
            """, (session_id,))
    

    # GAME ROUND OPERATIONS

    
    def save_game_round(self, session_id, round_number, bet_amount, player_hand, 
                       dealer_hand, player_score, dealer_score, result, 
                       winnings, balance_after):
        """Save completed game round"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO game_rounds
                (session_id, round_number, bet_amount, player_hand, dealer_hand,
                 player_score, dealer_score, result, winnings, balance_after)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING round_id
            """, (session_id, round_number, bet_amount, json.dumps(player_hand),
                  json.dumps(dealer_hand), player_score, dealer_score, 
                  result, winnings, balance_after))
            
            return cursor.fetchone()['round_id']
    
    def get_session_rounds(self, session_id):
        """Get all rounds for a session"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM game_rounds
                WHERE session_id = %s
                ORDER BY round_number
            """, (session_id,))
            return cursor.fetchall()
    

    # LEADERBOARD OPERATIONS

    
    def add_to_leaderboard(self, user_id, session_id, final_money, 
                          rounds_completed, profit):
        """Add score to leaderboard"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO leaderboard
                (user_id, session_id, final_money, rounds_completed, profit)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING leaderboard_id
            """, (user_id, session_id, final_money, rounds_completed, profit))
            
            return cursor.fetchone()['leaderboard_id']
    
    def get_leaderboard(self, limit=10):
        """Get top leaderboard entries"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM top_leaderboard
                LIMIT %s
            """, (limit,))
            return cursor.fetchall()
    
    def get_user_leaderboard_entries(self, user_id):
        """Get all leaderboard entries for a user"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT l.*, u.username
                FROM leaderboard l
                JOIN users u ON l.user_id = u.user_id
                WHERE l.user_id = %s
                ORDER BY l.final_money DESC
            """, (user_id,))
            return cursor.fetchall()
    

    # FRIENDSHIP OPERATIONS

    
    def send_friend_request(self, user_id, friend_id):
        """Send a friend request"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO friendships (user_id, friend_id, status)
                VALUES (%s, %s, 'pending')
                RETURNING friendship_id
            """, (user_id, friend_id))
            
            return cursor.fetchone()['friendship_id']
    
    def accept_friend_request(self, friendship_id):
        """Accept a friend request"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE friendships
                SET status = 'accepted', updated_at = CURRENT_TIMESTAMP
                WHERE friendship_id = %s
            """, (friendship_id,))
    
    def get_friends(self, user_id):
        """Get user's friends"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM active_friends
                WHERE user_id = %s OR friend_id = %s
            """, (user_id, user_id))
            return cursor.fetchall()
    
    def get_pending_friend_requests(self, user_id):
        """Get pending friend requests"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT f.*, u.username as requester_name
                FROM friendships f
                JOIN users u ON f.user_id = u.user_id
                WHERE f.friend_id = %s AND f.status = 'pending'
            """, (user_id,))
            return cursor.fetchall()
    

    # MESSAGE OPERATIONS

    
    def send_message(self, sender_id, receiver_id, message_text):
        """Send a message"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO messages (sender_id, receiver_id, message_text)
                VALUES (%s, %s, %s)
                RETURNING message_id
            """, (sender_id, receiver_id, message_text))
            
            return cursor.fetchone()['message_id']
    
    def get_conversation(self, user_id, other_user_id, limit=50):
        """Get conversation between two users"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT m.*, 
                       u1.username as sender_name,
                       u2.username as receiver_name
                FROM messages m
                JOIN users u1 ON m.sender_id = u1.user_id
                JOIN users u2 ON m.receiver_id = u2.user_id
                WHERE (m.sender_id = %s AND m.receiver_id = %s)
                   OR (m.sender_id = %s AND m.receiver_id = %s)
                ORDER BY m.sent_at DESC
                LIMIT %s
            """, (user_id, other_user_id, other_user_id, user_id, limit))
            
            messages = cursor.fetchall()
            return list(reversed(messages))  # Return chronological order
    
    def mark_messages_read(self, receiver_id, sender_id):
        """Mark messages as read"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE messages
                SET is_read = TRUE
                WHERE receiver_id = %s AND sender_id = %s AND is_read = FALSE
            """, (receiver_id, sender_id))
    
    def get_unread_count(self, user_id):
        """Get count of unread messages"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM messages
                WHERE receiver_id = %s AND is_read = FALSE
            """, (user_id,))
            
            return cursor.fetchone()['count']
    
    # ADMIN OPERATIONS
    
    def log_admin_action(self, admin_id, action_type, target_user_id, 
                        description, details=None):
        """Log admin action"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO admin_logs 
                (admin_id, action_type, target_user_id, description, details)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING log_id
            """, (admin_id, action_type, target_user_id, description,
                  json.dumps(details) if details else None))
            
            return cursor.fetchone()['log_id']
    
    def get_admin_logs(self, limit=100):
        """Get recent admin logs"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT al.*, 
                       u1.username as admin_name,
                       u2.username as target_username
                FROM admin_logs al
                JOIN users u1 ON al.admin_id = u1.user_id
                LEFT JOIN users u2 ON al.target_user_id = u2.user_id
                ORDER BY al.performed_at DESC
                LIMIT %s
            """, (limit,))
            return cursor.fetchall()
    
    def get_all_users(self, limit=100, offset=0):
        """Get all users (admin only)"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM user_statistics
                ORDER BY total_games_played DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            return cursor.fetchall()
    
    def update_game_setting(self, setting_key, setting_value, admin_id):
        """Update game setting"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE game_settings
                SET setting_value = %s, 
                    updated_by = %s, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE setting_key = %s
            """, (setting_value, admin_id, setting_key))
            
            self.log_admin_action(admin_id, 'update_setting', None,
                                f'Updated {setting_key} to {setting_value}')
    
    def get_game_settings(self):
        """Get all game settings"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM game_settings
            """)
            return cursor.fetchall()
    
    def get_game_setting(self, setting_key):
        """Get specific game setting"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT setting_value FROM game_settings
                WHERE setting_key = %s
            """, (setting_key,))
            
            result = cursor.fetchone()
            return result['setting_value'] if result else None
    

    # STATISTICS OPERATIONS
    
    def update_user_statistics(self, user_id):
        """Update user profile statistics"""
        with self.get_cursor() as cursor:
            # Calculate total winnings and losses
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN winnings > 0 THEN winnings ELSE 0 END), 0) as total_winnings,
                    COALESCE(SUM(CASE WHEN winnings < 0 THEN ABS(winnings) ELSE 0 END), 0) as total_losses,
                    MAX(balance_after) as highest_balance
                FROM game_rounds gr
                JOIN game_sessions gs ON gr.session_id = gs.session_id
                WHERE gs.user_id = %s
            """, (user_id,))
            
            stats = cursor.fetchone()
            
            # Update user profile
            cursor.execute("""
                UPDATE user_profiles
                SET total_winnings = %s,
                    total_losses = %s,
                    highest_balance = %s
                WHERE user_id = %s
            """, (stats['total_winnings'], stats['total_losses'],
                  stats['highest_balance'], user_id))
            
            # Update total games played
            cursor.execute("""
                UPDATE users
                SET total_games_played = (
                    SELECT COUNT(*) FROM game_sessions
                    WHERE user_id = %s AND status = 'completed'
                )
                WHERE user_id = %s
            """, (user_id, user_id))