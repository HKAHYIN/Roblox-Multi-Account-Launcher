import requests
import time
import subprocess
import os

class RobloxLauncher:
    def __init__(self, cookie):
        self.cookie = cookie
        self.session = requests.Session()
        self.session.cookies['.ROBLOSECURITY'] = cookie
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.roblox.com/'
        }

    def _kill_mutex(self):
        """
        Use handle64.exe to kill the Roblox singleton mutex/event.
        使用 handle64.exe 強制關閉 Roblox 的單例互斥鎖/事件。
        """
        tool = "handle64.exe"
        if not os.path.exists(tool):
            print("Error: handle64.exe not found. / 錯誤: 找不到 handle64.exe")
            return

        # Target handle name
        # 目標 Handle 名稱
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
            # Decode using utf-8 / 使用 utf-8 解碼
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
                                # Check if next part is a path / 檢查下一個部分是否為路徑
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
                        print(f"Parse Error / 解析錯誤: {e}")

        except subprocess.CalledProcessError:
            pass # No lock found is normal / 沒找到鎖是正常的
        except Exception as e:
            print(f"Scan Failed / 掃描失敗: {e}")

    def _get_csrf_token(self):
        try:
            # Send logout request to get CSRF token
            # 發送請求獲取 CSRF Token
            response = self.session.post('https://auth.roblox.com/v2/logout', headers=self.headers)
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
            return "Error: Invalid Cookie / 錯誤: Cookie 無效"

        self.headers['X-CSRF-TOKEN'] = csrf
        self.headers['Origin'] = 'https://www.roblox.com'
        
        try:
            auth_url = "https://auth.roblox.com/v1/authentication-ticket"
            post_data = {"gameId": "12345"}
            resp = self.session.post(auth_url, headers=self.headers, json=post_data)
            ticket = resp.headers.get('rbx-authentication-ticket')
            
            if not ticket:
                return f"Error: No Ticket / 錯誤: 無票券 ({resp.status_code})"

            browser_tracker_id = int(time.time() * 1000)
            launch_url = (
                f"roblox-player:1+launchmode:play+gameinfo:{ticket}"
                f"+launchtime:{browser_tracker_id}+placelauncherurl:"
                f"https%3A%2F%2Fassetgame.roblox.com%2Fgame%2FPlaceLauncher.ashx%3Frequest%3DRequestGame%26browserTrackerId%3D{browser_tracker_id}%26placeId%3D{place_id}%26isPlayTogetherGame%3Dfalse"
                f"+browsertrackerid:{browser_tracker_id}+robloxLocale:en_us+gameLocale:en_us+channel:"
            )
            
            print(f"Launching to ID: {place_id}...")
            subprocess.Popen(['start', launch_url], shell=True)

            # Wait 3s and kill again to ensure multi-instance works
            # 啟動後等待 3 秒再殺一次，確保多開功能正常
            time.sleep(3)
            self._kill_mutex()
            
            return "Launch Command Sent / 啟動指令已發送"
            
        except Exception as e:
            return f"Exception / 例外: {e}"
