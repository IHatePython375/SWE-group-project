import random
import json
import os

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

class Gamestatistics:
    def __init__(self):
        self.filename = "blackjack_scores.json"
        self.scores = self.load_scores()


    def load_scores(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    


    def score_game(self, player_name, final_money, rounds_completed):
        score_entry = {
            'player': player_name,
            'final_money': final_money,
            'rounds_completed': rounds_completed,
            'profit': final_money - 1000
        }
        self.scores.append(score_entry)
        self.scores.sort(key=lambda x: x['final_money'], reverse=True)
        self.scores = self.scores[:10]
        
        with open(self.filename, 'w') as f:
            json.dump(self.scores, f, indent=2)

    def display_leaderboard(self):
        if not self.scores:
            print("\nNo scores recorded. Play some games to create a leaderboard!\n")
            return
        
        print("\n" + "=" * 60)
        print("LEADERBOARD - Top 10 Players ")
        print("=" * 60)
        for i, score in enumerate(self.scores, 1):
            profit = score['profit']
            profit_str = f"+${profit}" if profit >= 0 else f"-${abs(profit)}"
            print(f"{i}. {score['player']}: ${score['final_money']} ({profit_str}) - {score['rounds_completed']} rounds")
        print("=" * 60)

def get_valid_bet(money):
    while True:
        try:
            bet = int(input(f"\nYour money: ${money}\nEnter your bet:"))
            if bet <= 0:
                print("Bet must be positive!")
            elif bet > money:
                print("You cannot bet more than you have!")
            else:
                return bet
        except ValueError:
            print("Please enter a valid number!")

def play_round(money):
    print("\n" + "=" * 50)
    
    bet = get_valid_bet(money)
    
    deck = Deck()
    deck.shuffle()
    
    player_hand = Hand()
    dealer_hand = Hand()
    
    player_hand.add_card(deck.deal())
    dealer_hand.add_card(deck.deal())
    player_hand.add_card(deck.deal())
    dealer_hand.add_card(deck.deal())
    
    print("\nDealer's Hand:")
    dealer_hand.display(hidden=True)
    
    print("\nYour Hand:")
    player_hand.display()
    
    if player_hand.calculate_value() == 21:
        print("\nBlackjack! You win 1.5x your bet!")
        winnings = int(bet * 1.5)
        return money + winnings
    
    while True:
        choice = input("\nWould you like to (h)it or (s)tand? ").lower()
        
        if choice == 'h':
            player_hand.add_card(deck.deal())
            print("\nYour Hand:")
            player_hand.display()
            
            if player_hand.calculate_value() > 21:
                print(f"\nBust! You lose ${bet} haha!")
                return money - bet
            elif player_hand.calculate_value() == 21:
                print("\n21! Standing automatically.")
                break
        elif choice == 's':
            break
        else:
            print("Invalid choice. Please enter 'h' or 's' bro.")
    
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
    
    player_value = player_hand.calculate_value()
    dealer_value = dealer_hand.calculate_value()
    
    print("\n" + "=" * 50)
    print("Final Results:")
    print("=" * 50)
    print(f"Your total: {player_value}")
    print(f"Dealer's total: {dealer_value}")
    
    if dealer_value > 21:
        print(f"\nDealer busts! You win ${bet}!")
        return money + bet
    elif player_value > dealer_value:
        print(f"\nYou win ${bet}!")
        return money + bet
    elif player_value < dealer_value:
        print(f"\nDealer wins! You lose ${bet}!")
        return money - bet
    else:
        print("\nIt's a tie! Bet returned.")
        return money

def play_game_mode(mode):
    stats = Gamestatistics()
    
    if mode == 'tournament':
        print("\n" + "=" * 60)
        print("TOURNAMENT MODE - 10 ROUNDS")
        print("=" * 60)
        print("Starting money: $1000")
        print("Complete 10 rounds or go broke!")
        print("=" * 60)
        
        player_name = input("\nEnter your name: ").strip()
        if not player_name:
            player_name = "Player"
        
        money = 1000
        max_rounds = 10
        
        for round_num in range(1, max_rounds + 1):
            print(f"\n{'='*60}")
            print(f"ROUND {round_num}/{max_rounds}")
            print(f"{'='*60}")
            
            money = play_round(money)
            
            if money <= 0:
                print("\n" + "=" * 60)
                print("GAME OVER!")
                print("=" * 60)
                print(f"You completed {round_num} rounds")
                return
            
            print(f"\nCurrent money: ${money}")
        
        print("\n" + "=" * 60)
        print("TOURNAMENT COMPLETE!")
        print("=" * 60)
        print(f"Final money: ${money}")
        profit = money - 1000
        if profit > 0:
            print(f"Total profit: +${profit}")
        elif profit < 0:
            print(f"Total loss: -${abs(profit)}")
        else:
            print("Break even!")
        
        stats.score_game(player_name, money, max_rounds)
        print("\nScore saved to leaderboard!")
        stats.display_leaderboard()
    
    else:
        print("\n" + "=" * 60)
        print("FREE PLAY MODE")
        print("=" * 60)
        print("Starting money: $1000")
        print("Play until you quit or broke!")
        print("=" * 60)
        
        money = 1000
        round_num = 0
        
        while True:
            round_num += 1
            print(f"\n{'='*60}")
            print(f"ROUND {round_num}")
            print(f"{'='*60}")
            
            money = play_round(money)
            
            if money <= 0:
                print("\n" + "=" * 60)
                print("GAME OVER!")
                print("=" * 60)
                return
            
            print(f"\nCurrent money: ${money}")
            
            play_again = input("\nContinue playing? (y/n): ").lower()
            if play_again != 'y':
                print(f"\nYou ended with ${money}. Thanks for playing!")
                return

def main():
    stats = Gamestatistics()
    
    while True:
        print("\n" + "=" * 60)
        print("WELCOME TO BLACKJACK SWE!")
        print("=" * 60)
        print("\nGame Modes:")
        print("1. Tournament Mode (10 rounds, save score)")
        print("2. Free Play Mode (play until broke or quit)")
        print("3. View Leaderboard")
        print("4. Quit")
        
        choice = input("\nSelect mode (1-4): ").strip()
        
        if choice == '1':
            play_game_mode('tournament')
        elif choice == '2':
            play_game_mode('freeplay')
        elif choice == '3':
            stats.display_leaderboard()
        elif choice == '4':
            print("\nThanks for playing! Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()