from pydantic import BaseModel, Field

class MasterLoginRequest(BaseModel):
    username: str = Field(..., example="superadmin")
    password: str = Field(..., example="secure_password123")