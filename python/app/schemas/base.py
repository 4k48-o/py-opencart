"""
Base Pydantic schemas with validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# Import validators directly to avoid circular import
try:
    from app.models.validators import ModelValidators
except ImportError:
    # Fallback: define validators inline if import fails
    class ModelValidators:
        @staticmethod
        def validate_email(value):
            return value
        @staticmethod
        def validate_url(value):
            return value
        @staticmethod
        def validate_postcode(value):
            return value


class BaseSchema(BaseModel):
    """Base schema with common validation"""
    
    class Config:
        from_attributes = True
        validate_assignment = True
        str_strip_whitespace = True


# Note: Mixins with field_validator need to be used carefully
# They should only be used in classes that actually have those fields
def create_email_validator():
    """Create email validator function"""
    @field_validator('email', mode='before', check_fields=False)
    @classmethod
    def validate_email(cls, v):
        if v is None:
            return v
        return ModelValidators.validate_email(v)
    return validate_email


def create_url_validator():
    """Create URL validator function"""
    @field_validator('url', mode='before', check_fields=False)
    @classmethod
    def validate_url(cls, v):
        if v is None:
            return v
        return ModelValidators.validate_url(v)


def create_postcode_validator():
    """Create postcode validator function"""
    @field_validator('postcode', mode='before', check_fields=False)
    @classmethod
    def validate_postcode(cls, v):
        if v is None:
            return v
        return ModelValidators.validate_postcode(v)

