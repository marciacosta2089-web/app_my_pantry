from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

from pantry_app.models import SessionLocal, User, ensure_default_user


class AuthService:
    def __init__(self):
        self.db = SessionLocal()
        ensure_default_user(self.db)

    def get_user(self, username: str) -> Optional[User]:
        return self.db.query(User).filter_by(username=username).first()

    def register(self, username: str, password: str) -> User:
        existing = self.get_user(username)
        if existing:
            raise ValueError("User already exists")
        user = User(username=username, password_hash=generate_password_hash(password))
        self.db.add(user)
        self.db.commit()
        return user

    def verify(self, username: str, password: str) -> Optional[User]:
        user = self.get_user(username)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
