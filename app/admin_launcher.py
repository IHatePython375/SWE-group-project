from database import DatabaseHelper
from auth import AuthManager
from admin import AdminPanel, admin_login

def main():
    """Main admin panel entry point"""
    
    # Initialize database and auth
    db = DatabaseHelper(
        host='localhost',
        port=5432,
        database='blackjack_db',
        user='postgres',
        password='1234'  # CHANGE THIS!
    )
    
    auth = AuthManager(db)
    
    print("=" * 60)
    print("BLACKJACK SWE - ADMIN PANEL")
    print("=" * 60)
    
    # Admin login
    admin_session = admin_login(db, auth)
    
    if not admin_session:
        print("\nAccess denied. Exiting.")
        return
    
    # Launch admin panel
    admin_panel = AdminPanel(db, auth, admin_session['user'])
    admin_panel.display_menu()
    
    # Logout
    auth.logout(admin_session['token'])
    print("\n[LOGGED OUT] Admin session ended. Goodbye!")

if __name__ == "__main__":
    main()