from fastapi import APIRouter, Depends

from ..dependencies import get_current_user
from ..models import User
from ..models.schemas import ThemeIn
from ..services.theme_service import theme_css

router = APIRouter(tags=["theme"])


@router.post("/theme/css")
def make_css(theme: ThemeIn, user: User = Depends(get_current_user)):
    """Devuelve el CSS que se enviará al generador con el siguiente build (sirve para verlo en la interfaz)."""
    return {"css": theme_css(theme)}
