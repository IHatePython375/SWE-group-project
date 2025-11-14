import getpass
from database import DatabaseHelper
from auth import AuthManager

class AdminPanel:
    """Admin panel for managing users, games, and settings"""
    
    def __init__(self, db: DatabaseHelper, auth: AuthManager, admin_user: dict):
        self.db = db
        self.auth = auth
        self.admin_user = admin_user
    
    def display_menu(self):
        """Display admin panel menu"""
        while True:
            print("\n" + "=" * 60)
            print(f"ADMIN PANEL - {self.admin_user['username']}")
            print("=" * 60)
            print("\n1. View All Users")
            print("2. View User Details")
            print("3. Ban/Unban User")
            print("4. Delete User")
            print("5. View Game Settings")
            print("6. Edit Game Settings")
            print("7. View Admin Logs")
            print("8. View All Game Sessions")
            print("9. Create Admin User")
            print("10. Back to Main Menu")
            
            choice = input("\nSelect option (1-10): ").strip()
            
            if choice == '1':
                self.view_all_users()
            elif choice == '2':
                self.view_user_details()
            elif choice == '3':
                self.ban_unban_user()
            elif choice == '4':
                self.delete_user()
            elif choice == '5':
                self.view_game_settings()
            elif choice == '6':
                self.edit_game_settings()
            elif choice == '7':
                self.view_admin_logs()
            elif choice == '8':
                self.view_all_sessions()
            elif choice == '9':
                self.create_admin_user()
            elif choice == '10':
                return
            else:
                print("Invalid choice. Please enter 1-10.")
    
    def view_all_users(self):
        """View all users in the system"""
        print("\n" + "=" * 60)
        print("ALL USERS")
        print("=" * 60)
        
        # Query users directly, not from view
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT user_id, username, email, role, is_banned, 
                       total_games_played, created_at, last_login
                FROM users
                ORDER BY user_id
                LIMIT 100
            """)
            users = cursor.fetchall()
        
        if not users:
            print("No users found.")
            return
        
        print(f"\nTotal Users: {len(users)}")
        print("\n{:<5} {:<20} {:<10} {:<15} {:<10}".format(
            "ID", "Username", "Role", "Games Played", "Status"
        ))
        print("-" * 60)
        
        for user in users:
            status = "BANNED" if user['is_banned'] else "Active"
            print("{:<5} {:<20} {:<10} {:<15} {:<10}".format(
                user['user_id'],
                user['username'][:19],
                user['role'],
                user['total_games_played'],
                status
            ))
    
    def view_user_details(self):
        """View detailed information about a specific user"""
        username = input("\nEnter username: ").strip()
        
        user = self.db.get_user_by_username(username)
        
        if not user:
            print(f"\n[ERROR] User '{username}' not found.")
            return
        
        profile = self.db.get_user_profile(user['user_id'])
        sessions = self.db.get_all_users(limit=100)  # This should be user-specific
        
        print("\n" + "=" * 60)
        print(f"USER DETAILS - {user['username']}")
        print("=" * 60)
        print(f"User ID: {user['user_id']}")
        print(f"Email: {user['email']}")
        print(f"Role: {user['role']}")
        print(f"Status: {'BANNED' if user['is_banned'] else 'Active'}")
        print(f"Created: {user['created_at']}")
        print(f"Last Login: {user['last_login']}")
        print(f"\n--- Game Statistics ---")
        print(f"Total Games: {user['total_games_played']}")
        print(f"Total Winnings: ${profile['total_winnings']:.2f}")
        print(f"Total Losses: ${profile['total_losses']:.2f}")
        print(f"Highest Balance: ${profile['highest_balance']:.2f}")
        print(f"Net Profit/Loss: ${profile['total_winnings'] - profile['total_losses']:.2f}")
        
        # Get leaderboard entries
        leaderboard_entries = self.db.get_user_leaderboard_entries(user['user_id'])
        if leaderboard_entries:
            print(f"\n--- Leaderboard Entries ({len(leaderboard_entries)}) ---")
            for i, entry in enumerate(leaderboard_entries[:5], 1):
                print(f"{i}. ${entry['final_money']} (Profit: ${entry['profit']}) - {entry['rounds_completed']} rounds")
    
    def ban_unban_user(self):
        """Ban or unban a user"""
        username = input("\nEnter username to ban/unban: ").strip()
        
        user = self.db.get_user_by_username(username)
        
        if not user:
            print(f"\n[ERROR] User '{username}' not found.")
            return
        
        if user['user_id'] == self.admin_user['user_id']:
            print("\n[ERROR] You cannot ban yourself!")
            return
        
        current_status = "BANNED" if user['is_banned'] else "Active"
        print(f"\nCurrent status: {current_status}")
        
        if user['is_banned']:
            action = input("Unban this user? (y/n): ").lower()
            if action == 'y':
                # Unban user
                with self.db.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE users SET is_banned = FALSE WHERE user_id = %s
                    """, (user['user_id'],))
                
                self.db.log_admin_action(
                    self.admin_user['user_id'],
                    'unban_user',
                    user['user_id'],
                    f"User {username} unbanned"
                )
                print(f"\n[SUCCESS] User '{username}' has been unbanned.")
        else:
            action = input("Ban this user? (y/n): ").lower()
            if action == 'y':
                reason = input("Reason for ban: ").strip()
                
                self.db.ban_user(user['user_id'], self.admin_user['user_id'])
                
                self.db.log_admin_action(
                    self.admin_user['user_id'],
                    'ban_user',
                    user['user_id'],
                    f"User {username} banned. Reason: {reason}"
                )
                print(f"\n[SUCCESS] User '{username}' has been banned.")
    
    def delete_user(self):
        """Delete a user account"""
        username = input("\nEnter username to DELETE: ").strip()
        
        user = self.db.get_user_by_username(username)
        
        if not user:
            print(f"\n[ERROR] User '{username}' not found.")
            return
        
        if user['user_id'] == self.admin_user['user_id']:
            print("\n[ERROR] You cannot delete yourself!")
            return
        
        print(f"\n[WARNING] This will permanently delete user '{username}' and all their data!")
        confirm = input("Type 'DELETE' to confirm: ").strip()
        
        if confirm != 'DELETE':
            print("\n[CANCELLED] User deletion cancelled.")
            return
        
        # Log before deletion
        self.db.log_admin_action(
            self.admin_user['user_id'],
            'delete_user',
            user['user_id'],
            f"User {username} deleted"
        )
        
        # Delete user (CASCADE will handle related data)
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM users WHERE user_id = %s
            """, (user['user_id'],))
        
        print(f"\n[SUCCESS] User '{username}' has been deleted.")
    
    def view_game_settings(self):
        """View current game settings"""
        print("\n" + "=" * 60)
        print("GAME SETTINGS")
        print("=" * 60)
        
        settings = self.db.get_game_settings()
        
        print("\n{:<25} {:<20} {:<30}".format("Setting", "Value", "Description"))
        print("-" * 60)
        
        for setting in settings:
            print("{:<25} {:<20} {:<30}".format(
                setting['setting_key'],
                setting['setting_value'],
                setting['description'][:29] if setting['description'] else ""
            ))
    
    def edit_game_settings(self):
        """Edit game settings"""
        print("\n" + "=" * 60)
        print("EDIT GAME SETTINGS")
        print("=" * 60)
        
        settings = self.db.get_game_settings()
        
        print("\nAvailable settings:")
        for i, setting in enumerate(settings, 1):
            print(f"{i}. {setting['setting_key']}: {setting['setting_value']}")
        
        try:
            choice = int(input("\nSelect setting to edit (number): ")) - 1
            
            if choice < 0 or choice >= len(settings):
                print("\n[ERROR] Invalid selection.")
                return
            
            selected_setting = settings[choice]
            current_value = selected_setting['setting_value']
            
            print(f"\nCurrent value: {current_value}")
            new_value = input("Enter new value: ").strip()
            
            if not new_value:
                print("\n[CANCELLED] No changes made.")
                return
            
            # Update setting
            self.db.update_game_setting(
                selected_setting['setting_key'],
                new_value,
                self.admin_user['user_id']
            )
            
            print(f"\n[SUCCESS] {selected_setting['setting_key']} updated to {new_value}")
            
        except ValueError:
            print("\n[ERROR] Please enter a valid number.")
    
    def view_admin_logs(self):
        """View recent admin actions"""
        print("\n" + "=" * 60)
        print("ADMIN LOGS (Last 20 Actions)")
        print("=" * 60)
        
        logs = self.db.get_admin_logs(limit=20)
        
        if not logs:
            print("\nNo admin logs found.")
            return
        
        for log in logs:
            timestamp = log['performed_at'].strftime('%Y-%m-%d %H:%M:%S')
            admin_name = log['admin_name']
            action = log['action_type']
            target = log['target_username'] if log['target_username'] else 'N/A'
            description = log['description']
            
            print(f"\n[{timestamp}]")
            print(f"  Admin: {admin_name}")
            print(f"  Action: {action}")
            print(f"  Target: {target}")
            print(f"  Details: {description}")
            print("-" * 60)
    
    def view_all_sessions(self):
        """View all game sessions"""
        print("\n" + "=" * 60)
        print("ALL GAME SESSIONS (Last 20)")
        print("=" * 60)
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT gs.*, u.username
                FROM game_sessions gs
                JOIN users u ON gs.user_id = u.user_id
                ORDER BY gs.started_at DESC
                LIMIT 20
            """)
            sessions = cursor.fetchall()
        
        if not sessions:
            print("\nNo game sessions found.")
            return
        
        print("\n{:<10} {:<15} {:<12} {:<12} {:<10} {:<10}".format(
            "Session", "Player", "Mode", "Money", "Rounds", "Status"
        ))
        print("-" * 70)
        
        for session in sessions:
            print("{:<10} {:<15} {:<12} ${:<11.2f} {:<10} {:<10}".format(
                session['session_id'],
                session['username'][:14],
                session['game_mode'],
                float(session['current_money']),
                session['rounds_completed'],
                session['status']
            ))
    
    def create_admin_user(self):
        """Create a new admin user"""
        print("\n" + "=" * 60)
        print("CREATE ADMIN USER")
        print("=" * 60)
        
        username = input("\nAdmin Username (min 3 chars): ").strip()
        email = input("Admin Email: ").strip()
        password = getpass.getpass("Admin Password (min 6 chars): ")
        
        result = self.auth.register_user(username, email, password, role='admin')
        
        if result['success']:
            print(f"\n[SUCCESS] Admin user '{username}' created!")
            
            self.db.log_admin_action(
                self.admin_user['user_id'],
                'create_admin',
                result['user_id'],
                f"Created admin user: {username}"
            )
        else:
            print(f"\n[ERROR] {result['message']}")


def admin_login(db: DatabaseHelper, auth: AuthManager):
    """Admin login interface"""
    print("\n" + "=" * 60)
    print("ADMIN LOGIN")
    print("=" * 60)
    
    username = input("\nAdmin Username: ").strip()
    password = getpass.getpass("Admin Password: ")
    
    result = auth.login(username, password)
    
    if not result['success']:
        print(f"\n[ERROR] {result['message']}")
        return None
    
    if result['user']['role'] != 'admin':
        print("\n[ERROR] Access denied. Admin privileges required.")
        auth.logout(result['session_token'])
        return None
    
    print(f"\n[SUCCESS] Welcome, Admin {result['user']['username']}!")
    
    return {
        'user': result['user'],
        'token': result['session_token']
    }