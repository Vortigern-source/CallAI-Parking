import json
import os


def read_params():
    """
    Read parameters from a JSON file.

    Returns:
        dict: A dictionary containing the parameters.
    """
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the params.json file (two levels up)
    params_file = os.path.join(current_dir, "..", "params.json")

    # Read and parse the JSON file
    with open(params_file, "r") as f:
        params = json.load(f)

    return params
