import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import requests
import json
import os
import re
import random
import asyncio
import aiohttp
from threading import Thread

# --- Constants from app.py ---
BOOKMARKS_FILE = "bookmarks.json"
TRANSLATIONS = ['kjv', 'esv', 'web', 'bbe']
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

# --- Helper Functions ---
async def get_verse_async(reference, version='kjv'):
    """Fetches a verse from bible-api.com asynchronously."""
    url = f"https://bible-api.com/{reference}?translation={version}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return "error", "Verse not found or invalid reference."
                data = await response.json()
                return data.get('text'), data.get('reference', reference)
    except aiohttp.ClientError:
        return "error", "Network error. Could not connect to the API."

def load_bookmarks():
    """Loads bookmarks from a JSON file."""
    if os.path.exists(BOOKMARKS_FILE):
        try:
            with open(BOOKMARKS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_bookmarks(bookmarks):
    """Saves bookmarks to a JSON file."""
    try:
        with open(BOOKMARKS_FILE, 'w') as f:
            json.dump(bookmarks, f, indent=4)
    except IOError as e:
        messagebox.showerror("Error", f"Failed to save bookmarks: {e}")

def highlight_keywords(text, keywords):
    """Highlights keywords by wrapping them in ** for visual emphasis."""
    if not keywords or not text:
        return text
    pattern = re.compile(r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b', re.IGNORECASE)
    highlighted_text = pattern.sub(lambda m: f"**{m.group(0)}**", text)
    return highlighted_text

# --- GUI Application ---
class BibleApp:
    def __init__(self, root):
        self.root = root
        ctk.set_appearance_mode("System")  # Follow system light/dark mode
        ctk.set_default_color_theme("blue")  # Base theme
        self.root.title("Mugabi Life Ministries Bible App")
        self.root.geometry("900x700")
        self.bookmarks = load_bookmarks()
        self.current_version = 'kjv'
        self.keywords_to_highlight = ['God', 'love', 'Jesus', 'Lord', 'faith', 'hope', 'spirit', 'Christ', 'grace', 'peace']

        # Main container
        self.main_frame = ctk.CTkFrame(root, corner_radius=10, fg_color="#F0F4F8" if ctk.get_appearance_mode() == "Light" else "#2B2D42")
        self.main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Header
        ctk.CTkLabel(self.main_frame, text="📖 Mugabi Life Ministries Bible App", font=("Roboto", 24, "bold"), text_color="#4A90E2").pack(pady=10)

        # Status label
        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready to explore the Word!", font=("Roboto", 12), text_color="#50C878")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

        # Theme and version controls
        controls_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="transparent")
        controls_frame.pack(fill="x", padx=10, pady=5)
        self.theme_button = ctk.CTkButton(controls_frame, text="🌙 Dark Mode", command=self.toggle_theme, corner_radius=10, fg_color="#F7DC6F", text_color="#2B2D42")
        self.theme_button.pack(side="right", padx=5)
        ctk.CTkLabel(controls_frame, text="Version:", font=("Roboto", 14)).pack(side="left", padx=5)
        self.version_combo = ctk.CTkComboBox(controls_frame, values=TRANSLATIONS, font=("Roboto", 12), width=100, command=self.switch_version)
        self.version_combo.set(self.current_version.upper())
        self.version_combo.pack(side="left", padx=5)

        # Notebook (tabs)
        self.notebook = ctk.CTkTabview(self.main_frame, corner_radius=10, fg_color="#FFFFFF" if ctk.get_appearance_mode() == "Light" else "#3A3F5C")
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
        bg_color = "#F0F4F8" if new_mode == "Light" else "#2B2D42"
        text_color = "#2B2D42" if new_mode == "Light" else "#FFFFFF"
        self.main_frame.configure(fg_color=bg_color)
        self.search_results.configure(bg=bg_color, fg=text_color)
        self.bookmarks_list.configure(bg=bg_color, fg=text_color)

    def switch_version(self, choice):
        self.current_version = choice.lower()
        self.status_label.configure(text=f"Switched to {self.current_version.upper()}", text_color="#50C878")

    def setup_lookup_tab(self):
        self.lookup_tab = self.notebook.add("Lookup 📖")
        
        # Input frame
        input_frame = ctk.CTkFrame(self.lookup_tab, corner_radius=10, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=10)
        
        # Freeform reference entry
        ctk.CTkLabel(input_frame, text="Reference (e.g., John 3:16):", font=("Roboto", 14), text_color="#4A90E2").pack(side="left", padx=5)
        self.reference_entry = ctk.CTkEntry(input_frame, width=300, font=("Roboto", 12), placeholder_text="Enter verse reference")
        self.reference_entry.pack(side="left", padx=5)
        
        # Buttons
        ctk.CTkButton(input_frame, text="Go", command=self.lookup_verse, corner_radius=10, font=("Roboto", 12), fg_color="#50C878", text_color="#FFFFFF").pack(side="left", padx=5)
        ctk.CTkButton(input_frame, text="Bookmark", command=self.bookmark_verse, corner_radius=10, font=("Roboto", 12), fg_color="#F7DC6F", text_color="#2B2D42").pack(side="left", padx=5)

        # Text display
        self.lookup_text = ctk.CTkTextbox(self.lookup_tab, wrap="word", font=("Courier New", 14), height=400, corner_radius=10)
        self.lookup_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.lookup_text.configure(state="disabled")

    async def fetch_verse(self, reference, version):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: asyncio.run(get_verse_async(reference, version)))

    def lookup_verse(self):
        ref = self.reference_entry.get().strip()
        if not ref:
            messagebox.showerror("Error", "Please enter a verse reference (e.g., John 3:16).")
            return
        if not re.match(r"^[a-zA-Z\s]+\s+\d+(:\d+)?(-\d+)?$", ref):
            messagebox.showwarning("Warning", "Reference format seems off. Try 'Book Chapter:Verse' (e.g., John 3:16).")
        
        self.status_label.configure(text="Fetching verse...", text_color="#4A90E2")
        self.root.config(cursor="wait")
        self.root.update()

        # Run async fetch in a thread to avoid blocking GUI
        def fetch_and_display():
            text, ref_out = asyncio.run(get_verse_async(ref, self.current_version))
            self.root.after(0, lambda: self.display_verse(text, ref_out))

        Thread(target=fetch_and_display).start()

    def display_verse(self, text, ref_out):
        self.lookup_text.configure(state="normal")
        self.lookup_text.delete("1.0", "end")
        if text != "error":
            highlighted_text = highlight_keywords(text, self.keywords_to_highlight)
            self.lookup_text.insert("end", f"{ref_out} ({self.current_version.upper()})\n\n{highlighted_text}")
            self.status_label.configure(text=f"Displayed {ref_out}", text_color="#50C878")
        else:
            self.lookup_text.insert("end", f"Error: {ref_out}")
            self.status_label.configure(text=f"Error: {ref_out}", text_color="#FF6B6B")
        self.lookup_text.configure(state="disabled")
        self.root.config(cursor="")

    def bookmark_verse(self):
        ref = self.reference_entry.get().strip()
        if not ref:
            messagebox.showerror("Error", "Please enter a verse to bookmark.")
            return

        def fetch_and_bookmark():
            text, ref_out = asyncio.run(get_verse_async(ref, self.current_version))
            self.root.after(0, lambda: self.save_bookmark(text, ref_out))

        Thread(target=fetch_and_bookmark).start()

    def save_bookmark(self, text, ref_out):
        if text != "error":
            self.bookmarks[ref_out] = text
            save_bookmarks(self.bookmarks)
            self.update_bookmarks_tab()
            messagebox.showinfo("Success", f"Bookmarked {ref_out}!")
            self.status_label.configure(text=f"Bookmarked {ref_out}", text_color="#50C878")
        else:
            messagebox.showerror("Error", f"Cannot bookmark: {ref_out}")
            self.status_label.configure(text=f"Error: {ref_out}", text_color="#FF6B6B")

    def setup_search_tab(self):
        self.search_tab = self.notebook.add("Search 🔍")
        
        # Search input
        input_frame = ctk.CTkFrame(self.search_tab, corner_radius=10, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(input_frame, text="Keyword:", font=("Roboto", 14), text_color="#4A90E2").pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(input_frame, width=400, font=("Roboto", 12), placeholder_text="Enter keyword")
        self.search_entry.pack(side="left", padx=5)
        ctk.CTkButton(input_frame, text="Search", command=self.perform_search, corner_radius=10, font=("Roboto", 12), fg_color="#50C878", text_color="#FFFFFF").pack(side="left", padx=5)

        # Search results
        self.search_results = tk.Listbox(self.search_tab, height=20, font=("Roboto", 12), bg="#F0F4F8" if ctk.get_appearance_mode() == "Light" else "#2B2D42", fg="#2B2D42" if ctk.get_appearance_mode() == "Light" else "#FFFFFF")
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
        for verse_data in POPULAR_VERSES_DATA:
            if search_pattern.search(verse_data['text']):
                results.append(verse_data)
        if results:
            for result in results[:20]:
                self.search_results.insert("end", result['reference'])
            self.status_label.configure(text=f"Found {len(results)} results for '{keyword}'", text_color="#50C878")
        else:
            self.search_results.insert("end", "No results found.")
            self.status_label.configure(text=f"No results for '{keyword}'", text_color="#FF6B6B")

    def show_search_result(self, event):
        selection = self.search_results.curselection()
        if not selection:
            return
        ref = self.search_results.get(selection[0])
        if ref == "No results found.":
            return
        text = next((v['text'] for v in POPULAR_VERSES_DATA if v['reference'] == ref), None)
        if text:
            highlighted_text = highlight_keywords(text, [self.search_entry.get().strip()])
            dialog = ctk.CTkToplevel(self.root)
            dialog.title(ref)
            dialog.geometry("600x400")
            text_area = ctk.CTkTextbox(dialog, wrap="word", font=("Courier New", 14), height=300, corner_radius=10)
            text_area.pack(padx=10, pady=10, fill="both", expand=True)
            text_area.insert("end", f"{ref} ({self.current_version.upper()})\n\n{highlighted_text}")
            text_area.configure(state="disabled")
            ctk.CTkButton(dialog, text="Bookmark", command=lambda: self.bookmark_from_search(ref, text), corner_radius=10, font=("Roboto", 12), fg_color="#F7DC6F", text_color="#2B2D42").pack(pady=10)

    def bookmark_from_search(self, ref, text):
        self.bookmarks[ref] = text
        save_bookmarks(self.bookmarks)
        self.update_bookmarks_tab()
        messagebox.showinfo("Success", f"Bookmarked {ref}!")
        self.status_label.configure(text=f"Bookmarked {ref}", text_color="#50C878")

    def setup_bookmarks_tab(self):
        self.bookmarks_tab = self.notebook.add("Bookmarks 📌")
        self.bookmarks_list = tk.Listbox(self.bookmarks_tab, height=20, font=("Roboto", 12), bg="#F0F4F8" if ctk.get_appearance_mode() == "Light" else "#2B2D42", fg="#2B2D42" if ctk.get_appearance_mode() == "Light" else "#FFFFFF")
        self.bookmarks_list.pack(fill="both", expand=True, padx=10, pady=10)
        self.bookmarks_list.bind("<<ListboxSelect>>", self.show_bookmark)
        ctk.CTkButton(self.bookmarks_tab, text="Delete Selected", command=self.delete_bookmark, corner_radius=10, font=("Roboto", 12), fg_color="#FF6B6B", text_color="#FFFFFF").pack(pady=10)
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
        highlighted_text = highlight_keywords(text, self.keywords_to_highlight)
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(ref)
        dialog.geometry("600x400")
        text_area = ctk.CTkTextbox(dialog, wrap="word", font=("Courier New", 14), height=300, corner_radius=10)
        text_area.pack(padx=10, pady=10, fill="both", expand=True)
        text_area.insert("end", f"{ref} ({self.current_version.upper()})\n\n{highlighted_text}")
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
            self.status_label.configure(text=f"Deleted bookmark {ref}", text_color="#50C878")

    def setup_daily_tab(self):
        self.daily_tab = self.notebook.add("Daily Verse ✨")
        ctk.CTkButton(self.daily_tab, text="Show Daily Verse", command=self.show_daily_verse, corner_radius=10, font=("Roboto", 14), fg_color="#50C878", text_color="#FFFFFF", width=200).pack(pady=20)
        self.daily_text = ctk.CTkTextbox(self.daily_tab, wrap="word", font=("Courier New", 14), height=400, corner_radius=10)
        self.daily_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.daily_text.configure(state="disabled")

    def show_daily_verse(self):
        daily_refs = [
            "John 3:16", "Psalm 23:1", "Romans 12:2", "Philippians 4:13", "Proverbs 3:5",
            "Matthew 6:33", "Jeremiah 29:11", "Isaiah 41:10", "Romans 8:28", "Joshua 1:9",
            "1 Corinthians 13:4-7", "Psalm 46:10", "John 14:6", "Galatians 5:22-23",
            "Matthew 11:28", "Hebrews 11:1", "Psalm 119:105", "Ephesians 2:8-9",
            "2 Timothy 3:16", "1 John 4:7-8"
        ]
        ref = random.choice(daily_refs)
        
        self.status_label.configure(text="Fetching daily verse...", text_color="#4A90E2")
        self.root.config(cursor="wait")
        self.root.update()

        def fetch_and_display():
            text, ref_out = asyncio.run(get_verse_async(ref, self.current_version))
            self.root.after(0, lambda: self.display_daily_verse(text, ref_out))

        Thread(target=fetch_and_display).start()

    def display_daily_verse(self, text, ref_out):
        self.daily_text.configure(state="normal")
        self.daily_text.delete("1.0", "end")
        if text != "error":
            highlighted_text = highlight_keywords(text, self.keywords_to_highlight)
            self.daily_text.insert("end", f"{ref_out} ({self.current_version.upper()})\n\n{highlighted_text}")
            self.status_label.configure(text=f"Daily verse: {ref_out}", text_color="#50C878")
            for widget in self.daily_tab.winfo_children():
                if isinstance(widget, ctk.CTkButton) and widget.cget("text") == "Bookmark":
                    widget.destroy()
            ctk.CTkButton(self.daily_tab, text="Bookmark", command=lambda: self.bookmark_from_search(ref_out, text), corner_radius=10, font=("Roboto", 12), fg_color="#F7DC6F", text_color="#2B2D42").pack(pady=10)
        else:
            self.daily_text.insert("end", f"Error: {ref_out}")
            self.status_label.configure(text=f"Error: {ref_out}", text_color="#FF6B6B")
        self.daily_text.configure(state="disabled")
        self.root.config(cursor="")

if __name__ == "__main__":
    root = ctk.CTk()
    app = BibleApp(root)
    root.mainloop()