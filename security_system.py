import logs_system as log
import hashlib
import os, tempfile
import base64
import errors_exceptions as err
import logs_system as log
import sqlite3 as sql
import database_manager as db_manger
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from enum import Enum
from dataclasses import dataclass
from cryptography.hazmat.backends import default_backend

@dataclass
class Checks:
    salt_exist: bool
    public_db_exists: bool
    encrypted_db_exists: bool

@dataclass
class database_dependency:
    fn_key: Fernet
    sql_conn: sql.Connection

class Condition(Enum):
    First_time = "first_user"
    normal = "subsequent"

class SercuritySystem():
    def __init__(self, logging_manger: log.Logging, db_path = "face_locking_system.db",
                  encrypted_db = "FolderLockApp_System.db", salt = "imp_salt"):
        self.log_instance = logging_manger
        self.db_path = db_path
        self.salt = salt
        self.encrypted_db_path = encrypted_db

    
    # hash pins
    def hash_pin(self, pin: str):
        pin = pin.strip()
        hashed_pin = hashlib.sha256(pin.encode("utf-8")).hexdigest()
        return hashed_pin
    
    # check if salt and database exists
    def run_check(self):
        salt = os.path.exists(self.salt)
        public_db = os.path.exists(self.db_path)
        encrypted_db = os.path.exists(self.encrypted_db_path)
        res = Checks(salt_exist=salt,public_db_exists=public_db,encrypted_db_exists=encrypted_db)
        return res
    
    # encrypt the database
    def encrypt_db_v2(self, master_password: str):
        #master_password =  master_password.strip()
        salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,
            backend=default_backend(),
        )

        master_password_bytes = master_password.encode('utf-8')
        master_key = kdf.derive(master_password_bytes)
        fernet_key = base64.urlsafe_b64encode(master_key)

        try:
            with open(self.db_path, "rb") as d:
                db_data = d.read()
        except FileNotFoundError as e:
            raise err.DatabaseNotFound(f"{self.db_path} not found: {e}")
        
        fn = Fernet(fernet_key)
        encrypted_db_data = fn.encrypt(db_data)

        with open(self.encrypted_db_path, "wb") as d:
            d.write(encrypted_db_data)
        
        with open(self.salt, "wb") as f:
            f.write(salt)
        
        os.remove(self.db_path)

        in_memory_conn = sql.connect(":memory:", check_same_thread=False)
        in_memory_conn.deserialize(db_data)
        feedback = database_dependency(fn_key=fn, sql_conn=in_memory_conn)

        return feedback
    
    # decrypt the database
    def decrypt_db_v2(self, password: str):
        try:
            with open(self.salt, "rb") as d:
                salt = d.read()
        except FileNotFoundError as e:
            raise err.SaltNotFound(f"Error: salt ,{self.salt} , not found: {e}")
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,
            backend=default_backend(),
        )

        password_bytes = password.encode("utf-8")
        password_key = kdf.derive(password_bytes)
        fernet_password = base64.urlsafe_b64encode(password_key)

        try:
            with open(self.encrypted_db_path, "rb") as d:
                encrypted_data = d.read()
        except FileNotFoundError as e:
            raise err.DatabaseNotFound(f"{self.encrypted_db_path} not found: {e}")
        
        fn = Fernet(fernet_password)
        try:
            decrypted_data = fn.decrypt(encrypted_data)
            in_memory_conn = sql.connect(":memory:", check_same_thread=False)
            in_memory_conn.deserialize(decrypted_data)
            feedback = database_dependency(fn_key=fn,sql_conn=in_memory_conn)
            return feedback
        except InvalidToken as e:
            self.log_instance.generic_error(f"wrong database password: {e}")
            return False

    # saves current work
    def save(self, db_conn: sql.Connection, fn_key: Fernet):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_name = tmp.name

        backup_conn = sql.connect(tmp_name)
        db_conn.backup(backup_conn)
        backup_conn.close()

        with open(tmp_name, "rb") as f:
            db_bytes = f.read()

        try:
            db_info = fn_key.encrypt(db_bytes)
            with open(self.encrypted_db_path, "wb") as d:
                d.write(db_info)
            os.remove(tmp_name)
            return True
        except Exception as e:
            raise err.SaveError(f"Error: could not save: {e}")
        
    # check if the database is encrypted or not
    def check_if_encrypted(self):
        try:
            with open(self.encrypted_db_path, "rb") as f:
                header = f.read(16)
            return not header.startswith(b"SQLite format 3\x00")
        except FileNotFoundError:
            return False
        except Exception as e:
            self.log_instance.generic_error(f"Error checking encryption status: {e}")
            return True