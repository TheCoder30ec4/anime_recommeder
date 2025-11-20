from pydantic import BaseModel, field_validator


class Chat(BaseModel):
    session_id: str
    query: str

    @field_validator("session_id", "query", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: str) -> str:
        if not value:
            raise ValueError("session_id must not be empty.")
        return value

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        if not value:
            raise ValueError("query must not be empty.")
        if len(value) < 3:
            raise ValueError("query must contain at least 3 characters.")
        if len(value) > 2000:
            raise ValueError("query must be at most 2000 characters.")
        return value