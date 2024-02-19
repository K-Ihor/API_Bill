from fastapi.testclient import TestClient
from src.main import app, get_db
from src.models import UserCreate, User
from passlib.hash import bcrypt


def test_register_user(test_db):
    app.dependency_overrides[get_db] = lambda: test_db
    client = TestClient(app)
    test_db.query(User).delete()

    response = client.post("/register", json={"username": "test_user", "password": "test_password"})

    assert response.status_code == 200
    assert response.json()["username"] == "test_user"
    user = test_db.query(User).filter(User.username == "test_user").first()
    assert user is not None
    assert user.username == "test_user"
    assert bcrypt.verify("test_password", user.hashed_password)


def test_login_for_access_token(test_db):
    app.dependency_overrides[get_db] = lambda: test_db
    client = TestClient(app)
    test_db.query(User).delete()

    user_create = UserCreate(username="test_user4", password="test_password")
    response = client.post("/register", json=user_create.dict(), headers={"Content-Type": "application/json"})
    assert response.status_code == 200

    login_data = {"username": "test_user4", "password": "test_password"}
    response = client.post("/token", data=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"




