import sqlite3 as sql
import pickle
import numpy as np
import errors_exceptions as err
import pathlib
import security_system as ss
from enum import Enum
from dataclasses import dataclass

@dataclass
class FaceData:
    id: int
    name : str
    encoding: np.ndarray

@dataclass
class UserInfo:
    id: int
    name: str
    access: str

@dataclass
class FolderInfo:
    id: int
    name: str
    path: str

class Access(Enum):
    level_full = "FULL"
    level_limited = "LIMITED"

class DataBaseManager():
    def __init__(self, db_path = "face_locking_system.db"):
        self.db_path = db_path
        self.security = ss.SercuritySystem()
        self.conn = None
        try:
            self.conn = sql.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self._create_tables()
        except sql.Error as e:
            raise err.InaccessbleDatabase(e)
    
    def _create_tables(self):
        self.cursor.execute("""  CREATE TABLE IF NOT EXISTS faces(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            encoding BLOB NOT NULL,
                            access TEXT NOT NULL,
                            pin TEXT NOT NULL
                            ) 
                            """)

        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS encrypted_folders (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            folder_path TEXT NOT NULL,
                            encryption_key BLOB NOT NULL
                            )
                            """)
        
        self.conn.commit()

    # checks if the there are entres in faces table
    def not_empty_database(self):
        self.cursor.execute("SELECT id FROM faces")
        result = self.cursor.fetchall()
        if len(result) > 0:
            return True
        return False

    # compare the path with the paths in encrypted_folders >> folder_path
    def check_enc_list(self, path_to_check):
        path_to_check = str(path_to_check)
        self.cursor.execute("SELECT 1 FROM encrypted_folders WHERE folder_path = ?", (path_to_check,))
        already_encrypted = self.cursor.fetchone()
        return already_encrypted
    
    # return name and access
    def return_login_info(self, id: int):
        self.cursor.execute("SELECT name, access FROM faces WHERE id = ?", (id,))
        login_info = self.cursor.fetchone()

        if login_info:
            login_info = UserInfo(id=id, name=login_info[0], access=login_info[1])
            return login_info
        else:
            return
        
    # adds a new user, insert name, face_encoding, access, pin into faces
    def add_user_info(self, name: str, encoding, pin: str, access: Access):
        encoding = pickle.dumps(encoding)
        pin = self.security.hash_pin(pin)
        self.cursor.execute("INSERT INTO faces(name, encoding, access, pin) VALUES (?, ?, ?, ?)", (name, encoding, access, pin,))
        user_id = self.cursor.lastrowid
        self.conn.commit()
        return user_id
    
    # fetches id, name and face_encodings for compare_faces
    def fetch_personal_info_for_compar(self):
        face_data_list = []
        self.cursor.execute("SELECT id, name, encoding FROM faces")
        results = self.cursor.fetchall()
        for user_id, name, encoding_blob in results:
            norm_encoding = pickle.loads(encoding_blob)
            face_data_list.append(FaceData(id=user_id, name=name, encoding=norm_encoding))
        return face_data_list

    # fetch keys fro decryption proccess
    def fetch_keys(self, folder_path):
        folder_path = str(folder_path)
        self.cursor.execute("SELECT encryption_key FROM encrypted_folders WHERE folder_path = ?", (folder_path,))
        keys = self.cursor.fetchall()
        if keys:
            return keys[0][0]
        else:
            return
    
    # add an encrypted folder with thire key into encrypted_folders
    def add_encrypted_folder(self, folder_path, key):
        folder_path = str(folder_path)
        self.cursor.execute("INSERT INTO encrypted_folders (folder_path, encryption_key) VALUES (?, ?)",(folder_path, key,))
        self.conn.commit()

    # remove the encrypted folder and all related elements for decryption
    def remove_encrypted_folder(self, folder_path):
        folder_path = str(folder_path)
        self.cursor.execute("DELETE FROM encrypted_folders WHERE folder_path = ?", (folder_path,))
        self.conn.commit()

    # check if the pin is correct for login
    def check_pin(self, id, pin):
        self.cursor.execute("SELECT pin FROM faces WHERE id = ?", (id,))
        stored_hash = self.cursor.fetchone()
        pin = self.security.hash_pin(pin)
        if stored_hash[0] == pin:
            return True
        return False

    # return encrypted folders for ui display
    def list_encrypted_folders(self):
        folders_info = []
        self.cursor.execute("SELECT id, folder_path FROM encrypted_folders")
        folders_list = self.cursor.fetchall()
        for data in folders_list:
            folder_path = pathlib.Path(data[1])
            folders_info.append(FolderInfo(id=data[0], name=folder_path.name, path=data[1]))
        return folders_info

    # list all users for ui display
    def list_users(self):
        user_info = []
        self.cursor.execute("SELECT id, name, access FROM faces")
        user_list = self.cursor.fetchall()
        for data in user_list:
            user_info.append(UserInfo(id=data[0], name=data[1], access=data[2]))
        return user_info

    # exit proccess
    def close(self):
        if self.conn:
            self.conn.close()
            print("Database connection close.")
