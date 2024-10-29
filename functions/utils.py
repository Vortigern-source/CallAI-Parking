from typing import Dict, Any, Optional
import json
import re


def create_response(success: bool, message: str, additional_data: dict = None) -> str:
    """Create a standardized JSON response"""
    response = {"success" if success else "error": message}
    if additional_data:
        response.update(additional_data)
    return json.dumps(response)


def format_registration(registration: str) -> str:
    """
    Formats a vehicle registration number by removing special characters and spaces,
    and converting to uppercase.

    Args:
        registration (str): The registration number to format

    Returns:
        str: The formatted registration number
    """
    if not registration:
        return ""
    # Remove all non-alphanumeric characters and convert to uppercase
    return "".join(char for char in registration if char.isalnum()).upper()


def validate_required_args(arguments: dict, required_fields: list) -> None:
    """Validate required arguments"""
    missing = [field for field in required_fields if not arguments.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
