import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from security import Security

class AuthManager:
    def __init__(self):
        self.accounts_file = "accounts.json"
        self.accounts = {}
        self.is_encrypted = False
        self.password = None
        self.state = "UNLOADED" # UNLOADED, LOCKED, READY, SETUP_REQUIRED

        self.check_status()

    def check_status(self):
        """Checks if file exists and if it is encrypted."""
        if not os.path.exists(self.accounts_file):
            self.state = "SETUP_REQUIRED"
            return

        try:
            with open(self.accounts_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if data.get("is_encrypted"):
                self.is_encrypted = True
                self.state = "LOCKED"
                self.encrypted_blob = data
            else:
                self.is_encrypted = False
                self.accounts = data
                self.state = "READY"
        except:
            self.state = "SETUP_REQUIRED"

    def unlock(self, password):
        """Attempts to decrypt the accounts."""
        try:
            self.accounts = Security.decrypt(self.encrypted_blob, password)
            self.password = password
            self.state = "READY"
            return True
        except Exception as e:
            print(f"Decryption failed: {e}")
            return False

    def setup_new(self, password=None):
        """Initializes empty file, optionally encrypted."""
        self.accounts = {}
        if password:
            self.is_encrypted = True
            self.password = password
        else:
            self.is_encrypted = False
            self.password = None
        self.state = "READY"
        self.save_accounts()

    def save_accounts(self):
        """Saves accounts, encrypting them if a password is set."""
        if self.is_encrypted and self.password:
            # Encrypt
            json_str = json.dumps(self.accounts) 
            salt = Security.generate_salt()
            key = Security.derive_key(self.password, salt)
            from cryptography.fernet import Fernet
            f = Fernet(key)
            token = f.encrypt(json_str.encode())
            
            save_data = {
                "is_encrypted": True,
                "salt": import_base64(salt),
                "data": token.decode('utf-8')
            }
        else:
            # Plain text
            save_data = self.accounts

        with open(self.accounts_file, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False)

    def delete_account(self, username: str) -> bool:
        if username in self.accounts:
            del self.accounts[username]
            self.save_accounts()
            return True
        return False

    def add_account_via_browser(self, timeout_seconds=120):
        """Opens browser to login and captures cookie."""
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = None
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get("https://www.roblox.com/login")

            start_time = time.time()
            cookie_value = None

            while time.time() - start_time < timeout_seconds:
                try:
                    current_url = driver.current_url.lower()
                except: break

                if any(p in current_url for p in ['/home', '/games', '/discover', '/users']):
                    time.sleep(1.0)
                    cookies = driver.get_cookies()
                    for cookie in cookies:
                        if cookie.get('name') == '.ROBLOSECURITY':
                            cookie_value = cookie.get('value')
                            break
                    if cookie_value: break
                time.sleep(0.5)

            if not cookie_value:
                if driver: driver.quit()
                return "Error: Login timeout."

            # Get Username
            username = None
            try:
                elem = driver.find_element(By.CSS_SELECTOR, '[data-testid="navigation-username"], .navigation-user-name')
                username = elem.text.strip()
            except: pass

            if not username:
                try:
                    response = driver.execute_async_script("""
                        var callback = arguments[arguments.length - 1];
                        fetch('https://www.roblox.com/my/settings/json', {credentials: 'include'})
                        .then(r => r.json()).then(data => callback(data.Name)).catch(() => callback(null));
                    """)
                    if response: username = str(response)
                except: pass

            if not username: username = "Unknown_" + str(int(time.time()))[-4:]

            self.accounts[username] = {
                "cookie": cookie_value,
                "added_at": time.time()
            }
            self.save_accounts()
            driver.quit()
            return f"Success: Added {username}"

        except Exception as e:
            if driver: 
                try: driver.quit()
                except: pass
            return f"Error: {str(e)}"

def import_base64(b):
    import base64
    return base64.b64encode(b).decode('utf-8')
