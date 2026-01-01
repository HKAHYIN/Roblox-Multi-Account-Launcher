# Copyright (C) 2025
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License v3.

# Multi-Instance Logic inspired by evanovar (https://github.com/evanovar/RobloxAccountManager)

import os
import time
import requests
import win32event
import win32api
import msvcrt
import random
import logging
import traceback

class RobloxLauncher:
    def __init__(self):
        self.multi_roblox_mutex = None
        self.mutex_global = None
        self.cookie_file_handle = None
        
        logging.info("RobloxLauncher initialized.")
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
        logging.info("Enabling Multi-Instance Mode...")

        # Mutex Handling (Global + Local)
        try:
            # Try Global Mutex first
            self.mutex_global = win32event.CreateMutex(None, True, r"Global\ROBLOX_singletonEvent")
            if win32api.GetLastError() == 183: 
                logging.warning("Global Mutex already exists.")
            else:
                logging.info("Global Mutex created successfully.")
        except Exception as e:
            logging.debug(f"Could not create Global Mutex (Normal if not Admin): {e}")

        try:
            # create Local Mutex as fallback
            self.multi_roblox_mutex = win32event.CreateMutex(None, True, "ROBLOX_singletonEvent")
            if win32api.GetLastError() == 183:
                logging.warning("Local Mutex already exists.")
            else:
                logging.info("Local Mutex created successfully.")
        except Exception as e:
            logging.error(f"Failed to create Local Mutex: {e}")

        # Cookie File Locking
        try:
            base_local = os.getenv('LOCALAPPDATA')
            if not base_local: return

            possible_paths = [
                os.path.join(base_local, r'Roblox\LocalStorage\RobloxCookies.dat'),
                os.path.join(base_local, r'Packages\ROBLOXCORPORATION.ROBLOX_55nm5eh3cm0pr\LocalState\RobloxCookies.dat'),
            ]

            target_path = None
            for p in possible_paths:
                if os.path.exists(p):
                    target_path = p
                    break
            
            if target_path:
                logging.info(f"Found Cookie file at: {target_path}")
                self.cookie_file_handle = open(target_path, 'r+b')
                msvcrt.locking(self.cookie_file_handle.fileno(), msvcrt.LK_NBLCK, os.path.getsize(target_path))
                logging.info("Cookie file locked successfully.")
            else:
                logging.warning("No RobloxCookies.dat found. Skipping lock.")

        except OSError as e:
            logging.warning(f"Cookie file already locked/in-use: {e}")
        except Exception as e:
            logging.error(f"Error locking cookie file: {e}")

    def _get_csrf_token(self, session):
        try:
            response = session.post("https://auth.roblox.com/v2/logout")
            token = response.headers.get('x-csrf-token')
            if not token:
                logging.error(f"Failed to get CSRF. Status: {response.status_code}")
                return None
            return token
        except Exception as e:
            logging.error(f"Exception getting CSRF: {e}")
            return None

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
                logging.error(f"Ticket fetch failed. Status: {response.status_code}")
                return None
            return response.headers.get("rbx-authentication-ticket")
        except Exception as e:
            logging.error(f"Ticket exception: {e}")
            return None

    def _get_user_id(self, username):
        try:
            r = requests.post("https://users.roblox.com/v1/usernames/users",
                              json={"usernames": [username], "excludeBannedUsers": True})
            data = r.json().get('data', [])
            if data: return data[0]['id']
            return None
        except Exception: return None

    def launch_account(self, cookie, input_value, mode="place"):
        session = requests.Session()
        session.cookies['.ROBLOSECURITY'] = cookie
        session.headers.update({"User-Agent": "Roblox/WinInet"})

        try:
            logging.info(f"Preparing launch... Mode: {mode}, Target: {input_value}")
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

            protocol = (
                f"roblox-player:1+launchmode:play+gameinfo:{ticket}"
                f"+launchtime:{launch_time}"
                f"+placelauncherurl:{final_launcher_url}"
                f"+browsertrackerid:{browser_id}"
                f"+robloxLocale:en_us+gameLocale:en_us"
            )

            logging.info("Executing protocol...")
            os.startfile(protocol)
            return "Launched"

        except Exception as e:
            logging.error(f"Launch Error: {e}")
            logging.debug(traceback.format_exc())
            return f"Error: {e}"
