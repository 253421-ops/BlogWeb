from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

SlugStr = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=160)]
Status = Literal["draft", "published"]
PageType = Literal["landing", "page"]


class CamelModel(BaseModel):
    """Entrada y salida en camelCase (blogId, createdAt...), como en el PDF."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


# --- Auth ---
class LoginIn(CamelModel):
    email: str
    password: str = Field(max_length=72)


class TokenOut(CamelModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(CamelModel):
    id: int
    email: str
    name: str


# --- Blogs ---
class BlogIn(CamelModel):
    name: str = Field(min_length=1, max_length=120)
    slug: SlugStr | None = None
    description: str | None = None


class BlogOut(CamelModel):
    id: int
    name: str
    slug: str
    description: str | None
    created_at: datetime


# --- Páginas ---
class PageIn(CamelModel):
    title: str = Field(min_length=1, max_length=200)
    slug: SlugStr | None = None
    type: PageType = "page"
    content: str = ""
    status: Status = "draft"


class PageOut(CamelModel):
    id: int
    blog_id: int
    type: PageType
    slug: str
    title: str
    content: str
    status: Status
    created_at: datetime
    updated_at: datetime


# --- Categorías ---
class CategoryIn(CamelModel):
    name: str = Field(min_length=1, max_length=120)
    slug: SlugStr | None = None


class CategoryOut(CamelModel):
    id: int
    blog_id: int
    name: str
    slug: str


# --- Publicaciones ---
class PostIn(CamelModel):
    title: str = Field(min_length=1, max_length=200)
    slug: SlugStr | None = None
    excerpt: str | None = None
    content: str = ""
    cover_url: str | None = None
    category_id: int | None = None
    status: Status = "draft"


class PostSummary(CamelModel):
    id: int
    blog_id: int
    category_id: int | None
    slug: str
    title: str
    excerpt: str | None
    cover_url: str | None
    status: Status
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PostOut(PostSummary):
    content: str


class PostList(CamelModel):
    items: list[PostSummary]
    total: int
    page: int
    limit: int


class StatusIn(CamelModel):
    status: Status


# --- Imágenes ---
class MediaOut(CamelModel):
    id: int
    blog_id: int
    filename: str
    url: str
    content_type: str
    size: int
    created_at: datetime


# --- Build ---
class BuildIn(CamelModel):
    blog_id: int
    include_drafts: bool = False


HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]


class ThemeIn(CamelModel):
    """Tema visual del sitio. Todo se valida: el color es #rrggbb y plantilla y tipografía salen de listas cerradas."""
    scene: Literal["noche", "atardecer", "amanecer"] = "noche"     # plantilla: paisaje y paleta del sitio
    accent: HexColor | None = None                                 # color de acento propio (si no, el de la plantilla)
    font: Literal["manuscrita", "clasica", "moderna"] = "manuscrita"
    blog: Literal["tarjetas", "lista"] = "tarjetas"                # cómo se ve el listado del blog


class BuildOut(CamelModel):
    id: int
    blog_id: int
    status: Literal["running", "success", "failed"]
    message: str | None
    result: dict | None
    created_at: datetime
    finished_at: datetime | None


# --- Métricas ---
class MetricsOut(CamelModel):
    visitas: int
    visitantes_unicos: int
    simulated: bool = False
    sesiones: int = 0
    tiempo_medio_seg: int = 0
    rebote_bp: int = 0
    dispositivos: dict = {}
    por_dia: list[dict] = []
    paginas: list[dict] = []
