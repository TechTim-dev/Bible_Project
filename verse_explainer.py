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

# --- Placeholder Commentary Data ---
COMMENTARY_DATA = {
    {
  "Mark 1:1": "The beginning of the gospel of Jesus Christ, the Son of God, marks the start of Mark’s vivid account. It emphasizes Jesus as the divine Messiah, fulfilling Old Testament prophecies and launching the good news of salvation.",
  "Mark 1:2": "Quoting Malachi 3:1 and Isaiah 40:3, Mark shows John the Baptist as the promised messenger preparing the way for Jesus, calling people to repentance in the wilderness.",
  "Mark 1:3": "John’s voice in the wilderness echoes Isaiah’s prophecy, urging spiritual preparation for the Lord’s coming, a call to make straight paths through repentance.",
  "Mark 1:4": "John’s baptism of repentance signifies a public turning from sin, preparing hearts for Jesus’ ministry and the forgiveness offered through faith in Him.",
  "Mark 1:5": "The widespread response to John’s preaching shows the spiritual hunger of Judea and Jerusalem, as people confessed sins and sought renewal through baptism.",
  "Mark 8:31": "Jesus’ first prediction of His suffering, death, and resurrection reveals His role as the suffering Messiah, challenging the disciples’ expectations of a political savior.",
  "Mark 16:15": "The Great Commission commands believers to spread the gospel worldwide, reflecting Jesus’ universal mission to save all who believe.",
  "Mark 16:16": "Faith and baptism are linked to salvation, while unbelief leads to condemnation, emphasizing the urgency of responding to the gospel."
}
}

# --- Helper Functions ---
_spinner_running = False
def _spinner_task():
    """Show a spinner during API calls."""
    spinner_chars = cycle(['/', '—', '\\', '|'])
    while _spinner_running:
        sys.stdout.write(f"\r{C_CYAN}⏳ Fetching verse... {next(spinner_chars)}{C_END}")
        sys.stdout.flush()
        time.sleep(0.1)
    try:
        terminal_width = os.get_terminal_size().columns
        sys.stdout.write('\r' + ' ' * terminal_width + '\r')
    except OSError:
        sys.stdout.write('\r' + ' ' * 40 + '\r')
    sys.stdout.flush()

def with_spinner(func):
    """Decorator to show a spinner while a function executes."""
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
    """Prints content inside a formatted box."""
    lines = content.strip().split('\n')
    max_len = max(len(line) for line in lines) if lines else 0
    max_len = max(max_len, len(title))
    print(f"{color}╭{'─' * (max_len + 2)}╮{C_END}")
    print(f"{color}│ {C_BOLD}{title.center(max_len)}{C_END}{color} │{C_END}")
    print(f"{color}├{'─' * (max_len + 2)}┤{C_END}")
    for line in lines:
        print(f"{color}│ {line.ljust(max_len)} │{C_END}")
    print(f"{color}╰{'─' * (max_len + 2)}╯{C_END}")

def highlight_keywords(text, keywords):
    """Highlights keywords in a string using ANSI escape codes."""
    if not keywords or not text:
        return text
    pattern = re.compile(r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b', re.IGNORECASE)
    highlighted_text = pattern.sub(lambda m: f"{C_YELLOW}{C_BOLD}{m.group(0)}{C_END}", text)
    return highlighted_text

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

def get_commentary(reference):
    """Fetches commentary for a verse or suggests an alternative."""
    commentary = COMMENTARY_DATA.get(reference)
    if commentary:
        return commentary
    else:
        available_verses = list(COMMENTARY_DATA.keys())
        if available_verses:
            suggested_ref = random.choice(available_verses)
            return f"No commentary for {reference}, but {suggested_ref} has one. Try it!"
        return f"No commentary available for {reference}."

# --- Main Application ---
def main():
    """Main function to run the CLI verse explainer."""
    keywords_to_highlight = ['God', 'love', 'Jesus', 'Lord', 'faith', 'hope', 'spirit', 'Christ', 'grace', 'peace']
    current_version = 'kjv'
    
    clear_screen()
    print(f"{C_BOLD}{C_MAGENTA}📖 Mugabi Life Ministries Verse Explainer! 📖{C_END}")
    print("Type 'help' for commands, or 'exit' to close.\n")

    while True:
        prompt = f"\n{C_CYAN}({current_version.upper()})>{C_END} Enter command: "
        command = input(prompt).strip().lower()

        if command == 'exit':
            print(f"\n{C_GREEN}God bless, bro! Keep studying! 🙏{C_END}")
            break

        elif command == 'help':
            clear_screen()
            help_title = "COMMANDS 🆘"
            help_text = """
  explain [ref]  - Fetch a verse and its commentary (e.g., explain John 3:16)
  search [key]   - Search for a keyword in verses and show commentary
  daily          - Show a random verse with commentary
  clear          - Clear the terminal screen
  help           - Show this help menu
  exit           - Quit the application
"""
            print_boxed(help_title, help_text, C_BLUE)

        elif command.startswith('explain '):
            ref = command[8:].strip()
            if not ref:
                print(f"{C_RED}❌ Please provide a verse reference (e.g., explain John 3:16){C_END}")
                continue
            if not re.match(r"^[a-zA-Z\s]+\s+\d+(:\d+)?(-\d+)?$", ref):
                print(f"{C_RED}⚠️ Reference format seems off. Try 'Book Chapter:Verse' (e.g., John 3:16){C_END}")

            clear_screen()
            text, ref_out = get_verse(ref, current_version)
            commentary = get_commentary(ref_out)

            if text != "error":
                highlighted_text = highlight_keywords(text, keywords_to_highlight)
                content = f"{highlighted_text}\n\n{C_BOLD}Commentary:{C_END}\n{commentary}"
                title = f"{ref_out} ({current_version.upper()}) 🙏"
                print_boxed(title, content, C_GREEN)
            else:
                print(f"{C_RED}❌ Error: {ref_out}{C_END}")

        elif command.startswith('search '):
            keyword = command[7:].strip()
            if not keyword:
                print(f"{C_RED}❌ Please provide a keyword to search.{C_END}")
                continue

            clear_screen()
            search_results = []
            search_pattern = re.compile(re.escape(keyword), re.IGNORECASE)

            for verse_data in COMMENTARY_DATA.items():
                ref, comm = verse_data
                text, ref_out = get_verse(ref, current_version)
                if text != "error" and search_pattern.search(text):
                    search_results.append({"reference": ref_out, "text": text, "commentary": comm})

            if search_results:
                content = ""
                for i, result in enumerate(search_results[:10]):
                    highlighted_text = highlight_keywords(result['text'], [keyword])
                    content += f"{C_BOLD}{C_YELLOW}{result['reference']}:{C_END}\n{highlighted_text}\n{C_BOLD}Commentary:{C_END}\n{result['commentary']}\n"
                    if i < len(search_results) - 1:
                        content += "---\n"
                print_boxed(f"SEARCH RESULTS for '{keyword}' 🔍", content, C_CYAN)
                print(f"\n{C_BLUE}Note: Search covers verses with commentary. More data needed for full Bible search!{C_END}")
            else:
                print(f"{C_YELLOW}🤔 No verses with commentary found for '{keyword}'.{C_END}")

        elif command == 'daily':
            available_refs = list(COMMENTARY_DATA.keys())
            ref = random.choice(available_refs)
            
            clear_screen()
            text, ref_out = get_verse(ref, current_version)
            commentary = get_commentary(ref_out)
            
            if text != "error":
                highlighted_text = highlight_keywords(text, keywords_to_highlight)
                content = f"{highlighted_text}\n\n{C_BOLD}Commentary:{C_END}\n{commentary}"
                title = f"Daily Verse: {ref_out} ({current_version.upper()}) ✨"
                print_boxed(title, content, C_MAGENTA)
            else:
                print(f"{C_RED}❌ Error: {ref_out}{C_END}")

        elif command == 'clear':
            clear_screen()

        else:
            print(f"{C_RED}🤨 Unknown command. Type 'help' to see the list.{C_END}")

if __name__ == "__main__":
    main()