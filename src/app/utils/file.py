# File: application/src/app/utils/file.py
import os
import uuid
import logging
from typing import Optional

from fastapi import UploadFile, HTTPException, status
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Import Cloudinary configuration
from app.config.cloudinary_config import cloudinary

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create file handler
log_path = os.path.join("/tmp", "cloudinary_upload.log")
fh = logging.FileHandler(log_path)
fh.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(fh)

def upload_file_to_cloudinary(file_obj, public_id: str, folder: Optional[str] = None) -> str:
    """
    Upload file to Cloudinary.
    
    Args:
        file_obj: File-like object containing the data
        public_id: The public ID to assign to the uploaded file
        folder: Optional folder path in Cloudinary
        
    Returns:
        str: URL to the uploaded file
    """
    try:
        file_obj.seek(0)
        
        # Prepare upload options
        upload_options = {
            'resource_type': 'auto',  # Automatically detect the resource type
            'public_id': public_id,
        }
        
        if folder:
            upload_options['folder'] = folder.rstrip('/')
        
        # Upload the file
        result = cloudinary.uploader.upload(file_obj, **upload_options)
        
        # Get the secure URL
        url, options = cloudinary_url(
            result['public_id'],
            format=result.get('format', ''),
            secure=True
        )
        
        logger.debug(f"Successfully uploaded file to Cloudinary: {url}")
        return url
        
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to Cloudinary: {str(e)}"
        )

def save_upload_and_get_url(file: UploadFile, folder: str = "") -> str:
    """
    Upload the file to Cloudinary and return the URL.
    
    Args:
        file: UploadFile object from FastAPI
        folder: Optional folder path in Cloudinary
        
    Returns:
        str: URL to the uploaded file
    """
    try:
        # Generate a unique filename
        ext = os.path.splitext(file.filename)[1].lower()
        file_id = uuid.uuid4().hex
        public_id = f"{file_id}"
        
        # Upload the file
        file.file.seek(0)
        return upload_file_to_cloudinary(file.file, public_id, folder)
        
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        if not isinstance(e, HTTPException):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process file upload: {str(e)}"
            )
        raise
