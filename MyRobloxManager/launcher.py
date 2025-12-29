#  Copyright (C) 2025
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License v3.
#
#  Multi-Instance Logic inspired by evanovar (https://github.com/evanovar/RobloxAccountManager)

import os
import time
import requests
import win32event
import win32api
import msvcrt
import random

class RobloxLauncher:
    def __init__(self):
        self.multi_roblox_mutex = None
        self.cookie_file_handle = None
        # Initialize Multi-Instance lock
        self._enable_multi_roblox()

    def _enable_multi_roblox(self):
        """
        Hey fellow developers
        I know you may be trying to figure out how to handle problem for multi-instance launching, like what I have done before.
        Here's a brief breakdown of it. 

        1. We grab and hold the "ROBLOX_singletonEvent" mutex BEFORE Roblox can create it
           → When Roblox starts, it sees the mutex already exists
        2. We lock the RobloxCookies.dat file so no instance can write to it
           → Prevents the file from getting corrupted when multiple instances
        """
        try:
            self.multi_roblox_mutex = win32event.CreateMutex(None, True, "ROBLOX_singletonEvent")
            if win32api.GetLastError() == 183: pass 
            
            cookies_path = os.path.join(os.getenv('LOCALAPPDATA'), r'Roblox\LocalStorage\RobloxCookies.dat')
            if os.path.exists(cookies_path):
                self.cookie_file_handle = open(cookies_path, 'r+b')
                msvcrt.locking(self.cookie_file_handle.fileno(), msvcrt.LK_NBLCK, os.path.getsize(cookies_path))
        except: pass

    def _get_csrf_token(self, session):
        try:
            return session.post("https://auth.roblox.com/v2/logout").headers.get('x-csrf-token')
        except: return None

    def _get_auth_ticket(self, session, csrf_token):
        url = "https://auth.roblox.com/v1/authentication-ticket/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.roblox.com/",
            "Origin": "https://www.roblox.com",
            "Content-Type": "application/json",
            "RBX-For-Gameauth": "true",
            "X-CSRF-TOKEN": csrf_token
        }
        try:
            response = session.post(url, headers=headers, json={}) 
            
            if "rbx-authentication-ticket" not in response.headers:
                print(f"Ticket Error: {response.status_code} - {response.text}")
                return None
                
            return response.headers.get("rbx-authentication-ticket")
        except Exception as e:
            print(f"Ticket Exception: {e}")
            return None

    def _get_user_id(self, username):
        try:
            r = requests.post("https://users.roblox.com/v1/usernames/users", 
                              json={"usernames": [username], "excludeBannedUsers": True})
            return r.json()['data'][0]['id']
        except: return None

    def launch_account(self, cookie, input_value, mode="place"):
        session = requests.Session()
        session.cookies['.ROBLOSECURITY'] = cookie
        session.headers.update({"User-Agent": "Roblox/WinInet"})

        try:
            csrf = self._get_csrf_token(session)
            if not csrf: return "Invalid Cookie"
            
            ticket = self._get_auth_ticket(session, csrf)
            if not ticket: return "Ticket Failed"

            launch_time = int(time.time() * 1000)
            browser_id = random.randint(10000000000, 99999999999)
            final_launcher_url = ""

            if mode == "user":
                uid = self._get_user_id(input_value)
                if not uid: return "User Not Found"
                params = f"request=RequestFollowUser&browserTrackerId={browser_id}&userId={uid}&isPlayTogetherGame=false"
                final_launcher_url = f"https://assetgame.roblox.com/game/PlaceLauncher.ashx?{params}"
            else: # Standard Place
                params = f"request=RequestGame&browserTrackerId={browser_id}&placeId={input_value}&isPlayTogetherGame=false"
                final_launcher_url = f"https://assetgame.roblox.com/game/PlaceLauncher.ashx?{params}"

            # Construct Protocol String
            protocol = (
                f"roblox-player:1+launchmode:play+gameinfo:{ticket}"
                f"+launchtime:{launch_time}"
                f"+placelauncherurl:{final_launcher_url}"
                f"+browsertrackerid:{browser_id}"
                f"+robloxLocale:en_us+gameLocale:en_us"
            )
            
            os.startfile(protocol)
            return "Launched"

        except Exception as e:
            return f"Error: {e}"
