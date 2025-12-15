"""
Shared logging utilities for GUI event handlers
"""

import re


def classify_log_message(message: str, level: str) -> tuple[str, str]:
    """Classify log message and extract context for status display.

    Args:
        message: The log message text
        level: Log level (info, warning, error, etc.)

    Returns:
        (category, status_text) tuple
        category: "rate_limit", "server_error", "end_content", "mode_info", "generic"
        status_text: Concise text for status label, or empty string
    """
    # Rate limiting detection
    if "Rate limited" in message or "HTTP 429" in message:
        # Extract retry info: "retry attempt 2/5"
        match = re.search(r'attempt (\d+)/(\d+)', message)
        if match:
            return ("rate_limit", f"Rate limited - retry {match.group(1)}/{match.group(2)}")
        return ("rate_limit", "Rate limited - retrying")

    # Server error detection
    if "Server error" in message:
        match = re.search(r'Server error (\d+)', message)
        if match:
            return ("server_error", f"Server error {match.group(1)} - retrying")
        return ("server_error", "Server error - retrying")

    # End of content detection
    if any(phrase in message for phrase in [
        "Reached end", "No posts in timeline", "Next cursor is None"
    ]):
        return ("end_content", "Reached end of timeline")

    # Mode information
    if "Incremental mode" in message:
        return ("mode_info", "Incremental mode active")

    if "Post limit enabled" in message:
        match = re.search(r'up to (\d+)', message)
        if match:
            return ("mode_info", f"Post limit: {match.group(1)} posts")
        return ("mode_info", "Post limit active")

    return ("generic", "")


def update_status_with_context(status_label, context: str, platform_prefix: str = "Status"):
    """Update status label with operational context.

    Args:
        status_label: The CTk label widget to update
        context: Context text to append (e.g., "Rate limited - retry 2/5")
        platform_prefix: Prefix for status text (e.g., "Status" or "OnlyFans")
    """
    current = status_label.cget("text")

    # Determine base status
    if "Downloading" in current:
        base = f"{platform_prefix}: Downloading..."
    elif "Complete" in current:
        base = f"{platform_prefix}: Complete"
    elif "Stopped" in current:
        base = f"{platform_prefix}: Stopped"
    else:
        base = current

    # Append context
    new_status = f"{base} ({context})"
    status_label.configure(text=new_status)


def update_log_button_badge(
    log_button,
    unread_warnings: int,
    unread_errors: int,
    is_visible: bool
):
    """Update log button text and color based on unread messages.

    Args:
        log_button: The CTk button widget to update
        unread_warnings: Number of unread warning messages
        unread_errors: Number of unread error messages
        is_visible: Whether the log window is currently visible
    """
    total_unread = unread_warnings + unread_errors
    base_text = "Hide Log" if is_visible else "Show Log"

    if total_unread == 0:
        # No badge - use default
        log_button.configure(text=base_text, fg_color=["#3B8ED0", "#1F6AA5"])
    else:
        # Show badge with count
        badge_text = f"{base_text} ({total_unread})"

        # Color: Red for errors, orange for warnings only
        if unread_errors > 0:
            color = ["#DC3545", "#C82333"]  # Red
        else:
            color = ["#FD7E14", "#E8590C"]  # Orange

        log_button.configure(text=badge_text, fg_color=color)
