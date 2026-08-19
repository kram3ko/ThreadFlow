import os

import boto3
from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the configured S3-compatible bucket when it does not exist."

    def handle(self, *args, **options) -> None:
        endpoint = os.getenv("S3_ENDPOINT_URL")
        bucket = os.getenv("S3_BUCKET")
        if not endpoint or not bucket:
            return
        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
            region_name=os.getenv("S3_REGION", "us-east-1"),
            use_ssl=os.getenv("S3_USE_SSL", "false").lower() == "true",
        )
        try:
            client.head_bucket(Bucket=bucket)
        except ClientError:
            client.create_bucket(Bucket=bucket)
