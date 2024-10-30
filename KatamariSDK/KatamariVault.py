import os
import json
import logging
from KatamariSDK.KatamariKMS import KatamariKMS
from KatamariSDK.KatamariDB import KatamariMVCC

logger = logging.getLogger('KatamariVault')

class KatamariVault(KatamariMVCC):
    def __init__(self, kms: KatamariKMS):
        super().__init__()
        self.kms = kms

    def store_secret(self, key_name: str, secret_name: str, secret_value: str):
        """Encrypt and store a secret securely."""
        encrypted_secret = self.kms.encrypt(key_name, secret_value.encode())
        tx_id = self.begin_transaction()

        secret_version = self.get_latest_version(secret_name) + 1
        secret_data = {
            'secret': encrypted_secret,
            'version': secret_version,
            'created_at': str(self._get_current_time()),
        }

        # Store encrypted secret in the KatamariDB with MVCC
        self.put(f"secret:{secret_name}", secret_data, tx_id)
        self.commit(tx_id)
        logger.info(f"Stored secret {secret_name} with version {secret_version}")

    def get_secret(self, key_name: str, secret_name: str, version: int = None) -> str:
        """Retrieve and decrypt a secret."""
        tx_id = self.begin_transaction()

        if version is None:
            secret_data = self.get_latest_version_data(secret_name)
        else:
            secret_data = self.get(f"secret:{secret_name}:v{version}", tx_id)

        if not secret_data:
            raise ValueError(f"Secret {secret_name} not found.")

        decrypted_secret = self.kms.decrypt(key_name, secret_data['secret'])
        self.commit(tx_id)

        return decrypted_secret.decode('utf-8')

    def get_latest_version(self, secret_name: str) -> int:
        """Get the latest version of a secret."""
        secrets = self.search(f"secret:{secret_name}")
        return max([secret['version'] for secret in secrets]) if secrets else 0

    def get_latest_version_data(self, secret_name: str) -> dict:
        """Get the latest secret data."""
        latest_version = self.get_latest_version(secret_name)
        return self.get(f"secret:{secret_name}:v{latest_version}")

# Example Usage
if __name__ == "__main__":
    kms = KatamariKMS()
    vault = KatamariVault(kms)

    vault.store_secret("katamari_secret_key", "db_password", "MyDBPassword123")
    secret = vault.get_secret("katamari_secret_key", "db_password")
    logger.info(f"Retrieved secret: {secret}")

