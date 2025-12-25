# Roblox Multi Account Launcher (Python)

A simple, Python-based tool to manage multiple Roblox accounts and launch them simultaneously on a single PC.

---

### ⚠️ Disclaimer
This tool is for **educational and personal use only**. It interacts with the Roblox client using standard launch protocols. Use at your own risk.

---

### ✨ Features
*   **Multi-Instance Support**: Automatically bypasses the Roblox singleton lock (using `handle64.exe`) to allow multiple windows.
*   **Account Management**: Securely load accounts from a local `.env` file.
*   **Batch Launch**: Launch all accounts sequentially with a single click.
*   **Modern GUI**: Built with `customtkinter` for a clean dark-mode interface.

---

### 🛠️ Setup Guide

#### 1. Prerequisites (optional)
*   Python 3.8+ installed.
*   **handle64.exe** (Required for multi-instance):
    1.  Download from [Microsoft Sysinternals](https://learn.microsoft.com/en-us/sysinternals/downloads/handle).
    2.  Extract `handle64.exe` and place it in this project folder.

#### 2. Install Dependencies
Open your terminal in the project folder and run: pip install requests customtkinter python-dotenv

#### 3. Configure Accounts
1.  Rename `env.example` to `.env`.
2.  Open `.env` and paste your Roblox cookies (Format: `Name=Cookie`).
    *   Use an Incognito window to get cookies without logging out your main browser.*

#### 4. Run
**Important**: You must run the script as **Administrator** for in terminal to work properly.
**py main.py**


---

### 🔧 How It Works

1.  **Launch**: The app requests an Authentication Ticket from Roblox API using your stored cookie.
2.  **Protocol**: It constructs a `roblox-player:` URL with the ticket and launches it.
3.  **Bypass**:
    *   Before and after launching, it calls `handle64.exe` to scan for specific mutex/event handles (`ROBLOX_singletonEvent`).
    *   It forcibly closes these handles, tricking Roblox into thinking it's the first instance running.

---

### 🔒 Safety & Privacy
*   **Credentials**: Your cookies are stored locally in `.env`
*   **Open Source**: The code is fully transparent and does not communicate with any third-party servers.
