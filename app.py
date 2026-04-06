import os
import random
from typing import Dict, List, Optional

from flask import Flask, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

WORD_LIST = [
    "python",
    "flask",
    "hangman",
    "session",
    "template",
    "routing",
    "backend",
    "frontend",
    "variable",
    "function",
]
MAX_ATTEMPTS = 6


def initialize_game() -> None:
    """Set up a new game in the session."""
    session["word"] = random.choice(WORD_LIST)
    session["max_attempts"] = MAX_ATTEMPTS
    session["wrong_attempts"] = 0
    session["guessed_letters"] = []
    session["message"] = ""
    session["message_type"] = ""


def ensure_game() -> None:
    """Create a game if one is not already stored in the session."""
    required_keys = {"word", "max_attempts", "wrong_attempts", "guessed_letters"}
    if not required_keys.issubset(session.keys()):
        initialize_game()


def get_display_word(word: str, guessed_letters: List[str]) -> str:
    """Build the masked word shown to the player."""
    return " ".join(letter if letter in guessed_letters else "_" for letter in word)


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
    won = is_won(word, guessed_letters)
    lost = is_lost(wrong_attempts, max_attempts)

    return {
        "display_word": get_display_word(word, guessed_letters),
        "guessed_letters": ", ".join(guessed_letters) if guessed_letters else "None",
        "remaining_attempts": max_attempts - wrong_attempts,
        "wrong_attempts": wrong_attempts,
        "max_attempts": max_attempts,
        "won": won,
        "lost": lost,
        "word": word,
        "message": session.get("message", ""),
        "message_type": session.get("message_type", ""),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    ensure_game()

    if request.method == "POST":
        process_guess(request.form.get("guess", ""))
        return redirect(url_for("index"))

    context = get_game_context()
    session["message"] = ""
    session["message_type"] = ""
    return render_template("index.html", **context)


@app.post("/restart")
def restart():
    initialize_game()
    session["message"] = "A new game has started."
    session["message_type"] = "success"
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
