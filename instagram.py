import os
import time
import requests

def publish_media(creation_id: str, ig_user_id: str, access_token: str) -> str:
    publish_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }
    
    print("Publishing to Instagram...")
    publish_res = requests.post(publish_url, data=publish_payload)
    if publish_res.status_code != 200:
        print(f"Error publishing media: {publish_res.text}")
        return None
        
    media_id = publish_res.json().get("id")
    print(f"Successfully posted to Instagram! Media ID: {media_id}")
    
    # Get Permalink
    permalink_url = f"https://graph.facebook.com/v20.0/{media_id}?fields=permalink&access_token={access_token}"
    try:
        p_res = requests.get(permalink_url, timeout=10)
        permalink = p_res.json().get("permalink", f"https://instagram.com/p/{media_id}")
        return permalink
    except Exception:
        return f"https://instagram.com/"

def post_to_instagram(image_url: str, caption: str) -> str:
    """
    Posts an image URL to Instagram using the Meta Graph API.
    Requires IG_USER_ID and IG_ACCESS_TOKEN environment variables.
    """
    ig_user_id = os.environ.get("IG_USER_ID")
    access_token = os.environ.get("IG_ACCESS_TOKEN")
    
    if not ig_user_id or not access_token:
        print("Skipping Instagram post: IG_USER_ID or IG_ACCESS_TOKEN not set.")
        return None

    # Step 1: Create Media Container
    container_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media"
    container_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }
    
    print("Creating Instagram media container...")
    container_res = requests.post(container_url, data=container_payload)
    if container_res.status_code != 200:
        print(f"Error creating container: {container_res.text}")
        return None
        
    creation_id = container_res.json().get("id")
    if not creation_id:
        print("Failed to get creation_id from Meta API.")
        return None
        
    print(f"Media container created (ID: {creation_id}). Waiting for Meta to process...")
    # Wait a few seconds for Meta's servers to process the image URL
    time.sleep(5)
    
    # Step 2: Publish the Container
    return publish_media(creation_id, ig_user_id, access_token)
