import bcrypt
from datetime import timedelta, datetime
from src.utils import (
    hash_password,
    user_to_pydantic,
    create_access_token,
    generate_receipt_text,
)
from src.models import User, Receipt


def test_hash_password():
    password = "test_password"
    hashed_password = hash_password(password)
    assert bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def test_user_to_pydantic():
    user = User(id=1, username="test_user", hashed_password="hashed_password")
    user_out = user_to_pydantic(user)
    assert user_out.id == user.id
    assert user_out.username == user.username


def test_create_access_token():
    data = {"sub": "test_user"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta)
    assert token


def test_generate_receipt_text():
    receipt = Receipt(
        total_amount=50.0,
        rest_amount=20.0,
        created_at=datetime(2024, 2, 19, 12, 30),
    )
    chars = 80
    receipt_text = generate_receipt_text(receipt, chars)
    assert receipt_text


def test_generate_receipt_text_invalid_chars():
    receipt = Receipt(total_amount=50.0, rest_amount=20.0, created_at=datetime(2024, 2, 19, 12, 30))
    chars = 5
    result = generate_receipt_text(receipt, chars)

    assert len(result) > chars
