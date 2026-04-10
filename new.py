import random

# Word list with hints
words = {
    "python": "A popular programming language",
    "hangman": "The name of this game",
    "developer": "Someone who writes code",
    "chatgpt": "An AI assistant",
    "programming": "The act of writing code"
}

# Hangman ASCII stages
hangman_stages = [
    """
     -----
     |   |
         |
         |
         |
         |
    =========
    """,
    """
     -----
     |   |
     O   |
         |
         |
         |
    =========
    """,
    """
     -----
     |   |
     O   |
     |   |
         |
         |
    =========
    """,
    """
     -----
     |   |
     O   |
    /|   |
         |
         |
    =========
    """,
    """
     -----
     |   |
     O   |
    /|\\  |
         |
         |
    =========
    """,
    """
     -----
     |   |
     O   |
    /|\\  |
    /    |
         |
    =========
    """,
    """
     -----
     |   |
     O   |
    /|\\  |
    / \\  |
         |
    =========
    """
]

# Choose random word
word, hint = random.choice(list(words.items()))

guessed_letters = []
wrong_guesses = 0
max_attempts = len(hangman_stages) - 1
hint_used = False

print("🎮 Welcome to Hangman (with hints!)")

def display_word():
    return " ".join([letter if letter in guessed_letters else "_" for letter in word])

while wrong_guesses < max_attempts:

    print(hangman_stages[wrong_guesses])
    print("Word:", display_word())
    print("Guessed letters:", ", ".join(guessed_letters) if guessed_letters else "None")
    print("Attempts left:", max_attempts - wrong_guesses)

    if not hint_used:
        print("💡 Type 'hint' to get a hint (only once)")

    guess = input("Enter a letter: ").lower().strip()

    # Hint logic
    if guess == "hint" and not hint_used:
        print("💡 Hint:", hint)
        hint_used = True
        continue

    # Validation
    if len(guess) != 1 or not guess.isalpha():
        print("⚠️ Enter a single valid letter!")
        continue

    if guess in guessed_letters:
        print("⚠️ Already guessed!")
        continue

    guessed_letters.append(guess)

    if guess in word:
        print("✅ Correct!")
    else:
        print("❌ Wrong!")
        wrong_guesses += 1

    # Win condition
    if all(letter in guessed_letters for letter in word):
        print("\n🎉 You WON! The word was:", word)
        break

# Lose condition
if wrong_guesses == max_attempts:
    print(hangman_stages[wrong_guesses])
    print("\n💀 You LOST! The word was:", word)