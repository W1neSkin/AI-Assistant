from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    use_cloud: bool = False
    # use_cloud is missing but being accessed in register endpoint 