import customtkinter as ctk
import threading
import time
from tkinter import messagebox, simpledialog
from auth_manager import AuthManager
from launcher import RobloxLauncher

ctk.set_appearance_mode("Dark")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Roblox Manager Pro")
        self.geometry("850x600")
        
        self.auth = AuthManager()
        
        # --- Authentication Check ---
        if self.auth.state == "SETUP_REQUIRED":
            self.show_setup_dialog()
        elif self.auth.state == "LOCKED":
            self.show_unlock_dialog()
            
        if self.auth.state != "READY":
            self.destroy()
            return

        # --- Main App ---
        self.launcher = RobloxLauncher()
        self.build_ui()

    def show_setup_dialog(self):
        """Ask new user about encryption."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Security Setup")
        dialog.geometry("400x300")
        dialog.attributes("-topmost", True)
        
        # Modal blocking
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Welcome!", font=("Arial", 20, "bold")).pack(pady=10)
        ctk.CTkLabel(dialog, text="Do you want to encrypt your account data?\nThis requires a password to open the app.", 
                     wraplength=350).pack(pady=10)

        def enable_enc():
            pwd = ctk.CTkInputDialog(text="Create a Password:", title="Set Password").get_input()
            if pwd:
                self.auth.setup_new(password=pwd)
                dialog.destroy()
            else:
                pass # User cancelled password input

        def disable_enc():
            self.auth.setup_new(password=None)
            dialog.destroy()

        ctk.CTkButton(dialog, text="Enable Encryption (Recommended)", fg_color="green", command=enable_enc).pack(pady=10)
        ctk.CTkButton(dialog, text="No Encryption (Plain Text)", fg_color="gray", command=disable_enc).pack(pady=10)
        
        self.wait_window(dialog)

    def show_unlock_dialog(self):
        """Ask for password."""
        while True:
            pwd = ctk.CTkInputDialog(text="Enter Password to Unlock:", title="Encrypted Storage").get_input()
            if pwd is None: # Cancelled
                self.auth.state = "EXIT"
                break
            
            if self.auth.unlock(pwd):
                break
            else:
                messagebox.showerror("Error", "Wrong Password!")

    def build_ui(self):
        # Top Bar
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(fill="x", padx=10, pady=10)
        
        # Input Mode
        self.mode_var = ctk.StringVar(value="place")
        ctk.CTkRadioButton(self.top_frame, text="Place ID", variable=self.mode_var, value="place").pack(side="left", padx=5)
        ctk.CTkRadioButton(self.top_frame, text="Username", variable=self.mode_var, value="user").pack(side="left", padx=5)
        
        self.input_entry = ctk.CTkEntry(self.top_frame, placeholder_text="ID or Username", width=200)
        self.input_entry.insert(0, "116405044285330")
        self.input_entry.pack(side="left", padx=10)
        
        # Buttons
        ctk.CTkButton(self.top_frame, text="Add Account", command=self.start_add_account).pack(side="right", padx=5)
        ctk.CTkButton(self.top_frame, text="Launch All", fg_color="green", command=self.launch_all).pack(side="right", padx=5)

        # List
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Your Accounts")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.status_lbl = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_lbl.pack(pady=5)
        
        self.refresh_list()

    def refresh_list(self):
        for w in self.scroll.winfo_children(): w.destroy()
            
        if not self.auth.accounts:
            ctk.CTkLabel(self.scroll, text="No accounts.").pack(pady=20)
            return

        for name, data in self.auth.accounts.items():
            row = ctk.CTkFrame(self.scroll)
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=name, font=("Arial", 14, "bold"), width=150, anchor="w").pack(side="left", padx=10)
            ctk.CTkButton(row, text="X", width=40, fg_color="#FF5555", hover_color="#CC0000",
                          command=lambda n=name: self.confirm_delete(n)).pack(side="right", padx=5)
            ctk.CTkButton(row, text="Launch", width=80, 
                          command=lambda c=data['cookie']: self.launch_one(c)).pack(side="right", padx=5)

    def confirm_delete(self, name):
        if messagebox.askyesno("Delete", f"Remove {name}?"):
            self.auth.delete_account(name)
            self.refresh_list()

    def start_add_account(self):
        self.status_lbl.configure(text="Login in browser...", text_color="yellow")
        threading.Thread(target=self._add_account_thread).start()
        
    def _add_account_thread(self):
        res = self.auth.add_account_via_browser()
        self.status_lbl.configure(text=res, text_color="white")
        self.after(0, self.refresh_list)

    def launch_one(self, cookie):
        val = self.input_entry.get()
        mode = self.mode_var.get()
        threading.Thread(target=lambda: self.status_lbl.configure(text=self.launcher.launch_account(cookie, val, mode))).start()

    def launch_all(self):
        val = self.input_entry.get()
        mode = self.mode_var.get()
        def _run():
            for name, data in self.auth.accounts.items():
                self.launcher.launch_account(data['cookie'], val, mode)
                time.sleep(6)
            self.status_lbl.configure(text="All Launched")
        threading.Thread(target=_run).start()

if __name__ == "__main__":
    app = App()
    try:
        app.mainloop()
    except Exception:
        pass
