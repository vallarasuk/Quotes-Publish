import requests
import time
import sys

TOKEN = "8704938774:AAEqur29onf8k4-MLc1JFyrfk7tjZFFeyiQ"

def get_chat_id():
    print("Waiting for you to send a message to the bot...")
    print("Please go to Telegram, search for your bot (@romantic_notes_for_you_bot) and send any message (like 'hello').")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            res = requests.get(url).json()
            
            if res.get("ok") and len(res["result"]) > 0:
                chat_id = res["result"][0]["message"]["chat"]["id"]
                print(f"\nSuccess! Found your Chat ID: {chat_id}")
                return chat_id
                
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    get_chat_id()
