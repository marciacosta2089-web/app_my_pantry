import json
from pantry_app.models import SessionLocal, User


class SettingsService:
    def __init__(self, user_id: int):
        self.db = SessionLocal()
        self.user_id = user_id

    def get_user(self) -> User:
        return self.db.query(User).get(self.user_id)

    def update(self, default_units: str = None, theme: str = None, llm_config: str = None):
        user = self.get_user()
        if default_units:
            user.default_units = default_units
        if theme:
            user.theme = theme
        if llm_config is not None:
            user.llm_config = llm_config
        self.db.commit()
        return user
