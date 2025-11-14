from database import DatabaseHelper
from auth import AuthManager

db = DatabaseHelper(
    host='localhost',
    port=5432,
    database='blackjack_db',
    user='postgres',
    password='1234'
)

auth = AuthManager(db)

# Create admin
result = auth.register_user('admin', 'admin@blackjack.com', 'admin123', role='admin')

if result['success']:
    print(f"✓ Admin user created!")
    print(f"Username: admin")
    print(f"Password: admin123")
else:
    print(f"✗ Error: {result['message']}")