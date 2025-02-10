from pydantic import BaseModel

class UserSettings(BaseModel):
    use_openai: bool = False
    enable_document_search: bool = True
    handle_urls: bool = True
    check_db: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "use_openai": False,
                "enable_document_search": True,
                "handle_urls": True,
                "check_db": True
            }
        } 