import os
from datetime import datetime


def get_file_path_from_raw(call_sid, to_number, folder_name, file_prefix, file_extension, params):
    """
    Generate a file path based on the given parameters.

    Args:
        call_sid (str): The call SID.
        to_number (str): The recipient's phone number.
        folder_name (str): The name of the folder to store the file.
        file_prefix (str): The prefix for the file name.
        file_extension (str): The file extension.
        params (dict): A dictionary containing configuration parameters.

    Returns:
        str: The generated file path, or None if the path couldn't be created.
    """
    # Extract the relevant parameters
    base_path = params.get("base_path", "")
    company_name = params.get("company_name", "")

    # Create the directory structure
    date_str = datetime.now().strftime("%Y-%m-%d")
    directory = os.path.join(base_path, company_name, folder_name, date_str)

    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Generate the file name
    file_name = f"{file_prefix}_{call_sid}_{to_number}.{file_extension}"

    # Combine the directory and file name
    file_path = os.path.join(directory, file_name)

    return file_path
