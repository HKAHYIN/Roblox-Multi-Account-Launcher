import customtkinter as ctk
import os
import threading
import time
from dotenv import load_dotenv
from launcher import RobloxLauncher

# Set UI Theme / 設定介面主題
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Load accounts from .env / 載入 .env 檔案中的帳號
        load_dotenv()
        self.accounts = {k: v for k, v in os.environ.items() if v.startswith("_|WARNING")}
        
        self.title("Roblox Multi-Launcher")
        # Modify window size / 加寬視窗尺寸
        self.geometry("700x500")
        
        # Title Label / 標題標籤
        self.label = ctk.CTkLabel(self, text="Roblox Account Manager", font=("Arial", 22, "bold"))
        self.label.pack(pady=15)

        # Place ID Input Frame / Place ID 輸入框區域
        self.id_frame = ctk.CTkFrame(self)
        self.id_frame.pack(pady=10, padx=20, fill="x")
        
        self.id_label = ctk.CTkLabel(self.id_frame, text="Place ID:")
        self.id_label.pack(side="left", padx=10)
        
        self.place_id_entry = ctk.CTkEntry(self.id_frame, placeholder_text="Game ID")
        self.place_id_entry.insert(0, "116405044285330") 
        self.place_id_entry.pack(side="left", fill="x", expand=True, padx=10, pady=5)

        # Launch All Button / 啟動全部按鈕
        self.launch_all_btn = ctk.CTkButton(
            self.id_frame, 
            text="Launch All", 
            fg_color="green", 
            hover_color="darkgreen",
            width=100,
            command=self.launch_all_thread
        )
        self.launch_all_btn.pack(side="right", padx=10, pady=5)

        # Account List / 帳號列表
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Accounts")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Status Label / 狀態標籤
        self.status_label = ctk.CTkLabel(
            self, 
            text="Ready", 
            text_color="gray",
            wraplength=600
        )
        self.status_label.pack(pady=10)

        self.create_buttons()
        self.is_launching_all = False

    def create_buttons(self):
        if not self.accounts:
            ctk.CTkLabel(self.scroll, text="No accounts found in .env").pack(pady=20)
            return

        for name, cookie in self.accounts.items():
            btn_frame = ctk.CTkFrame(self.scroll)
            btn_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(btn_frame, text=name, font=("Arial", 14)).pack(side="left", padx=15)
            
            ctk.CTkButton(
                btn_frame, 
                text="Launch", 
                width=80, 
                command=lambda c=cookie, n=name: self.launch_thread(c, n)
            ).pack(side="right", padx=10, pady=8)

    def launch_thread(self, cookie, name):
        place_id = self.place_id_entry.get()
        if not place_id.isdigit():
            self.status_label.configure(text="Invalid ID", text_color="red")
            return
            
        self.status_label.configure(text=f"Launching {name}...", text_color="yellow")
        threading.Thread(target=self.do_launch, args=(cookie, place_id, name)).start()

    def do_launch(self, cookie, place_id, name):
        # Initialize launcher
        # 初始化啟動器
        launcher = RobloxLauncher(cookie)
        result = launcher.launch_game(place_id)
        
        color = "green" if "Launch Command Sent" in result or "Success" in result else "red"
        self.status_label.configure(text=f"[{name}]: {result}", text_color=color)

    # Multi Launch Logic / 批量啟動邏輯
    def launch_all_thread(self):
        if self.is_launching_all:
            return
        
        place_id = self.place_id_entry.get()
        if not place_id.isdigit():
            self.status_label.configure(text="Invalid ID", text_color="red")
            return

        self.is_launching_all = True
        self.launch_all_btn.configure(state="disabled", text="Running...")
        
        threading.Thread(target=self.do_launch_all, args=(place_id,)).start()

    def do_launch_all(self, place_id):
        total = len(self.accounts)
        current = 0
        
        for name, cookie in self.accounts.items():
            current += 1
            self.status_label.configure(text=f"Batch Launching ({current}/{total}): {name}...", text_color="cyan")
            
            # Launch single account / 啟動單個帳號
            self.do_launch(cookie, place_id, name)
            
            if current < total:
                # Wait 10s between accounts / 每個帳號之間等待 10 秒
                wait_time = 10
                for i in range(wait_time, 0, -1):
                    self.status_label.configure(text=f"Waiting {i}s before next account...", text_color="orange")
                    time.sleep(1)
        
        self.status_label.configure(text="All accounts launched!", text_color="green")
        self.launch_all_btn.configure(state="normal", text="Launch All")
        self.is_launching_all = False

if __name__ == "__main__":
    app = App()
    app.mainloop()
