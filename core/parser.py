import json

def parse(filepath):
 
    try:
        with open(filepath, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise SystemExit(f"Error: File '{filepath}' not found.")
    except json.JSONDecodeError as e:
        raise SystemExit(f"Error: Invalid JSON format. {e}")

    if not isinstance(data, dict):
        raise SystemExit("Error: JSON root must be an object with a 'deliveries' key.")

    deliveries = data.get("deliveries", [])

    if not isinstance(deliveries, list):
        raise SystemExit("Error: 'deliveries' must be a list.")

    return deliveries