from pydantic import BaseModel, ConfigDict

class UserSettings(BaseModel):
    use_cloud: bool = False
    enable_document_search: bool = True
    handle_urls: bool = True
    check_db: bool = True

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "use_cloud": False,
                "enable_document_search": True,
                "handle_urls": True,
                "check_db": True
            }
        }
    )
         