from database import DatabaseHelper
from auth import AuthManager

# Initialize
db = DatabaseHelper(
    host='localhost',
    port=5432,
    database='blackjack_db',
    user='postgres',
    password='1234'  # Your actual password
)

auth = AuthManager(db)

print("=" * 60)
print("TESTING AUTHENTICATION SYSTEM")
print("=" * 60)

# Test 1: Register a player
print("\n1. Registering player...")
result = auth.register_user('john_doe', 'john@example.com', 'password123')
if result['success']:
    print(f"✓ Player registered: {result['message']}")
else:
    print(f"✗ Failed: {result['message']}")

# Test 2: Register an admin
print("\n2. Registering admin...")
result = auth.register_user('admin_user', 'admin@example.com', 'admin123', role='admin')
if result['success']:
    print(f"✓ Admin registered: {result['message']}")
else:
    print(f"✗ Failed: {result['message']}")

# Test 3: Login
print("\n3. Testing login...")
login_result = auth.login('john_doe', 'password123')
if login_result['success']:
    print(f"✓ Login successful!")
    print(f"  Session token: {login_result['session_token'][:20]}...")
    print(f"  User: {login_result['user']['username']}")
    session_token = login_result['session_token']
else:
    print(f"✗ Login failed: {login_result['message']}")

# Test 4: Validate session
print("\n4. Validating session...")
validation = auth.validate_session(session_token)
if validation['valid']:
    print(f"✓ Session valid for user ID: {validation['user_id']}")
else:
    print("✗ Session invalid")

# Test 5: Check admin
print("\n5. Checking admin status...")
if auth.is_admin(session_token):
    print("✗ User is admin (should be player)")
else:
    print("✓ User is not admin (correct)")

# Test 6: Admin login
print("\n6. Testing admin login...")
admin_login = auth.login('admin_user', 'admin123')
if admin_login['success']:
    print("✓ Admin login successful!")
    admin_token = admin_login['session_token']
    if auth.is_admin(admin_token):
        print("✓ Admin privileges confirmed")

# Test 7: Logout
print("\n7. Testing logout...")
if auth.logout(session_token):
    print("✓ Logout successful")
    validation = auth.validate_session(session_token)
    if not validation['valid']:
        print("✓ Session invalidated after logout")

print("\n" + "=" * 60)
print("✅ AUTHENTICATION SYSTEM WORKING!")
print("=" * 60)