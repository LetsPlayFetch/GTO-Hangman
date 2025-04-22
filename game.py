import random
import re
from collections import defaultdict
from colorama import Fore, Back, Style, init
import time

# Initialize colorama
init(autoreset=True)

class HangmanGame:
    def __init__(self, word_list_file="words.txt"):
        # Load words from file
        with open(word_list_file) as f:
            self.all_words = [word.strip().lower() for word in f.readlines()]
        
        # Organize words by length
        self.words_by_length = defaultdict(list)
        for word in self.all_words:
            self.words_by_length[len(word)].append(word)
        
        # Precompute letter frequencies for each word length
        self.letter_frequencies = {}
        for length, words in self.words_by_length.items():
            freq = defaultdict(int)
            for word in words:
                for letter in word:
                    freq[letter] += 1
            # Convert to sorted list of (letter, count) tuples
            sorted_freq = sorted(freq.items(), key=lambda x: -x[1])
            self.letter_frequencies[length] = sorted_freq
    
    def select_random_word(self, min_length=4, max_length=8):
        valid_words = [w for w in self.all_words if min_length <= len(w) <= max_length]
        return random.choice(valid_words)
    
    def get_possible_words(self, masked_word, guessed_letters):
        if not guessed_letters:
            pattern = ''.join([c if c != '_' else '.' for c in masked_word])
        else:
            pattern = ''.join([c if c != '_' else f"[^{''.join(guessed_letters)}]" for c in masked_word])

        regex = re.compile(f"^{pattern}$")
        length = len(masked_word)

        # Filter words from full word list, not just by length, since length may include spaces
        return [word for word in self.all_words if len(word) == length and regex.match(word)]

    def get_best_guess(self, masked_word, guessed_letters):
        length = len(masked_word)
    
        # If no letters guessed yet, use precomputed frequencies
        if not guessed_letters:
            return self.letter_frequencies[length][0][0] if self.letter_frequencies.get(length) else None
    
        possible_words = self.get_possible_words(masked_word, guessed_letters)
    
        if not possible_words:
            return None
    
        # Count letter frequencies in remaining possible words
        freq = defaultdict(int)
        for word in possible_words:
            for letter in set(word):  # Avoid double-counting repeated letters
                if letter not in guessed_letters:
                    freq[letter] += 1
    
        # Return letter with highest frequency
        return max(freq.items(), key=lambda x: x[1])[0] if freq else None
    
    def play(self, ai_mode=False, word=None):
        """Play a game of Hangman"""
        if ai_mode:
            word = input(Fore.YELLOW + "Enter a word for the AI to guess (letters and spaces only): ").strip().lower()
            while not all(char.isalpha() or char.isspace() for char in word):
                word = input(Fore.RED + "Please enter a valid word (letters and spaces only): ").strip().lower()
        else:
            if word is None:
                word = self.select_random_word()
            else:
                word = word.lower()
        
        masked_word = [" " if c == " " else "_" for c in word]
        word_parts = word.split()
        part_offsets = []
        offset = 0
        for part in word_parts:
            part_offsets.append((offset, offset + len(part)))
            offset += len(part) + 1  # account for space
        current_part_index = 0
        guessed_letters = set()
        incorrect_guesses = 0
        max_incorrect = 6
        game_over = False
        
        print(Fore.CYAN + "\n=== HANGMAN ===")
        print(Fore.YELLOW + f"Word has {len(word)} letters. Good luck!")
        
        while not game_over:
            # Display current game state
            self.display_game_state(masked_word, incorrect_guesses, guessed_letters)
            
            # Get player's guess (or AI's guess)
            if ai_mode:
                if current_part_index >= len(part_offsets):
                    print(Fore.RED + "AI has completed all parts.")
                    break

                start, end = part_offsets[current_part_index]
                partial_masked = "".join(masked_word[start:end])
                guess = self.get_best_guess(partial_masked, guessed_letters)

                if guess is None:
                    # Fallback: pick a random letter not guessed yet
                    unused_letters = [chr(i) for i in range(97, 123) if chr(i) not in guessed_letters]
                    if unused_letters:
                        guess = random.choice(unused_letters)
                    else:
                        print(Fore.RED + "AI has no letters left to guess. Ending game.")
                        break
                print(Fore.MAGENTA + "Input: ", end='', flush=True)
                for char in guess:
                    time.sleep(0.25)
                    print(char, end='', flush=True)
                # print()
                time.sleep(1)
            else:
                guess = input(Fore.GREEN + "\nGuess a letter: ").lower()
                while not guess.isalpha() or len(guess) != 1:
                    guess = input(Fore.RED + "Please enter a single letter: ").lower()
            
            # Check if letter was already guessed
            if guess in guessed_letters:
                print(Fore.YELLOW + "You already guessed that letter!")
                continue
                
            guessed_letters.add(guess)
            
            # Check if guess is correct
            if guess in word:
                for i, letter in enumerate(word):
                    if letter == guess:
                        masked_word[i] = guess
                print(Fore.GREEN + " -> Correct!")
                # Check if current word part is complete
                start, end = part_offsets[current_part_index]
                if "_" not in masked_word[start:end]:
                    current_part_index += 1
            else:
                incorrect_guesses += 1
                print(Fore.RED + f" -> Wrong! {max_incorrect - incorrect_guesses} incorrect guesses left.")
            
            # Check win/lose conditions
            if "_" not in masked_word:
                self.display_game_state(masked_word, incorrect_guesses, guessed_letters)
                print(Fore.GREEN + Style.BRIGHT + "\nCongratulations! You won!")
                print(Fore.GREEN + f"The word was: {word}")
                game_over = True
            elif incorrect_guesses >= max_incorrect:
                self.display_hangman(incorrect_guesses)
                print(Fore.RED + Style.BRIGHT + "\nGame Over! You lost.")
                print(Fore.RED + f"The word was: {word}")
                game_over = True
    
    def display_game_state(self, masked_word, incorrect_guesses, guessed_letters):
        """Show the current game status"""
        print("\n" + " ".join(masked_word))
        remaining = 6 - incorrect_guesses
        print(" " * 15 + Fore.RED + f"Guesses left: {remaining}\n")
        self.display_hangman(incorrect_guesses)
        print(Fore.BLUE + f"\nGuessed letters: {', '.join(sorted(guessed_letters))}")
    
    def display_hangman(self, incorrect_guesses):
        """ASCII art for hangman"""
        stages = [
            """
         +---+
         |   |
             |
             |
             |
             |
    =============""",
            """
         +---+
         |   |
         O   |  
             |
             |
             |
    =============""",
            """
         +---+
         |   |
         O   |
         |   |
             |
             |
    =============""",
            """
         +---+
         |   |
         O   |
        /|   |
             |
             |
    =============""",
            """
         +---+
         |   |
         O   |
        /|\\  |
             |
             |
    =============""",
            """
         +---+
         |   |
         O   |
        /|\\  |
        /    |
             |
    =============""",
            """
         +---+
         |   |
         O   |
        /|\\  |
        / \\  |
             |
    ============="""
        ]
        print(Fore.YELLOW + stages[min(incorrect_guesses, 6)])

def main():
    game = HangmanGame()
    
    print(Fore.CYAN + Style.BRIGHT + "Welcome to Hangman!")
    print("1. Play against the computer")
    print("2. Watch the AI play")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            game.play(ai_mode=False)
        elif choice == "2":
            game.play(ai_mode=True)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
