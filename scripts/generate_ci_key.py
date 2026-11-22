
from pathlib import Path
from getpass import getpass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


directory = Path.home() / ".dbt"
directory.mkdir(exist_ok=True)

private_path = directory / "retail_ci_private_key.p8"
public_path = directory / "retail_ci_public_key.pub"

if private_path.exists() or public_path.exists():
    raise RuntimeError("CI key files already exist")

passphrase = getpass("Create CI key passphrase: ")

if not passphrase:
    raise ValueError("Passphrase cannot be empty")

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

private_path.write_bytes(
    private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(
            passphrase.encode()
        )
    )
)

public_key = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

public_path.write_bytes(public_key)

public_body = "".join(
    line for line in public_key.decode().splitlines()
    if not line.startswith("-----")
)

print(f"Private key saved to: {private_path}")
print(f"Public key saved to: {public_path}")
print("\nSnowflake public key:")
print(public_body)
