import customtkinter as ctk
from auth_manager import AuthManager
from launcher import RobloxLauncher
import threading
from tkinter import messagebox
import time
import logging
import os
import sys

# 1. Determine the REAL folder where the .exe or script is located
if getattr(sys, 'frozen', False):
    # If running as compiled EXE
    application_path = os.path.dirname(sys.executable)
else:
    # If running as Python script
    application_path = os.path.dirname(os.path.abspath(__file__))

# 2. Set log file path to that real folder
log_file_path = os.path.join(application_path, 'debug.log')

logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    filemode='w',
    encoding='utf-8'
)

# SILENCE NOISY LIBRARIES
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("WDM").setLevel(logging.WARNING)

# Print location to console
print(f"DEBUG: Log file is being saved to: {log_file_path}")
logging.info(f"Application Started. Running in: {application_path}")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Roblox Multi-Instance Manager")
        self.geometry("600x500")
        
        logging.info("Initializing UI...")
        
        try:
            self.auth = AuthManager()
            self.launcher = RobloxLauncher()
        except Exception as e:
            logging.critical(f"Init Error: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to initialize: {e}")
            return

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Check Auth State (Password / Setup / Ready)
        self.check_auth_state()

    def check_auth_state(self):
        # Clear current frame
        for widget in self.main_container.winfo_children():
            widget.destroy()

        if self.auth.state == "LOCKED":
            self.show_password_screen()
        elif self.auth.state == "SETUP_REQUIRED":
            self.show_setup_screen()
        else:
            self.show_dashboard()

    # UI: PASSWORD SCREEN
    def show_password_screen(self):
        ctk.CTkLabel(self.main_container, text="Vault Locked", font=("Arial", 20)).pack(pady=20)
        
        self.pass_entry = ctk.CTkEntry(self.main_container, placeholder_text="Enter Password", show="*")
        self.pass_entry.pack(pady=10)
        
        ctk.CTkButton(self.main_container, text="Unlock", command=self.unlock_vault).pack(pady=10)

    def unlock_vault(self):
        pwd = self.pass_entry.get()
        if self.auth.unlock(pwd):
            self.check_auth_state() # Refresh to Dashboard
        else:
            messagebox.showerror("Error", "Invalid Password")

    # UI: SETUP SCREEN
    def show_setup_screen(self):
        ctk.CTkLabel(self.main_container, text="Welcome! Create a Password?", font=("Arial", 18)).pack(pady=20)
        
        self.new_pass = ctk.CTkEntry(self.main_container, placeholder_text="New Password (Optional)", show="*")
        self.new_pass.pack(pady=10)
        
        ctk.CTkButton(self.main_container, text="Initialize", command=self.do_setup).pack(pady=10)

    def do_setup(self):
        pwd = self.new_pass.get()
        self.auth.setup_new(pwd if pwd else None)
        self.check_auth_state()

    # UI: MAIN DASHBOARD
    def show_dashboard(self):
        self.label = ctk.CTkLabel(self.main_container, text="Roblox Account Manager", font=("Arial", 20, "bold"))
        self.label.pack(pady=10)

        self.status_lbl = ctk.CTkLabel(self.main_container, text="Status: Ready", text_color="green")
        self.status_lbl.pack(pady=5)

        # Input for Place ID / User ID
        self.input_entry = ctk.CTkEntry(self.main_container, placeholder_text="Place ID / Username")
        self.input_entry.pack(pady=5)
        self.input_entry.insert(0, "116405044285330") 

        # Mode Selection
        self.mode_var = ctk.StringVar(value="place")
        self.mode_switch = ctk.CTkSwitch(self.main_container, text="Username Mode", variable=self.mode_var, onvalue="user", offvalue="place")
        self.mode_switch.pack(pady=5)

        # Buttons
        self.add_btn = ctk.CTkButton(self.main_container, text="Add Account", command=self.add_account_thread)
        self.add_btn.pack(pady=5)

        self.launch_all_btn = ctk.CTkButton(self.main_container, text="Launch All", fg_color="red", command=self.launch_all)
        self.launch_all_btn.pack(pady=5)

        # Account List
        self.account_list = ctk.CTkScrollableFrame(self.main_container, height=200)
        self.account_list.pack(fill="x", pady=10)
        self.refresh_list()

    def refresh_list(self):
        for widget in self.account_list.winfo_children():
            widget.destroy()

        if not self.auth.accounts:
            ctk.CTkLabel(self.account_list, text="No accounts.").pack()
            return

        for username, data in self.auth.accounts.items():
            f = ctk.CTkFrame(self.account_list)
            f.pack(fill="x", pady=2)
            
            ctk.CTkLabel(f, text=username, width=100, anchor="w").pack(side="left", padx=5)
            
            ctk.CTkButton(f, text="Launch", width=60, 
                          command=lambda c=data['cookie']: self.launch_one(c)).pack(side="right", padx=5)
            
            ctk.CTkButton(f, text="X", width=30, fg_color="gray",
                          command=lambda u=username: self.delete_account(u)).pack(side="right", padx=2)

    def delete_account(self, username):
        if self.auth.delete_account(username):
            self.refresh_list()

    def add_account_thread(self):
        threading.Thread(target=self.add_account_logic, daemon=True).start()

    def add_account_logic(self):
        self.status_lbl.configure(text="Status: Browser Opening...", text_color="orange")
        result = self.auth.add_account_via_browser()
        self.status_lbl.configure(text=f"Status: {result}", text_color="white")
        self.after(0, self.refresh_list)

    def launch_one(self, cookie):
        val = self.input_entry.get()
        mode = self.mode_var.get()
        logging.info(f"Launching one. Mode: {mode}")
        threading.Thread(target=lambda: self.status_lbl.configure(text=self.launcher.launch_account(cookie, val, mode))).start()

    def launch_all(self):
        val = self.input_entry.get()
        mode = self.mode_var.get()
        logging.info("Launching ALL.")
        def _run():
            for name, data in self.auth.accounts.items():
                self.status_lbl.configure(text=f"Launching {name}...")
                self.launcher.launch_account(data['cookie'], val, mode)
                time.sleep(6)
            self.status_lbl.configure(text="All Launched")
        threading.Thread(target=_run).start()

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        logging.critical("App Crashed", exc_info=True)
