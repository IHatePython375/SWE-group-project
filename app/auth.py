import bcrypt
import secrets
from datetime import datetime, timedelta
from database import DatabaseHelper

class AuthManager:
    """
    Handles user authentication, registration, and session management
    """
    
    def __init__(self, db: DatabaseHelper):
        self.db = db
        self.active_sessions = {}  # {session_token: {'user_id': int, 'expires': datetime}}
    
    # ============================================
    # PASSWORD HASHING
    # ============================================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    # ============================================
    # USER REGISTRATION
    # ============================================
    
    def register_user(self, username: str, email: str, password: str, role: str = 'player') -> dict:
        """
        Register a new user
        Returns: {'success': bool, 'message': str, 'user_id': int}
        """
        # Validation
        if len(username) < 3:
            return {'success': False, 'message': 'Username must be at least 3 characters', 'user_id': None}
        
        if len(password) < 6:
            return {'success': False, 'message': 'Password must be at least 6 characters', 'user_id': None}
        
        if '@' not in email:
            return {'success': False, 'message': 'Invalid email format', 'user_id': None}
        
        # Check if username already exists
        existing_user = self.db.get_user_by_username(username)
        if existing_user:
            return {'success': False, 'message': 'Username already exists', 'user_id': None}
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Create user
        try:
            user_id = self.db.create_user(username, email, password_hash, role)
            return {
                'success': True,
                'message': 'User registered successfully',
                'user_id': user_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Registration failed: {str(e)}',
                'user_id': None
            }
    
    # ============================================
    # USER LOGIN
    # ============================================
    
    def login(self, username: str, password: str) -> dict:
        """
        Login a user
        Returns: {'success': bool, 'message': str, 'session_token': str, 'user': dict}
        """
        # Get user from database
        user = self.db.get_user_by_username(username)
        
        if not user:
            return {
                'success': False,
                'message': 'Invalid username or password',
                'session_token': None,
                'user': None
            }
        
        # Check if user is banned
        if user['is_banned']:
            return {
                'success': False,
                'message': 'This account has been banned',
                'session_token': None,
                'user': None
            }
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return {
                'success': False,
                'message': 'Invalid username or password',
                'session_token': None,
                'user': None
            }
        
        # Update last login
        self.db.update_last_login(user['user_id'])
        
        # Create session token
        session_token = self.create_session(user['user_id'])
        
        # Remove sensitive data
        user_data = dict(user)
        del user_data['password_hash']
        
        return {
            'success': True,
            'message': 'Login successful',
            'session_token': session_token,
            'user': user_data
        }
    
    # ============================================
    # SESSION MANAGEMENT
    # ============================================
    
    def create_session(self, user_id: int, duration_hours: int = 24) -> str:
        """Create a new session token"""
        session_token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=duration_hours)
        
        self.active_sessions[session_token] = {
            'user_id': user_id,
            'expires': expires
        }
        
        return session_token
    
    def validate_session(self, session_token: str) -> dict:
        """
        Validate a session token
        Returns: {'valid': bool, 'user_id': int or None}
        """
        if session_token not in self.active_sessions:
            return {'valid': False, 'user_id': None}
        
        session = self.active_sessions[session_token]
        
        # Check if expired
        if datetime.now() > session['expires']:
            del self.active_sessions[session_token]
            return {'valid': False, 'user_id': None}
        
        return {'valid': True, 'user_id': session['user_id']}
    
    def logout(self, session_token: str) -> bool:
        """Logout a user by removing their session"""
        if session_token in self.active_sessions:
            del self.active_sessions[session_token]
            return True
        return False
    
    def get_current_user(self, session_token: str) -> dict:
        """Get current user from session token"""
        validation = self.validate_session(session_token)
        
        if not validation['valid']:
            return None
        
        user = self.db.get_user_by_id(validation['user_id'])
        
        if user:
            user_data = dict(user)
            del user_data['password_hash']
            return user_data
        
        return None
    
    # ============================================
    # ADMIN FUNCTIONS
    # ============================================
    
    def is_admin(self, session_token: str) -> bool:
        """Check if current user is an admin"""
        user = self.get_current_user(session_token)
        return user and user['role'] == 'admin'
    
    def require_admin(self, session_token: str) -> dict:
        """
        Require admin authentication
        Returns: {'authorized': bool, 'message': str, 'user': dict}
        """
        validation = self.validate_session(session_token)
        
        if not validation['valid']:
            return {
                'authorized': False,
                'message': 'Not authenticated',
                'user': None
            }
        
        user = self.db.get_user_by_id(validation['user_id'])
        
        if not user or user['role'] != 'admin':
            return {
                'authorized': False,
                'message': 'Admin privileges required',
                'user': None
            }
        
        user_data = dict(user)
        del user_data['password_hash']
        
        return {
            'authorized': True,
            'message': 'Authorized',
            'user': user_data
        }
    
    # ============================================
    # UTILITY FUNCTIONS
    # ============================================
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> dict:
        """Change user password"""
        user = self.db.get_user_by_id(user_id)
        
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        # Verify old password
        if not self.verify_password(old_password, user['password_hash']):
            return {'success': False, 'message': 'Incorrect current password'}
        
        # Validate new password
        if len(new_password) < 6:
            return {'success': False, 'message': 'New password must be at least 6 characters'}
        
        # Hash new password
        new_hash = self.hash_password(new_password)
        
        # Update in database
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = %s
                    WHERE user_id = %s
                """, (new_hash, user_id))
            
            return {'success': True, 'message': 'Password changed successfully'}
        except Exception as e:
            return {'success': False, 'message': f'Failed to change password: {str(e)}'}
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions (run periodically)"""
        current_time = datetime.now()
        expired_tokens = [
            token for token, session in self.active_sessions.items()
            if current_time > session['expires']
        ]
        
        for token in expired_tokens:
            del self.active_sessions[token]
        
        return len(expired_tokens)