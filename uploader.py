import requests
from pathlib import Path

def upload_image(file_path: Path | str) -> str:
    """
    Uploads an image to Catbox.moe and returns the public HTTPS URL.
    This URL can be used directly with Meta (Instagram/Facebook) Graph APIs.
    """
    url = "https://catbox.moe/user/api.php"
    
    with open(file_path, "rb") as f:
        files = {
            "fileToUpload": f
        }
        data = {
            "reqtype": "fileupload"
        }
        
        print("Uploading image to get a public HTTPS URL for Meta...")
        response = requests.post(url, data=data, files=files, timeout=60)
        response.raise_for_status()
        
        return response.text.strip()
