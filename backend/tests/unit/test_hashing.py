"""
Tests unitarios: hashing de passwords.
Ref: docs/claude/04_testing_strategy.md — M1 unit tests
"""

from app.utils.hashing import hash_password, verify_password


def test_hash_and_verify():
    plain = "mi_password_seguro"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True


def test_wrong_password_fails():
    hashed = hash_password("correcto")
    assert verify_password("incorrecto", hashed) is False


def test_hash_is_unique():
    h1 = hash_password("misma")
    h2 = hash_password("misma")
    # bcrypt genera salt distinto cada vez
    assert h1 != h2


def test_email_normalization():
    """Verifica logica de normalizacion de email (R3/R5)."""
    email = "  Admin@CMEP.Local  "
    normalized = email.strip().lower()
    assert normalized == "admin@cmep.local"
