from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class RegisterRequest(BaseModel):
    username: str
    password: str
    confirm_password: str
    use_cloud: bool = False
    enable_document_search: bool = True
    handle_urls: bool = True
    check_db: bool = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer" 