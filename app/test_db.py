from database import DatabaseHelper

# Use YOUR password that you set during PostgreSQL installation
db = DatabaseHelper(
    host='localhost',
    port=5432,
    database='blackjack_db',
    user='postgres',
    password='1234'  # Change this!
)

try:
    # Test 1: Create a user
    user_id = db.create_user('testplayer', 'test@example.com', 'hashed_password123')
    print(f"✓ User created with ID: {user_id}")
    
    # Test 2: Retrieve the user
    user = db.get_user_by_username('testplayer')
    print(f"✓ User retrieved: {user['username']}, Role: {user['role']}")
    
    # Test 3: Get game settings
    settings = db.get_game_settings()
    print(f"✓ Game settings loaded: {len(settings)} settings found")
    
    print("\n✅ DATABASE IS WORKING PERFECTLY!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()