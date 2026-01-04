"""
Pydantic validators for model field validation
"""
from typing import Any, Optional
from pydantic import field_validator, ValidationError


class ModelValidators:
    """Collection of reusable validators for model fields"""
    
    @staticmethod
    def validate_email(value: Optional[str]) -> Optional[str]:
        """Validate email format"""
        if value is None or value == '':
            return value
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError(f"Invalid email format: {value}")
        return value
    
    @staticmethod
    def validate_url(value: Optional[str]) -> Optional[str]:
        """Validate URL format"""
        if value is None or value == '':
            return value
        import re
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, value):
            raise ValueError(f"Invalid URL format: {value}")
        return value
    
    @staticmethod
    def validate_positive_int(value: Optional[int]) -> Optional[int]:
        """Validate that integer is positive"""
        if value is None:
            return value
        if value < 0:
            raise ValueError(f"Value must be positive, got: {value}")
        return value
    
    @staticmethod
    def validate_non_negative_int(value: Optional[int]) -> Optional[int]:
        """Validate that integer is non-negative"""
        if value is None:
            return value
        if value < 0:
            raise ValueError(f"Value must be non-negative, got: {value}")
        return value
    
    @staticmethod
    def validate_postcode(value: Optional[str]) -> Optional[str]:
        """Validate postcode format (basic validation)"""
        if value is None or value == '':
            return value
        # Basic validation: alphanumeric, spaces, hyphens, 3-10 characters
        import re
        if not re.match(r'^[A-Za-z0-9\s\-]{3,10}$', value):
            raise ValueError(f"Invalid postcode format: {value}")
        return value
    
    @staticmethod
    def validate_phone(value: Optional[str]) -> Optional[str]:
        """Validate phone number format (basic validation)"""
        if value is None or value == '':
            return value
        import re
        # Basic validation: digits, spaces, hyphens, parentheses, plus sign
        if not re.match(r'^[\d\s\-\+\(\)]{7,20}$', value):
            raise ValueError(f"Invalid phone number format: {value}")
        return value

