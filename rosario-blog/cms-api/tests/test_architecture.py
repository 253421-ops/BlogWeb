"""Verifica que las cuatro capas del CMS respeten sus dependencias."""
import re
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"

# capa -> fragmentos que NO puede importar
RULES = {
    "controllers": ["repository", "sqlalchemy"],
    "services": ["fastapi", "controllers", "sqlalchemy"],
    "repository": ["fastapi", "services", "controllers"],
    "models": ["fastapi", "services", "controllers", "repository"],
}


def _imports(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"\s*(from|import)\s", line):
            yield line.strip()


def test_layers_respect_dependencies():
    violations = []
    for layer, forbidden in RULES.items():
        for file in (APP / layer).glob("*.py"):
            for line in _imports(file):
                for word in forbidden:
                    if re.search(rf"\b{word}\b", line):
                        violations.append(f"{layer}/{file.name}: {line}")
    assert not violations, "\n".join(violations)


def test_four_layers_exist():
    for layer in ("controllers", "services", "repository", "models"):
        assert (APP / layer).is_dir()
