from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = PROJECT_ROOT / "src/bookshelf/seeds/taxonomy.yaml"


class FakeThumbnailStorage:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, str]] = []
        self.deletions: list[str] = []

    def upload_from_path(self, path: str) -> tuple[str, None]:
        self.uploads.append(("path", path))
        return (f"thumbnails/fake-path-object-{len(self.uploads)}", None)

    def upload_from_url(self, url: str) -> tuple[str, str]:
        self.uploads.append(("url", url))
        return (f"thumbnails/fake-url-object-{len(self.uploads)}", url)

    def delete_object(self, object_key: str) -> None:
        self.deletions.append(object_key)
