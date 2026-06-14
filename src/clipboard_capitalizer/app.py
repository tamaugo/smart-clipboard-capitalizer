import json
import os
import threading
import time
from datetime import datetime
import socket
import sys
import math
import tkinter as tk
import customtkinter as ctk

try:
    from . import engine
except ImportError:
    import engine

# Resolve project paths dynamically
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
icon_path = os.path.join(root_dir, "assets", "icon.ico")

# Save user settings in Windows AppData Roaming directory for clean packaging
appdata_dir = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "ClipboardCapitalizer")
os.makedirs(appdata_dir, exist_ok=True)
SETTINGS_FILE = os.path.join(appdata_dir, "settings.json")


class SmartCapitalizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Clipboard Capitalizer")
        self.root.geometry("560x800")
        self.root.minsize(560, 700)
        self.root.resizable(False, True)  # Lock horizontal resizing to preserve the editorial layout
        self.root.configure(fg_color="#F5F0E8")  # Warm parchment base background

        # Load native Windows taskbar and titlebar icon if available
        if sys.platform == "win32" and os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # Application state
        self.is_monitoring = False
        self.monitor_thread = None
        self.history_items = []  # List of tuples: (original_text, processed_text)
        self.toast_label = None

        # Typography (Editorial Display, modern UI, JetBrains Mono for logs)
        self.display_font = ctk.CTkFont(family="DM Serif Display", size=22, weight="bold")
        self.header_font = ctk.CTkFont(family="Inter", size=12, weight="bold")
        self.normal_font = ctk.CTkFont(family="Inter", size=12)
        self.small_font = ctk.CTkFont(family="Inter", size=10)
        self.code_font = ctk.CTkFont(family="JetBrains Mono", size=11)

        # Style colors (Tactile Parchment Editorial Palette)
        self.bg_color = "#F5F0E8"      # Warm parchment base
        self.card_bg = "#E8E3DA"       # Cool-warm card surface
        self.elevated_bg = "#FFFFFF"   # Pure white elevated panels
        self.text_primary = "#2C2A26"  # Near-black ink
        self.text_secondary = "#B8A99A"# Dusty rose-grey
        self.accent_color = "#C9763A"  # Burnt copper electric accent
        self.accent_hover = "#DF8C50"  # Active hover
        self.stone_muted = "#B8A99A"   # Inactive button stone
        self.stone_hover = "#C9B6A3"   # Inactive button hover

        # Living breathing status bar stripe at the very top of the window
        self.pulse_bar = tk.Frame(self.root, height=4, bg=self.text_secondary, bd=0, highlightthickness=0)
        self.pulse_bar.pack(fill=tk.X, side=tk.TOP)

        # Load settings
        self.load_settings()

        # Build UI
        self.setup_ui()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Auto-start monitoring if configured
        if self.settings.get("auto_start", False):
            self.start_monitoring()

    def adjust_textbox_height(self, textbox, min_lines=1, max_lines=6, line_height=18, base_padding=12):
        """Dynamically resizes a CTkTextbox based on its visual lines count."""
        txt = textbox._textbox
        try:
            # count the number of display lines
            res = txt.count("1.0", "end-1c", "displaylines")
            display_lines = res[0] if res else 1
        except Exception:
            # fallback if count fails
            display_lines = len(txt.get("1.0", "end-1c").split("\n"))
            
        display_lines = max(min_lines, min(max_lines, display_lines))
        new_height = base_padding + (display_lines * line_height)
        textbox.configure(height=new_height)

    def load_settings(self):
        """Loads configuration from JSON file, setting defaults if missing."""
        defaults = {
            "min_part_len": 4,
            "auto_detect_parts": True,
            "custom_uppercase": "XY2594YX684, 9-YCC142",
            "whitelist": "iPhone, macOS",
            "blacklist": "draft, ignore",
            "auto_start": False
        }
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    self.settings = json.load(f)
                # Fill in missing default keys if any
                for k, v in defaults.items():
                    if k not in self.settings:
                        self.settings[k] = v
            except Exception:
                self.settings = defaults
        else:
            self.settings = defaults

    def save_settings(self):
        """Saves current GUI settings back to the JSON file."""
        try:
            self.settings["min_part_len"] = int(self.min_len_var.get())
            self.settings["auto_detect_parts"] = bool(self.auto_detect_var.get())
            self.settings["custom_uppercase"] = self.uppercase_entry.get().strip()
            if hasattr(self, "whitelist_text"):
                self.settings["whitelist"] = self.whitelist_text.get("1.0", "end-1c").strip()
            if hasattr(self, "blacklist_text"):
                self.settings["blacklist"] = self.blacklist_text.get("1.0", "end-1c").strip()
            self.settings["auto_start"] = bool(self.auto_start_var.get())

            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f, indent=4)
        except ValueError:
            pass  # Handled during validation

    def setup_ui(self):
        # Master padding container (Airy and generous spacing)
        main_container = ctk.CTkFrame(self.root, fg_color=self.bg_color, corner_radius=0)
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=(15, 25))

        # ----------------------------------------------------
        # HEADER PANEL (Title & Status)
        # ----------------------------------------------------
        header_frame = ctk.CTkFrame(main_container, fg_color=self.bg_color, height=45)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ctk.CTkLabel(
            header_frame, text="Smart Clipboard Capitalizer",
            font=self.display_font, text_color=self.text_primary
        )
        title_label.pack(side=tk.LEFT)

        # Status dot & indicator
        self.status_label = ctk.CTkLabel(
            header_frame, text="STATUS: INACTIVE",
            font=self.header_font, text_color=self.text_secondary
        )
        self.status_label.pack(side=tk.RIGHT)

        self.status_dot = ctk.CTkLabel(
            header_frame, text="●",
            font=("Segoe UI", 14), text_color=self.text_secondary
        )
        self.status_dot.pack(side=tk.RIGHT, padx=(0, 8))

        # ----------------------------------------------------
        # ACTION PANEL (Start/Stop Card)
        # ----------------------------------------------------
        action_frame = ctk.CTkFrame(
            main_container, fg_color=self.card_bg, border_color=self.text_secondary, border_width=1, corner_radius=8
        )
        action_frame.pack(fill=tk.X, pady=(0, 20))

        action_inner = ctk.CTkFrame(action_frame, fg_color=self.card_bg)
        action_inner.pack(fill=tk.X, padx=20, pady=20)

        # Toggle Button: Full-width and changes character between states
        self.toggle_btn = ctk.CTkButton(
            action_inner, text="Start Clipboard Monitor",
            font=self.header_font, fg_color=self.stone_muted, text_color=self.text_primary,
            hover_color=self.stone_hover, height=45, corner_radius=8,
            command=self.toggle_monitoring
        )
        self.toggle_btn.pack(fill=tk.X, pady=(0, 10))

        # Auto-run switch (Toggle switch instead of checkbox)
        self.auto_start_var = tk.BooleanVar(value=self.settings.get("auto_start", False))
        auto_start_cb = ctk.CTkSwitch(
            action_inner, text="Auto-run on app launch",
            variable=self.auto_start_var, font=self.small_font,
            text_color=self.text_primary, progress_color=self.accent_color,
            button_color=self.text_primary, button_hover_color=self.accent_color,
            command=self.save_settings
        )
        auto_start_cb.pack(side=tk.LEFT)

        # ----------------------------------------------------
        # SETTINGS PANEL (Modern Flat Card on Parchment)
        # ----------------------------------------------------
        rules_header = ctk.CTkLabel(
            main_container, text="Configuration Rules", font=self.header_font,
            text_color=self.text_primary, anchor="w"
        )
        rules_header.pack(fill=tk.X, pady=(0, 6))

        settings_frame = ctk.CTkFrame(
            main_container, fg_color=self.card_bg, border_color=self.text_secondary, border_width=1, corner_radius=8
        )
        settings_frame.pack(fill=tk.X, pady=(0, 20))

        rules_grid = ctk.CTkFrame(settings_frame, fg_color=self.card_bg)
        rules_grid.pack(fill=tk.X, padx=20, pady=20)

        # Rule 1: Auto-detect alphanumeric part numbers
        self.auto_detect_var = tk.BooleanVar(value=self.settings.get("auto_detect_parts", True))
        auto_detect_cb = ctk.CTkSwitch(
            rules_grid, text="Auto-detect alphanumeric part numbers (e.g. XY2594YX684)",
            variable=self.auto_detect_var, font=self.normal_font,
            text_color=self.text_primary, progress_color=self.accent_color,
            button_color=self.text_primary, button_hover_color=self.accent_color,
            command=self.save_settings
        )
        auto_detect_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))

        # Rule 2: Minimum Alphanumeric Length
        min_len_label = ctk.CTkLabel(
            rules_grid, text="Minimum length for part numbers:",
            font=self.normal_font, text_color=self.text_primary
        )
        min_len_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 15))

        self.min_len_var = tk.StringVar(value=str(self.settings.get("min_part_len", 4)))
        vcmd = (self.root.register(self.validate_digit), "%P")

        # White elevated entry field
        self.min_len_entry = ctk.CTkEntry(
            rules_grid, textvariable=self.min_len_var, width=55, font=self.normal_font,
            fg_color=self.elevated_bg, border_color=self.text_secondary, text_color=self.text_primary,
            height=30, border_width=1, corner_radius=6, validate="key", validatecommand=vcmd
        )
        self.min_len_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=(0, 15))
        self.min_len_entry.bind("<FocusIn>", lambda e: self.min_len_entry.configure(border_color=self.accent_color))
        self.min_len_entry.bind("<FocusOut>", lambda e: [self.min_len_entry.configure(border_color=self.text_secondary), self.save_settings()])
        self.min_len_entry.bind("<Return>", lambda e: self.save_settings())

        # Rule 3: Custom Uppercase Words
        uppercase_label = ctk.CTkLabel(
            rules_grid, text="Custom UPPERCASE words (comma-separated):",
            font=self.normal_font, text_color=self.text_primary
        )
        uppercase_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))

        # White elevated entry field
        self.uppercase_entry = ctk.CTkEntry(
            rules_grid, font=self.normal_font, fg_color=self.elevated_bg,
            border_color=self.text_secondary, text_color=self.text_primary,
            height=30, border_width=1, corner_radius=6
        )
        self.uppercase_entry.insert(0, self.settings.get("custom_uppercase", ""))
        self.uppercase_entry.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(0, 5))
        self.uppercase_entry.bind("<FocusIn>", lambda e: self.uppercase_entry.configure(border_color=self.accent_color))
        self.uppercase_entry.bind("<FocusOut>", lambda e: [self.uppercase_entry.configure(border_color=self.text_secondary), self.save_settings()])
        self.uppercase_entry.bind("<Return>", lambda e: self.save_settings())

        # Rule 4: Whitelist Phrases (Auto-growing Textbox)
        whitelist_label = ctk.CTkLabel(
            rules_grid, text="🟢 Whitelisted Phrases (preserve custom case, e.g. iPhone, macOS):",
            font=self.normal_font, text_color=self.text_primary
        )
        whitelist_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(5, 4))

        self.whitelist_text = ctk.CTkTextbox(
            rules_grid, font=self.normal_font, fg_color=self.elevated_bg,
            border_color=self.text_secondary, text_color=self.text_primary,
            height=30, border_width=1, corner_radius=6, wrap="word",
            activate_scrollbars=True
        )
        self.whitelist_text.insert("1.0", self.settings.get("whitelist", ""))
        self.adjust_textbox_height(self.whitelist_text)
        self.whitelist_text.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(0, 5))
        self.whitelist_text.bind("<FocusIn>", lambda e: self.whitelist_text.configure(border_color=self.accent_color))
        self.whitelist_text.bind("<FocusOut>", lambda e: [self.whitelist_text.configure(border_color=self.text_secondary), self.save_settings()])
        self.whitelist_text.bind("<KeyRelease>", lambda e: self.adjust_textbox_height(self.whitelist_text))

        # Rule 5: Blacklist Phrases (Auto-growing Textbox)
        blacklist_label = ctk.CTkLabel(
            rules_grid, text="🔴 Blacklisted Phrases (prevent capitalization, e.g. draft, ignored):",
            font=self.normal_font, text_color=self.text_primary
        )
        blacklist_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(5, 4))

        self.blacklist_text = ctk.CTkTextbox(
            rules_grid, font=self.normal_font, fg_color=self.elevated_bg,
            border_color=self.text_secondary, text_color=self.text_primary,
            height=30, border_width=1, corner_radius=6, wrap="word",
            activate_scrollbars=True
        )
        self.blacklist_text.insert("1.0", self.settings.get("blacklist", ""))
        self.adjust_textbox_height(self.blacklist_text)
        self.blacklist_text.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=(0, 5))
        self.blacklist_text.bind("<FocusIn>", lambda e: self.blacklist_text.configure(border_color=self.accent_color))
        self.blacklist_text.bind("<FocusOut>", lambda e: [self.blacklist_text.configure(border_color=self.text_secondary), self.save_settings()])
        self.blacklist_text.bind("<KeyRelease>", lambda e: self.adjust_textbox_height(self.blacklist_text))

        rules_grid.columnconfigure(0, weight=0)
        rules_grid.columnconfigure(1, weight=1)

        # ----------------------------------------------------
        # HISTORY PANEL
        # ----------------------------------------------------
        history_header_frame = ctk.CTkFrame(main_container, fg_color=self.bg_color)
        history_header_frame.pack(fill=tk.X, pady=(5, 5))

        self.history_title = ctk.CTkLabel(
            history_header_frame, text="Clipboard Activity History (0)",
            font=self.header_font, text_color=self.text_primary
        )
        self.history_title.pack(side=tk.LEFT)

        clear_btn = ctk.CTkButton(
            history_header_frame, text="Clear History",
            font=self.small_font, fg_color=self.card_bg, hover_color=self.text_secondary,
            text_color=self.text_primary, width=90, height=24, corner_radius=6,
            command=self.clear_history
        )
        clear_btn.pack(side=tk.RIGHT)

        # Scrollable Text History View (White elevated card surface, scrollbars disabled)
        history_view_frame = ctk.CTkFrame(
            main_container, fg_color=self.elevated_bg, border_color=self.text_secondary, border_width=1, corner_radius=8
        )
        history_view_frame.pack(fill=tk.BOTH, expand=True)

        self.history_text = ctk.CTkTextbox(
            history_view_frame, font=self.code_font, fg_color=self.elevated_bg,
            text_color=self.text_primary, wrap="none", cursor="arrow",
            activate_scrollbars=False  # Hide scrollbar for clean card layout
        )
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Configure rich history tags directly on the underlying Tkinter Text widget
        txt = self.history_text._textbox
        txt.tag_configure("time", foreground=self.text_secondary)
        txt.tag_configure("orig", foreground=self.text_secondary)
        txt.tag_configure("arrow", foreground=self.accent_color)
        txt.tag_configure("proc", foreground=self.text_primary)
        txt.tag_configure("hover", background=self.card_bg)

        # Motion binds for row hover highlight
        txt.bind("<Motion>", self.on_history_hover)
        txt.bind("<Leave>", self.on_history_leave)

        # Double click to restore original text
        txt.bind("<Double-Button-1>", self.on_history_double_click)

        # Right-click context menu
        self.context_menu = tk.Menu(self.root, tearoff=0, bg=self.elevated_bg, fg=self.text_primary, bd=1, relief="solid")
        self.context_menu.add_command(label="Copy Original Text", command=self.copy_selected_original)
        self.context_menu.add_command(label="Copy Processed Text", command=self.copy_selected_processed)
        txt.bind("<Button-3>", self.show_context_menu)

        # Initialize empty history placeholder state
        self.check_empty_history()

        # ----------------------------------------------------
        # FOOTER / STATUS BAR
        # ----------------------------------------------------
        footer_label = ctk.CTkLabel(
            main_container, text="💡 Tip: Double-click an entry to restore original text to clipboard",
            font=self.small_font, text_color=self.text_secondary
        )
        footer_label.pack(fill=tk.X, pady=(8, 0))

    def draw_status_dot(self, color):
        """Updates the status dot character color."""
        self.status_dot.configure(text_color=color)

    def interpolate_color(self, color1, color2, factor):
        """Linearly interpolates between two hex color codes."""
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def animate_pulse_bar(self, step=0):
        """Animates a living breathing heartbeat glow in the status bar frame."""
        if not self.is_monitoring:
            self.pulse_bar.configure(bg=self.text_secondary)  # Flat cool grey when off
            return
        
        # Pulsing sine wave between 0.0 and 1.0
        factor = (math.sin(step * 0.15) + 1.0) / 2.0
        color = self.interpolate_color(self.card_bg, self.accent_color, factor)
        self.pulse_bar.configure(bg=color)

        self.root.after(45, lambda: self.animate_pulse_bar(step + 1))

    def check_empty_history(self):
        """Displays a clean placeholder message when the history list is empty."""
        txt = self.history_text._textbox
        if not self.history_items:
            self.history_text.configure(state="normal")
            txt.delete("1.0", tk.END)
            txt.insert("1.0", "\n\n        No clipboard activity logged yet.\n        Copy some text to begin!", "empty_msg")
            txt.tag_configure("empty_msg", foreground=self.text_secondary, justify="center", font=self.normal_font)
            self.history_text.configure(state="disabled")

    def show_toast(self, message):
        """Displays a clean bottom toast notification overlay that fades after 2 seconds."""
        if self.toast_label and self.toast_label.winfo_exists():
            self.toast_label.destroy()

        self.toast_label = ctk.CTkLabel(
            self.root, text=message, font=self.normal_font,
            text_color="#FFFFFF", fg_color=self.accent_color,
            corner_radius=6, padx=15, pady=6
        )
        self.toast_label.place(relx=0.5, rely=0.88, anchor=tk.CENTER)
        self.root.after(2000, self.hide_toast)

    def hide_toast(self):
        """Destroys the current active toast label."""
        if self.toast_label and self.toast_label.winfo_exists():
            self.toast_label.destroy()

    def validate_digit(self, val):
        """Validation routine: only allow positive integers or empty input."""
        return val == "" or val.isdigit()

    def toggle_monitoring(self):
        """Starts or stops the clipboard monitoring thread based on current state."""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        """Activates the clipboard listener and spins up a worker thread."""
        try:
            int(self.min_len_var.get())
        except ValueError:
            self.show_toast("Error: Min length must be an integer!")
            return

        self.save_settings()
        self.is_monitoring = True

        # Toggle button glows copper when ON
        self.toggle_btn.configure(
            text="Stop Clipboard Monitor", fg_color=self.accent_color,
            text_color="#FFFFFF", hover_color=self.accent_hover
        )
        self.status_label.configure(text="STATUS: MONITORING ACTIVE", text_color=self.accent_color)
        self.draw_status_dot(self.accent_color)
        
        # Start animations
        self.animate_pulse_bar()
        self.show_toast("Clipboard monitoring active")

        # Spawn background polling thread
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Signals the background thread to exit and updates GUI states."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=0.2)

        # Toggle button turns muted stone when OFF
        self.toggle_btn.configure(
            text="Start Clipboard Monitor", fg_color=self.stone_muted,
            text_color=self.text_primary, hover_color=self.stone_hover
        )
        self.status_label.configure(text="STATUS: INACTIVE", text_color=self.text_secondary)
        self.draw_status_dot(self.text_secondary)
        self.pulse_bar.configure(bg=self.text_secondary)  # Reset pulse bar immediately
        self.show_toast("Monitoring stopped")

    def get_settings(self):
        """
        Thread-safe snapshot of settings currently entered in GUI.
        Used by the monitor loop to perform formatting.
        """
        try:
            min_len = int(self.min_len_var.get())
        except ValueError:
            min_len = 4

        import re
        whitelist_raw = self.whitelist_text.get("1.0", "end-1c")
        blacklist_raw = self.blacklist_text.get("1.0", "end-1c")

        return {
            "min_len": min_len,
            "auto_detect": self.auto_detect_var.get(),
            "uppercase": [w.strip() for w in self.uppercase_entry.get().split(",") if w.strip()],
            "whitelist": [w.strip() for w in re.split(r'[,\n]', whitelist_raw) if w.strip()],
            "blacklist": [w.strip() for w in re.split(r'[,\n]', blacklist_raw) if w.strip()]
        }

    def monitor_loop(self):
        """Background thread loop that polls the system clipboard for changes."""
        last_seq = engine.get_clipboard_sequence_number()
        last_text = None

        while self.is_monitoring:
            time.sleep(0.1)  # Lightweight sleep to avoid CPU spikes

            current_seq = engine.get_clipboard_sequence_number()
            if current_seq == last_seq:
                continue

            last_seq = current_seq
            text = engine.get_clipboard_text()

            # Ignore empty or unreadable clipboards, or loops on our own writes
            if not text or text == last_text:
                continue

            settings = self.get_settings()
            processed = engine.capitalize_text(
                text,
                min_part_len=settings["min_len"],
                auto_detect_parts=settings["auto_detect"],
                custom_uppercase_list=settings["uppercase"],
                whitelist_list=settings["whitelist"],
                blacklist_list=settings["blacklist"]
            )

            # If our processing rule altered the copied string, write it back
            if processed != text:
                last_text = processed
                engine.set_clipboard_text(processed)
                # Capture the new sequence number from our own write to prevent self-triggering
                last_seq = engine.get_clipboard_sequence_number()

                # Dispatch log insertion back to the main Tkinter thread safely
                self.root.after(0, self.add_history_entry, text, processed)
            else:
                last_text = text

    def add_history_entry(self, original, processed):
        """Inserts a formatted logs entry into the history panel from main thread."""
        # If it was empty (first item), clear the empty message first!
        if not self.history_items:
            self.history_text.configure(state="normal")
            self.history_text.delete("1.0", tk.END)
            self.history_text.configure(state="disabled")

        self.history_items.append((original, processed))

        # Format original/processed preview to fit nicely on one line
        orig_short = original.replace("\n", " ↵ ").replace("\r", "")
        proc_short = processed.replace("\n", " ↵ ").replace("\r", "")

        # Truncate extremely long strings in the history preview
        if len(orig_short) > 30:
            orig_short = orig_short[:27] + "..."
        if len(proc_short) > 30:
            proc_short = proc_short[:27] + "..."

        timestamp = datetime.now().strftime("[%H:%M:%S] ")

        # Unlock text box, write elements with corresponding tag styles, lock it again
        self.history_text.configure(state="normal")
        txt = self.history_text._textbox
        txt.insert(tk.END, timestamp, "time")
        txt.insert(tk.END, f'"{orig_short}"', "orig")
        txt.insert(tk.END, " ➜ ", "arrow")
        txt.insert(tk.END, f'"{proc_short}"\n', "proc")
        
        # Update counter badge
        self.history_title.configure(text=f"Clipboard Activity History ({len(self.history_items)})")
        
        txt.see(tk.END)  # Scroll to bottom
        self.history_text.configure(state="disabled")

    def clear_history(self):
        """Clears the internal history and GUI history textbox."""
        self.history_items.clear()
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", tk.END)
        self.history_text.configure(state="disabled")
        self.history_title.configure(text="Clipboard Activity History (0)")
        
        # Reset placeholder empty state
        self.check_empty_history()
        self.show_toast("History cleared")

    def get_clicked_item_index(self):
        """Utility to resolve which history list item corresponds to cursor position."""
        try:
            txt = self.history_text._textbox
            click_index = txt.index("current")
            line_num = int(click_index.split(".")[0])
            item_idx = line_num - 1
            if 0 <= item_idx < len(self.history_items):
                return item_idx
        except Exception:
            pass
        return None

    def on_history_hover(self, event):
        """Highlights the history line that the mouse is currently hovering over."""
        # Only highlight if there are actual logged entries (avoid highlighting the empty message)
        if not self.history_items:
            return

        txt = self.history_text._textbox
        pos = txt.index(f"@{event.x},{event.y}")
        line_num = int(pos.split(".")[0])
        
        txt.tag_remove("hover", "1.0", tk.END)
        if 1 <= line_num <= len(self.history_items):
            txt.tag_add("hover", f"{line_num}.0", f"{line_num}.end")

    def on_history_leave(self, event):
        """Removes the hover highlight when mouse leaves the text widget."""
        self.history_text._textbox.tag_remove("hover", "1.0", tk.END)

    def on_history_double_click(self, event):
        """Double clicking a history line restores the original text to clipboard."""
        if not self.history_items:
            return

        idx = self.get_clicked_item_index()
        if idx is not None:
            original, _ = self.history_items[idx]
            # Temporarily pause monitoring thread so it doesn't immediately re-capitalize it!
            was_monitoring = self.is_monitoring
            if was_monitoring:
                self.is_monitoring = False
                time.sleep(0.15)  # Allow monitor loop to finish sleep cycle

            engine.set_clipboard_text(original)

            # Restart monitor if it was active
            if was_monitoring:
                self.is_monitoring = True
                self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
                self.monitor_thread.start()

            self.show_toast("Restored original text to clipboard!")

    def show_context_menu(self, event):
        """Display right-click context menu over history entry."""
        if not self.history_items:
            return

        idx = self.get_clicked_item_index()
        if idx is not None:
            self.clicked_item_idx = idx
            self.context_menu.post(event.x_root, event.y_root)

    def copy_selected_original(self):
        """Copy the original string from the selected history item to clipboard."""
        if hasattr(self, "clicked_item_idx") and self.clicked_item_idx is not None:
            original, _ = self.history_items[self.clicked_item_idx]
            engine.set_clipboard_text(original)
            self.show_toast("Copied original text")

    def copy_selected_processed(self):
        """Copy the processed string from the selected history item to clipboard."""
        if hasattr(self, "clicked_item_idx") and self.clicked_item_idx is not None:
            _, processed = self.history_items[self.clicked_item_idx]
            engine.set_clipboard_text(processed)
            self.show_toast("Copied processed text")

    def on_close(self):
        """Gracefully shuts down thread worker, saves settings, terminates related processes, and exits."""
        # 1. Stop monitoring loop
        self.is_monitoring = False
        
        # 2. Save settings
        self.save_settings()
        
        # 3. Terminate related Node.js processes (Vite/npm dev server for deck-run)
        try:
            import subprocess
            # Powershell command targeting node.exe running vite/npm dev servers
            cmd = (
                "powershell -Command \""
                "Get-CimInstance Win32_Process -Filter \\\"name = 'node.exe'\\\" | "
                "Where-Object { $_.CommandLine -like '*deck-run*' -or $_.CommandLine -like '*vite*' -or $_.CommandLine -like '*npm-cli.js*' } | "
                "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
                "\""
            )
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
            
        # 4. Destroy GUI widgets
        try:
            self.root.destroy()
        except Exception:
            pass
            
        # 5. Explicitly exit Python 3.13 process
        import sys
        sys.exit(0)


if __name__ == "__main__":
    # Force Windows to treat the script as a separate app on the taskbar so it uses assets/icon.ico
    if sys.platform == "win32":
        import ctypes
        myappid = 'alfie.clipboardcapitalizer.gui.1.0' # arbitrary unique string
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # Single instance lock to prevent background processes from conflicting
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('127.0.0.1', 47200))
    except socket.error:
        # Show warning and exit immediately
        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showwarning("Already Running", "Smart Clipboard Capitalizer is already running in the background!")
        sys.exit(0)

    ctk.set_appearance_mode("light")  # Force light-mode to support tactile parchment look
    root = ctk.CTk()
    app = SmartCapitalizerApp(root)
    root.mainloop()
