"""Service for interacting with AWS S3 storage."""
import logging
import boto3
import aioboto3
from botocore.exceptions import ClientError
from ..config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for uploading, downloading, and deleting files from S3."""

    def __init__(self):
        self.session = aioboto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self.bucket_name = settings.s3_bucket_name
        self.endpoint_url = settings.aws_endpoint_url

        # Sync boto3 client reused for presigned URL generation (pure CPU, no network)
        self._sync_s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            endpoint_url=settings.aws_endpoint_url,
        )

    async def upload_file(
        self,
        file_data: bytes,
        s3_key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload a file to S3.

        Args:
            file_data: The binary content of the file
            s3_key: The S3 key (path) where the file will be stored
            content_type: The MIME type of the file

        Returns:
            The S3 key of the uploaded file

        Raises:
            Exception: If upload fails
        """
        try:
            async with self.session.client(
                "s3", endpoint_url=self.endpoint_url
            ) as s3_client:
                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_data,
                    ContentType=content_type,
                )
                logger.info(f"Successfully uploaded file to S3: {s3_key}")
                return s3_key
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise Exception(f"S3 upload failed: {str(e)}")

    async def download_file(self, s3_key: str) -> bytes:
        """
        Download a file from S3.

        Args:
            s3_key: The S3 key of the file to download

        Returns:
            The binary content of the file

        Raises:
            Exception: If download fails
        """
        try:
            async with self.session.client(
                "s3", endpoint_url=self.endpoint_url
            ) as s3_client:
                response = await s3_client.get_object(
                    Bucket=self.bucket_name, Key=s3_key
                )
                async with response["Body"] as stream:
                    file_data = await stream.read()
                logger.info(f"Successfully downloaded file from S3: {s3_key}")
                return file_data
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise Exception(f"S3 download failed: {str(e)}")

    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_key: The S3 key of the file to delete

        Returns:
            True if deletion was successful

        Raises:
            Exception: If deletion fails
        """
        try:
            async with self.session.client(
                "s3", endpoint_url=self.endpoint_url
            ) as s3_client:
                await s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                logger.info(f"Successfully deleted file from S3: {s3_key}")
                return True
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            raise Exception(f"S3 deletion failed: {str(e)}")

    async def delete_files(self, s3_keys: list[str]) -> dict:
        """
        Delete multiple files from S3 in a single batch request.
        S3 allows up to 1000 keys per batch delete.

        Args:
            s3_keys: List of S3 keys to delete

        Returns:
            dict with 'deleted' (list of keys) and 'errors' (list of failed keys)
        """
        if not s3_keys:
            return {"deleted": [], "errors": []}

        results = {"deleted": [], "errors": []}

        try:
            async with self.session.client(
                "s3", endpoint_url=self.endpoint_url
            ) as s3_client:
                for i in range(0, len(s3_keys), 1000):
                    batch = s3_keys[i:i + 1000]
                    delete_objects = {"Objects": [{"Key": key} for key in batch]}

                    response = await s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete=delete_objects,
                    )

                    for deleted in response.get("Deleted", []):
                        results["deleted"].append(deleted["Key"])

                    for error in response.get("Errors", []):
                        logger.error(
                            f"Failed to delete {error['Key']}: {error['Message']}"
                        )
                        results["errors"].append(error["Key"])

            logger.info(
                f"Batch delete: {len(results['deleted'])} succeeded, "
                f"{len(results['errors'])} failed"
            )
        except ClientError as e:
            logger.error(f"Batch delete failed: {e}")
            results["errors"].extend(s3_keys)

        return results

    async def list_keys_by_prefix(self, prefix: str) -> list[str]:
        """List all S3 keys under a given prefix."""
        keys = []
        try:
            async with self.session.client(
                "s3", endpoint_url=self.endpoint_url
            ) as s3_client:
                paginator = s3_client.get_paginator("list_objects_v2")
                async for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                    for obj in page.get("Contents", []):
                        keys.append(obj["Key"])
        except ClientError as e:
            logger.error(f"Failed to list objects by prefix {prefix}: {e}")
        return keys

    async def generate_presigned_url(
        self, s3_key: str, expiration: int = 3600
    ) -> str:
        """Generate a presigned URL using the cached sync client (pure CPU, no network)."""
        try:
            url = self._sync_s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"Presigned URL generation failed: {str(e)}")


# Singleton instance
s3_service = S3Service()
