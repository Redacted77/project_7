import os
import stat
import platform
from pathlib import Path
from datetime import datetime

class Logging():
    def __init__(self):
        self.log_folder = Path.cwd() / '__logs__'
        os.makedirs(self.log_folder, exist_ok=True)
        self.log_text_file = 'logs.txt'
        self.logs_file = os.path.join(self.log_folder, self.log_text_file)
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.logs_file, 'a') as L:
            L.write(f"Logging Start --- {t}\n")
            L.write("----------------\n")
            L.write("\n")
        
        if platform.system() == "Windows":
            os.chmod(self.logs_file, stat.S_IREAD)
        else:
            os.chmod(self.logs_file, 0o600)

    def _log(self, status: bool, event: str, user: int, target: str = None, error: str = None):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{t}] --- User: {user} - [{event.upper()}] - Target: {target} - status: {'Successful' if status else 'Failed'}"
        if error:
            entry += f' - error: "{error}"'

        with open(self.logs_file, 'a') as L:
            L.write(entry + "\n")

    def announce_login(self, user: int):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.logs_file, 'a') as L:
            L.write(f"[{t}] --- User: {user} has logged in. \n")

    def announce_logout(self, user: int):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.logs_file, 'a') as L:
            L.write(f"[{t}] --- Sesession end --- User: {user} has logged out. \n")

    def announce_folder(self, folder, status: bool, user: int, error: str = None):
       t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       entry = f"[{t}] --- User: {user} has targeted {folder} status: {'Successful' if status else 'Failed'}"
       if error:
            entry += f' - error: "{error}"'
       with open(self.logs_file, 'a') as L:
           L.write(entry + '\n')

    def announce_file_encrypt(self, user: int, status: bool, file: str, error: str = None):
        self._log(status, "Encrypted", user, file, error)

    def announce_file_decrypt(self, user: int, status: bool, file: str, error: str = None):
        self._log(status, "Decrypted", user, file, error)

    def announce_attempt_face_scan(self, status: bool, error: str = None):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{t}] --- [FACE_SCAN_ATTEMPT] - status: {'Successful' if status else 'Failed'}"
        if error:
            entry += f' - error: "{error}"'
        with open(self.logs_file, 'a') as L:
            L.write(entry + '\n')
    
    def announce_face_match_result(self, status: bool, event: str, user: int = None, error: str = None):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{t}] --- [{event.upper()}] Called face_compre - status: {f'Match found {user}' if status else 'No match found'}"
        if error:
            entry += f' - error: "{error}"'
        
        with open(self.logs_file, 'a') as L:
            L.write(entry + '\n')

    def announce_add_user(self, user_took_action: int, added_user: int, status: bool, error: str = None):
        self._log(status, "Added a user", user_took_action, added_user, error)

    def announce_admin_menu_start(self, user: int, status: bool, error: str = None):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{t}] --- User: {user} Requested access to Admin menu - status: {'Approved' if status else 'Denied'}"
        if error:
            entry += f' - error: "{error}"'
        
        with open(self.logs_file, 'a') as L:
            L.write(entry + '\n')
    
    def log_admin_action(self, user: int, status: bool, event: str):
        self._log(status, event, user)