import os
import logging
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
from KatamariSDK.KatamariDB import KatamariMVCC
from typing import Any, Dict, Optional, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('KatamariKMS')

class KatamariKMS(KatamariMVCC):
    def __init__(self, key_store_path: str = './kms_keys'):
        super().__init__()
        self.key_store_path = key_store_path
        if not os.path.exists(self.key_store_path):
            os.makedirs(self.key_store_path)

    def generate_key(self, key_name: str) -> str:
        """Generate a new AES 256-bit key, store it with version control."""
        key = get_random_bytes(32)  # 256 bits AES key
        tx_id = self.begin_transaction()

        key_version = self.get_latest_version(key_name) + 1
        key_data = {
            'key': b64encode(key).decode('utf-8'),
            'version': key_version,
            'created_at': str(self._get_current_time()),
        }

        # Store the key in the KatamariDB with MVCC
        self.put(f"key:{key_name}", key_data, tx_id)
        self.commit(tx_id)
        logger.info(f"Generated and stored key {key_name} with version {key_version}")

        return key_data['key']

    def load_key(self, key_name: str, version: int = None) -> AES:
        """Load a specific version of the AES key from storage."""
        tx_id = self.begin_transaction()

        if version is None:
            key_data = self.get_latest_version_data(key_name)
        else:
            key_data = self.get(f"key:{key_name}:v{version}", tx_id)

        if not key_data:
            raise ValueError(f"Key {key_name} not found.")

        self.commit(tx_id)
        key = b64decode(key_data['key'])
        return AES.new(key, AES.MODE_GCM)

    def encrypt(self, key_name: str, data: bytes, version: int = None) -> Dict[str, Any]:
        """Encrypt data using the specified key version."""
        aes_cipher = self.load_key(key_name, version)
        nonce = get_random_bytes(12)
        cipher_text, tag = aes_cipher.encrypt_and_digest(data)
        
        return {
            'nonce': b64encode(nonce).decode('utf-8'),
            'cipher_text': b64encode(cipher_text).decode('utf-8'),
            'tag': b64encode(tag).decode('utf-8')
        }

    def decrypt(self, key_name: str, encrypted_data: Dict[str, Any], version: int = None) -> bytes:
        """Decrypt data using the specified key version."""
        aes_cipher = self.load_key(key_name, version)
        nonce = b64decode(encrypted_data['nonce'])
        cipher_text = b64decode(encrypted_data['cipher_text'])
        tag = b64decode(encrypted_data['tag'])
        
        aes_cipher = AES.new(aes_cipher.key, AES.MODE_GCM, nonce=nonce)
        return aes_cipher.decrypt_and_verify(cipher_text, tag)

    def rotate_key(self, key_name: str) -> str:
        """Rotate the AES key and update the version control."""
        return self.generate_key(key_name)

    def get_latest_version(self, key_name: str) -> int:
        """Get the latest version of a key."""
        keys = self.search(f"key:{key_name}")
        return max([key['version'] for key in keys]) if keys else 0

    def get_latest_version_data(self, key_name: str) -> Dict[str, Any]:
        """Get the latest key data."""
        latest_version = self.get_latest_version(key_name)
        return self.get(f"key:{key_name}:v{latest_version}")

# Example Usage
if __name__ == "__main__":
    kms = KatamariKMS()
    key = kms.generate_key("katamari_secret_key")
    encrypted_data = kms.encrypt("katamari_secret_key", b"MySecretData")
    decrypted_data = kms.decrypt("katamari_secret_key", encrypted_data)
    logger.info(f"Decrypted data: {decrypted_data.decode('utf-8')}")

