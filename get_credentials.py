import os
import webbrowser
import urllib.parse
import urllib.request
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# Global variable to store the authorization code received from the callback
auth_code = None

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        
        if 'code' in query:
            auth_code = query['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization successful!</h1><p>You can close this window and return to your terminal.</p></body></html>")
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization failed.</h1><p>No code provided.</p></body></html>")
            
    def log_message(self, format, *args):
        pass # Suppress logging

def get_credentials():
    print("=" * 60)
    print("📸 INSTAGRAM API CREDENTIALS GENERATOR 📸")
    print("=" * 60)
    print("To get your credentials, you MUST have:")
    print("  1. A Facebook Developer App (https://developers.facebook.com/)")
    print("  2. An Instagram Professional/Business account connected to a Facebook Page")
    print("  3. Your Facebook App must have 'instagram_basic', 'instagram_content_publish', and 'pages_read_engagement' permissions.")
    print("  4. Your Facebook App must have 'http://localhost:5000/' registered as a Valid OAuth Redirect URI.")
    print("\n")
    
    app_id = input("Enter your Facebook App ID: ").strip()
    app_secret = input("Enter your Facebook App Secret: ").strip()
    
    if not app_id or not app_secret:
        print("App ID and App Secret are required. Exiting.")
        return

    redirect_uri = "http://localhost:5000/"
    
    # Step 1: Open browser for user authorization
    auth_url = (
        f"https://www.facebook.com/v20.0/dialog/oauth?"
        f"client_id={app_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"
    )
    
    print("\nOpening your browser to authorize the app...")
    webbrowser.open(auth_url)
    
    print("Waiting for authorization on localhost:5000...")
    server = HTTPServer(('localhost', 5000), OAuthHandler)
    while auth_code is None:
        server.handle_request()
        
    print("\n✅ Authorization code received! Exchanging for tokens...")
    
    # Step 2: Exchange code for short-lived token
    token_url = (
        f"https://graph.facebook.com/v20.0/oauth/access_token?"
        f"client_id={app_id}&"
        f"redirect_uri={redirect_uri}&"
        f"client_secret={app_secret}&"
        f"code={auth_code}"
    )
    
    try:
        req = urllib.request.Request(token_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            short_token = data.get("access_token")
    except Exception as e:
        print(f"❌ Failed to get short-lived token: {e}")
        return

    # Step 3: Exchange short-lived token for long-lived token
    long_token_url = (
        f"https://graph.facebook.com/v20.0/oauth/access_token?"
        f"grant_type=fb_exchange_token&"
        f"client_id={app_id}&"
        f"client_secret={app_secret}&"
        f"fb_exchange_token={short_token}"
    )
    
    try:
        req = urllib.request.Request(long_token_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            long_token = data.get("access_token")
    except Exception as e:
        print(f"❌ Failed to get long-lived token: {e}")
        return
        
    # Step 4: Get User's Facebook Pages
    pages_url = f"https://graph.facebook.com/v20.0/me/accounts?access_token={long_token}"
    try:
        req = urllib.request.Request(pages_url)
        with urllib.request.urlopen(req) as response:
            pages_data = json.loads(response.read().decode())
            pages = pages_data.get("data", [])
    except Exception as e:
        print(f"❌ Failed to get Facebook pages: {e}")
        return
        
    if not pages:
        print("❌ No Facebook Pages found for this user.")
        return

    # Step 5: Find connected Instagram Business Accounts
    print("\n🔍 Scanning for connected Instagram Business Accounts...")
    ig_accounts = []
    
    for page in pages:
        page_id = page.get("id")
        # This page token is generated from a long-lived user token, so it NEVER expires!
        page_token = page.get("access_token")
        
        # Fetch the connected Instagram account AND its username
        ig_url = f"https://graph.facebook.com/v20.0/{page_id}?fields=name,instagram_business_account{{id,username}}&access_token={long_token}"
        try:
            req = urllib.request.Request(ig_url)
            with urllib.request.urlopen(req) as response:
                ig_data = json.loads(response.read().decode())
                if "instagram_business_account" in ig_data:
                    ig_accounts.append({
                        "page_name": ig_data.get("name", "Unknown Facebook Page"),
                        "ig_id": ig_data["instagram_business_account"]["id"],
                        "ig_username": ig_data["instagram_business_account"].get("username", "Unknown Instagram"),
                        "page_token": page_token
                    })
        except Exception as e:
            continue
            
    if not ig_accounts:
        print("❌ Could not find any Instagram Business Accounts connected to your Facebook Pages.")
        print("Please ensure your Instagram account is set to Professional/Business and linked to a Facebook Page.")
        return
        
    print("\n" + "=" * 60)
    print("🎉 SUCCESS! HERE ARE YOUR CREDENTIALS 🎉")
    print("=" * 60)
    
    if len(ig_accounts) > 1:
        print(f"I found {len(ig_accounts)} Instagram accounts connected to your Facebook profile!")
        print("Pick the IG_USER_ID for the account you want to post to:\n")
    else:
        print("I found 1 Instagram account connected to your Facebook profile:\n")
        
    for idx, acc in enumerate(ig_accounts):
        print(f"Account {idx + 1}: @{acc['ig_username']} (Linked to FB Page: '{acc['page_name']}')")
        print(f"export IG_USER_ID=\"{acc['ig_id']}\"")
        print("-" * 40)
        
    print(f"\nexport IG_ACCESS_TOKEN=\"(Hidden for security)\"")
    print("\n(Note: This token is a non-expiring Page Access Token! It will never expire.)")
    
    # --- NEW LOGIC: Save to .env ---
    choice = 0
    if len(ig_accounts) > 1:
        while True:
            try:
                sel = input(f"\nEnter the Account Number (1 to {len(ig_accounts)}) you want to use for the bot: ")
                choice = int(sel) - 1
                if 0 <= choice < len(ig_accounts):
                    break
                print("Invalid selection.")
            except ValueError:
                print("Please enter a valid number.")
                
    chosen_acc = ig_accounts[choice]
    env_file = ".env"
    env_lines = []
    
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            env_lines = f.readlines()
            
    # Filter out old IG credentials
    new_env_lines = [line for line in env_lines if not line.startswith("IG_USER_ID=") and not line.startswith("IG_ACCESS_TOKEN=")]
    
    # Ensure there is a newline before appending if the file wasn't empty and didn't end with one
    if new_env_lines and not new_env_lines[-1].endswith("\n"):
        new_env_lines[-1] += "\n"
        
    new_env_lines.append(f'IG_USER_ID="{chosen_acc["ig_id"]}"\n')
    new_env_lines.append(f'IG_ACCESS_TOKEN="{chosen_acc["page_token"]}"\n')
    
    with open(env_file, "w") as f:
        f.writelines(new_env_lines)
        
    print(f"\n✅ Automatically saved non-expiring credentials for @{chosen_acc['ig_username']} to your .env file!")
    print("You no longer need to copy-paste. Just run `python3 quote_poster.py` whenever you are ready!")

if __name__ == "__main__":
    get_credentials()
