from pydantic import BaseModel, ConfigDict


class OnboardResponse(BaseModel):
    """Response schema for POST /me/onboard."""

    id: int
    clerk_user_id: str
    name: str | None
    email: str | None
    department: str | None

    model_config = ConfigDict(from_attributes=True)


class OnboardRequest(BaseModel):
    name: str
    email: str
    department: str | None = None
