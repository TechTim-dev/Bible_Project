import requests
import random
import json
import os
import re
import time
import sys
from threading import Thread
from itertools import cycle

# --- Style & Color Constants ---
C_END = '\033[0m'
C_BOLD = '\033[1m'
C_RED = '\033[91m'
C_GREEN = '\033[92m'
C_YELLOW = '\033[93m'
C_BLUE = '\033[94m'
C_MAGENTA = '\033[95m'
C_CYAN = '\033[96m'

BOOKMARKS_FILE = "bookmarks.json"
TRANSLATIONS = ['kjv', 'esv', 'web', 'bbe']

# --- Hardcoded Popular Verses for Basic Search (Remaster Feature) ---
# In a real-world scenario, you'd fetch/store the entire Bible for robust search.
# This serves as a functional placeholder for the 'search' command.
POPULAR_VERSES_DATA = [
    {"reference": "John 3:16", "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."},
    {"reference": "Psalm 23:1", "text": "The Lord is my shepherd; I shall not want."},
    {"reference": "Romans 12:2", "text": "And be not conformed to this world: but be ye transformed by the renewing of your mind, that ye may prove what is that good, and acceptable, and perfect, will of God."},
    {"reference": "Philippians 4:13", "text": "I can do all things through Christ which strengtheneth me."},
    {"reference": "Proverbs 3:5", "text": "Trust in the Lord with all thine heart; and lean not unto thine own understanding."},
    {"reference": "Matthew 6:33", "text": "But seek ye first the kingdom of God, and his righteousness; and all these things shall be added unto you."},
    {"reference": "Jeremiah 29:11", "text": "For I know the thoughts that I think toward you, saith the Lord, thoughts of peace, and not of evil, to give you an expected end."},
    {"reference": "Isaiah 41:10", "text": "Fear thou not; for I am with thee: be not dismayed; for I am thy God: I will strengthen thee; yea, I will help thee; yea, I will uphold thee with the right hand of my righteousness."},
    {"reference": "Romans 8:28", "text": "And we know that all things work together for good to them that love God, to them who are the called according to his purpose."},
    {"reference": "Joshua 1:9", "text": "Have not I commanded thee? Be strong and of a good courage; be not afraid, neither be thou dismayed: for the Lord thy God is with thee whithersoever thou goest."},
    {"reference": "1 Corinthians 13:4-7", "text": "Charity suffereth long, and is kind; charity envieth not; charity vaunteth not itself, is not puffed up, Doth not behave itself unseemly, seeketh not her own, is not easily provoked, thinketh no evil; Rejoiceth not in iniquity, but rejoiceth in the truth; Beareth all things, believeth all things, hopeth all things, endureth all things."},
    {"reference": "Psalm 46:10", "text": "Be still, and know that I am God: I will be exalted among the heathen, I will be exalted in the earth."},
    {"reference": "John 14:6", "text": "Jesus saith unto him, I am the way, the truth, and the life: no man cometh unto the Father, but by me."},
    {"reference": "Galatians 5:22-23", "text": "But the fruit of the Spirit is love, joy, peace, longsuffering, gentleness, goodness, faith, Meekness, temperance: against such there is no law."},
]


# --- Helper Functions for UI ---
_spinner_running = False
def _spinner_task():
    """The task that runs in a separate thread to show a spinner."""
    spinner_chars = cycle(['/', '—', '\\', '|'])
    while _spinner_running:
        sys.stdout.write(f"\r{C_CYAN}⏳ Fetching verse... {next(spinner_chars)}{C_END}")
        sys.stdout.flush()
        time.sleep(0.1)
    # Clear the line more robustly using terminal width
    try:
        terminal_width = os.get_terminal_size().columns
        sys.stdout.write('\r' + ' ' * terminal_width + '\r') 
    except OSError: # Fallback if terminal size can't be determined
        sys.stdout.write('\r' + ' ' * 40 + '\r') # Clear a standard amount
    sys.stdout.flush()

def with_spinner(func):
    """A decorator to show a spinner while a function executes."""
    def wrapper(*args, **kwargs):
        global _spinner_running
        _spinner_running = True
        spinner_thread = Thread(target=_spinner_task)
        spinner_thread.start()
        
        result = func(*args, **kwargs)
        
        _spinner_running = False
        spinner_thread.join()
        return result
    return wrapper

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_boxed(title, content, color=C_MAGENTA):
    """Prints content inside a nicely formatted box."""
    lines = content.strip().split('\n')
    max_len = max(len(line) for line in lines) if lines else 0
    max_len = max(max_len, len(title))
    
    print(f"{color}╭{'─' * (max_len + 2)}╮{C_END}")
    print(f"{color}│ {C_BOLD}{title.center(max_len)}{C_END}{color} │{C_END}")
    print(f"{color}├{'─' * (max_len + 2)}┤{C_END}")
    for line in lines:
        print(f"{color}│ {line.ljust(max_len)} │{C_END}")
    print(f"{color}╰{'─' * (max_len + 2)}╯{C_END}")

# --- Core App Logic ---
@with_spinner
def get_verse(reference, version='kjv'):
    """Fetches a verse from the bible-api.com API."""
    url = f"https://bible-api.com/{reference}?translation={version}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return "error", "Verse not found or invalid reference."
        data = response.json()
        return data.get('text'), data.get('reference', reference)
    except requests.exceptions.RequestException:
        return "error", "Network error. Could not connect to the API."

def load_bookmarks():
    """Loads bookmarks from a JSON file."""
    if os.path.exists(BOOKMARKS_FILE):
        with open(BOOKMARKS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} # Return empty if file is corrupt
    return {}

def save_bookmarks(bookmarks):
    """Saves bookmarks to a JSON file."""
    with open(BOOKMARKS_FILE, 'w') as f:
        json.dump(bookmarks, f, indent=4)

def highlight_keywords(text, keywords):
    """Highlights a list of keywords in a string using ANSI escape codes."""
    if not keywords or not text:
        return text
    # Create a regex pattern to match any of the keywords, case-insensitively
    # Use word boundaries (\b) to match whole words and prevent partial matches
    pattern = re.compile(r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b', re.IGNORECASE)
    highlighted_text = pattern.sub(lambda m: f"{C_YELLOW}{C_BOLD}{m.group(0)}{C_END}", text)
    return highlighted_text

# --- Main Application ---
def main():
    """Main function to run the CLI app."""
    bookmarks = load_bookmarks()
    keywords_to_highlight = ['God', 'love', 'Jesus', 'Lord', 'faith', 'hope', 'spirit', 'Christ'] # Added Christ
    current_version = 'kjv'
    
    clear_screen()
    print(f"{C_BOLD}{C_MAGENTA}📖 Welcome to the Bible CLI App! 📖{C_END}")
    print("Type 'help' for commands, or 'exit' to close.\n")

    while True:
        prompt = f"\n{C_CYAN}({current_version.upper()})>{C_END} Enter command: "
        command = input(prompt).strip().lower()

        if command == 'exit':
            print(f"\n{C_GREEN}Goodbye and God bless! 🙏{C_END}")
            break

        elif command == 'help':
            clear_screen()
            help_title = "COMMANDS 🆘"
            help_text = """
  get [ref]      - Fetch a verse (e.g., get John 3:16)
  search [key]   - Search for a keyword in popular verses
  bookmark [ref] - Save a verse to your bookmarks
  show bookmarks   - List all your saved bookmarks
  daily            - Show a random daily verse
  version [ver]  - Switch Bible version (kjv, esv, etc.)
  clear            - Clear the terminal screen
  help             - Show this help menu
  exit             - Quit the application
"""
            print_boxed(help_title, help_text, C_BLUE)

        elif command.startswith('get '):
            ref = command[4:].strip()
            # NEW: Basic input validation for verse format
            if not ref:
                print(f"{C_RED}❌ Please provide a verse reference. E.g., 'get John 3:16'{C_END}")
                continue
            # Regex to check for common Bible verse formats (Book Chapter:Verse)
            # This is a basic check, the API will do the final validation.
            if not re.match(r"^[a-zA-Z\s]+\s+\d+(:\d+)?(-\d+)?$", ref):
                print(f"{C_RED}⚠️ Reference format seems off. Try 'Book Chapter:Verse' (e.g., John 3:16) or 'Book Chapter' (e.g., Psalm 23).{C_END}")
                # continue # Allow API to handle slightly malformed but valid references sometimes
            
            clear_screen() # NEW: Clear screen before displaying verse
            text, ref_out = get_verse(ref, current_version)

            if text != "error":
                highlighted_text = highlight_keywords(text, keywords_to_highlight)
                title = f"{ref_out} ({current_version.upper()}) 🙏"
                print_boxed(title, highlighted_text, C_GREEN)
            else:
                print(f"{C_RED}❌ Error: {ref_out}{C_END}")

        elif command.startswith('search '):
            keyword = command[7:].strip()
            if not keyword:
                print(f"{C_RED}❌ Please provide a keyword to search.{C_END}")
                continue

            clear_screen() # NEW: Clear screen for search results
            search_results = []
            search_pattern = re.compile(re.escape(keyword), re.IGNORECASE)

            for verse_data in POPULAR_VERSES_DATA:
                if search_pattern.search(verse_data['text']):
                    search_results.append(verse_data)
            
            if search_results:
                content = ""
                for i, result in enumerate(search_results):
                    highlighted_text = highlight_keywords(result['text'], [keyword]) # Highlight only the search keyword
                    content += f"{C_BOLD}{C_YELLOW}{result['reference']}:{C_END}\n{highlighted_text}\n"
                    if i < len(search_results) - 1:
                        content += "---" + "\n"
                print_boxed(f"SEARCH RESULTS for '{keyword}' 🔍", content, C_CYAN)
                print(f"\n{C_BLUE}Note: Search currently covers popular verses. Full Bible search needs more data!{C_END}")
            else:
                print(f"{C_YELLOW}🤔 No popular verses found containing '{keyword}'.{C_END}")


        elif command.startswith('bookmark '):
            ref = command[9:].strip()
            if not ref:
                print(f"{C_RED}❌ Please provide a verse to bookmark.{C_END}")
                continue

            text, ref_out = get_verse(ref, current_version)

            if text != "error":
                bookmarks[ref_out] = text
                save_bookmarks(bookmarks)
                print(f"{C_GREEN}✅ Bookmarked {ref_out}!{C_END}")
            else:
                print(f"{C_RED}❌ Error: {ref_out}{C_END}")

        elif command == 'show bookmarks':
            clear_screen()
            if bookmarks:
                content = ""
                for i, (ref, text) in enumerate(bookmarks.items()):
                    content += f"{C_BOLD}{C_YELLOW}{ref}:{C_END}\n{text}\n"
                    if i < len(bookmarks) - 1:
                        content += "---" + "\n"
                print_boxed("MY BOOKMARKS 📌", content, C_BLUE)
            else:
                print(f"{C_YELLOW}🤔 You have no bookmarks saved yet.{C_END}")

        elif command == 'daily':
            # Expanded daily_refs for more variety
            daily_refs = [
                "John 3:16", "Psalm 23:1", "Romans 12:2", "Philippians 4:13", "Proverbs 3:5",
                "Matthew 6:33", "Jeremiah 29:11", "Isaiah 41:10", "Romans 8:28", "Joshua 1:9",
                "1 Corinthians 13:4-7", "Psalm 46:10", "John 14:6", "Galatians 5:22-23",
                "Matthew 11:28", "Hebrews 11:1", "Psalm 119:105", "Ephesians 2:8-9",
                "2 Timothy 3:16", "1 John 4:7-8"
            ]
            ref = random.choice(daily_refs)
            
            clear_screen() # NEW: Clear screen before displaying verse
            text, ref_out = get_verse(ref, current_version)
            
            if text != "error":
                highlighted_text = highlight_keywords(text, keywords_to_highlight)
                title = f"Daily Verse: {ref_out} ({current_version.upper()}) ✨"
                print_boxed(title, highlighted_text, C_MAGENTA)
            else:
                print(f"{C_RED}❌ Error: {ref_out}{C_END}")
        
        elif command == 'clear':
            clear_screen()

        elif command.startswith('version '):
            ver = command[8:].strip().lower()
            if ver in TRANSLATIONS:
                current_version = ver
                print(f"{C_GREEN}✅ Switched to {ver.upper()}{C_END}")
            else:
                print(f"{C_RED}Unsupported version. Try: {', '.join(TRANSLATIONS)}{C_END}")

        else:
            print(f"{C_RED}🤨 Unknown command. Type 'help' to see the list.{C_END}")

if __name__ == "__main__":
    main()