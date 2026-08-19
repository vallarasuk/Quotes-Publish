import requests
from pathlib import Path

def upload_image(file_path: Path | str) -> str:
    """
    Uploads an image to uguu.se and returns the public HTTPS URL.
    This URL can be used directly with Meta (Instagram/Facebook) Graph APIs.
    """
    url = "https://uguu.se/upload.php"
    
    with open(file_path, "rb") as f:
        files = {
            "files[]": f
        }
        
        print("Uploading image to get a public HTTPS URL for Meta...")
        response = requests.post(url, files=files, timeout=60)
        response.raise_for_status()
        
        # uguu.se returns: {"success":true,"files":[{"url":"https://a.uguu.se/abc.png"}]}
        data = response.json()
        download_url = data["files"][0]["url"]
        
        return download_url
