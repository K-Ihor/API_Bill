from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import sessionmaker, Session
from fastapi.responses import PlainTextResponse
from sqlalchemy import create_engine
import bcrypt
from jose import JWTError, jwt
from datetime import timedelta
from passlib.hash import bcrypt
from fastapi import Query


from src.models import *
from src.utils import (generate_receipt_text, hash_password,
                       user_to_pydantic, create_access_token,
                       oauth2_scheme)
from src.config import *


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


@app.post("/register", response_model=UserOut)
def register_user(user_create: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_create.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    new_user = User(username=user_create.username, hashed_password=hash_password(user_create.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return user_to_pydantic(new_user)


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not bcrypt.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/create_receipt", response_model=ReceiptView)
def create_receipt(receipt_create: ReceiptCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    new_receipt = Receipt(
        user_id=current_user.id,
        total_amount=0.0,
        payment_type=receipt_create.payment["type"],
        rest_amount=0.0,
    )
    db.add(new_receipt)
    db.commit()
    db.refresh(new_receipt)

    total_amount = 0.0
    for product_info in receipt_create.products:
        product = Product(
            receipt_id=new_receipt.id,
            name=product_info["name"],
            price=product_info["price"],
            quantity=product_info["quantity"],
            total=product_info["price"] * product_info["quantity"],
        )
        db.add(product)
        total_amount += product.total

    new_receipt.total_amount = total_amount

    if receipt_create.payment["type"] == "cash":
        rest_amount = receipt_create.payment["amount"] - total_amount
        new_receipt.rest_amount = rest_amount

    db.commit()
    db.refresh(new_receipt)

    response_data = {
        "id": new_receipt.id,
        "products": [
            {
                "name": product.name,
                "price": product.price,
                "quantity": product.quantity,
                "total": product.total,
            }
            for product in new_receipt.products
        ],
        "payment": receipt_create.payment,
        "total": new_receipt.total_amount,
        "rest": new_receipt.rest_amount,
        "created_at": new_receipt.created_at,
    }

    return response_data


@app.get("/receipts", response_model=List[ReceiptView])
def get_user_receipts(
    current_user: User = Depends(get_current_user),
    filter_params: ReceiptFilter = Depends(),
    db: Session = Depends(get_db),
):
    query = db.query(Receipt).filter(Receipt.user_id == current_user.id)

    if filter_params.start_date:
        query = query.filter(Receipt.created_at >= filter_params.start_date)
    if filter_params.end_date:
        query = query.filter(Receipt.created_at <= filter_params.end_date)
    if filter_params.min_total_amount is not None:
        query = query.filter(Receipt.total_amount >= filter_params.min_total_amount)
    if filter_params.payment_type:
        query = query.filter(Receipt.payment_type == filter_params.payment_type)

    receipts = query.all()

    result = [
        ReceiptView(
            id=receipt.id,
            products=[
                {
                    "name": product.name,
                    "price": product.price,
                    "quantity": product.quantity,
                    "total": product.total,
                }
                for product in receipt.products
            ],
            payment={
                "type": receipt.payment_type,
                "amount": receipt.total_amount,
            },
            total=receipt.total_amount,
            rest=receipt.rest_amount,
            created_at=receipt.created_at,
        )
        for receipt in receipts
    ]

    return result


@app.get("/receipts/{receipt_id}/view", response_class=PlainTextResponse)
def view_receipt(receipt_id: int, chars: int = Query(50, ge=10, le=200), db: Session = Depends(get_db)):
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found",
        )
    receipt_text = generate_receipt_text(receipt, chars)
    return receipt_text
