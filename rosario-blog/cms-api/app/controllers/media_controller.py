from fastapi import APIRouter, Depends, File, Response, UploadFile

from ..dependencies import get_current_user, get_media_service
from ..models import User
from ..models.schemas import MediaOut
from ..services.media_service import MAX_BYTES, MediaService

router = APIRouter(prefix="/blogs/{blog_id}/media", tags=["media"])


@router.get("", response_model=list[MediaOut])
def list_media(blog_id: int, service: MediaService = Depends(get_media_service),
               user: User = Depends(get_current_user)):
    return service.list_media(blog_id, user)


@router.post("", response_model=MediaOut, status_code=201)
async def upload_media(blog_id: int, file: UploadFile = File(...),
                       service: MediaService = Depends(get_media_service),
                       user: User = Depends(get_current_user)):
    data = await file.read(MAX_BYTES + 1)
    return service.upload(blog_id, user, file.filename, file.content_type, data)


@router.delete("/{media_id}", status_code=204)
def delete_media(blog_id: int, media_id: int, service: MediaService = Depends(get_media_service),
                 user: User = Depends(get_current_user)):
    service.delete(blog_id, media_id, user)
    return Response(status_code=204)
