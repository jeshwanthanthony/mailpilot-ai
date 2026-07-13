from cryptography.fernet import Fernet

from app.config import Settings
from app.repository import ConnectionRepository


def test_token_encryption_round_trip() -> None:
    settings = Settings(token_encryption_key=Fernet.generate_key().decode())
    repository = ConnectionRepository(settings)
    encrypted = repository.encrypt_token("oauth-token")
    assert encrypted != "oauth-token"
    assert repository.decrypt_token(encrypted) == "oauth-token"


def test_existing_plaintext_token_is_readable() -> None:
    settings = Settings(token_encryption_key=Fernet.generate_key().decode())
    repository = ConnectionRepository(settings)
    assert repository.decrypt_token("legacy-token") == "legacy-token"
