import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DatabaseHelper

db = DatabaseHelper(
    host='localhost',
    port=5432,
    database='blackjack_db',
    user='postgres',         
    password='1234'
)

db.create_dummy_leaderboard()