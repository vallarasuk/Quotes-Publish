import requests
from pathlib import Path

def upload_image(file_path: Path | str) -> str:
    """
    Uploads an image to tmpfiles.org and returns the public HTTPS URL.
    This URL can be used directly with Meta (Instagram/Facebook) Graph APIs.
    """
    url = "https://tmpfiles.org/api/v1/upload"
    
    with open(file_path, "rb") as f:
        files = {
            "file": f
        }
        
        print("Uploading image to get a public HTTPS URL for Meta...")
        response = requests.post(url, files=files, timeout=60)
        response.raise_for_status()
        
        # tmpfiles.org returns: {"data": {"url": "https://tmpfiles.org/12345/image.png"}}
        # We need the direct download link which is "tmpfiles.org/dl/12345/..."
        data = response.json()
        download_url = data["data"]["url"]
        direct_url = download_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        
        return direct_url
