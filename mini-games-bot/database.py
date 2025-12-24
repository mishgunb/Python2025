import sqlite3

DB_PATH = "games.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            user_id INTEGER,
            game_name TEXT,
            score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS game_status (
            game_name TEXT PRIMARY KEY,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blocked_users (
            user_id INTEGER PRIMARY KEY,
            reason TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO users (id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def is_user_blocked(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM blocked_users WHERE user_id = ?", (user_id,))
    res = cur.fetchone()
    conn.close()
    return res is not None

def block_user(user_id, reason=""):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO blocked_users (user_id, reason) VALUES (?, ?)", (user_id, reason))
    conn.commit()
    conn.close()

def unblock_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM blocked_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_blocked_users_with_reason():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT u.username, b.reason
        FROM blocked_users b
        JOIN users u ON b.user_id = u.id
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_rating(user_id, game_name=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if game_name:
        cur.execute("SELECT SUM(score) FROM scores WHERE user_id = ? AND game_name = ?", (user_id, game_name))
    else:
        cur.execute("SELECT SUM(score) FROM scores WHERE user_id = ?", (user_id,))
    res = cur.fetchone()[0]
    conn.close()
    return res or 0

def get_global_rating(game_name=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if game_name:
        cur.execute("""
            SELECT u.username, SUM(s.score) AS total
            FROM scores s
            JOIN users u ON s.user_id = u.id
            WHERE s.game_name = ?
            GROUP BY u.id
            ORDER BY total DESC
            LIMIT 10
        """, (game_name,))
    else:
        cur.execute("""
            SELECT u.username, SUM(s.score) AS total
            FROM scores s
            JOIN users u ON s.user_id = u.id
            GROUP BY u.id
            ORDER BY total DESC
            LIMIT 10
        """)
    res = cur.fetchall()
    conn.close()
    return res

def save_score(user_id, game_name, score):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO scores (user_id, game_name, score) VALUES (?, ?, ?)", (user_id, game_name, score))
    conn.commit()
    conn.close()

def toggle_game(game_name, is_active):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO game_status (game_name, is_active) VALUES (?, ?)", (game_name, int(is_active)))
    conn.commit()
    conn.close()

def is_game_active(game_name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT is_active FROM game_status WHERE game_name = ?", (game_name,))
    row = cur.fetchone()
    conn.close()
    return bool(row[0]) if row else True

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM scores")
    games_played = cur.fetchone()[0]
    cur.execute("SELECT SUM(score) FROM scores")
    total_score = cur.fetchone()[0] or 0
    conn.close()
    return {
        "users": users,
        "games_played": games_played,
        "total_score": total_score
    }

def get_user_stats(username):
    """Возвращает статистику игрока: общее количество игр, общий счёт и детали по играм."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    user_id = row[0]
    
    cur.execute("""
        SELECT 
            game_name,
            COUNT(*) as game_count,
            SUM(score) as total_score
        FROM scores
        WHERE user_id = ?
        GROUP BY game_name
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        return {
            "total_games": 0,
            "total_score": 0,
            "details": {}
        }
    
    details = {}
    total_games = 0
    total_score = 0
    
    for game_name, count, score_sum in rows:
        details[game_name] = {"games": count, "score": score_sum}
        total_games += count
        total_score += score_sum
    
    return {
        "total_games": total_games,
        "total_score": total_score,
        "details": details
    }