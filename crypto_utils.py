import json
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

# Secret key for encryption (in production, use environment variable)
SECRET_KEY = "your-secret-key-change-this-in-production"

def get_encryption_key() -> bytes:
    """Generate encryption key from secret passphrase using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'static_salt_change_in_prod',  # In production, use random salt per encryption
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return key

def encrypt_data(data: dict) -> str:
    """Encrypt JSON data and return base64-encoded ciphertext."""
    key = get_encryption_key()
    fernet = Fernet(key)
    
    # Convert dict to JSON string
    json_str = json.dumps(data)
    
    # Encrypt
    encrypted = fernet.encrypt(json_str.encode())
    
    # Return as base64 string
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt_data(encrypted_str: str) -> dict:
    """Decrypt base64-encoded ciphertext and return JSON data."""
    key = get_encryption_key()
    fernet = Fernet(key)
    
    # Decode from base64
    encrypted = base64.urlsafe_b64decode(encrypted_str.encode())
    
    # Decrypt
    decrypted = fernet.decrypt(encrypted)
    
    # Convert JSON string back to dict
    return json.loads(decrypted.decode())
