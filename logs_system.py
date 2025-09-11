import os
from pathlib import Path
from datetime import datetime

class Logging():
    def __init__(self):
        t = timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_folder = Path.cwd() / '__logs__'
        os.makedirs(self.log_folder, exist_ok=True)
        self.log_name = 'Log'
        self.log_ext = '.txt'
        self.logs_file = os.path.join(self.log_folder, f'{self.log_name}_{t}{self.log_ext}')
        
        with open(self.logs_file, 'w') as L:
            L.write(f"Logging Start --- {t}\n")
            L.write("----------------\n")
            L.write("\n")

    # base log method
    def _log(self, status: bool, event: str, user: int = None, target: str = None, error: str = None):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{t}]"
        
        if user:
            entry+= f' User id: {user}'
        
        entry+= f'- [{event.upper()}]'
        
        if target:
            entry+= f'- Target: {target}'

        entry+= f"- status: {'Successful' if status else 'Failed'}"

        if error:
            entry+= f' - error: "{error}"'

        with open(self.logs_file, 'a') as L:
            L.write(entry + "\n")
    
    # announce user logging in
    def announce_login(self, user: int):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.logs_file, 'a') as L:   
            L.write(f"[{t}] --- User id: {user} has logged in. \n")
            
    # announce user logging out
    def announce_logout(self, user: int):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.logs_file, 'a') as L:         
            L.write(f"[{t}] --- Sesession end --- User id: {user} has logged out. \n")

    # for login facescan and face match
    def announce_face_scan(self, status: bool, event: str, user: int = None, error: str = None):
        self._log(user=user, status=status, event=event, error=error)
    # for encryption
    def announce_file_encrypt(self, user: int, status: bool, file: str, error: str = None):
        self._log(status, "Encrypted", user, file, error)
    # for decryption
    def announce_file_decrypt(self, user: int, status: bool, file: str, error: str = None):
        self._log(status, "Decrypted", user, file, error)
    # to clarify the folder that was accessd for encryption and decryption
    def announce_folder_encrypt(self, user: int, folder: str):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.logs_file, 'a') as L:         
            L.write(f"[{t}] --- User id: {user} --- [Attempted Encryption] --- Folder: {folder}\n")
    def announce_folder_decrypt(self, user: int, folder: str):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.logs_file, 'a') as L:         
            L.write(f"[{t}] --- User id: {user} --- [Attempted Decryption] --- Folder: {folder}\n")
    # for logging admin actions (remove/add users ect.)
    def log_admin_action(self, status: bool, event: str, user: int, target: str = None, error: str = None):
        self._log(status=status, event=event, user=user, target=target, error=error)
    # announce attempt logins
    def announce_attempt_login(self):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.logs_file, 'a') as L:   
            L.write(f"[{t}] --- failed login attempt. \n")
    # for generic errors that dont need detail
    def generic_error(self, error: str):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.logs_file, 'a') as L:         
            L.write(f"[{t}] --- Error: '{error}'\n")
    # for logging generic messages
    def generic_log(self, mess: str):
        t = timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.logs_file, 'a') as L:         
            L.write(f"[{t}] --- '{mess}'\n")