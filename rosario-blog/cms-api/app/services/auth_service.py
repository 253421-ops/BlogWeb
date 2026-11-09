import jwt

from ..exceptions import UnauthorizedError
from ..models import User
from ..repository.user_repository import UserRepository
from ..security import create_token, decode_token, hash_password, verify_password


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    def login(self, email: str, password: str) -> str:
        user = self.users.get_by_email(email.lower())
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Credenciales inválidas")
        return create_token(user.id)

    def user_from_token(self, token: str) -> User:
        try:
            user_id = int(decode_token(token))
        except (jwt.PyJWTError, ValueError):
            raise UnauthorizedError("Token inválido o expirado")
        user = self.users.get(user_id)
        if user is None:
            raise UnauthorizedError("Usuario no encontrado")
        return user

    def ensure_admin(self, email: str, password: str) -> None:
        email = email.lower()
        if self.users.get_by_email(email) is None:
            self.users.save(User(email=email, name="Administrador", password_hash=hash_password(password)))
