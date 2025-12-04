"""OnlyFans Authentication Section

OF-specific authentication widget with:
- Session cookie (sess)
- Auth ID
- Auth UID (2FA only)
- User Agent
- X-BC token
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox


class OnlyFansAuthSection(ctk.CTkFrame):
    """OnlyFans authentication credentials widget"""

    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        # Title
        title = ctk.CTkLabel(
            self,
            text="OnlyFans Authentication",
            font=("Arial", 16, "bold")
        )
        title.pack(pady=(10, 5))

        # Help button
        help_frame = ctk.CTkFrame(self)
        help_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            help_frame,
            text="How to get OF credentials?",
            command=self.show_credential_guide,
            width=200,
            fg_color="orange",
            hover_color="darkorange"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            help_frame,
            text="Test Connection",
            command=self.test_connection,
            width=150
        ).pack(side="left", padx=5)

        # Session cookie
        self.create_field("Session Cookie (sess):", "sess")

        # Auth ID
        self.create_field("Auth ID:", "auth_id")

        # Auth UID (optional)
        self.create_field("Auth UID (2FA only, optional):", "auth_uid")

        # User Agent
        self.create_field("User Agent:", "user_agent")

        # X-BC Token
        self.create_field("X-BC Token:", "x_bc")

        # Load values from config
        self.load_from_config()

    def create_field(self, label_text: str, field_name: str):
        """Create labeled entry field"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=10, pady=5)

        label = ctk.CTkLabel(
            frame,
            text=label_text,
            width=250,
            anchor="w"
        )
        label.pack(side="left", padx=5)

        # Store reference as attribute
        entry = ctk.CTkEntry(
            frame,
            width=400,
            show="*" if "cookie" in label_text.lower() or "token" in label_text.lower() else None
        )
        entry.pack(side="left", fill="x", expand=True, padx=5)

        # Bind to save on change
        entry.bind("<FocusOut>", lambda e: self.save_to_config())
        entry.bind("<Return>", lambda e: self.save_to_config())

        setattr(self, f"{field_name}_entry", entry)

    def load_from_config(self):
        """Load values from config"""
        if hasattr(self, 'sess_entry'):
            self.sess_entry.delete(0, tk.END)
            if self.config.sess:
                self.sess_entry.insert(0, self.config.sess)

        if hasattr(self, 'auth_id_entry'):
            self.auth_id_entry.delete(0, tk.END)
            if self.config.auth_id:
                self.auth_id_entry.insert(0, self.config.auth_id)

        if hasattr(self, 'auth_uid_entry'):
            self.auth_uid_entry.delete(0, tk.END)
            if self.config.auth_uid:
                self.auth_uid_entry.insert(0, self.config.auth_uid)

        if hasattr(self, 'user_agent_entry'):
            self.user_agent_entry.delete(0, tk.END)
            if self.config.user_agent:
                self.user_agent_entry.insert(0, self.config.user_agent)

        if hasattr(self, 'x_bc_entry'):
            self.x_bc_entry.delete(0, tk.END)
            if self.config.x_bc:
                self.x_bc_entry.insert(0, self.config.x_bc)

    def save_to_config(self):
        """Save values to config"""
        if hasattr(self, 'sess_entry'):
            self.config.sess = self.sess_entry.get().strip() or None

        if hasattr(self, 'auth_id_entry'):
            self.config.auth_id = self.auth_id_entry.get().strip() or None

        if hasattr(self, 'auth_uid_entry'):
            self.config.auth_uid = self.auth_uid_entry.get().strip() or None

        if hasattr(self, 'user_agent_entry'):
            self.config.user_agent = self.user_agent_entry.get().strip() or None

        if hasattr(self, 'x_bc_entry'):
            self.config.x_bc = self.x_bc_entry.get().strip() or None

        # Save to file
        self.config._save_config()

    def test_connection(self):
        """Test OF authentication"""
        # Save first
        self.save_to_config()

        if not self.config.has_credentials():
            messagebox.showerror(
                "Missing Credentials",
                "Please fill in all required fields (sess, auth_id, user_agent, x_bc)"
            )
            return

        try:
            from api.onlyfans_api import OnlyFansApi

            api = OnlyFansApi(
                sess=self.config.sess,
                auth_id=self.config.auth_id,
                auth_uid=self.config.auth_uid,
                user_agent=self.config.user_agent,
                x_bc=self.config.x_bc
            )

            # Test auth
            if api.test_auth():
                messagebox.showinfo("Success", "OnlyFans authentication successful!")
            else:
                messagebox.showerror("Error", "Authentication failed")

        except Exception as e:
            messagebox.showerror("Error", f"Authentication failed:\n{str(e)[:200]}")

    def show_credential_guide(self):
        """Show credential extraction guide"""
        from gui.widgets.credential_help import show_of_credential_guide
        show_of_credential_guide(self)
