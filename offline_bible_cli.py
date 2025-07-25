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

BOOKMARKS_FILE = "bookmarks_offline.json"  # Separate bookmarks file for this script
TRANSLATIONS = ['kjv']  # Only KJV for this offline script
BIBLE_DATA_DIR = "Bible-kjv-master"  # Path to local Bible JSON data

# Global variables
FULL_BIBLE_DATA = {}
SEARCHABLE_BIBLE_FLAT = []  # Flattened list for efficient searching

# Define a mapping for common book name variations and abbreviations
BOOK_NAME_MAP = {
    "genesis": "Genesis", "gen": "Genesis",
    "exodus": "Exodus", "ex": "Exodus",
    "leviticus": "Leviticus", "lev": "Leviticus",
    "numbers": "Numbers", "num": "Numbers",
    "deuteronomy": "Deuteronomy", "deut": "Deuteronomy",
    "joshua": "Joshua", "jos": "Joshua",
    "judges": "Judges", "jdg": "Judges",
    "ruth": "Ruth", "rth": "Ruth",
    "1 samuel": "1 Samuel", "1sa": "1 Samuel",
    "2 samuel": "2 Samuel", "2sa": "2 Samuel",
    "1 kings": "1 Kings", "1ki": "1 Kings",
    "2 kings": "2 Kings", "2ki": "2 Kings",
    "1 chronicles": "1 Chronicles", "1ch": "1 Chronicles",
    "2 chronicles": "2 Chronicles", "2ch": "2 Chronicles",
    "ezra": "Ezra",
    "nehemiah": "Nehemiah", "neh": "Nehemiah",
    "esther": "Esther", "est": "Esther",
    "job": "Job",
    "psalm": "Psalms", "ps": "Psalms", "psalms": "Psalms",
    "proverbs": "Proverbs", "prv": "Proverbs",
    "ecclesiastes": "Ecclesiastes", "ecc": "Ecclesiastes",
    "song of solomon": "Song of Solomon", "sol": "Song of Solomon", "sos": "Song of Solomon",
    "isaiah": "Isaiah", "isa": "Isaiah",
    "jeremiah": "Jeremiah", "jer": "Jeremiah",
    "lamentations": "Lamentations", "lam": "Lamentations",
    "ezekiel": "Ezekiel", "eze": "Ezekiel",
    "daniel": "Daniel", "dan": "Daniel",
    "hosea": "Hosea", "hos": "Hosea",
    "joel": "Joel",
    "amos": "Amos",
    "obadiah": "Obadiah", "ob": "Obadiah",
    "jonah": "Jonah",
    "micah": "Micah", "mic": "Micah",
    "nahum": "Nahum", "nah": "Nahum",
    "habakkuk": "Habakkuk", "hab": "Habakkuk",
    "zephaniah": "Zephaniah", "zep": "Zephaniah",
    "haggai": "Haggai", "hag": "Haggai",
    "zechariah": "Zechariah", "zec": "Zechariah",
    "malachi": "Malachi", "mal": "Malachi",
    "matthew": "Matthew", "mat": "Matthew",
    "mark": "Mark", "mrk": "Mark",
    "luke": "Luke", "luk": "Luke",
    "john": "John", "jhn": "John",
    "acts": "Acts", "act": "Acts",
    "romans": "Romans", "rom": "Romans",
    "1corinthians": "1Corinthians", "1co": "1Corinthians",
    "2corinthians": "2Corinthians", "2co": "2Corinthians",
    "galatians": "Galatians", "gal": "Galatians",
    "ephesians": "Ephesians", "eph": "Ephesians",
    "philippians": "Philippians", "php": "Philippians",
    "colossians": "Colossians", "col": "Colossians",
    "1 thessalonians": "1 Thessalonians", "1th": "1 Thessalonians",
    "2 thessalonians": "2 Thessalonians", "2th": "2 Thessalonians",
    "1 timothy": "1 Timothy", "1ti": "1 Timothy",
    "2 timothy": "2 Timothy", "2ti": "2 Timothy",
    "titus": "Titus", "tit": "Titus",
    "philemon": "Philemon", "phm": "Philemon",
    "hebrews": "Hebrews", "heb": "Hebrews",
    "james": "James", "jas": "James",
    "1 peter": "1 Peter", "1pe": "1 Peter",
    "2 peter": "2 Peter", "2pe": "2 Peter",
    "1 john": "1 John", "1jn": "1 John",
    "2 john": "2 John", "2jn": "2 John",
    "3 john": "3 John", "3jn": "3 John",
    "jude": "Jude",
    "revelation": "Revelation", "rev": "Revelation"
}

# --- Helper Functions for UI ---
_spinner_running = False

def _spinner_task(message="Loading..."):
    """The task that runs in a separate thread to show a spinner."""
    spinner_chars = cycle(['/', '—', '\\', '|'])
    while _spinner_running:
        sys.stdout.write(f"\r{C_CYAN}⏳ {message} {next(spinner_chars)}{C_END}")
        sys.stdout.flush()
        time.sleep(0.1)
    try:
        terminal_width = os.get_terminal_size().columns
        sys.stdout.write('\r' + ' ' * terminal_width + '\r')
    except OSError:
        sys.stdout.write('\r' + ' ' * 80 + '\r')  # Default to 80 columns
    sys.stdout.flush()

def with_spinner(message="Loading..."):
    """A decorator to show a spinner while a function executes."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            global _spinner_running
            _spinner_running = True
            spinner_thread = Thread(target=_spinner_task, args=(message,))
            spinner_thread.start()
            result = func(*args, **kwargs)
            _spinner_running = False
            spinner_thread.join()
            return result
        return wrapper
    return decorator

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

# --- Local Data Loading and Parsing ---
@with_spinner(message="Loading local KJV Bible data...")
def load_all_local_bible_data():
    """Loads all KJV Bible data from local JSON files into a global dictionary."""
    global FULL_BIBLE_DATA
    global SEARCHABLE_BIBLE_FLAT
    local_bible_data = {}
    searchable_flat_list = []
    books_list_path = os.path.join(BIBLE_DATA_DIR, "Books.json")

    if not os.path.exists(books_list_path):
        print(f"\n{C_RED}❌ Error: Books.json not found at '{os.path.abspath(books_list_path)}'. Ensure 'Bible-kjv-master' directory is present.{C_END}")
        return None

    try:
        with open(books_list_path, 'r', encoding='utf-8') as f:
            book_names_from_json = json.load(f)
        missing_files = []
        for book_name_full in book_names_from_json:
            book_file_path = os.path.join(BIBLE_DATA_DIR, f"{book_name_full}.json")
            if not os.path.exists(book_file_path):
                missing_files.append(book_name_full)
                print(f"{C_YELLOW}⚠️ Warning: Book file '{book_file_path}' not found. Skipping '{book_name_full}'.{C_END}")
                continue
            with open(book_file_path, 'r', encoding='utf-8') as f:
                try:
                    book_data = json.load(f)
                    if not isinstance(book_data, dict) or 'chapters' not in book_data or not isinstance(book_data['chapters'], list):
                        print(f"{C_RED}❌ Invalid JSON structure in '{book_file_path}'. Expected dict with 'chapters' key containing a list.{C_END}")
                        continue
                except json.JSONDecodeError as e:
                    print(f"{C_RED}❌ Malformed JSON in '{book_file_path}': {e}{C_END}")
                    continue
            local_bible_data[book_name_full] = book_data
            for chapter_data in book_data['chapters']:
                chapter_num = int(chapter_data['chapter'])
                for verse_data in chapter_data['verses']:
                    verse_num = int(verse_data['verse'])
                    reference = f"{book_name_full} {chapter_num}:{verse_num}"
                    searchable_flat_list.append({'reference': reference, 'text': verse_data['text']})
        if missing_files:
            print(f"{C_RED}❌ {len(missing_files)} book(s) missing: {', '.join(missing_files[:5])}{'...' if len(missing_files) > 5 else ''}. Functionality may be limited.{C_END}")
        FULL_BIBLE_DATA = local_bible_data
        SEARCHABLE_BIBLE_FLAT = searchable_flat_list
        return local_bible_data
    except Exception as e:
        print(f"\n{C_RED}❌ CRITICAL ERROR loading local Bible data from '{os.path.abspath(BIBLE_DATA_DIR)}': {type(e).__name__} - {e}. Exiting.{C_END}")
        return None

def _parse_reference(reference_string):
    """Parses a Bible reference string into components."""
    ref_clean = ' '.join(reference_string.strip().split())  # Remove extra spaces
    match = re.match(r"([a-z0-9\s]+?)\s*(\d+)(?::(\d+)(?:-(\d+))?)?$", ref_clean.lower())
    if not match:
        return None, None, None, None
    book_part, chapter_str, verse_start_str, verse_end_str = match.groups()
    book_name_standardized = BOOK_NAME_MAP.get(book_part.strip(), book_part.strip().title())
    try:
        chapter_num = int(chapter_str)
        verse_start = int(verse_start_str) if verse_start_str else 1
        verse_end = int(verse_end_str) if verse_end_str else verse_start
        if verse_start > verse_end:
            return None, None, None, None
    except ValueError:
        return None, None, None, None
    return book_name_standardized, chapter_num, verse_start, verse_end

def get_verse(reference):
    """Fetches a verse or range of verses from the locally loaded KJV Bible data."""
    book_name, chapter_num, verse_start, verse_end = _parse_reference(reference)
    if not all([book_name, chapter_num, verse_start]):
        return None, "Invalid reference format. Use 'Book Chapter:Verse' (e.g., John 3:16) or 'Book Chapter:Verse-Verse' (e.g., John 3:16-18)."
    if verse_start > verse_end:
        return None, f"Invalid verse range: {verse_start} is greater than {verse_end}."
    book_data = FULL_BIBLE_DATA.get(book_name)
    if not book_data:
        valid_books = ', '.join(list(FULL_BIBLE_DATA.keys())[:5]) + ('...' if len(FULL_BIBLE_DATA) > 5 else '')
        return None, f"Book '{book_name}' not found. Valid books include: {valid_books}. Type 'help' for more info."
    chapter_data = next((ch for ch in book_data['chapters'] if int(ch['chapter']) == chapter_num), None)
    if not chapter_data:
        return None, f"Chapter {chapter_num} not found in {book_name}. Max chapter is {len(book_data['chapters'])}."
    verses = chapter_data['verses']
    if not (1 <= verse_start <= len(verses)):
        return None, f"Verse {verse_start} not found in {book_name} {chapter_num}. Max verse is {len(verses)}."
    actual_verse_end = min(verse_end, len(verses))
    verse_texts = []
    for i in range(verse_start - 1, actual_verse_end):
        verse_data = verses[i]
        verse_num = int(verse_data['verse'])
        verse_texts.append(f"{verse_num} {verse_data['text']}")
    if verse_start == actual_verse_end:
        formatted_reference = f"{book_name} {chapter_num}:{verse_start}"
    else:
        formatted_reference = f"{book_name} {chapter_num}:{verse_start}-{actual_verse_end}"
    return "\n".join(verse_texts), formatted_reference

def load_bookmarks():
    """Loads bookmarks from a JSON file."""
    if os.path.exists(BOOKMARKS_FILE):
        try:
            with open(BOOKMARKS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"{C_RED}❌ Error: Corrupted bookmarks file. Starting with empty bookmarks.{C_END}")
            return {}
    return {}

def save_bookmarks(bookmarks):
    """Saves bookmarks to a JSON file."""
    try:
        with open(BOOKMARKS_FILE, 'w') as f:
            json.dump(bookmarks, f, indent=4)
    except IOError as e:
        print(f"{C_RED}❌ Error saving bookmarks: {e}{C_END}")

def highlight_keywords(text, keywords):
    """Highlights a list of keywords in a string using ANSI escape codes."""
    if not keywords or not text:
        return text
    pattern = re.compile(r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b', re.IGNORECASE)
    highlighted_text = pattern.sub(lambda m: f"{C_YELLOW}{C_BOLD}{m.group(0)}{C_END}", text)
    return highlighted_text

# --- Main Application ---
def main():
    """Main function to run the CLI app."""
    global FULL_BIBLE_DATA
    global SEARCHABLE_BIBLE_FLAT
    bookmarks = load_bookmarks()
    keywords_to_highlight = ['God', 'love', 'Jesus', 'Lord', 'faith', 'hope', 'spirit', 'Christ', 'grace', 'peace']
    current_version = 'kjv'
    FULL_BIBLE_DATA = load_all_local_bible_data()
    if not FULL_BIBLE_DATA:
        print(f"{C_RED}❌ CRITICAL: No Bible data loaded. Ensure 'Bible-kjv-master' contains valid JSON files. Exiting.{C_END}")
        sys.exit(1)
    clear_screen()
    print(f"{C_BOLD}{C_MAGENTA}📖 Welcome to the OFFLINE KJV Bible CLI App! 📖{C_END}")
    print(f"{C_YELLOW}🚀 Uses local KJV data only. No internet required!{C_END}")
    print(f"{C_GREEN}✅ Loaded {len(SEARCHABLE_BIBLE_FLAT)} verses. Ready to use!{C_END}")
    print("Type 'help' for commands, or 'exit' to close.\n")
    while True:
        prompt = f"\n{C_CYAN}({current_version.upper()})>{C_END} Enter command: "
        command = input(prompt).strip().lower()
        if command == 'exit':
            print(f"\n{C_GREEN}Goodbye and God bless! 🙏{C_END}")
            break
        elif command == 'help':
            clear_screen()
            help_title = "COMMANDS 🆘 (OFFLINE KJV ONLY)"
            help_text = """
            get [ref]      - Fetch a verse (e.g., get John 3:16)
            search [key]   - Search for a keyword in the KJV Bible
            bookmark [ref] - Save a verse to your bookmarks
            show bookmarks - List all saved bookmarks
            daily          - Show a random daily verse
            clear          - Clear the terminal screen
            help           - Show this help menu
            exit           - Quit the application
            """
            print_boxed(help_title, help_text, C_BLUE)
        elif command.startswith('get '):
            parts = command.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                print(f"{C_RED}❌ Please provide a verse reference. E.g., 'get John 3:16'{C_END}")
                continue
            ref = parts[1].strip()
            if not re.match(r"^[a-zA-Z0-9\s]+\s+\d+(:\d+(?:-\d+)?)?$", ref):
                print(f"{C_RED}⚠️ Invalid format. Use 'Book Chapter:Verse' (e.g., John 3:16) or 'Book Chapter:Verse-Verse' (e.g., John 3:16-18).{C_END}")
                continue
            clear_screen()
            text, ref_out = get_verse(ref)
            if text:
                highlighted_text = highlight_keywords(text, keywords_to_highlight)
                title = f"{ref_out} ({current_version.upper()}) 🙏"
                print_boxed(title, highlighted_text, C_GREEN)
            else:
                print(f"{C_RED}❌ Error: {ref_out}{C_END}")
        elif command.startswith('search '):
            parts = command.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                print(f"{C_RED}❌ Please provide a keyword to search. E.g., 'search love'{C_END}")
                continue
            keyword = parts[1].strip()
            clear_screen()
            search_results = []
            search_pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            for verse_data in SEARCHABLE_BIBLE_FLAT:
                if search_pattern.search(verse_data['text']):
                    search_results.append(verse_data)
            if search_results:
                content = ""
                display_limit = 20
                for i, result in enumerate(search_results):
                    if i >= display_limit:
                        content += f"\n... {len(search_results) - display_limit} more results not shown."
                        break
                    highlighted_text = highlight_keywords(result['text'], [keyword])
                    content += f"{C_BOLD}{C_YELLOW}{result['reference']}:{C_END}\n{highlighted_text}\n"
                    if i < display_limit - 1 and i < len(search_results) - 1:
                        content += "---" + "\n"
                print_boxed(f"SEARCH RESULTS for '{keyword}' ({len(search_results)} found) 🔍", content, C_CYAN)
                print(f"\n{C_BLUE}Note: Displaying up to {display_limit} results.{C_END}")
            else:
                print(f"{C_YELLOW}🤔 No results found for '{keyword}' in the KJV Bible.{C_END}")
        elif command.startswith('bookmark '):
            parts = command.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                print(f"{C_RED}❌ Please provide a verse to bookmark. E.g., 'bookmark John 3:16'{C_END}")
                continue
            ref = parts[1].strip()
            text, ref_out = get_verse(ref)
            if text:
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
                print_boxed("MY BOOKMARKS 📌 (OFFLINE)", content, C_BLUE)
            else:
                print(f"{C_YELLOW}🤔 You have no bookmarks saved yet.{C_END}")
        elif command == 'daily':
            random_verse_data = random.choice(SEARCHABLE_BIBLE_FLAT)
            ref = random_verse_data['reference']
            clear_screen()
            text, ref_out = get_verse(ref)
            if text:
                highlighted_text = highlight_keywords(text, keywords_to_highlight)
                title = f"Daily Verse (OFFLINE KJV): {ref_out} ✨"
                print_boxed(title, highlighted_text, C_MAGENTA)
            else:
                print(f"{C_RED}❌ Error fetching daily verse: {ref_out}{C_END}")
        elif command == 'clear':
            clear_screen()
        else:
            print(f"{C_RED}🤨 Unknown command. Type 'help' to see the list.{C_END}")

if __name__ == "__main__":
    main()