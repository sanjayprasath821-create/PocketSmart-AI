import base64
import hashlib
import hmac
import json
import time

from app.config import get_settings


settings = get_settings()


def hash_password(password: str) -> str:
    salt = hashlib.sha256(
        (settings.secret_key + "::salt").encode()
    ).digest()

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        120000,
    )

    return base64.urlsafe_b64encode(hashed).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(
        hash_password(password),
        password_hash,
    )


def _b64(data: bytes) -> str:
    return (
        base64.urlsafe_b64encode(data)
        .rstrip(b"=")
        .decode()
    )


def create_access_token(subject: int) -> str:
    header = _b64(
        b'{"alg":"HS256","typ":"JWT"}'
    )

    payload_data = {
        "sub": str(subject),
        "exp": int(
            time.time()
            + settings.access_token_expire_minutes * 60
        ),
    }

    payload = _b64(
        json.dumps(
            payload_data,
            separators=(",", ":"),
        ).encode()
    )

    signature = _b64(
        hmac.new(
            settings.secret_key.encode(),
            f"{header}.{payload}".encode(),
            hashlib.sha256,
        ).digest()
    )

    return f"{header}.{payload}.{signature}"


def decode_access_token(token: str):
    try:
        header, payload, signature = token.split(".")

        expected_signature = _b64(
            hmac.new(
                settings.secret_key.encode(),
                f"{header}.{payload}".encode(),
                hashlib.sha256,
            ).digest()
        )

        if not hmac.compare_digest(
            signature,
            expected_signature,
        ):
            return None

        padding = "=" * (
            (4 - len(payload) % 4) % 4
        )

        data = json.loads(
            base64.urlsafe_b64decode(
                payload + padding
            )
        )

        if data.get("exp", 0) < time.time():
            return None

        return data.get("sub")

    except Exception:
        return None