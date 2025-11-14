import random
import json
import getpass
from database import DatabaseHelper
from auth import AuthManager
from admin import AdminPanel

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"
    
    def value(self):
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11  
        else:
            return int(self.rank)
    
    def to_dict(self):
        """Convert card to dictionary for JSON storage"""
        return {'suit': self.suit, 'rank': self.rank}
    
    @staticmethod
    def from_dict(data):
        """Create card from dictionary"""
        return Card(data['suit'], data['rank'])

class Deck:
    def __init__(self):
        self.cards = []
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        return self.cards.pop()
    
    def to_dict(self):
        """Convert deck to dictionary for JSON storage"""
        return [card.to_dict() for card in self.cards]
    
    @staticmethod
    def from_dict(data):
        """Create deck from dictionary"""
        deck = Deck()
        deck.cards = [Card.from_dict(card_data) for card_data in data]
        return deck

class Hand:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def calculate_value(self):
        value = 0
        aces = 0

        for card in self.cards:
            value += card.value()
            if card.rank == 'A':
                aces += 1

        while value > 21 and aces > 0:
            value -= 10
            aces -= 1

        return value
    
    def display(self, hidden=False):
        if hidden:
            print("The card is hidden!!!")
            for card in self.cards[1:]:
                print(f" {card}")
        else:
            for card in self.cards:
                print(f" {card}")
            print(f" Score: {self.calculate_value()}")
    
    def to_dict(self):
        """Convert hand to dictionary for JSON storage"""
        return [card.to_dict() for card in self.cards]
    
    @staticmethod
    def from_dict(data):
        """Create hand from dictionary"""
        hand = Hand()
        hand.cards = [Card.from_dict(card_data) for card_data in data]
        return hand

class BlackjackGame:
    """Main game class that integrates with database"""
    
    def __init__(self, db: DatabaseHelper, auth: AuthManager):
        self.db = db
        self.auth = auth
        self.current_user = None
        self.session_token = None
        self.current_session_id = None
    
    def save_game_state(self, session_id, round_number, player_hand, dealer_hand, deck, bet, phase):
        """Save current game state to database"""
        self.db.save_game_state(
            session_id, round_number,
            player_hand.to_dict(),
            dealer_hand.to_dict(),
            deck.to_dict(),
            bet, phase
        )
    
    def load_game_state(self, session_id):
        """Load saved game state from database"""
        state = self.db.load_game_state(session_id)
        if not state:
            return None
        
        # Reconstruct game objects
        player_hand = Hand.from_dict(state['player_hand'])
        dealer_hand = Hand.from_dict(state['dealer_hand'])
        deck = Deck.from_dict(state['deck_state'])
        
        return {
            'round_number': state['round_number'],
            'player_hand': player_hand,
            'dealer_hand': dealer_hand,
            'deck': deck,
            'bet': float(state['current_bet']),
            'phase': state['game_phase']
        }
    
    def get_valid_bet(self, money):
        """Get valid bet from player"""
        while True:
            try:
                bet_input = input(f"\nYour money: ${money}\nEnter your bet (or 'save' to save and quit): ")
                
                if bet_input.lower() == 'save':
                    return 'SAVE'
                
                bet = int(bet_input)
                if bet <= 0:
                    print("Bet must be positive!")
                elif bet > money:
                    print("You cannot bet more than you have!")
                else:
                    return bet
            except ValueError:
                print("Please enter a valid number or 'save'!")
    
    def play_round(self, money, session_id, round_number):
        """Play a single round and save to database"""
        print("\n" + "=" * 50)
        
        bet = self.get_valid_bet(money)
        
        # Check if player wants to save at betting phase
        if bet == 'SAVE':
            print("\n[SAVED] Game saved! You can resume later.")
            # Save with minimal state - just track the round we're on
            deck = Deck()
            player_hand = Hand()
            dealer_hand = Hand()
            self.save_game_state(session_id, round_number, player_hand, dealer_hand,
                                deck, 0, 'betting')
            return None
        
        deck = Deck()
        deck.shuffle()
        
        player_hand = Hand()
        dealer_hand = Hand()
        
        # Deal initial cards
        player_hand.add_card(deck.deal())
        dealer_hand.add_card(deck.deal())
        player_hand.add_card(deck.deal())
        dealer_hand.add_card(deck.deal())
        
        # Save initial game state
        self.save_game_state(session_id, round_number, player_hand, dealer_hand, 
                            deck, bet, 'player_turn')
        
        print("\nDealer's Hand:")
        dealer_hand.display(hidden=True)
        
        print("\nYour Hand:")
        player_hand.display()
        
        # Check for blackjack
        if player_hand.calculate_value() == 21:
            print("\nBlackjack! You win 1.5x your bet!")
            winnings = int(bet * 1.5)
            new_money = money + winnings
            
            # Save to database and clear save state
            self.db.save_game_round(
                session_id, round_number, bet,
                player_hand.to_dict(), dealer_hand.to_dict(),
                21, dealer_hand.calculate_value(),
                'blackjack', winnings, new_money
            )
            self.db.delete_game_state(session_id)
            
            return new_money
        
        # Player's turn
        while True:
            choice = input("\n(h)it, (s)tand, or (save) and quit? ").lower()
            
            if choice == 'save':
                print("\n[SAVED] Game saved! You can resume later.")
                self.save_game_state(session_id, round_number, player_hand, dealer_hand,
                                    deck, bet, 'player_turn')
                return None  # Signal to exit
            
            elif choice == 'h':
                player_hand.add_card(deck.deal())
                print("\nYour Hand:")
                player_hand.display()
                
                # Update save state
                self.save_game_state(session_id, round_number, player_hand, dealer_hand,
                                    deck, bet, 'player_turn')
                
                if player_hand.calculate_value() > 21:
                    print(f"\nBust! You lose ${bet}!")
                    new_money = money - bet
                    
                    # Save to database and clear save state
                    self.db.save_game_round(
                        session_id, round_number, bet,
                        player_hand.to_dict(), dealer_hand.to_dict(),
                        player_hand.calculate_value(), dealer_hand.calculate_value(),
                        'bust', -bet, new_money
                    )
                    self.db.delete_game_state(session_id)
                    
                    return new_money
                elif player_hand.calculate_value() == 21:
                    print("\n21! Standing automatically.")
                    break
            elif choice == 's':
                break
            else:
                print("Invalid choice. Please enter 'h', 's', or 'save'.")
        
        # Dealer's turn
        print("\n" + "=" * 50)
        print("Dealer's turn")
        print("=" * 50)
        print("\nDealer's Hand:")
        dealer_hand.display()
        
        while dealer_hand.calculate_value() < 17:
            print("\nDealer hits")
            dealer_hand.add_card(deck.deal())
            print("\nDealer's Hand:")
            dealer_hand.display()
        
        # Determine winner
        player_value = player_hand.calculate_value()
        dealer_value = dealer_hand.calculate_value()
        
        print("\n" + "=" * 50)
        print("Final Results:")
        print("=" * 50)
        print(f"Your total: {player_value}")
        print(f"Dealer's total: {dealer_value}")
        
        if dealer_value > 21:
            print(f"\nDealer busts! You win ${bet}!")
            result = 'win'
            winnings = bet
            new_money = money + bet
        elif player_value > dealer_value:
            print(f"\nYou win ${bet}!")
            result = 'win'
            winnings = bet
            new_money = money + bet
        elif player_value < dealer_value:
            print(f"\nDealer wins! You lose ${bet}!")
            result = 'loss'
            winnings = -bet
            new_money = money - bet
        else:
            print("\nIt's a tie! Bet returned.")
            result = 'push'
            winnings = 0
            new_money = money
        
        # Save to database and clear save state
        self.db.save_game_round(
            session_id, round_number, bet,
            player_hand.to_dict(), dealer_hand.to_dict(),
            player_value, dealer_value,
            result, winnings, new_money
        )
        self.db.delete_game_state(session_id)
        
        return new_money
    
    def resume_game(self, session_id, money):
        """Resume a saved game"""
        saved_state = self.load_game_state(session_id)
        
        if not saved_state:
            print("\n[ERROR] No saved game found.")
            return money
        
        print("\n" + "=" * 50)
        print("[RESUMING] Resuming Saved Game")
        print("=" * 50)
        
        round_number = saved_state['round_number']
        phase = saved_state['phase']
        
        # If saved during betting phase, just start fresh round
        if phase == 'betting':
            print(f"\nResuming at Round {round_number} (betting phase)")
            self.db.delete_game_state(session_id)
            return self.play_round(money, session_id, round_number)
        
        # Otherwise resume mid-round
        player_hand = saved_state['player_hand']
        dealer_hand = saved_state['dealer_hand']
        deck = saved_state['deck']
        bet = saved_state['bet']
        
        print(f"\nRound {round_number}")
        print(f"Your bet: ${bet}")
        
        print("\nDealer's Hand:")
        dealer_hand.display(hidden=True)
        
        print("\nYour Hand:")
        player_hand.display()
        
        # Continue from player's turn
        while True:
            choice = input("\n(h)it, (s)tand, or (save) and quit? ").lower()
            
            if choice == 'save':
                print("\n[SAVED] Game saved!")
                self.save_game_state(session_id, round_number, player_hand, dealer_hand,
                                    deck, bet, 'player_turn')
                return None
            
            elif choice == 'h':
                player_hand.add_card(deck.deal())
                print("\nYour Hand:")
                player_hand.display()
                
                self.save_game_state(session_id, round_number, player_hand, dealer_hand,
                                    deck, bet, 'player_turn')
                
                if player_hand.calculate_value() > 21:
                    print(f"\nBust! You lose ${bet}!")
                    new_money = money - bet
                    
                    self.db.save_game_round(
                        session_id, round_number, bet,
                        player_hand.to_dict(), dealer_hand.to_dict(),
                        player_hand.calculate_value(), dealer_hand.calculate_value(),
                        'bust', -bet, new_money
                    )
                    self.db.delete_game_state(session_id)
                    
                    return new_money
                elif player_hand.calculate_value() == 21:
                    print("\n21! Standing automatically.")
                    break
            elif choice == 's':
                break
            else:
                print("Invalid choice. Please enter 'h', 's', or 'save'.")
        
        # Dealer's turn
        print("\n" + "=" * 50)
        print("Dealer's turn")
        print("=" * 50)
        print("\nDealer's Hand:")
        dealer_hand.display()
        
        while dealer_hand.calculate_value() < 17:
            print("\nDealer hits")
            dealer_hand.add_card(deck.deal())
            print("\nDealer's Hand:")
            dealer_hand.display()
        
        # Determine winner
        player_value = player_hand.calculate_value()
        dealer_value = dealer_hand.calculate_value()
        
        print("\n" + "=" * 50)
        print("Final Results:")
        print("=" * 50)
        print(f"Your total: {player_value}")
        print(f"Dealer's total: {dealer_value}")
        
        if dealer_value > 21:
            result = 'win'
            winnings = bet
            new_money = money + bet
            print(f"\nDealer busts! You win ${bet}!")
        elif player_value > dealer_value:
            result = 'win'
            winnings = bet
            new_money = money + bet
            print(f"\nYou win ${bet}!")
        elif player_value < dealer_value:
            result = 'loss'
            winnings = -bet
            new_money = money - bet
            print(f"\nDealer wins! You lose ${bet}!")
        else:
            result = 'push'
            winnings = 0
            new_money = money
            print("\nIt's a tie! Bet returned.")
        
        self.db.save_game_round(
            session_id, round_number, bet,
            player_hand.to_dict(), dealer_hand.to_dict(),
            player_value, dealer_value,
            result, winnings, new_money
        )
        self.db.delete_game_state(session_id)
        
        return new_money
    
    def play_tournament(self):
        """Play tournament mode - 10 rounds"""
        # Check for saved game
        active_session = self.db.get_active_session(self.current_user['user_id'])
        saved_state = None
        
        if active_session:
            saved_state = self.load_game_state(active_session['session_id'])
            if saved_state:
                resume = input("\n[SAVED GAME FOUND] Resume? (y/n): ").lower()
                if resume == 'y':
                    session_id = active_session['session_id']
                    money = float(active_session['current_money'])
                    start_round = saved_state['round_number']
                    max_rounds = active_session['max_rounds']
                    
                    # Resume saved round
                    result = self.resume_game(session_id, money)
                    if result is None:
                        return  # User saved and quit
                    money = result
                    
                    # Continue remaining rounds
                    for round_num in range(start_round + 1, max_rounds + 1):
                        if money <= 0:
                            break
                        print(f"\n{'='*60}")
                        print(f"ROUND {round_num}/{max_rounds}")
                        print(f"{'='*60}")
                        
                        result = self.play_round(money, session_id, round_num)
                        if result is None:
                            return  # User saved and quit
                        
                        money = result
                        self.db.update_session(session_id, money, round_num)
                        
                        if money <= 0:
                            print("\n" + "=" * 60)
                            print("GAME OVER - BROKE!")
                            print("=" * 60)
                            self.db.complete_session(session_id)
                            self.db.update_user_statistics(self.current_user['user_id'])
                            return
                        
                        print(f"\nCurrent money: ${money}")
                    
                    # Tournament complete
                    self.finish_tournament(session_id, money, max_rounds)
                    return
        
        # Start new tournament
        print("\n" + "=" * 60)
        print("TOURNAMENT MODE - 10 ROUNDS")
        print("=" * 60)
        print("Starting money: $1000")
        print("Complete 10 rounds or go broke!")
        print("=" * 60)
        
        starting_money_setting = self.db.get_game_setting('starting_money')
        starting_money = float(starting_money_setting) if starting_money_setting else 1000.0
        
        max_rounds_setting = self.db.get_game_setting('tournament_rounds')
        max_rounds = int(max_rounds_setting) if max_rounds_setting else 10
        
        session_id = self.db.create_game_session(
            self.current_user['user_id'],
            'tournament',
            starting_money,
            max_rounds
        )
        
        money = starting_money
        
        for round_num in range(1, max_rounds + 1):
            print(f"\n{'='*60}")
            print(f"ROUND {round_num}/{max_rounds}")
            print(f"{'='*60}")
            
            result = self.play_round(money, session_id, round_num)
            
            if result is None:
                # User saved and quit
                return
            
            money = result
            self.db.update_session(session_id, money, round_num)
            
            if money <= 0:
                print("\n" + "=" * 60)
                print("GAME OVER - BROKE!")
                print("=" * 60)
                print(f"You completed {round_num} rounds")
                self.db.complete_session(session_id)
                self.db.update_user_statistics(self.current_user['user_id'])
                return
            
            print(f"\nCurrent money: ${money}")
        
        self.finish_tournament(session_id, money, max_rounds)
    
    def finish_tournament(self, session_id, money, max_rounds):
        """Finish tournament and save to leaderboard"""
        starting_money_setting = self.db.get_game_setting('starting_money')
        starting_money = float(starting_money_setting) if starting_money_setting else 1000.0
        
        print("\n" + "=" * 60)
        print("TOURNAMENT COMPLETE!")
        print("=" * 60)
        print(f"Final money: ${money}")
        profit = money - starting_money
        if profit > 0:
            print(f"Total profit: +${profit}")
        elif profit < 0:
            print(f"Total loss: -${abs(profit)}")
        else:
            print("Break even!")
        
        self.db.complete_session(session_id)
        self.db.add_to_leaderboard(
            self.current_user['user_id'],
            session_id,
            money,
            max_rounds,
            profit
        )
        self.db.update_user_statistics(self.current_user['user_id'])
        
        print("\nScore saved to leaderboard!")
        self.display_leaderboard()
    
    def play_freeplay(self):
        """Play free play mode - unlimited rounds"""
        print("\n" + "=" * 60)
        print("FREE PLAY MODE")
        print("=" * 60)
        print("Starting money: $1000")
        print("Play until you quit or go broke!")
        print("=" * 60)
        
        starting_money_setting = self.db.get_game_setting('starting_money')
        starting_money = float(starting_money_setting) if starting_money_setting else 1000.0
        
        session_id = self.db.create_game_session(
            self.current_user['user_id'],
            'freeplay',
            starting_money,
            None
        )
        
        money = starting_money
        round_num = 0
        
        while True:
            round_num += 1
            print(f"\n{'='*60}")
            print(f"ROUND {round_num}")
            print(f"{'='*60}")
            
            result = self.play_round(money, session_id, round_num)
            
            if result is None:
                # User saved and quit
                return
            
            money = result
            self.db.update_session(session_id, money, round_num)
            
            if money <= 0:
                print("\n" + "=" * 60)
                print("GAME OVER - BROKE!")
                print("=" * 60)
                self.db.complete_session(session_id)
                self.db.update_user_statistics(self.current_user['user_id'])
                return
            
            print(f"\nCurrent money: ${money}")
            
            play_again = input("\nContinue playing? (y/n): ").lower()
            if play_again != 'y':
                print(f"\nYou ended with ${money}. Thanks for playing!")
                self.db.complete_session(session_id)
                self.db.update_user_statistics(self.current_user['user_id'])
                return
    
    def display_leaderboard(self):
        """Display top 10 leaderboard"""
        leaderboard = self.db.get_leaderboard(10)
        
        if not leaderboard:
            print("\nNo scores recorded. Play some games to create a leaderboard!\n")
            return
        
        print("\n" + "=" * 60)
        print("LEADERBOARD - Top 10 Players")
        print("=" * 60)
        for i, entry in enumerate(leaderboard, 1):
            profit = entry['profit']
            profit_str = f"+${profit}" if profit >= 0 else f"-${abs(profit)}"
            print(f"{i}. {entry['username']}: ${entry['final_money']} ({profit_str}) - {entry['rounds_completed']} rounds")
        print("=" * 60)
    
    def display_user_stats(self):
        """Display current user's statistics"""
        profile = self.db.get_user_profile(self.current_user['user_id'])
        
        print("\n" + "=" * 60)
        print(f"PLAYER STATISTICS - {self.current_user['username']}")
        print("=" * 60)
        print(f"Total Games Played: {profile['total_games_played']}")
        print(f"Total Winnings: ${profile['total_winnings']:.2f}")
        print(f"Total Losses: ${profile['total_losses']:.2f}")
        print(f"Highest Balance: ${profile['highest_balance']:.2f}")
        print(f"Net Profit/Loss: ${profile['total_winnings'] - profile['total_losses']:.2f}")
        print("=" * 60)
    
    def login_menu(self):
        """Login/Register menu"""
        while True:
            print("\n" + "=" * 60)
            print("WELCOME TO BLACKJACK SWE!")
            print("=" * 60)
            print("\n1. Login")
            print("2. Register")
            print("3. Quit")
            
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == '1':
                # Login
                username = input("\nUsername: ").strip()
                password = getpass.getpass("Password: ")
                
                result = self.auth.login(username, password)
                
                if result['success']:
                    self.session_token = result['session_token']
                    self.current_user = result['user']
                    print(f"\n✓ Welcome back, {self.current_user['username']}!")
                    return True
                else:
                    print(f"\n✗ {result['message']}")
            
            elif choice == '2':
                # Register
                print("\n--- REGISTRATION ---")
                username = input("Username (min 3 chars): ").strip()
                email = input("Email: ").strip()
                password = getpass.getpass("Password (min 6 chars): ")
                
                result = self.auth.register_user(username, email, password)
                
                if result['success']:
                    print(f"\n✓ {result['message']}")
                    print("Please login with your new account.")
                else:
                    print(f"\n✗ {result['message']}")
            
            elif choice == '3':
                print("\nGoodbye!")
                return False
            
            else:
                print("Invalid choice. Please enter 1-3.")
    
    def main_menu(self):
        """Main game menu after login"""
        while True:
            # Check for saved game
            active_session = self.db.get_active_session(self.current_user['user_id'])
            saved_state = None
            
            if active_session:
                saved_state = self.load_game_state(active_session['session_id'])
            
            print("\n" + "=" * 60)
            print(f"BLACKJACK SWE - Welcome, {self.current_user['username']}!")
            print("=" * 60)
            print("\nGame Modes:")
            print("1. Tournament Mode (10 rounds, save score)")
            print("2. Free Play Mode (play until broke or quit)")
            
            if saved_state:
                print("3. [SAVED] Resume Saved Game")
                print("4. View Leaderboard")
                print("5. View My Statistics")
                print("6. Logout")
                max_option = '6'
            else:
                print("3. View Leaderboard")
                print("4. View My Statistics")
                print("5. Logout")
                max_option = '5'
            
            choice = input(f"\nSelect mode (1-{max_option}): ").strip()
            
            if choice == '1':
                self.play_tournament()
            elif choice == '2':
                self.play_freeplay()
            elif choice == '3' and saved_state:
                # Resume game
                session_id = active_session['session_id']
                money = float(active_session['current_money'])
                
                if active_session['game_mode'] == 'tournament':
                    start_round = saved_state['round_number']
                    max_rounds = active_session['max_rounds']
                    
                    result = self.resume_game(session_id, money)
                    if result is None:
                        continue
                    money = result
                    
                    # Continue remaining rounds
                    for round_num in range(start_round + 1, max_rounds + 1):
                        if money <= 0:
                            break
                        print(f"\n{'='*60}")
                        print(f"ROUND {round_num}/{max_rounds}")
                        print(f"{'='*60}")
                        
                        result = self.play_round(money, session_id, round_num)
                        if result is None:
                            break
                        
                        money = result
                        self.db.update_session(session_id, money, round_num)
                        
                        if money <= 0:
                            print("\n" + "=" * 60)
                            print("GAME OVER - BROKE!")
                            print("=" * 60)
                            self.db.complete_session(session_id)
                            self.db.update_user_statistics(self.current_user['user_id'])
                            break
                        
                        print(f"\nCurrent money: ${money}")
                    
                    if money > 0 and round_num >= max_rounds:
                        self.finish_tournament(session_id, money, max_rounds)
            elif choice == '3' and not saved_state:
                self.display_leaderboard()
            elif choice == '4' and saved_state:
                self.display_leaderboard()
            elif choice == '4' and not saved_state:
                self.display_user_stats()
            elif choice == '5' and saved_state:
                self.display_user_stats()
            elif choice == '5' and not saved_state:
                self.auth.logout(self.session_token)
                print(f"\n✓ Logged out. Goodbye, {self.current_user['username']}!")
                return
            elif choice == '6' and saved_state:
                self.auth.logout(self.session_token)
                print(f"\n✓ Logged out. Goodbye, {self.current_user['username']}!")
                return
            else:
                print(f"Invalid choice. Please enter 1-{max_option}.")
    
    def run(self):
        """Main game loop"""
        if self.login_menu():
            # Check if user is admin
            if self.current_user['role'] == 'admin':
                # Go straight to admin panel
                print("\n[ADMIN MODE] Launching Admin Panel...")
                admin_panel = AdminPanel(self.db, self.auth, self.current_user)
                admin_panel.display_menu()
                # Logout after admin panel
                self.auth.logout(self.session_token)
                print(f"\n[LOGGED OUT] Goodbye, {self.current_user['username']}!")
            else:
                # Regular player - show game menu
                self.main_menu()

def main():
    # Initialize database and auth
    db = DatabaseHelper(
        host='localhost',
        port=5432,
        database='blackjack_db',
        user='postgres',
        password='1234'  # CHANGE THIS!
    )
    
    auth = AuthManager(db)
    
    # Create and run game
    game = BlackjackGame(db, auth)
    game.run()

if __name__ == "__main__":
    main()