import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    DB_PATH, init_db, add_user, save_score,
    get_user_rating, block_user, unblock_user, is_user_blocked
)

def setup_function(function):
    """Создаём чистую БД перед каждым тестом."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

def test_user_rating_calculation():
    """Тест 1: проверка расчёта личного рейтинга пользователя."""
    add_user(101, "test_user1", "Test", "User")
    save_score(101, "quiz", 5)
    save_score(101, "guess_number", 7)
    
    total = get_user_rating(101)
    assert total == 12

def test_block_user():
    """Тест 2: проверка на блокировку пользователя."""
    block_user(555, "test")
    assert is_user_blocked(555) == True

def test_unblock_user():
    """Тест 3: проверка на разблокировку пользователя."""
    block_user(777, "test")
    unblock_user(777)
    assert is_user_blocked(777) == False

def test_new_user_rating_is_zero():
    """Тест 4: проверка, что новый пользователь имеет рейтинг 0."""
    assert get_user_rating(9999) == 0