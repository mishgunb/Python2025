import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
database.DB_PATH = "test_games.db"

from database import add_user, save_score, get_user_rating, block_user, unblock_user, is_user_blocked

def setup_function(_):
    if os.path.exists(database.DB_PATH):
        os.remove(database.DB_PATH)
    database.init_db()

def test_user_rating_calculation():
    add_user(101, "test_user1", "Test", "User")
    save_score(101, "quiz", 5)
    save_score(101, "guess_number", 7)
    assert get_user_rating(101) == 12

def test_block_user():
    block_user(555, "test")
    assert is_user_blocked(555) == True

def test_unblock_user():
    block_user(777, "test")
    unblock_user(777)
    assert is_user_blocked(777) == False

def test_new_user_rating_is_zero():
    assert get_user_rating(9999) == 0

