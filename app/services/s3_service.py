"""S3 service: the one piece of cloud infrastructure used by the API.

This isolates all interaction with Amazon S3 behind a small, testable class, in
the same spirit as the repository isolating database access. The router and the
business logic never import boto3 directly.

Credentials are intentionally NOT passed in code. When the app runs on EC2 the
attached IAM role supplies them automatically via boto3's default credential
chain; locally, boto3 falls back to `~/.aws/credentials` or environment
variables if you have them. If no bucket is configured the service reports
itself as unconfigured and the export endpoint returns a clean 503 rather than
crashing -- so the API still runs perfectly well without AWS during local
development.
"""

from __future__ import annotations

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


class S3NotConfiguredError(RuntimeError):
    """Raised when an S3 operation is attempted without a bucket configured."""


class S3UploadError(RuntimeError):
    """Raised when an upload or presign call to S3 fails."""


class S3Service:
    """Thin wrapper around the S3 operations the API needs."""

    def __init__(
        self,
        bucket_name: str | None = None,
        region: str | None = None,
        presign_ttl: int | None = None,
    ) -> None:
        self._bucket = bucket_name if bucket_name is not None else settings.S3_BUCKET_NAME
        self._region = region or settings.AWS_REGION
        self._ttl = presign_ttl if presign_ttl is not None else settings.S3_PRESIGNED_URL_TTL
        self._client = None  # created lazily so import never needs AWS

    @property
    def is_configured(self) -> bool:
        """True when a bucket name is set and S3 can be used."""
        return bool(self._bucket)

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def ttl(self) -> int:
        """Validity window (seconds) for generated presigned URLs."""
        return self._ttl

    def _get_client(self):
        if self._client is None:
            self._client = boto3.client("s3", region_name=self._region)
        return self._client

    def upload_text(
        self,
        *,
        content: str,
        key: str,
        content_type: str = "text/plain",
    ) -> str:
        """Upload a text body to S3 and return a time-limited presigned URL.

        The bucket itself stays private (no public access); the presigned URL
        grants temporary read access to this single object only.
        """
        if not self.is_configured:
            raise S3NotConfiguredError(
                "S3_BUCKET_NAME is not set; the export feature is unavailable. "
                "Set S3_BUCKET_NAME (and run on a host with S3 permissions) to "
                "enable it."
            )

        client = self._get_client()
        try:
            client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType=content_type,
            )
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=self._ttl,
            )
        except (BotoCoreError, ClientError) as exc:  # pragma: no cover - network
            raise S3UploadError(f"Failed to upload to S3: {exc}") from exc

        return url
