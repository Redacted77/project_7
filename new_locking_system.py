import os
import shutil
import database_manager as dbm
import errors_exceptions as err
import logging_system as log
import cryptography.fernet
from cryptography.fernet import Fernet
from enum import Enum
from pathlib import Path

class Mode(Enum):
    ENC = 1
    DEC = 2

class LockSystem():
    def __init__(self, logging_manger: log.Logging, db_manger: dbm.DataBaseManager = None):
        if not db_manger:
            db_manger = dbm.DataBaseManager()
        self.working_dir = Path(os.getcwd()).resolve()
        self.db_instance = db_manger
        self.log_instance = logging_manger

    # checks if the target folder is valid to encrypt or decrypt
    def confirm_target_folder(self, user_path: str, mode = Mode):
        user_path = Path(user_path).resolve()
        
        if not user_path.is_dir():
            raise err.PathNotFoundError(f"Invalid path: '{user_path}' is not a valid dirctory.")
        
        if user_path == self.working_dir or user_path in self.working_dir.parents:
            raise err.WorkingDirectoryError(f"Invalid path: Cannot target the application's working directory or any of its parent folders.")
        
        is_encrypted = self.db_instance.check_enc_list(user_path)

        if is_encrypted and mode == Mode.ENC:
            raise err.AlreadyEncryptedError(f"'{user_path}' is already encrypted.")
        
        if not is_encrypted and mode == Mode.DEC:
            raise err.CanNotDecryptError(f"Invalid target: '{user_path}' is not encrypted.")
        
        return user_path
        
    # the encryption logic
    def encrypt(self, key, target_folder_path: Path, temp_folder: Path):
        fn = Fernet(key)
        for folder, _, files in os.walk(target_folder_path):
            for file in files:
                file_path = Path(folder) / file
                relative_filepath = file_path.relative_to(target_folder_path)
                copied_filepath = temp_folder / relative_filepath
                
                try:
                    self.encrypt_helper(file_path=file_path, fn_key=fn, copied_filepath=copied_filepath)
                except err.FileProccessingError:
                    self.failed_files_recovery(failed_file=file_path, copied_folder=temp_folder, target_folder=target_folder_path)
                    continue

    # the decryption logic
    def decrypt(self, key,target_folder_path: Path, temp_folder: Path):
        fn = Fernet(key)
        for folder, _, files in os.walk(target_folder_path):
            for file in files:
                file_path = Path(folder) / file
                relative_filepath = file_path.relative_to(target_folder_path)
                copied_filepath = temp_folder / relative_filepath
                
                try:
                    self.decrypt_helper(file_path=file_path, fn_key=fn, copied_filepath=copied_filepath)
                except err.FileProccessingError:
                    self.failed_files_recovery(failed_file=file_path, copied_folder=temp_folder, target_folder=target_folder_path)
                    continue

    # generate keys for the ecryption/decryption logics & decide which one will run
    def enc_dec_dispatcher(self, target_folder_path, mode = Mode):
        if mode == Mode.DEC:
            key = self.db_instance.fetch_keys(target_folder_path)
            if not key:
                raise err.DecKeyNotFoundError(f"Key not found: decrypt key for {target_folder_path} not in database.")
            copied_folder_path = self.recreate_target_folder(target_folder_path=target_folder_path)
            self.decrypt(key=key, target_folder_path=target_folder_path,temp_folder=copied_folder_path)
            shutil.rmtree(target_folder_path)
            os.rename(copied_folder_path, target_folder_path)
            self.db_instance.remove_encrypted_folder(folder_path=target_folder_path)
        
        else:
            key = Fernet.generate_key()
            copied_folder_path = self.recreate_target_folder(target_folder_path=target_folder_path)
            self.encrypt(key=key, target_folder_path=target_folder_path, temp_folder=copied_folder_path)
            shutil.rmtree(target_folder_path)
            os.rename(copied_folder_path, target_folder_path)
            self.db_instance.add_encrypted_folder(folder_path=target_folder_path, key=key)

    # creat an empty copy of the target folder
    def recreate_target_folder(self, target_folder_path: Path, destination_name: str = "temp_recreated_for_dec_enc"):
        abs_path = Path(target_folder_path).resolve()
        parent_path = abs_path.parent
        copied_folder = parent_path / destination_name
        copied_folder.mkdir(exist_ok=True)
        for folderpath, _, _ in os.walk(target_folder_path):
            current_target = Path(folderpath)

            relative_path = current_target.relative_to(target_folder_path)
            new_dir = copied_folder / relative_path
            new_dir.mkdir(exist_ok=True)
        return copied_folder

    # helps dencrypt function, by make some error checks file by file
    def decrypt_helper(self, file_path: Path, fn_key: Fernet, copied_filepath: Path):
        
        try:
            with open(file_path, "rb") as file_data:
                data = file_data.read()
        except OSError as e:
            raise err.FileReadError(f"Error: could not read {file_path}") from e
        
        try:
            decrypted_data = fn_key.decrypt(data)
        except cryptography.fernet.InvalidToken:
            raise err.DecryptionTokenError(f"Error: could not decrypt {file_path}")
        
        try:
            with open(copied_filepath, "wb") as file_data:
                file_data.write(decrypted_data)
        except OSError as e:
            raise err.FileWriteError(f"Error: could not write {copied_filepath}") from e
    
    # helps encrypt function, by make some error checks file by file
    def encrypt_helper(self, file_path: Path, fn_key: Fernet, copied_filepath: Path):
        
        try:
            with open(file_path, "rb") as file_data:
                data = file_data.read()
        except OSError as e:
            raise err.FileReadError(f"Error: could not read {file_path}") from e
        
        encrypted_data = fn_key.encrypt(data)
        
        try:
            with open(copied_filepath, "wb") as file_data:
                file_data.write(encrypted_data)
        except OSError as e:
            raise err.FileWriteError(f"Error: could not write {copied_filepath}") from e
    
    # copies failed files into the quarantin folder
    def failed_files_recovery(self, failed_file: Path, copied_folder: Path, target_folder: Path):
        quarantin_folder = copied_folder / "_failed_files_"
        quarantin_folder.mkdir(exist_ok=True)
        file_structure = failed_file.relative_to(target_folder)
        file_structure = quarantin_folder / file_structure
        file_structure.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(failed_file, file_structure)