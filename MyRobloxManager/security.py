import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class Security:
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derives a 32-byte URL-safe base64 key from a password and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def generate_salt() -> bytes:
        return os.urandom(16)

    @staticmethod
    def encrypt(data_dict: dict, password: str, salt: bytes = None) -> dict:
        if not salt:
            salt = Security.generate_salt()
        
        key = Security.derive_key(password, salt)
        f = Fernet(key)
        
        json_str = str(data_dict).replace("'", '"') # Simple conversion to string
        token = f.encrypt(json_str.encode())
        
        return {
            "is_encrypted": True,
            "salt": base64.b64encode(salt).decode('utf-8'),
            "data": token.decode('utf-8')
        }

    @staticmethod
    def decrypt(encrypted_store: dict, password: str) -> dict:
        salt = base64.b64decode(encrypted_store['salt'])
        token = encrypted_store['data'].encode()
        
        key = Security.derive_key(password, salt)
        f = Fernet(key)
        
        decrypted_data = f.decrypt(token)
        
        import json
        return json.loads(decrypted_data.decode())
