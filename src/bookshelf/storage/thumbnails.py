from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

import boto3
import httpx

from bookshelf.config.settings import Settings


class ThumbnailStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    def ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self.settings.s3_bucket)
        except Exception:
            self._client.create_bucket(Bucket=self.settings.s3_bucket)

    def upload_from_path(self, path: str) -> tuple[str, None]:
        self.ensure_bucket()
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"thumbnail file not found: {path}")

        object_key = self._build_object_key(file_path.name)
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        with file_path.open("rb") as handle:
            self._client.upload_fileobj(
                handle,
                self.settings.s3_bucket,
                object_key,
                ExtraArgs={"ContentType": content_type},
            )
        return object_key, None

    def upload_from_url(self, url: str) -> tuple[str, str]:
        self.ensure_bucket()
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()

        filename = url.rstrip("/").split("/")[-1] or "thumbnail"
        object_key = self._build_object_key(filename)
        content_type = response.headers.get("content-type", "application/octet-stream")
        self._client.put_object(
            Bucket=self.settings.s3_bucket,
            Key=object_key,
            Body=response.content,
            ContentType=content_type,
        )
        return object_key, url

    def delete_object(self, object_key: str) -> None:
        self.ensure_bucket()
        self._client.delete_object(Bucket=self.settings.s3_bucket, Key=object_key)

    def _build_object_key(self, filename: str) -> str:
        sanitized = filename.replace(" ", "-")
        return f"thumbnails/{uuid4()}-{sanitized}"
