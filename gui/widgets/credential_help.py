"""OnlyFans Credential Help Dialog

Provides guidance on extracting OF credentials from browser
"""

import customtkinter as ctk
import tkinter as tk


def show_of_credential_guide(parent):
    """Show OF credential extraction guide dialog"""

    dialog = ctk.CTkToplevel(parent)
    dialog.title("How to Get OnlyFans Credentials")
    dialog.geometry("750x650")
    dialog.grab_set()  # Make modal

    # Title
    title = ctk.CTkLabel(
        dialog,
        text="OnlyFans Credential Extraction Guide",
        font=("Arial", 18, "bold")
    )
    title.pack(pady=15)

    # Create scrollable frame
    scroll_frame = ctk.CTkScrollableFrame(dialog, width=700, height=500)
    scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Guide text
    guide_text = """
You need to extract 5 values from your browser while logged into OnlyFans:

1. Session Cookie (sess)
2. Auth ID (auth_id)
3. Auth UID (auth_uid_) - Only if you have 2FA enabled
4. User Agent
5. X-BC Token

═══════════════════════════════════════════════════════════

METHOD: Using Browser Developer Tools

Step 1: Open OnlyFans
  • Go to onlyfans.com and log in
  • Navigate to your notifications or any page

Step 2: Open Developer Tools
  • Windows/Linux: Press Ctrl + Shift + I
  • Mac: Press Cmd + Option + I

Step 3: Go to Network Tab
  1. Click "Network" tab in developer tools
  2. Click "XHR" or "Fetch/XHR" sub-tab
  3. Refresh the page (F5 or Cmd+R)

Step 4: Find Request
  • Look for a request to "init" or any "onlyfans.com" request
  • Click on it to see details

Step 5: Extract Values

In the "Headers" section, find "Request Headers":

  Cookie:
    • Look for: sess=XXXXX;
      Copy the value after "sess=" (before the semicolon)

    • Look for: auth_id=XXXXX;
      Copy the value after "auth_id="

    • Look for: auth_uid_=XXXXX; (only if 2FA enabled)
      Copy the value after "auth_uid_="

  User-Agent:
    • Copy the entire value (long string like "Mozilla/5.0...")

  x-bc:
    • Copy the entire value

═══════════════════════════════════════════════════════════

EXAMPLE:

Cookie: sess=1234567890abcdef; auth_id=98765432; auth_uid_=11111111
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...
x-bc: abc123def456

═══════════════════════════════════════════════════════════

IMPORTANT NOTES:

⚠  Keep these private! Anyone with these can access your account
⚠  Credentials expire when you log out or after some time
⚠  If you change your password, extract new credentials
⚠  Copy the ENTIRE value (user-agent is very long)

═══════════════════════════════════════════════════════════

TROUBLESHOOTING:

"Authentication failed"
  • Check you copied full values (no spaces at start/end)
  • Make sure you're logged into OnlyFans
  • Try extracting credentials again
  • Check if cookies expired

"Can't find x-bc header"
  • Make sure you're looking at a request to onlyfans.com
  • Try refreshing and checking a different request
  • Header name might be capitalized: "X-BC"

═══════════════════════════════════════════════════════════

Adapted from OF-Scraper documentation
https://github.com/Frangus90/OF-Scraper
    """

    # Add text widget
    text_widget = ctk.CTkTextbox(
        scroll_frame,
        width=680,
        height=600,
        font=("Courier New", 10),
        wrap="word"
    )
    text_widget.pack(fill="both", expand=True, padx=5, pady=5)
    text_widget.insert("1.0", guide_text)
    text_widget.configure(state="disabled")

    # Close button
    ctk.CTkButton(
        dialog,
        text="Close",
        command=dialog.destroy,
        width=200,
        height=35,
        font=("Arial", 12)
    ).pack(pady=10)
