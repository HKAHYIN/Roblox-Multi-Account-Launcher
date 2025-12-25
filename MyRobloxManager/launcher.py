import requests
import time
import subprocess
import os

class RobloxLauncher:
    def __init__(self, cookie, account_name=None):
        self.cookie = cookie
        # Account Name for saving cookie / 帳號名稱 (用於存檔)
        self.account_name = account_name 
        self.session = requests.Session()
        self.session.cookies['.ROBLOSECURITY'] = cookie
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.roblox.com/'
        }

    def _update_env_cookie(self, new_cookie):
        """ Write new cookie to .env file / 將新 Cookie 寫回 .env """
        if not self.account_name:
            return

        env_path = ".env"
        if not os.path.exists(env_path):
            return

        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            with open(env_path, "w", encoding="utf-8") as f:
                for line in lines:
                    # Find and replace the specific account line / 找到並替換對應帳號行
                    if line.startswith(f"{self.account_name}="):
                        f.write(f"{self.account_name}={new_cookie}\n")
                        print(f"[{self.account_name}] Cookie Refreshed & Saved!")
                    else:
                        f.write(line)
        except Exception as e:
            print(f"Failed to save new cookie: {e}")

    def _check_and_refresh_cookie(self, response):
        """ Check if response contains a new cookie / 檢查回應是否有新 Cookie """
        # Roblox sends new cookie in Set-Cookie header / Roblox 在 Header 回傳新 Cookie
        new_cookie = response.cookies.get(".ROBLOSECURITY")
        if new_cookie and new_cookie != self.cookie:
            self.cookie = new_cookie
            self._update_env_cookie(new_cookie)

    def _kill_mutex(self):
        tool = "handle64.exe"
        if not os.path.exists(tool):
            print("Error: handle64.exe not found.")
            return

        target_name = "ROBLOX_singletonEvent"
        print(f"Scanning for {target_name}...")
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # Run handle64 / 執行 handle64
            output_bytes = subprocess.check_output(
                [tool, "-a", "singleton", "-nobanner"], 
                startupinfo=startupinfo
            )
            output = output_bytes.decode('utf-8', errors='ignore')

            for line in output.splitlines():
                if target_name in line and "RobloxPlayerBeta.exe" in line:
                    parts = line.split()
                    
                    try:
                        # Extract PID / 抓取 PID
                        pid = parts[parts.index("pid:") + 1] if "pid:" in parts else None

                        # Extract Handle Hex / 抓取 Handle Hex
                        handle_hex = None
                        for part in parts:
                            if part.endswith(":") and part.lower() not in ["pid:", "type:"]:
                                current_idx = parts.index(part)
                                if current_idx + 1 < len(parts) and parts[current_idx + 1].startswith("\\"):
                                    handle_hex = part.replace(":", "")
                                    break
                        
                        if pid and handle_hex:
                            # Kill Handle / 殺掉 Handle
                            subprocess.run(
                                [tool, "-c", handle_hex, "-p", pid, "-y", "-nobanner"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                startupinfo=startupinfo
                            )
                            time.sleep(0.1)

                    except Exception as e:
                        print(f"Parse Error: {e}")

        except subprocess.CalledProcessError:
            pass # No lock found is normal / 沒找到鎖是正常的
        except Exception as e:
            print(f"Scan Failed: {e}")

    def _get_csrf_token(self):
        try:
            # Trigger request to check for new cookie / 發送請求以檢查新 Cookie
            response = self.session.post('https://auth.roblox.com/v2/logout', headers=self.headers)
            
            # Check for refresh / 檢查刷新
            self._check_and_refresh_cookie(response)
            
            if 'x-csrf-token' in response.headers:
                return response.headers['x-csrf-token']
        except:
            pass
        return None

    def launch_game(self, place_id):
        # Kill lock before launch / 啟動前殺鎖
        self._kill_mutex()
        
        csrf = self._get_csrf_token()
        if not csrf:
            return "Error: Invalid Cookie"

        self.headers['X-CSRF-TOKEN'] = csrf
        self.headers['Origin'] = 'https://www.roblox.com'
        
        try:
            auth_url = "https://auth.roblox.com/v1/authentication-ticket"
            post_data = {"gameId": "12345"}
            resp = self.session.post(auth_url, headers=self.headers, json=post_data)
            
            # Check for refresh again / 再次檢查刷新
            self._check_and_refresh_cookie(resp)
            
            ticket = resp.headers.get('rbx-authentication-ticket')
            
            if not ticket:
                return f"Error: No Ticket ({resp.status_code})"

            browser_tracker_id = int(time.time() * 1000)
            launch_url = (
                f"roblox-player:1+launchmode:play+gameinfo:{ticket}"
                f"+launchtime:{browser_tracker_id}+placelauncherurl:"
                f"https%3A%2F%2Fassetgame.roblox.com%2Fgame%2FPlaceLauncher.ashx%3Frequest%3DRequestGame%26browserTrackerId%3D{browser_tracker_id}%26placeId%3D{place_id}%26isPlayTogetherGame%3Dfalse"
                f"+browsertrackerid:{browser_tracker_id}+robloxLocale:en_us+gameLocale:en_us+channel:"
            )
            
            print(f"Launching to ID: {place_id}...")
            subprocess.Popen(['start', launch_url], shell=True)

            # Wait 3s and kill again / 等待 3 秒再殺一次
            time.sleep(3)
            self._kill_mutex()
            
            return "Launch Command Sent"
            
        except Exception as e:
            return f"Exception: {e}"
