import re


class PasswordValidator:
    """
    Password validation utility
    """

    def validate_password(self, password: str):
        """
        Validate password strength

        Checks:
        - Minimum length of 8 characters
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        - Contains at least one special character
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character")

        return True
