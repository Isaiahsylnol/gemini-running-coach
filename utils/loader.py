import json

def load_image_bytes(path):
    with open(path, "rb") as f:
        return f.read()

def load_json_text(path):
    with open(path, "r") as f:
        return json.load(f)