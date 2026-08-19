import os
import requests
import urllib.parse

def send_whatsapp_message(text: str):
    phone = os.environ.get("WHATSAPP_PHONE")
    apikey = os.environ.get("WHATSAPP_APIKEY")
    
    if not phone or not apikey:
        print("Skipping WhatsApp notification (WHATSAPP_PHONE or WHATSAPP_APIKEY not set in .env)")
        return
        
    # CallMeBot API
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={urllib.parse.quote(text)}&apikey={apikey}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            print(f"✅ WhatsApp notification sent successfully!")
        else:
            print(f"❌ Failed to send WhatsApp notification: {res.text}")
    except Exception as e:
        print(f"❌ WhatsApp API error: {e}")

if __name__ == "__main__":
    send_whatsapp_message("Hello! This is a test message from your Instagram bot! 🤖")
