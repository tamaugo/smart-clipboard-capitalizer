import re
import ctypes
from ctypes import wintypes

# Load user32.dll and kernel32.dll for native Windows clipboard operations
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Win32 Clipboard Constants
CF_UNICODETEXT = 13
GHND = 0x0042

# Configure Win32 API function signatures
user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL

user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL

user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL

user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE

user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE

user32.GetClipboardSequenceNumber.argtypes = []
user32.GetClipboardSequenceNumber.restype = wintypes.DWORD

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL

kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = wintypes.LPVOID

kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL

kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalFree.restype = wintypes.HGLOBAL


def get_clipboard_text():
    """Reads unicode text directly from the Windows clipboard using native Win32 APIs."""
    if not user32.OpenClipboard(None):
        return ""
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return ""
        try:
            # CF_UNICODETEXT is UTF-16 LE encoded
            text = ctypes.wstring_at(ptr)
            return text
        finally:
            kernel32.GlobalUnlock(handle)
    except Exception:
        return ""
    finally:
        user32.CloseClipboard()


def set_clipboard_text(text):
    """Writes unicode text directly to the Windows clipboard using native Win32 APIs."""
    if not user32.OpenClipboard(None):
        return False
    try:
        user32.EmptyClipboard()
        # Encode as UTF-16 LE with null terminator
        text_bytes = (text + '\0').encode('utf-16le')
        handle = kernel32.GlobalAlloc(GHND, len(text_bytes))
        if not handle:
            return False
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            kernel32.GlobalFree(handle)
            return False
        try:
            ctypes.memmove(ptr, text_bytes, len(text_bytes))
        finally:
            kernel32.GlobalUnlock(handle)
        
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            kernel32.GlobalFree(handle)
            return False
        return True
    except Exception:
        return False
    finally:
        user32.CloseClipboard()


def get_clipboard_sequence_number():
    """Queries the current clipboard sequence number (fast, lightweight hardware event-like check)."""
    return user32.GetClipboardSequenceNumber()


def format_word(word, min_part_len=4, auto_detect_parts=True, custom_uppercase=None):
    """
    Applies smart capitalization to a single word token.
    - custom_uppercase: set of lowercase words to force to UPPERCASE.
    """
    if not word:
        return word

    word_lower = word.lower()

    # 1. Custom uppercase overrides
    if custom_uppercase and word_lower in custom_uppercase:
        return word.upper()

    # 2. Part Number auto-detection
    has_letter = any(c.isalpha() for c in word)
    has_digit = any(c.isdigit() for c in word)
    if auto_detect_parts:
        if has_letter and has_digit and len(word) >= min_part_len:
            return word.upper()

    # 3. Compound words (hyphenated) processing
    if '-' in word:
        # If it wasn't caught as a part number, capitalize each component
        parts = word.split('-')
        formatted_parts = [
            format_word(p, min_part_len, auto_detect_parts, custom_uppercase)
            for p in parts
        ]
        return '-'.join(formatted_parts)

    # 4. Standard Title Case capitalization for alphabetic words
    if has_letter:
        return word[0].upper() + word[1:].lower()

    # 5. Fallback for numeric or symbol-only words
    return word


def apply_blacklist(original_text, processed_text, blacklist_set):
    """
    Restores any blacklisted words/phrases to their exact casing in the original text.
    """
    if not blacklist_set:
        return processed_text
        
    for term in blacklist_set:
        if not term:
            continue
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        original_matches = list(pattern.finditer(original_text))
        if not original_matches:
            continue
            
        processed_chars = list(processed_text)
        for match in original_matches:
            start, end = match.span()
            # Capitalization process preserves 1-to-1 character length and spacing layout
            processed_chars[start:end] = list(original_text[start:end])
        processed_text = "".join(processed_chars)
        
    return processed_text


def apply_whitelist(processed_text, whitelist_dict):
    """
    Replaces any case-insensitive matches of whitelisted terms with their exact whitelisted casing.
    whitelist_dict: dictionary mapping lowercase term -> exact whitelisted term (e.g. "iphone" -> "iPhone")
    """
    if not whitelist_dict:
        return processed_text
        
    for lower_term, exact_term in whitelist_dict.items():
        if not lower_term:
            continue
        pattern = re.compile(re.escape(lower_term), re.IGNORECASE)
        processed_text = pattern.sub(exact_term, processed_text)
        
    return processed_text


def capitalize_text(text, min_part_len=4, auto_detect_parts=True, custom_uppercase_list=None, whitelist_list=None, blacklist_list=None):
    """
    Splits text into words and delimiters, formats the words, applies whitelist/blacklist rules, and reconstructs the text.
    """
    if not text:
        return text

    # Pre-process custom list filters (convert to sets of lowercase words for O(1) checks)
    custom_uppercase = {w.strip().lower() for w in custom_uppercase_list if w.strip()} if custom_uppercase_list else set()

    # Split using word boundaries for alphanumeric, apostrophe, and hyphen sequences
    parts = re.split(r'(\b[a-zA-Z0-9\'-]+\b)', text)

    formatted_parts = []
    for part in parts:
        # Check if the part is a word token (contains alphanumeric/apostrophe/hyphen)
        if re.match(r'^[a-zA-Z0-9\'-]+$', part):
            formatted_parts.append(format_word(
                part,
                min_part_len=min_part_len,
                auto_detect_parts=auto_detect_parts,
                custom_uppercase=custom_uppercase
            ))
        else:
            formatted_parts.append(part)

    processed = "".join(formatted_parts)

    # Apply blacklist (restores matching terms to original casing)
    if blacklist_list:
        blacklist_set = {w.strip() for w in blacklist_list if w.strip()}
        processed = apply_blacklist(text, processed, blacklist_set)

    # Apply whitelist (forces matching terms to exact specified casing)
    if whitelist_list:
        whitelist_dict = {w.strip().lower(): w.strip() for w in whitelist_list if w.strip()}
        processed = apply_whitelist(processed, whitelist_dict)

    return processed
