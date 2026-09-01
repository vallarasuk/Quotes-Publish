import os
import requests
from dotenv import load_dotenv

def update_env_file(new_chat_ids):
    """Updates the TELEGRAM_CHAT_ID in the .env file with merged IDs."""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        print(f"Error: {env_path} not found.")
        return
        
    with open(env_path, "r") as f:
        lines = f.readlines()
        
    # Find existing IDs to merge
    existing_ids = set()
    for line in lines:
        if line.startswith("TELEGRAM_CHAT_ID="):
            current_val = line.strip().split("=", 1)[1].strip('"\'')
            existing_ids.update([cid.strip() for cid in current_val.split(",") if cid.strip()])
            
    # Merge old and new IDs
    merged_ids = existing_ids.union(new_chat_ids)
    final_id_string = ",".join(str(cid) for cid in merged_ids)
    
    # Write back to .env
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("TELEGRAM_CHAT_ID="):
                f.write(f'TELEGRAM_CHAT_ID="{final_id_string}"\n')
            else:
                f.write(line)
                
    print(f"\n✅ Successfully updated .env with: TELEGRAM_CHAT_ID=\"{final_id_string}\"")


def main():
    load_dotenv()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env")
        return
        
    print("Fetching recent messages sent to your bot...")
    api_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        res = requests.get(api_url, timeout=10)
        res.raise_for_status()
        updates = res.json().get("result", [])
    except Exception as e:
        print(f"Failed to fetch updates: {e}")
        return
        
    found_chats = {}
    
    for update in updates:
        if "message" in update:
            chat = update["message"]["chat"]
            chat_id = chat.get("id")
            # Can be group title or user first name
            name = chat.get("title") or chat.get("first_name") or "Unknown"
            chat_type = chat.get("type", "unknown")
            
            if chat_id:
                found_chats[str(chat_id)] = f"{name} ({chat_type})"
                
    if not found_chats:
        print("\nNo recent messages found.")
        print("Please tell the person/group to send a message to the bot first, then run this script again.")
        return
        
    print(f"\nFound {len(found_chats)} recent chat(s):")
    for cid, name in found_chats.items():
        print(f"  - {name}: {cid}")
        
    choice = input("\nDo you want to add these Chat IDs to your .env file? (y/n): ").strip().lower()
    if choice == 'y':
        update_env_file(found_chats.keys())
    else:
        print("Skipped updating .env.")

if __name__ == "__main__":
    main()
