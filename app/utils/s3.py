import os
import logging
import tempfile
from typing import Optional, List, Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def get_s3_client():
    """
    Get an AWS S3 client instance.
    
    Returns:
        S3 client
    """
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION", "ap-southeast-1")
    
    try:
        return boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        raise

async def upload_file_to_s3(
    file_path: str,
    bucket_name: str,
    object_name: Optional[str] = None
) -> Optional[str]:
    """
    Upload a file to an S3 bucket.
    
    Args:
        file_path: Path to the file
        bucket_name: Name of the S3 bucket
        object_name: S3 object name (if not specified, file_path basename is used)
        
    Returns:
        S3 URI if successful, None otherwise
    """
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    try:
        s3_client = get_s3_client()
        s3_client.upload_file(file_path, bucket_name, object_name)
        
        s3_uri = f"s3://{bucket_name}/{object_name}"
        logger.info(f"Uploaded {file_path} to {s3_uri}")
        return s3_uri
    
    except ClientError as e:
        logger.error(f"Error uploading file to S3: {e}")
        return None

async def download_file_from_s3(
    s3_uri: str,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Download a file from S3.
    
    Args:
        s3_uri: S3 URI (s3://bucket-name/object-name)
        output_path: Path to save the file (if not specified, a temp file is created)
        
    Returns:
        Path to the downloaded file if successful, None otherwise
    """
    try:
        # Parse S3 URI
        if not s3_uri.startswith("s3://"):
            logger.error(f"Invalid S3 URI: {s3_uri}")
            return None
        
        parts = s3_uri[5:].split("/", 1)
        if len(parts) != 2:
            logger.error(f"Invalid S3 URI format: {s3_uri}")
            return None
        
        bucket_name = parts[0]
        object_name = parts[1]
        
        # Create output path if not specified
        if output_path is None:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, os.path.basename(object_name))
        
        # Download file
        s3_client = get_s3_client()
        s3_client.download_file(bucket_name, object_name, output_path)
        
        logger.info(f"Downloaded {s3_uri} to {output_path}")
        return output_path
    
    except ClientError as e:
        logger.error(f"Error downloading file from S3: {e}")
        return None

async def list_files_in_s3_bucket(
    bucket_name: str,
    prefix: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List files in an S3 bucket.
    
    Args:
        bucket_name: Name of the S3 bucket
        prefix: Filter objects by prefix
        
    Returns:
        List of objects in the bucket
    """
    try:
        s3_client = get_s3_client()
        
        params = {'Bucket': bucket_name}
        if prefix:
            params['Prefix'] = prefix
        
        response = s3_client.list_objects_v2(**params)
        
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'uri': f"s3://{bucket_name}/{obj['Key']}"
                })
        
        return files
    
    except ClientError as e:
        logger.error(f"Error listing files in S3 bucket: {e}")
        return []

async def delete_file_from_s3(s3_uri: str) -> bool:
    """
    Delete a file from S3.
    
    Args:
        s3_uri: S3 URI (s3://bucket-name/object-name)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Parse S3 URI
        if not s3_uri.startswith("s3://"):
            logger.error(f"Invalid S3 URI: {s3_uri}")
            return False
        
        parts = s3_uri[5:].split("/", 1)
        if len(parts) != 2:
            logger.error(f"Invalid S3 URI format: {s3_uri}")
            return False
        
        bucket_name = parts[0]
        object_name = parts[1]
        
        # Delete file
        s3_client = get_s3_client()
        s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        
        logger.info(f"Deleted {s3_uri}")
        return True
    
    except ClientError as e:
        logger.error(f"Error deleting file from S3: {e}")
        return False
