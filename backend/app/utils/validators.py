from fastapi import HTTPException
import magic
from typing import Set
from app.utils.logger import setup_logger

class FileValidator:
    def __init__(self, allowed_extensions: Set[str], max_size: int):
        self.allowed_extensions = allowed_extensions
        self.max_size = max_size
        self.mime = magic.Magic(mime=True)

    def validate_file(self, content: bytes, filename: str) -> None:
        """Validate file size, extension and mime type"""
        # Check file size
        if len(content) > self.max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {self.max_size/1024/1024}MB"
            )

        # Get file extension without the dot
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Supported types: {', '.join(self.allowed_extensions)}"
            )

        # Check mime type
        mime_type = self.mime.from_buffer(content)
        allowed_mimes = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'html': 'text/html',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }

        expected_mime = allowed_mimes.get(extension)
        if expected_mime and not mime_type.startswith(expected_mime):
            raise HTTPException(
                status_code=400,
                detail=f"File content doesn't match its extension"
            ) 