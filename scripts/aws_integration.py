"""Simple AWS helpers (stubs) for S3 upload and SQS send.

These functions try to use boto3 if available and AWS credentials are configured.
If boto3 is not available or credentials aren't present, they log the intended action.
This provides a safe integration point for later injection.
"""
import os
import logging

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    HAS_BOTO3 = True
except Exception:
    HAS_BOTO3 = False

logger = logging.getLogger(__name__)


def upload_to_s3(bucket_name, key, filename, extra_args=None):
    """Upload a local file to S3. Returns True on success, False otherwise.

    This is a lightweight wrapper to allow future injection.
    """
    if not HAS_BOTO3:
        logger.info(f"[stub] Would upload {filename} -> s3://{bucket_name}/{key}")
        return True
    try:
        s3 = boto3.client('s3')
        kwargs = extra_args or {}
        s3.upload_file(filename, bucket_name, key, ExtraArgs=kwargs)
        logger.info(f"Uploaded {filename} to s3://{bucket_name}/{key}")
        return True
    except (BotoCoreError, ClientError) as e:
        logger.exception("S3 upload failed")
        return False


def send_sqs_message(queue_url, message_body, message_attributes=None):
    """Send a message to SQS. Returns True on success, False otherwise."""
    if not HAS_BOTO3:
        logger.info(f"[stub] Would send message to SQS {queue_url}: {message_body}")
        return True
    try:
        sqs = boto3.client('sqs')
        params = {
            'QueueUrl': queue_url,
            'MessageBody': message_body
        }
        if message_attributes:
            params['MessageAttributes'] = message_attributes
        sqs.send_message(**params)
        logger.info(f"Sent message to SQS {queue_url}")
        return True
    except (BotoCoreError, ClientError):
        logger.exception("SQS send failed")
        return False
