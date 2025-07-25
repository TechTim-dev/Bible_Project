import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
import re
import random

# --- Constants and Global Variables ---
BOOKMARKS_FILE = "bookmarks_offline.json"
BIBLE_DATA_DIR = "Bible-kjv-master"
FULL_BIBLE_DATA = {}
SEARCHABLE_BIBLE_FLAT = []
VERSION = "KJV"

# Book name mappings (same as CLI)
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

# --- Data Loading ---
def load_all_local_bible_data(root, status_label):
    global FULL_BIBLE_DATA, SEARCHABLE_BIBLE_FLAT
    local_bible_data = {}
    searchable_flat_list = []
    books_list_path = os.path.join(BIBLE_DATA_DIR, "Books.json")

    status_label.configure(text="Loading Bible data...", text_color="blue")
    root.update()

    if not os.path.exists(books_list_path):
        status_label.configure(text=f"Error: Books.json not found at '{books_list_path}'.", text_color="red")
        return False

    try:
        with open(books_list_path, 'r', encoding='utf-8') as f:
            book_names_from_json = json.load(f)
        missing_files = []
        for book_name_full in book_names_from_json:
            book_file_path = os.path.join(BIBLE_DATA_DIR, f"{book_name_full}.json")
            if not os.path.exists(book_file_path):
                missing_files.append(book_name_full)
                continue
            with open(book_file_path, 'r', encoding='utf-8') as f:
                try:
                    book_data = json.load(f)
                    if not isinstance(book_data, dict) or 'chapters' not in book_data:
                        continue
                except json.JSONDecodeError:
                    continue
            local_bible_data[book_name_full] = book_data
            for chapter_data in book_data['chapters']:
                chapter_num = int(chapter_data['chapter'])
                for verse_data in chapter_data['verses']:
                    verse_num = int(verse_data['verse'])
                    reference = f"{book_name_full} {chapter_num}:{verse_num}"
                    searchable_flat_list.append({'reference': reference, 'text': verse_data['text']})
        FULL_BIBLE_DATA = local_bible_data
        SEARCHABLE_BIBLE_FLAT = searchable_flat_list
        if missing_files:
            status_label.configure(text=f"Warning: {len(missing_files)} book(s) missing.", text_color="orange")
        else:
            status_label.configure(text=f"Loaded {len(searchable_flat_list)} verses!", text_color="green")
        return True
    except Exception as e:
        status_label.configure(text=f"Error loading data: {str(e)}", text_color="red")
        return False

def _parse_reference(reference_string):
    ref_clean = ' '.join(reference_string.strip().split())
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
    book_name, chapter_num, verse_start, verse_end = _parse_reference(reference)
    if not all([book_name, chapter_num, verse_start]):
        return None, "Invalid reference format. Use 'Book Chapter:Verse' (e.g., John 3:16)."
    if verse_start > verse_end:
        return None, f"Invalid verse range: {verse_start} > {verse_end}."
    book_data = FULL_BIBLE_DATA.get(book_name)
    if not book_data:
        return None, f"Book '{book_name}' not found."
    chapter_data = next((ch for ch in book_data['chapters'] if int(ch['chapter']) == chapter_num), None)
    if not chapter_data:
        return None, f"Chapter {chapter_num} not found in {book_name}."
    verses = chapter_data['verses']
    if not (1 <= verse_start <= len(verses)):
        return None, f"Verse {verse_start} not found in {book_name} {chapter_num}."
    actual_verse_end = min(verse_end, len(verses))
    verse_texts = []
    for i in range(verse_start - 1, actual_verse_end):
        verse_data = verses[i]
        verse_num = int(verse_data['verse'])
        verse_texts.append(f"{verse_num}. {verse_data['text']}")
    if verse_start == actual_verse_end:
        formatted_reference = f"{book_name} {chapter_num}:{verse_start}"
    else:
        formatted_reference = f"{book_name} {chapter_num}:{verse_start}-{actual_verse_end}"
    return "\n".join(verse_texts), formatted_reference

def load_bookmarks():
    if os.path.exists(BOOKMARKS_FILE):
        try:
            with open(BOOKMARKS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_bookmarks(bookmarks):
    try:
        with open(BOOKMARKS_FILE, 'w') as f:
            json.dump(bookmarks, f, indent=4)
    except IOError as e:
        messagebox.showerror("Error", f"Failed to save bookmarks: {e}")

# --- GUI Application ---
class BibleApp:
    def __init__(self, root):
        self.root = root
        ctk.set_appearance_mode("System")  # Follow system light/dark mode
        ctk.set_default_color_theme("blue")  # Modern blue theme
        self.root.title("Offline KJV Bible App")
        self.root.geometry("900x700")
        self.bookmarks = load_bookmarks()

        # Main container
        self.main_frame = ctk.CTkFrame(root, corner_radius=10)
        self.main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Status label
        self.status_label = ctk.CTkLabel(self.main_frame, text="Initializing...", font=("Roboto", 12))
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

        # Load Bible data
        if not load_all_local_bible_data(root, self.status_label):
            messagebox.showerror("Error", "Failed to load Bible data. Ensure 'Bible-kjv-master' folder is present.")
            root.destroy()
            return

        # Theme toggle
        self.theme_button = ctk.CTkButton(self.main_frame, text="🌙 Dark Mode", command=self.toggle_theme, corner_radius=10)
        self.theme_button.pack(side="top", anchor="ne", padx=10, pady=5)

        # Notebook (tabs)
        self.notebook = ctk.CTkTabview(self.main_frame, corner_radius=10)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Initialize tabs
        self.setup_lookup_tab()
        self.setup_search_tab()
        self.setup_bookmarks_tab()
        self.setup_daily_tab()

    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Dark" if current_mode == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        self.theme_button.configure(text="☀️ Light Mode" if new_mode == "Dark" else "🌙 Dark Mode")
        # Update listbox colors
        bg_color = "#f0f0f0" if new_mode == "Light" else "#333333"
        fg_color = "black" if new_mode == "Light" else "white"
        self.search_results.configure(bg=bg_color, fg=fg_color)
        self.bookmarks_list.configure(bg=bg_color, fg=fg_color)

    def setup_lookup_tab(self):
        self.lookup_tab = self.notebook.add("Lookup 📖")
        
        # Input frame
        input_frame = ctk.CTkFrame(self.lookup_tab, corner_radius=10)
        input_frame.pack(fill="x", padx=10, pady=10)

        # Book selection
        ctk.CTkLabel(input_frame, text="Book:", font=("Roboto", 14)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.book_combo = ctk.CTkComboBox(input_frame, values=sorted(FULL_BIBLE_DATA.keys()), font=("Roboto", 12), width=200)
        self.book_combo.grid(row=0, column=1, padx=5, pady=5)
        self.book_combo.bind("<<ComboboxSelected>>", self.update_chapters)

        # Chapter selection
        ctk.CTkLabel(input_frame, text="Chapter:", font=("Roboto", 14)).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.chapter_combo = ctk.CTkComboBox(input_frame, values=[], font=("Roboto", 12), width=100)
        self.chapter_combo.grid(row=0, column=3, padx=5, pady=5)
        self.chapter_combo.bind("<<ComboboxSelected>>", self.update_verses)

        # Verse selection
        ctk.CTkLabel(input_frame, text="Verse:", font=("Roboto", 14)).grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.verse_combo = ctk.CTkComboBox(input_frame, values=[], font=("Roboto", 12), width=100)
        self.verse_combo.grid(row=0, column=5, padx=5, pady=5)

        # Buttons
        ctk.CTkButton(input_frame, text="Go", command=self.lookup_verse, corner_radius=10, font=("Roboto", 12)).grid(row=0, column=6, padx=5, pady=5)
        ctk.CTkButton(input_frame, text="Bookmark", command=self.bookmark_verse, corner_radius=10, font=("Roboto", 12)).grid(row=0, column=7, padx=5, pady=5)

        # Text display
        self.lookup_text = ctk.CTkTextbox(self.lookup_tab, wrap="word", font=("Courier New", 14), height=400, corner_radius=10)
        self.lookup_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.lookup_text.configure(state="disabled")

    def update_chapters(self, event=None):
        book = self.book_combo.get()
        if book:
            chapters = len(FULL_BIBLE_DATA[book]['chapters'])
            self.chapter_combo.configure(values=list(range(1, chapters + 1)))
            self.chapter_combo.set("")
            self.verse_combo.set("")
            self.verse_combo.configure(values=[])

    def update_verses(self, event=None):
        book = self.book_combo.get()
        chapter = self.chapter_combo.get()
        if book and chapter:
            chapter_data = next((ch for ch in FULL_BIBLE_DATA[book]['chapters'] if int(ch['chapter']) == int(chapter)), None)
            if chapter_data:
                verses = len(chapter_data['verses'])
                self.verse_combo.configure(values=list(range(1, verses + 1)))
                self.verse_combo.set("")
            else:
                self.verse_combo.configure(values=[])
                self.verse_combo.set("")

    def lookup_verse(self):
        book = self.book_combo.get()
        chapter = self.chapter_combo.get()
        verse = self.verse_combo.get()
        if not all([book, chapter, verse]):
            messagebox.showerror("Error", "Please select book, chapter, and verse.")
            return
        reference = f"{book} {chapter}:{verse}"
        text, ref_out = get_verse(reference)
        self.lookup_text.configure(state="normal")
        self.lookup_text.delete("1.0", "end")
        if text:
            highlighted_text = self.highlight_keywords(text.split("\n"), ['God', 'love', 'Jesus', 'Lord', 'faith', 'hope', 'spirit', 'Christ', 'grace', 'peace'])
            self.lookup_text.insert("end", f"{ref_out} ({VERSION})\n\n")
            for line in highlighted_text:
                self.lookup_text.insert("end", f"{line}\n")
            self.status_label.configure(text=f"Displayed {ref_out}", text_color="green")
        else:
            self.lookup_text.insert("end", f"Error: {ref_out}")
            self.status_label.configure(text=f"Error: {ref_out}", text_color="red")
        self.lookup_text.configure(state="disabled")

    def bookmark_verse(self):
        book = self.book_combo.get()
        chapter = self.chapter_combo.get()
        verse = self.verse_combo.get()
        if not all([book, chapter, verse]):
            messagebox.showerror("Error", "Please select book, chapter, and verse to bookmark.")
            return
        reference = f"{book} {chapter}:{verse}"
        text, ref_out = get_verse(reference)
        if text:
            self.bookmarks[ref_out] = text
            save_bookmarks(self.bookmarks)
            self.update_bookmarks_tab()
            messagebox.showinfo("Success", f"Bookmarked {ref_out}!")
        else:
            messagebox.showerror("Error", f"Cannot bookmark: {ref_out}")

    def setup_search_tab(self):
        self.search_tab = self.notebook.add("Search 🔍")
        
        # Search input
        input_frame = ctk.CTkFrame(self.search_tab, corner_radius=10)
        input_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(input_frame, text="Keyword:", font=("Roboto", 14)).pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(input_frame, width=400, font=("Roboto", 12))
        self.search_entry.pack(side="left", padx=5)
        ctk.CTkButton(input_frame, text="Search", command=self.perform_search, corner_radius=10, font=("Roboto", 12)).pack(side="left", padx=5)

        # Search results
        self.search_results = tk.Listbox(self.search_tab, height=20, font=("Roboto", 12), bg="#f0f0f0" if ctk.get_appearance_mode() == "Light" else "#333333", fg="black" if ctk.get_appearance_mode() == "Light" else "white")
        self.search_results.pack(fill="both", expand=True, padx=10, pady=10)
        self.search_results.bind("<<ListboxSelect>>", self.show_search_result)

    def perform_search(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showerror("Error", "Please enter a keyword to search.")
            return
        self.search_results.delete(0, "end")
        search_pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        results = []
        for verse_data in SEARCHABLE_BIBLE_FLAT:
            if search_pattern.search(verse_data['text']):
                results.append(verse_data)
        if results:
            for i, result in enumerate(results[:20]):
                self.search_results.insert("end", result['reference'])
            self.status_label.configure(text=f"Found {len(results)} results for '{keyword}'", text_color="green")
        else:
            self.search_results.insert("end", "No results found.")
            self.status_label.configure(text=f"No results for '{keyword}'", text_color="orange")

    def show_search_result(self, event):
        selection = self.search_results.curselection()
        if not selection:
            return
        ref = self.search_results.get(selection[0])
        if ref == "No results found.":
            return
        text, ref_out = get_verse(ref)
        if text:
            highlighted_text = self.highlight_keywords(text.split('\n'), [self.search_entry.get().strip()])
            dialog = ctk.CTkToplevel(self.root)
            dialog.title(ref_out)
            dialog.geometry("600x400")
            text_area = ctk.CTkTextbox(dialog, wrap="word", font=("Courier New", 14), height=300, corner_radius=10)
            text_area.pack(padx=10, pady=10, fill="both", expand=True)
            text_area.insert("end", f"{ref_out} ({VERSION})\n\n")
            for line in highlighted_text:
                text_area.insert("end", f"{line}\n")
            text_area.configure(state="disabled")
            ctk.CTkButton(dialog, text="Bookmark", command=lambda: self.bookmark_from_search(ref_out, text), corner_radius=10, font=("Roboto", 12)).pack(pady=10)

    def bookmark_from_search(self, ref, text):
        self.bookmarks[ref] = text
        save_bookmarks(self.bookmarks)
        self.update_bookmarks_tab()
        messagebox.showinfo("Success", f"Bookmarked {ref}!")

    def setup_bookmarks_tab(self):
        self.bookmarks_tab = self.notebook.add("Bookmarks 📌")
        self.bookmarks_list = tk.Listbox(self.bookmarks_tab, height=20, font=("Roboto", 12), bg="#f0f0f0" if ctk.get_appearance_mode() == "Light" else "#333333", fg="black" if ctk.get_appearance_mode() == "Light" else "white")
        self.bookmarks_list.pack(fill="both", expand=True, padx=10, pady=10)
        self.bookmarks_list.bind("<<ListboxSelect>>", self.show_bookmark)
        ctk.CTkButton(self.bookmarks_tab, text="Delete Selected", command=self.delete_bookmark, corner_radius=10, font=("Roboto", 12)).pack(pady=10)
        self.update_bookmarks_tab()

    def update_bookmarks_tab(self):
        self.bookmarks_list.delete(0, "end")
        if self.bookmarks:
            for ref in self.bookmarks:
                self.bookmarks_list.insert("end", ref)
        else:
            self.bookmarks_list.insert("end", "No bookmarks saved.")

    def show_bookmark(self, event):
        selection = self.bookmarks_list.curselection()
        if not selection:
            return
        ref = self.bookmarks_list.get(selection[0])
        if ref == "No bookmarks saved.":
            return
        text = self.bookmarks[ref]
        highlighted_text = self.highlight_keywords(text.split('\n'), ['God', 'love', 'Jesus', 'Lord', 'faith', 'hope', 'spirit', 'Christ', 'grace', 'peace'])
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(ref)
        dialog.geometry("600x400")
        text_area = ctk.CTkTextbox(dialog, wrap="word", font=("Courier New", 14), height=300, corner_radius=10)
        text_area.pack(padx=10, pady=10, fill="both", expand=True)
        text_area.insert("end", f"{ref} ({VERSION})\n\n")
        for line in highlighted_text:
            text_area.insert("end", f"{line}\n")
        text_area.configure(state="disabled")

    def delete_bookmark(self):
        selection = self.bookmarks_list.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a bookmark to delete.")
            return
        ref = self.bookmarks_list.get(selection[0])
        if ref == "No bookmarks saved.":
            return
        if ref in self.bookmarks:
            del self.bookmarks[ref]
            save_bookmarks(self.bookmarks)
            self.update_bookmarks_tab()
            messagebox.showinfo("Success", f"Deleted bookmark {ref}.")

    def setup_daily_tab(self):
        self.daily_tab = self.notebook.add("Daily Verse ✨")
        ctk.CTkButton(self.daily_tab, text="Show Daily Verse", command=self.show_daily_verse, corner_radius=10, font=("Roboto", 14), width=200).pack(pady=20)
        self.daily_text = ctk.CTkTextbox(self.daily_tab, wrap="word", font=("Courier New", 14), height=400, corner_radius=10)
        self.daily_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.daily_text.configure(state="disabled")

    def show_daily_verse(self):
        random_verse_data = random.choice(SEARCHABLE_BIBLE_FLAT)
        ref = random_verse_data['reference']
        text, ref_out = get_verse(ref)
        if text:
            self.daily_text.configure(state="normal")
            self.daily_text.delete("1.0", "end")
            highlighted_text = self.highlight_keywords(text.split('\n'), ['God', 'love', 'Jesus', 'Lord', 'faith', 'hope', 'spirit', 'Christ', 'grace', 'peace'])
            self.daily_text.insert("end", f"{ref_out} ({VERSION})\n\n")
            for line in highlighted_text:
                self.daily_text.insert("end", f"{line}\n")
            self.daily_text.configure(state="disabled")
            self.status_label.configure(text=f"Daily verse: {ref_out}", text_color="green")
            # Replace any existing Bookmark button
            for widget in self.daily_tab.winfo_children():
                if isinstance(widget, ctk.CTkButton) and widget.cget("text") == "Bookmark":
                    widget.destroy()
            ctk.CTkButton(self.daily_tab, text="Bookmark", command=lambda: self.bookmark_from_search(ref_out, text), corner_radius=10, font=("Roboto", 12)).pack(pady=10)
        else:
            self.daily_text.configure(state="normal")
            self.daily_text.delete("1.0", "end")
            self.daily_text.insert("end", f"Error: {ref_out}")
            self.daily_text.configure(state="disabled")
            self.status_label.configure(text=f"Error: {ref_out}", text_color="red")

    def highlight_keywords(self, lines, keywords):
        if not keywords or not lines:
            return lines
        pattern = re.compile(r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b', re.IGNORECASE)
        highlighted_lines = []
        for line in lines:
            highlighted_line = pattern.sub(lambda m: f"**{m.group(0)}**", line)
            highlighted_lines.append(highlighted_line)
        return highlighted_lines

if __name__ == "__main__":
    root = ctk.CTk()
    app = BibleApp(root)
    root.mainloop()