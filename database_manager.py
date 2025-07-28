import sqlite3 as sql
import pickle
import numpy as np
import errors_exceptions as err
from dataclasses import dataclass

@dataclass
class FaceData:
    id: int
    name : str
    encoding: np.ndarray

@dataclass
class user_info:
    id: int
    name: str
    access: str


class DataBaseManager():
    def __init__(self, db_path = "face_locking_system.db"):
        self.db_path = db_path
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
                            pin INTEGER NOT NULL
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
            name, access = login_info
            return {"name": name, "access": access}
        else:
            return
        
    # adds a new user, insert name, face_encoding, access, pin into faces
    def add_user_info(self, name: str, encoding, access, pin: int):
        encoding = pickle.dumps(encoding)
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

    # return encrypted folders for ui display
    def list_encrypted_folders(self):
        self.cursor.execute("SELECT folder_path FROM encrypted_folders")
        folders_list = self.cursor.fetchall()
        return folders_list

    # list all users for ui display
    def list_users(self):
        self.cursor.execute("SELECT id, name, access FROM faces")
        user_list = self.cursor.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()
            print("Database connection close.")
