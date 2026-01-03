"""Validation utilities"""


def validate_required_fields(data: dict, required_fields: list) -> tuple:
    """
    Validate that required fields are present in data
    
    Returns:
        tuple: (is_valid, error_message)
    """
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None


def validate_file_id(file_id: str) -> tuple:
    """
    Validate file ID format
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file_id or not isinstance(file_id, str):
        return False, "Invalid file ID"
    
    return True, None


def validate_folder_id(folder_id: str) -> tuple:
    """
    Validate folder ID format
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(folder_id, str):
        return False, "Invalid folder ID"
    
    return True, None
