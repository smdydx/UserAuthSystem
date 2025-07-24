"""
Image upload utilities and helpers
"""
import os
import uuid
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
import aiofiles
from PIL import Image
import io


class ImageUploadService:
    """Service for handling image uploads"""
    
    # Supported image formats
    SUPPORTED_FORMATS = {'jpeg', 'jpg', 'png', 'webp'}
    
    # Maximum file size (5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    # Image size limits
    MAX_WIDTH = 2048
    MAX_HEIGHT = 2048
    
    @staticmethod
    def validate_image(file: UploadFile) -> None:
        """Validate uploaded image file"""
        # Check file extension
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        extension = file.filename.lower().split('.')[-1]
        if extension not in ImageUploadService.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Supported formats: {', '.join(ImageUploadService.SUPPORTED_FORMATS)}"
            )
        
        # Check file size
        if file.size and file.size > ImageUploadService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size too large. Maximum size: {ImageUploadService.MAX_FILE_SIZE // (1024 * 1024)}MB"
            )
    
    @staticmethod
    async def process_image(file: UploadFile) -> dict:
        """Process and resize image if needed"""
        # Validate file
        ImageUploadService.validate_image(file)
        
        # Read file content
        content = await file.read()
        
        # Open image with PIL
        try:
            image = Image.open(io.BytesIO(content))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
        
        # Get original dimensions
        original_width, original_height = image.size
        
        # Resize if too large
        if original_width > ImageUploadService.MAX_WIDTH or original_height > ImageUploadService.MAX_HEIGHT:
            # Calculate new dimensions maintaining aspect ratio
            ratio = min(
                ImageUploadService.MAX_WIDTH / original_width,
                ImageUploadService.MAX_HEIGHT / original_height
            )
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary (for JPEG)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Save processed image
        processed_io = io.BytesIO()
        format_map = {'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 'webp': 'WEBP'}
        extension = file.filename.lower().split('.')[-1]
        save_format = format_map.get(extension, 'JPEG')
        
        image.save(processed_io, format=save_format, quality=85, optimize=True)
        processed_content = processed_io.getvalue()
        
        return {
            'content': processed_content,
            'width': image.width,
            'height': image.height,
            'size': len(processed_content),
            'format': save_format.lower()
        }
    
    @staticmethod
    async def save_local_image(
        file: UploadFile, 
        upload_dir: str = "uploads/products"
    ) -> dict:
        """Save image locally and return file info"""
        # Process image
        processed_image = await ImageUploadService.process_image(file)
        
        # Generate unique filename
        extension = processed_image['format']
        if extension == 'jpeg':
            extension = 'jpg'
        
        unique_filename = f"{uuid.uuid4()}.{extension}"
        
        # Ensure upload directory exists
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(processed_image['content'])
        
        # Return file information
        return {
            'filename': unique_filename,
            'original_filename': file.filename,
            'path': file_path,
            'url': f"/{file_path}",  # Relative URL
            'width': processed_image['width'],
            'height': processed_image['height'],
            'size': processed_image['size'],
            'format': processed_image['format']
        }
    
    @staticmethod
    def delete_local_image(file_path: str) -> bool:
        """Delete local image file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        return False
    
    @staticmethod
    def get_image_url(filename: str, base_url: str = "") -> str:
        """Generate full image URL"""
        return f"{base_url}/uploads/products/{filename}"


class CloudinaryUploadService:
    """Service for Cloudinary image uploads (placeholder for future implementation)"""
    
    @staticmethod
    async def upload_image(file: UploadFile, folder: str = "products") -> dict:
        """Upload image to Cloudinary"""
        # This is a placeholder for Cloudinary integration
        # You would need to install cloudinary package and configure it
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Cloudinary integration not implemented. Use local upload instead."
        )


class S3UploadService:
    """Service for AWS S3 image uploads (placeholder for future implementation)"""
    
    @staticmethod
    async def upload_image(file: UploadFile, bucket: str, folder: str = "products") -> dict:
        """Upload image to S3"""
        # This is a placeholder for S3 integration
        # You would need to install boto3 package and configure AWS credentials
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="S3 integration not implemented. Use local upload instead."
        )