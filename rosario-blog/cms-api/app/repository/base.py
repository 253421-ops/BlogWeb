from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..exceptions import ConflictError

T = TypeVar("T")


class BaseRepository(Generic[T]):
    model: type[T]

    def __init__(self, db: Session):
        self.db = db

    def get(self, entity_id: int) -> T | None:
        return self.db.get(self.model, entity_id)

    def save(self, entity: T, conflict_message: str = "El recurso ya existe") -> T:
        """Inserta o actualiza. Una violación de unicidad se informa como ConflictError."""
        self.db.add(entity)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError(conflict_message)
        return entity

    def delete(self, entity: T) -> None:
        self.db.delete(entity)
        self.db.commit()


class BlogScopedRepository(BaseRepository[T]):
    """Entidades que pertenecen a un blog (páginas, publicaciones, categorías...)."""

    def get_in_blog(self, blog_id: int, entity_id: int) -> T | None:
        entity = self.get(entity_id)
        return entity if entity is not None and entity.blog_id == blog_id else None

    def list_by_blog(self, blog_id: int) -> list[T]:
        q = select(self.model).where(self.model.blog_id == blog_id).order_by(self.model.id)
        return list(self.db.scalars(q).all())

    def slug_exists(self, blog_id: int, slug: str) -> bool:
        q = select(self.model.id).where(self.model.blog_id == blog_id, self.model.slug == slug)
        return self.db.scalar(q) is not None
