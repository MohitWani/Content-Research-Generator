from sqlalchemy.orm import Session

from app.modules.user.models.user_model import User


class UserRepository:
    def __init__(self):
        pass

    def list_users(self, db: Session) -> list[User]:
        return db.query(User).all()

    def get_user_by_id(self, db: Session, user_id: str) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def create_user(self, db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
