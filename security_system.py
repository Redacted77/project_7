import logs_system as log
import hashlib


class SercuritySystem():
    def __init__(self, logging_manger: log = None):
        if logging_manger:
            self.log_instance = logging_manger
    
    # hash pins
    def hash_pin(self, pin: str):
        pin = pin.strip()
        hashed_pin = hashlib.sha256(pin.encode("utf-8")).hexdigest()
        return hashed_pin
    
    # encrypt the database
    def encrypt_db(self, db):
        pass
    
    # decrypt the database
    def decrypt_db(self, pas):
        pass