from fastapi import HTTPException
import magic
import os
from typing import Set, Optional

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

        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Supported types: {', '.join(self.allowed_extensions)}"
            )

        # Check mime type
        mime_type = self.mime.from_buffer(content)
        allowed_mimes = {
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }

        if file_ext in allowed_mimes and mime_type != allowed_mimes[file_ext]:
            raise HTTPException(
                status_code=400,
                detail=f"File content doesn't match its extension"
            ) 