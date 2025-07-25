import tkinter as tk
from tkinter import ttk
import json
import os

class MarkChapter1Explainer:
    def __init__(self, root):
        self.root = root
        self.root.title("Mark Chapter 1 Verse Explainer")
        self.root.geometry("600x400")

        # Load JSON data
        self.data = self.load_json()

        # Create GUI elements
        self.create_widgets()

    def load_json(self):
        """Load the external JSON file."""
        try:
            with open("Mark_Chapter1_Commentary.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print("Error: Mark_Chapter1_Commentary.json not found.")
            return {"sections": [], "references": []}
        except json.JSONDecodeError:
            print("Error: Invalid JSON format.")
            return {"sections": [], "references": []}

    def create_widgets(self):
        """Create the GUI layout."""
        # Verse selection label and dropdown
        tk.Label(self.root, text="Select a Verse:", font=("Arial", 12)).pack(pady=10)
        self.verse_var = tk.StringVar()
        verses = self.get_verses()
        self.verse_dropdown = ttk.Combobox(self.root, textvariable=self.verse_var, values=verses, state="readonly")
        self.verse_dropdown.pack(pady=5)
        self.verse_dropdown.bind("<<ComboboxSelected>>", self.display_verse)

        # Text area for verse details
        self.text_area = tk.Text(self.root, height=15, width=60, wrap="word", font=("Arial", 10))
        self.text_area.pack(pady=10, padx=10)
        self.text_area.config(state="disabled")

    def get_verses(self):
        """Extract all verse identifiers from the JSON."""
        verses = []
        for section in self.data["sections"]:
            for subsection in section["subsections"]:
                for verse in subsection["verses"]:
                    verses.append(verse["verse"])
        return verses

    def display_verse(self, event=None):
        """Display the selected verse's details in the text area."""
        selected_verse = self.verse_var.get()
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)

        if not selected_verse:
            self.text_area.insert(tk.END, "Please select a verse.")
            self.text_area.config(state="disabled")
            return

        # Find the selected verse
        found_verse = None
        for section in self.data["sections"]:
            for subsection in section["subsections"]:
                for verse in subsection["verses"]:
                    if verse["verse"] == selected_verse:
                        found_verse = verse
                        break
                if found_verse:
                    break

        if found_verse:
            # Display verse text and commentary
            self.text_area.insert(tk.END, f"Verse: {found_verse['verse']}\n\n")
            self.text_area.insert(tk.END, f"Text: {found_verse['text']}\n\n")
            self.text_area.insert(tk.END, f"Commentary: {found_verse['commentary']}\n\n")

            # Find and display relevant references
            references = [ref for ref in self.data["references"] if ref["reference"] in found_verse["commentary"]]
            self.text_area.insert(tk.END, "References:\n")
            if references:
                for ref in references:
                    self.text_area.insert(tk.END, f"- {ref['reference']}: {ref['context']}\n")
            else:
                self.text_area.insert(tk.END, "- No specific references found.\n")
        else:
            self.text_area.insert(tk.END, "Verse not found.")

        self.text_area.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = MarkChapter1Explainer(root)
    root.mainloop()
