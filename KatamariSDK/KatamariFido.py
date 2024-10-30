import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict

from KatamariSDK.KatamariDB import KatamariMVCC
from KatamariSDK.KatamariKMS import KatamariKMS
from KatamariSDK.KatamariVault import KatamariVault
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KatamariFido")


class KatamariFido:
    """FIDO2-based Identity and Access Management using KatamariMVCC and Fido2Server for passwordless authentication."""

    def __init__(self):
        self.katamari_mvcc = KatamariMVCC()
        self.kms = KatamariKMS()  # Initialize KatamariKMS for encryption
        self.vault = KatamariVault(self.kms)  # Initialize KatamariVault for secure secret storage

        # FIDO2 server configuration for katamari.ai
        rp = PublicKeyCredentialRpEntity("katamari.ai", "Katamari Authentication")
        self.fido2_server = Fido2Server(rp)

    # FIDO2 registration for passwordless authentication
    def start_fido2_registration(self, username: str, display_name: str) -> dict:
        """Start FIDO2 registration process."""
        user_entity = PublicKeyCredentialUserEntity(username.encode(), username, display_name)
        registration_data, state = self.fido2_server.register_begin(user_entity)
        self.katamari_mvcc.put(f"fido2_registration_state:{username}", state)
        return registration_data

    def complete_fido2_registration(self, username: str, client_data: dict):
        """Complete FIDO2 registration process."""
        state = self.katamari_mvcc.get(f"fido2_registration_state:{username}")
        auth_data = self.fido2_server.register_complete(state, client_data["clientDataJSON"],
                                                        client_data["attestationObject"])
        fido2_data = {
            "credential_id": auth_data.credential_id,
            "public_key": auth_data.public_key,
            "sign_count": auth_data.sign_count,
        }
        self.katamari_mvcc.put(f"user:{username}_fido2_data", fido2_data)
        return fido2_data

    # FIDO2 authentication
    def start_fido2_authentication(self, username: str) -> dict:
        """Begin FIDO2 authentication for a user."""
        fido2_data = self.katamari_mvcc.get(f"user:{username}_fido2_data")
        if not fido2_data:
            raise ValueError("FIDO2 credentials not registered for user")
        auth_data, state = self.fido2_server.authenticate_begin([fido2_data])
        self.katamari_mvcc.put(f"fido2_authentication_state:{username}", state)
        return auth_data

    def complete_fido2_authentication(self, username: str, client_data: dict) -> bool:
        """Complete FIDO2 authentication process."""
        state = self.katamari_mvcc.get(f"fido2_authentication_state:{username}")
        fido2_data = self.katamari_mvcc.get(f"user:{username}_fido2_data")
        auth_result = self.fido2_server.authenticate_complete(
            state, fido2_data["credential_id"], client_data["clientDataJSON"], client_data["authenticatorData"],
            client_data["signature"]
        )
        # Update sign count for replay protection
        fido2_data["sign_count"] = auth_result.new_sign_count
        self.katamari_mvcc.put(f"user:{username}_fido2_data", fido2_data)
        return True


# Example Usage of KatamariFido
if __name__ == "__main__":
    katamari_fido = KatamariFido()

    # Start FIDO2 registration for a new user
    username = "user1"
    display_name = "User One"
    registration_data = katamari_fido.start_fido2_registration(username, display_name)
    print("Registration data:", registration_data)

    # Simulate client data for registration completion
    client_data = {
        "clientDataJSON": b"fakeClientDataJSON",
        "attestationObject": b"fakeAttestationObject"
    }
    fido2_data = katamari_fido.complete_fido2_registration(username, client_data)
    print("FIDO2 registration complete:", fido2_data)

    # Start FIDO2 authentication
    auth_data = katamari_fido.start_fido2_authentication(username)
    print("Authentication data:", auth_data)

    # Simulate client data for authentication completion
    auth_client_data = {
        "clientDataJSON": b"fakeClientDataJSON",
        "authenticatorData": b"fakeAuthenticatorData",
        "signature": b"fakeSignature"
    }
    is_authenticated = katamari_fido.complete_fido2_authentication(username, auth_client_data)
    print("FIDO2 authentication success:", is_authenticated)

