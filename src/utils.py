from fastapi.security import OAuth2PasswordBearer
from src.config import SECRET_KEY, ALGORITHM
import bcrypt
from datetime import timedelta
from passlib.hash import bcrypt
from jose import jwt


from src.models import *

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def user_to_pydantic(user: User) -> UserOut:
    return UserOut(id=user.id, username=user.username)


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_receipt_text(receipt: Receipt, chars: int) -> str:
    lines = [
        "      ФОП Джонсонюк Борис",
        "================================",
        # Додати рядки для кожного товару в чеку
        f"СУМА                {receipt.total_amount:.2f}",
        f"Картка              {receipt.total_amount:.2f}",
        f"Решта                       {receipt.rest_amount:.2f}",
        "================================",
        f"        {receipt.created_at.day:02d}.{receipt.created_at.month:02d}  "
        f"{receipt.created_at.hour:02d}:{receipt.created_at.minute:02d}        ",
        "      Дякуємо за покупку!",
    ]
    formatted_lines = [line[:chars].ljust(chars) for line in lines]

    return "\n".join(formatted_lines)
