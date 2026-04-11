import os
import random
from typing import Dict, List, Optional

from flask import Flask, jsonify, redirect, render_template, request, session, url_for


def normalize_windows_path(path: str) -> str:
    """Strip the Windows extended-length prefix when present."""
    if os.name == "nt" and path.startswith("\\\\?\\"):
        return path[4:]
    return path


BASE_DIR = normalize_windows_path(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

WORD_BANK = [
    {
        "word": "python",
        "hint": "A popular programming language named after a British comedy group.",
    },
    {
        "word": "flask",
        "hint": "A lightweight Python web framework often used for small apps and APIs.",
    },
    {
        "word": "hangman",
        "hint": "A classic game where players guess letters to uncover a hidden word.",
    },
    {
        "word": "session",
        "hint": "Temporary storage used by web apps to remember a user's game state.",
    },
    {
        "word": "template",
        "hint": "A file used to render dynamic HTML with placeholders for data.",
    },
    {
        "word": "routing",
        "hint": "The process of connecting a URL path to a view or function.",
    },
    {
        "word": "backend",
        "hint": "The server-side part of an application that handles logic and data.",
    },
    {
        "word": "frontend",
        "hint": "The part of a website or app that users directly see and interact with.",
    },
    {
        "word": "variable",
        "hint": "A named container in code that stores a value.",
    },
    {
        "word": "function",
        "hint": "A reusable block of code that performs a specific task.",
    },
]
MAX_ATTEMPTS = 6


def initialize_game() -> None:
    """Set up a new game in the session."""
    selected_entry = random.choice(WORD_BANK)
    session["word"] = selected_entry["word"]
    session["hint"] = selected_entry["hint"]
    session["hint_revealed"] = False
    session["max_attempts"] = MAX_ATTEMPTS
    session["wrong_attempts"] = 0
    session["guessed_letters"] = []
    session["message"] = ""
    session["message_type"] = ""


def ensure_game() -> None:
    """Create a game if one is not already stored in the session."""
    required_keys = {
        "word",
        "hint",
        "hint_revealed",
        "max_attempts",
        "wrong_attempts",
        "guessed_letters",
    }
    if not required_keys.issubset(session.keys()):
        initialize_game()


def get_display_word(word: str, guessed_letters: List[str]) -> str:
    """Build the masked word shown to the player."""
    return " ".join(letter if letter in guessed_letters else "_" for letter in word)


def get_display_letters(word: str, guessed_letters: List[str]) -> List[str]:
    """Return the masked word as a list for richer template rendering."""
    return [letter if letter in guessed_letters else "_" for letter in word]


def is_won(word: str, guessed_letters: List[str]) -> bool:
    """Return True when every unique letter in the word has been guessed."""
    return all(letter in guessed_letters for letter in set(word))


def is_lost(wrong_attempts: int, max_attempts: int) -> bool:
    """Return True when the maximum number of wrong attempts is reached."""
    return wrong_attempts >= max_attempts


def validate_guess(raw_guess: str) -> Optional[str]:
    """Validate user input and normalize it to a lowercase letter."""
    guess = raw_guess.strip().lower()
    if len(guess) != 1 or not guess.isalpha():
        return None
    return guess


def process_guess(raw_guess: str) -> None:
    """Apply one guess to the current game state."""
    word = session["word"]
    guessed_letters = session["guessed_letters"]
    wrong_attempts = session["wrong_attempts"]
    max_attempts = session["max_attempts"]

    if is_won(word, guessed_letters) or is_lost(wrong_attempts, max_attempts):
        session["message"] = "The game is over. Start a new round to keep playing."
        session["message_type"] = "info"
        return

    guess = validate_guess(raw_guess)
    if guess is None:
        session["message"] = "Please enter a single alphabet letter."
        session["message_type"] = "error"
        return

    if guess in guessed_letters:
        session["message"] = f"You already guessed '{guess}'."
        session["message_type"] = "info"
        return

    guessed_letters.append(guess)
    session["guessed_letters"] = guessed_letters

    if guess in word:
        session["message"] = f"Nice! '{guess}' is in the word."
        session["message_type"] = "success"
    else:
        session["wrong_attempts"] = wrong_attempts + 1
        session["message"] = f"Sorry, '{guess}' is not in the word."
        session["message_type"] = "error"


def get_game_context() -> Dict[str, object]:
    """Prepare template data from the session state."""
    word = session["word"]
    guessed_letters = session["guessed_letters"]
    wrong_attempts = session["wrong_attempts"]
    max_attempts = session["max_attempts"]
    unique_letters = set(word)
    revealed_letters = [letter for letter in unique_letters if letter in guessed_letters]
    won = is_won(word, guessed_letters)
    lost = is_lost(wrong_attempts, max_attempts)

    return {
        "display_word": get_display_word(word, guessed_letters),
        "display_letters": get_display_letters(word, guessed_letters),
        "guessed_letters": ", ".join(guessed_letters) if guessed_letters else "None",
        "guessed_letters_list": guessed_letters,
        "remaining_attempts": max_attempts - wrong_attempts,
        "wrong_attempts": wrong_attempts,
        "max_attempts": max_attempts,
        "solved_letters": len(revealed_letters),
        "total_unique_letters": len(unique_letters),
        "progress_percent": int((len(revealed_letters) / len(unique_letters)) * 100),
        "won": won,
        "lost": lost,
        "word": word,
        "hint": session["hint"],
        "hint_revealed": session["hint_revealed"],
        "message": session.get("message", ""),
        "message_type": session.get("message_type", ""),
    }


def clear_message() -> None:
    """Reset the flash-style status message after it has been sent to the client."""
    session["message"] = ""
    session["message_type"] = ""


def consume_game_context() -> Dict[str, object]:
    """Return the latest game state and clear one-time messages."""
    context = get_game_context()
    clear_message()
    return context


def is_ajax_request() -> bool:
    """Detect fetch/XHR requests so the UI can update without a full reload."""
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@app.route("/hint", methods=["POST"])
def reveal_hint():
    ensure_game()
    session["hint_revealed"] = True
    session["message"] = "Hint revealed."
    session["message_type"] = "info"
    if is_ajax_request():
        return jsonify(consume_game_context())
    return redirect(url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    ensure_game()

    if request.method == "POST":
        process_guess(request.form.get("guess", ""))
        if is_ajax_request():
            return jsonify(consume_game_context())
        return redirect(url_for("index"))

    return render_template("index.html", **consume_game_context())


@app.route("/restart", methods=["POST"])
def restart():
    initialize_game()
    session["message"] = "A new game has started."
    session["message_type"] = "success"
    if is_ajax_request():
        return jsonify(consume_game_context())
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
