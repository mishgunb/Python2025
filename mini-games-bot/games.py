import random

QUIZ_QUESTIONS = [
    {"q": "Столица Франции?", "a": "Париж"},
    {"q": "Столица Австрии?", "a": "Вена"},
    {"q": "Столица России?", "a": "Москва"},
    {"q": "2 + 2 = ?", "a": "4"},
    {"q": "Самая большая планета?", "a": "Юпитер"},
    {"q": "Кто написал 'Войну и мир'?", "a": "Толстой"},
    {"q": "Сколько будет 7²?", "a": "49"},
    {"q": "Чему равно 2³ + 3²?", "a": "17"},
    {"q": "Сколько сторон у пентагона?", "a": "5"},
    {"q": "Сколько континентов на Земле?", "a": "7"},
    {"q": "Какой язык самый распространённый?", "a": "Английский"},
]


def start_guess_number():
    secret = random.randint(1, 10)
    return {"type": "guess_number", "secret": secret, "attempts": 0}

def process_guess_number(game_data, user_input):
    try:
        guess = int(user_input.strip())
    except ValueError:
        return {"text": "Введите число от 1 до 10.", "finished": False, "score": 0}
    
    game_data["attempts"] += 1
    secret = game_data["secret"]
    
    if guess == secret:
        score = max(10 - game_data["attempts"] + 1, 1)
        return {"text": f"✅ Угадал! Загадано было {secret}. Очки: {score}", "finished": True, "score": score}
    elif game_data["attempts"] >= 3:
        return {"text": f"❌ Попытки закончились. Было загадано {secret}.", "finished": True, "score": 0}
    else:
        hint = "больше" if guess < secret else "меньше"
        return {"text": f"Неверно. Загаданное число {hint}. Осталось {3 - game_data['attempts']} попыток.", "finished": False, "score": 0}

def start_quiz():
    question = random.choice(QUIZ_QUESTIONS)
    return {"type": "quiz", "question": question["q"], "answer": question["a"]}

def process_quiz(game_data, user_input):
    user_answer = user_input.strip().lower()
    correct_answer = game_data["answer"].lower()
    if user_answer == correct_answer:
        return {"text": "✅ Правильно! +5 очков.", "finished": True, "score": 5}
    else:
        return {"text": f"❌ Неправильно. Правильный ответ: {game_data['answer']}", "finished": True, "score": 0}