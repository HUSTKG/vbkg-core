import re
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import uuid

def is_valid_email(email: str) -> bool:
    """
    Validate an email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if the email is valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def is_valid_uuid(value: str) -> bool:
    """
    Validate a UUID string.
    
    Args:
        value: String to validate
        
    Returns:
        True if the string is a valid UUID, False otherwise
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False

def is_valid_url(url: str) -> bool:
    """
    Validate a URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if the URL is valid, False otherwise
    """
    pattern = r"^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?(?:/[-\w%!$&'()*+,;=:@/~]+)*(?:\?[-\w%!$&'()*+,;=:@/~]*)?(?:#[-\w%!$&'()*+,;=:@/~]*)?$"
    return bool(re.match(pattern, url))

def is_valid_password(password: str, min_length: int = 8) -> Dict[str, Any]:
    """
    Validate a password.
    
    Args:
        password: Password to validate
        min_length: Minimum password length
        
    Returns:
        Dictionary with validation result and error messages
    """
    errors = []
    
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters long")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate that required fields are present and not empty.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Returns:
        Dictionary with validation result and error messages
    """
    errors = []
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            errors.append(f"Required field cannot be empty: {field}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def is_valid_iso_date(date_str: str) -> bool:
    """
    Validate an ISO 8601 date string.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        True if the date string is valid, False otherwise
    """
    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False

def validate_numeric_range(value: Union[int, float], min_value: Optional[Union[int, float]] = None, max_value: Optional[Union[int, float]] = None) -> Dict[str, Any]:
    """
    Validate that a numeric value is within a specified range.
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value, or None for no minimum
        max_value: Maximum allowed value, or None for no maximum
        
    Returns:
        Dictionary with validation result and error messages
    """
    errors = []
    
    if min_value is not None and value < min_value:
        errors.append(f"Value must be greater than or equal to {min_value}")
    
    if max_value is not None and value > max_value:
        errors.append(f"Value must be less than or equal to {max_value}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def is_valid_json(json_str: str) -> bool:
    """
    Validate a JSON string.
    
    Args:
        json_str: JSON string to validate
        
    Returns:
        True if the string is valid JSON, False otherwise
    """
    try:
        import json
        json.loads(json_str)
        return True
    except (ValueError, SyntaxError):
        return False

def sanitize_input(value: str) -> str:
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        value: Input string to sanitize
        
    Returns:
        Sanitized string
    """
    if not value:
        return value
    
    # Replace potentially dangerous characters
    sanitized = value
    sanitized = sanitized.replace('<', '&lt;')
    sanitized = sanitized.replace('>', '&gt;')
    sanitized = sanitized.replace('"', '&quot;')
    sanitized = sanitized.replace("'", '&#x27;')
    sanitized = sanitized.replace('/', '&#x2F;')
    
    return sanitized

def validate_entity_type(entity_type: str, allowed_types: List[str] = None) -> Dict[str, Any]:
    """
    Validate an entity type.
    
    Args:
        entity_type: Entity type to validate
        allowed_types: List of allowed entity types, or None to allow any type
        
    Returns:
        Dictionary with validation result and error messages
    """
    errors = []
    
    if not entity_type:
        errors.append("Entity type cannot be empty")
    
    if allowed_types and entity_type not in allowed_types:
        errors.append(f"Invalid entity type. Allowed types: {', '.join(allowed_types)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def validate_relationship_type(relationship_type: str, allowed_types: List[str] = None) -> Dict[str, Any]:
    """
    Validate a relationship type.
    
    Args:
        relationship_type: Relationship type to validate
        allowed_types: List of allowed relationship types, or None to allow any type
        
    Returns:
        Dictionary with validation result and error messages
    """
    errors = []
    
    if not relationship_type:
        errors.append("Relationship type cannot be empty")
    
    if allowed_types and relationship_type not in allowed_types:
        errors.append(f"Invalid relationship type. Allowed types: {', '.join(allowed_types)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
