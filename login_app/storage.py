"""Persist accounts under the project `data/` directory."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from login_app.config import DATA_DIR, USERS_FILE
from login_app.validators import SignInData, SignUpData, ValidationResult


@dataclass(frozen=True, slots=True)
class StoredUser:
    username: str
    password_hash: str
    salt: str
    email: str
    phone: str
    created_at: str


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return digest.hex()


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_raw() -> dict[str, dict[str, str]]:
    if not USERS_FILE.is_file():
        return {}
    with USERS_FILE.open(encoding="utf-8") as handle:
        return json.load(handle)


def _save_raw(users: dict[str, dict[str, str]]) -> None:
    _ensure_data_dir()
    with USERS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(users, handle, indent=2, sort_keys=True)


def register_user(data: SignUpData) -> ValidationResult:
    username = data.username.strip()
    users = _load_raw()
    if username.lower() in {key.lower() for key in users}:
        return ValidationResult.failure("That username is already registered.")

    salt = secrets.token_hex(16)
    record = StoredUser(
        username=username,
        password_hash=_hash_password(data.password, salt),
        salt=salt,
        email=data.email.strip(),
        phone=data.phone.strip(),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    users[username] = asdict(record)
    _save_raw(users)
    return ValidationResult.success()


def authenticate(data: SignInData) -> ValidationResult:
    username = data.username.strip()
    users = _load_raw()
    record = users.get(username)
    if record is None:
        for key, value in users.items():
            if key.lower() == username.lower():
                record = value
                break
    if record is None:
        return ValidationResult.failure("Unknown username or incorrect password.")

    expected = record["password_hash"]
    actual = _hash_password(data.password, record["salt"])
    if secrets.compare_digest(expected, actual):
        return ValidationResult.success()
    return ValidationResult.failure("Unknown username or incorrect password.")
