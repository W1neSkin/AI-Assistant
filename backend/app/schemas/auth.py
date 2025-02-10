from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class RegisterRequest(BaseModel):
    username: str
    password: str
    confirm_password: str
    use_openai: bool = False
    enable_document_search: bool = False
    handle_urls: bool = False
    check_db: bool = False

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer" 