from fastapi import APIRouter, Depends, Response

from ..dependencies import get_auth_service, get_current_user
from ..models import User
from ..models.schemas import LoginIn, TokenOut, UserOut
from ..services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, service: AuthService = Depends(get_auth_service)):
    return TokenOut(access_token=service.login(body.email, body.password))


@router.post("/logout", status_code=204)
def logout(_: User = Depends(get_current_user)):
    # El token es JWT sin estado: el cliente simplemente lo descarta.
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
