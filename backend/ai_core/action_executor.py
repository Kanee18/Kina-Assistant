# backend/ai_core/action_executor.py

import subprocess
import sys
import webbrowser
import os
import json
from dotenv import load_dotenv
from thefuzz import process as fuzzy_process
import datetime
import time
import pyautogui
from PIL import ImageGrab

if sys.platform == "win32":
    import winreg
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

try:
    import pygetwindow as gw
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    import google.generativeai as genai
except ImportError:
    gw, spotipy, genai = None, None, None

load_dotenv()

class ActionExecutor:
    def __init__(self):
        self.app_index_path = "app_index.json"
        self.app_index = self._load_or_create_app_index()
        print("Action Executor siap dengan indeks aplikasi, kontrol OS, dan otomatisasi browser.")

    def _load_or_create_app_index(self):
        if os.path.exists(self.app_index_path):
            with open(self.app_index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self.rebuild_app_index()

    def rebuild_app_index(self):
        index = {}
        if sys.platform == "win32":
            uninstall_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            for key_path in uninstall_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            sub_key_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub_key_name) as sub_key:
                                try:
                                    display_name = winreg.QueryValueEx(sub_key, "DisplayName")[0]
                                    install_location = winreg.QueryValueEx(sub_key, "InstallLocation")[0]
                                    if install_location and os.path.isdir(install_location):
                                        for file in os.listdir(install_location):
                                            if file.endswith(".exe") and "uninstall" not in file.lower():
                                                app_name_lower = display_name.lower()
                                                if app_name_lower not in index:
                                                    index[app_name_lower] = os.path.join(install_location, file)
                                                    break
                                except (FileNotFoundError, OSError):
                                    continue
                except FileNotFoundError:
                    continue
        
        common_apps = {"notepad": "notepad.exe", "calculator": "calc.exe", "paint": "mspaint.exe"}
        index.update(common_apps)

        with open(self.app_index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=4)
        print(f"Indeks aplikasi berhasil dibangun dengan {len(index)} entri.")
        return index

    def execute(self, action_object: dict) -> str:
        action_type = action_object.get("action")
        parameters = action_object.get("parameters", {})

        if action_type == "information_retrieval":
            return self._get_gemini_answer(parameters.get("question"))

        if action_type == "open_app":
            return self._open_application(parameters.get("app_name"))
        elif action_type == "search_web":
            return self._search_web(parameters.get("query"))
        elif action_type == "set_volume":
            return self._set_volume(parameters.get("level"))
        elif action_type == "mute_volume":
            return self._mute_volume(parameters.get("mute", True))
        elif action_type == "take_screenshot":
            return self._take_screenshot(parameters.get("path"))
        elif action_type == "navigate_browser":
            return self._navigate_browser(parameters.get("browser"), parameters.get("url"))
        elif action_type == "new_tab_and_navigate":
            return self._new_tab_and_navigate(parameters.get("url"))
        elif action_type == "rebuild_index":
            self.app_index = self.rebuild_app_index()
            return "Indeks aplikasi telah berhasil diperbarui."
        else:
            return f"Tindakan '{action_type}' tidak dikenali atau tidak dapat dieksekusi."

    def _open_application(self, app_name: str) -> str:
        if not app_name: return "Nama aplikasi tidak disebutkan."
        app_name_lower = app_name.lower()
        exact_match = self.app_index.get(app_name_lower)
        if exact_match and os.path.exists(exact_match):
            try:
                subprocess.Popen([exact_match])
                return f"Berhasil membuka {app_name}."
            except Exception as e:
                return f"Menemukan aplikasi, tapi gagal membukanya: {e}"
        best_match_tuple = fuzzy_process.extractOne(app_name_lower, self.app_index.keys(), score_cutoff=75)
        if best_match_tuple:
            match_name, score = best_match_tuple
            app_path = self.app_index[match_name]
            try:
                subprocess.Popen([app_path])
                return f"Membuka '{match_name}'."
            except Exception as e:
                return f"Menemukan aplikasi '{match_name}', tapi gagal membukanya: {e}"
        return f"Maaf, saya tidak dapat menemukan aplikasi yang cocok dengan '{app_name}' di sistem Anda."

    def _search_web(self, query: str) -> str:
        if not query: return "Query pencarian tidak disebutkan."
        try:
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            return f"Mencari '{query}' di web."
        except Exception as e:
            return f"Gagal melakukan pencarian di web: {e}"

    def _set_volume(self, level: int) -> str:
        if level is None: return "Harap sebutkan level volume antara 0 dan 100."
        if not (0 <= level <= 100): return "Level volume harus antara 0 dan 100."
        if sys.platform != "win32": return "Kontrol volume saat ini hanya didukung di Windows."
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100, None)
            return f"Volume sistem diatur ke {level}%."
        except Exception as e:
            return f"Gagal mengatur volume: {e}"

    def _mute_volume(self, mute: bool) -> str:
        if sys.platform != "win32": return "Kontrol mute saat ini hanya didukung di Windows."
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMute(1 if mute else 0, None)
            status = "dimatikan" if mute else "dinyalakan kembali"
            return f"Suara sistem telah {status}."
        except Exception as e:
            return f"Gagal mengubah status mute: {e}"

    def _take_screenshot(self, path: str = None) -> str:
        try:
            screenshot = ImageGrab.grab()
            if path:
                dir_name = os.path.dirname(path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                save_path = path
            else:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                save_path = os.path.join(desktop, f"screenshot_{timestamp}.png")
            screenshot.save(save_path)
            return f"Tangkapan layar berhasil disimpan di {save_path}"
        except Exception as e:
            return f"Gagal mengambil tangkapan layar: {e}"

    def _navigate_browser(self, browser: str, url: str) -> str:
        if not browser or not url: return "Perlu nama browser dan URL untuk navigasi."
        open_status = self._open_application(browser)
        if "gagal" in open_status.lower() or "tidak dapat menemukan" in open_status.lower():
            return f"Gagal membuka browser {browser}."
        time.sleep(3)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        try:
            pyautogui.write(url)
            pyautogui.press('enter')
            return f"Membuka {browser} dan menavigasi ke {url}."
        except Exception as e:
            return f"Gagal mengontrol browser: {e}"

    def _new_tab_and_navigate(self, url: str) -> str:
        if not url: return "Perlu URL untuk membuka tab baru."
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        try:
            time.sleep(0.5)
            if sys.platform == "darwin":
                pyautogui.hotkey('command', 't')
            else:
                pyautogui.hotkey('ctrl', 't')
            time.sleep(1)
            pyautogui.write(url)
            pyautogui.press('enter')
            return f"Membuka tab baru dan menavigasi ke {url}."
        except Exception as e:
            return f"Gagal membuka tab baru: {e}"