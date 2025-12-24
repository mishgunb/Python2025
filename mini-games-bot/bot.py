import requests
import time
import json
import logging
from urllib.parse import urljoin
from config import BOT_TOKEN, ADMIN_ID
from database import (
    init_db, add_user, is_user_blocked, block_user, unblock_user,
    save_score, is_game_active, toggle_game, get_stats,
    get_user_rating, get_global_rating,
    get_user_by_username, get_blocked_users_with_reason,
    get_user_stats
)

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
logging.basicConfig(level=logging.INFO)

user_states = {}

def send_message(chat_id, text, reply_markup=None):
    url = urljoin(BASE_URL, "sendMessage")
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

def get_updates(offset=None):
    url = urljoin(BASE_URL, "getUpdates")
    params = {"offset": offset, "timeout": 30}
    try:
        resp = requests.get(url, params=params, timeout=35)
        return resp.json().get("result", [])
    except Exception as e:
        logging.error(f"Ошибка получения обновлений: {e}")
        return []

def handle_message(message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    username = message["from"].get("username", "")
    first_name = message["from"].get("first_name", "")
    last_name = message["from"].get("last_name", "")

    add_user(user_id, username, first_name, last_name)

    if is_user_blocked(user_id):
        send_message(chat_id, "⚠️ Вы заблокированы.")
        return

    text = message.get("text", "").strip()

    # Админ-команды
    if user_id == ADMIN_ID:
        if text == "/admin":
            send_message(chat_id, "Команды админа:\n"
                                  "/toggle_quiz — вкл/выкл викторину\n"
                                  "/toggle_guess — вкл/выкл угадай число\n"
                                  "/block @username причина — заблокировать\n"
                                  "/unblock @username — разблокировать\n"
                                  "/blocked — список заблокированных\n"
                                  "/user_stats @username — статистика игрока\n"
                                  "/stats — общая статистика")
            return
        elif text.startswith("/block "):
            parts = text[7:].strip().split(" ", 1)
            if len(parts) < 2:
                send_message(chat_id, "Используйте: /block @username причина")
                return
            username_input = parts[0]
            reason = parts[1]
            username = username_input.lstrip("@")
            target_id = get_user_by_username(username)
            if not target_id:
                send_message(chat_id, f"Пользователь @{username} не найден в базе. Он должен хотя бы один раз написать боту.")
                return
            block_user(target_id, reason)
            send_message(chat_id, f"✅ Пользователь @{username} заблокирован.\nПричина: {reason}")
            try:
                send_message(target_id, f"⚠️ Вы были заблокированы в боте.\nПричина: {reason}")
            except:
                pass
            return
        elif text.startswith("/unblock "):
            username_input = text[9:].strip()
            username = username_input.lstrip("@")
            target_id = get_user_by_username(username)
            if not target_id:
                send_message(chat_id, f"Пользователь @{username} не найден.")
                return
            unblock_user(target_id)
            send_message(chat_id, f"✅ Пользователь @{username} разблокирован.")
            try:
                send_message(target_id, "✅ Вы были разблокированы в боте.")
            except:
                pass
            return
        elif text == "/blocked":
            blocked_list = get_blocked_users_with_reason()
            if not blocked_list:
                send_message(chat_id, "Нет заблокированных пользователей.")
            else:
                lines = [f"@{u} — {r}" for u, r in blocked_list]
                send_message(chat_id, "🚫 Заблокированные:\n" + "\n".join(lines))
            return
        elif text.startswith("/user_stats "):
            username_input = text[12:].strip().lstrip("@")
            stats = get_user_stats(username_input)
            if not stats:
                send_message(chat_id, f"Пользователь @{username_input} не найден или не играл.")
                return
            
            lines = [
                f"📊 Статистика игрока @{username_input}:",
                "",
                f"Всего сыграно игр: {stats['total_games']}",
                f"Общий рейтинг: {stats['total_score']} очк.",
                "",
                "Результаты по играм:"
            ]
            
            for game, data in stats["details"].items():
                lines.append(f"— {game}: {data['games']} игр., {data['score']} очк.")
            
            send_message(chat_id, "\n".join(lines))
            return
        elif text == "/stats":
            stats = get_stats()
            msg = (
                f"📊 Общая статистика:\n"
                f"Пользователей: {stats['users']}\n"
                f"Сыграно игр: {stats['games_played']}\n"
                f"Общее количество очков: {stats['total_score']} очк."
            )
            send_message(chat_id, msg)
            return
        elif text == "/toggle_quiz":
            current = is_game_active("quiz")
            toggle_game("quiz", not current)
            send_message(chat_id, f"Викторина {'включена' if not current else 'выключена'}")
            return
        elif text == "/toggle_guess":
            current = is_game_active("guess_number")
            toggle_game("guess_number", not current)
            send_message(chat_id, f"«Угадай число» {'включена' if not current else 'выключена'}")
            return

    # Обработка активных игр
    if user_id in user_states:
        state = user_states[user_id]
        game_type = state["game_type"]
        if game_type == "quiz":
            result = process_quiz(state["data"], text)
            if result["finished"]:
                save_score(user_id, "quiz", result["score"])
                del user_states[user_id]
            send_message(chat_id, result["text"])
            return
        elif game_type == "guess_number":
            result = process_guess_number(state["data"], text)
            if result["finished"]:
                save_score(user_id, "guess_number", result["score"])
                del user_states[user_id]
            send_message(chat_id, result["text"])
            return

    # Команды пользователя
    if text == "/start":
        send_message(chat_id, "🎮 Добро пожаловать! Выберите игру:\n"
                              "/quiz — Викторина (+5 за правильный ответ)\n"
                              "/guess — Угадай число (до 10 очков)\n"
                              "/rating — Ваш рейтинг и топ-10")
    elif text == "/quiz":
        if not is_game_active("quiz"):
            send_message(chat_id, "❌ Викторина временно недоступна.")
            return
        game_data = start_quiz()
        user_states[user_id] = {"game_type": "quiz", "data": game_data}
        send_message(chat_id, f"❓ {game_data['question']}")
    elif text == "/guess":
        if not is_game_active("guess_number"):
            send_message(chat_id, "❌ Игра «Угадай число» временно недоступна.")
            return
        game_data = start_guess_number()
        user_states[user_id] = {"game_type": "guess_number", "data": game_data}
        send_message(chat_id, "🔮 Я загадал число от 1 до 10. У вас 3 попытки. Введите число:")
    elif text == "/rating":
        personal_score = get_user_rating(user_id)
        personal_msg = f"👤 Ваш рейтинг: {personal_score} очк."

        top = get_global_rating()
        if top:
            top_lines = [f"{i+1}. @{u} — {s} очк." for i, (u, s) in enumerate(top)]
            top_msg = "🏆 Топ-10 игроков:\n" + "\n".join(top_lines)
        else:
            top_msg = "🏆 Топ-10 игроков:\n— пока пусто —"

        send_message(chat_id, f"{personal_msg}\n\n{top_msg}")
    else:
        send_message(chat_id, "Неизвестная команда. Используйте /start")

from games import start_quiz, process_quiz, start_guess_number, process_guess_number

if __name__ == "__main__":
    init_db()
    logging.info("Бот запущен. Ожидание сообщений...")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update:
                    handle_message(update["message"])
            time.sleep(0.5)
        except KeyboardInterrupt:
            logging.info("Бот остановлен.")
            break
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            time.sleep(5)