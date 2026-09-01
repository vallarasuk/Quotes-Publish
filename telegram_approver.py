import os
import time
import requests
import json
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

def generate_font_example_image(available_fonts: list) -> Path:
    width, height = 1200, max(500, len(available_fonts) * 120 + 150)
    img = Image.new("RGB", (width, height), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    
    try:
        if available_fonts[0].startswith("http"):
            t_path = "/tmp/font_0.ttf"
            if not os.path.exists(t_path):
                with open(t_path, "wb") as f:
                    f.write(requests.get(available_fonts[0]).content)
        else:
            t_path = available_fonts[0]
        title_font = ImageFont.truetype(t_path, 40)
    except:
        title_font = ImageFont.load_default()
        
    draw.text((50, 30), "Select a Font for your Reel:", fill=(255, 255, 255), font=title_font)
    
    y = 120
    for i, font_url in enumerate(available_fonts):
        try:
            if font_url.startswith("http"):
                font_path = f"/tmp/font_{i}.ttf"
                if not os.path.exists(font_path):
                    with open(font_path, "wb") as f:
                        f.write(requests.get(font_url).content)
            else:
                font_path = font_url
                
            fnt = ImageFont.truetype(font_path, 80)
            name = font_url.split("/")[-1].replace(".ttf", "").replace("-Regular", "")
            draw.text((50, y), f"[{i+1}] You are my everything - {name}", fill=(255, 200, 200), font=fnt)
        except Exception as e:
            draw.text((50, y), f"[{i+1}] Failed to load {font_url.split('/')[-1]}", fill=(255, 0, 0))
        y += 120
        
    out_path = Path("/tmp/font_showcase.png")
    img.save(out_path)
    return out_path

def ask_pre_generation_setup(quote: str, author: str, caption: str, available_fonts: list, available_music: list = None) -> tuple[bool, str, str, str, str, str]:
    """
    Sends pre-generation settings to Telegram for review.
    Allows editing quote, author, caption, and selecting a font and music.
    Returns (approved, quote, author, caption, selected_font, selected_music)
    """
    load_dotenv()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_ids_raw = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not bot_token or not chat_ids_raw:
        print("Skipping pre-generation setup: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return False, quote, author, caption, None, None
        
    chat_ids = [cid.strip() for cid in chat_ids_raw.split(",") if cid.strip()]
    if not chat_ids:
        return False, quote, author, caption, None, None

    api_url = f"https://api.telegram.org/bot{bot_token}"
    
    current_quote = quote
    current_author = author
    current_caption = caption
    selected_font_idx = None # None means random
    selected_music_idx = None # None means no music (Image only)
    
    def get_font_name(idx):
        if idx is None: return "Random (Default)"
        return available_fonts[idx].split("/")[-1].replace(".ttf", "").replace("-Regular", "").replace("-Bold", "")
        
    def get_music_name(idx):
        if not available_music or idx is None: return "None (Image Only)"
        return str(available_music[idx]).split("/")[-1]

    def get_main_text():
        return (
            f"🛠 Pre-Generation Setup\n\n"
            f"📝 Quote: {current_quote}\n"
            f"👤 Author: {current_author}\n"
            f"🔠 Font: {get_font_name(selected_font_idx)}\n"
            f"🎵 Music: {get_music_name(selected_music_idx)}\n\n"
            f"📋 Caption:\n{current_caption}"
        )

    def get_main_keyboard():
        return {
            "inline_keyboard": [
                [{"text": "✅ Generate Media", "callback_data": "generate_image"}],
                [
                    {"text": "✏️ Edit Quote", "callback_data": "edit_quote"},
                    {"text": "✏️ Edit Author", "callback_data": "edit_author"}
                ],
                [
                    {"text": "✏️ Edit Caption", "callback_data": "edit_caption_pre"},
                    {"text": "🔠 Select Font", "callback_data": "select_font"}
                ],
                [
                    {"text": "🎵 Select Music", "callback_data": "select_music"},
                    {"text": "❌ Cancel Generation", "callback_data": "cancel_generation"}
                ]
            ]
        }
        
    def get_font_keyboard():
        kb = []
        row = []
        # Add random option
        kb.append([{"text": "🎲 Random", "callback_data": f"set_font_random"}])
        
        for i in range(len(available_fonts)):
            row.append({"text": f"[{i+1}]", "callback_data": f"set_font_{i}"})
            if len(row) == 5:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        kb.append([{"text": "🔙 Cancel Select", "callback_data": "back_to_main"}])
        return {"inline_keyboard": kb}
        
    def get_music_keyboard():
        kb = []
        row = []
        kb.append([{"text": "🔇 None (Image Only)", "callback_data": f"set_music_none"}])
        kb.append([{"text": "📤 Upload New Music", "callback_data": "upload_music"}])
        
        if available_music:
            for i, m_path in enumerate(available_music):
                name = str(m_path).split("/")[-1][:20]
                row.append({"text": name, "callback_data": f"set_music_{i}"})
                if len(row) == 2:
                    kb.append(row)
                    row = []
            if row:
                kb.append(row)
        kb.append([{"text": "🔙 Back", "callback_data": "back_to_main"}])
        return {"inline_keyboard": kb}

    sent_messages = {}
    font_showcase_msgs = {}
    print("Sending pre-generation setup to Telegram...")
    for chat_id in chat_ids:
        msg_data = {
            "chat_id": chat_id,
            "text": get_main_text(),
            "reply_markup": get_main_keyboard()
        }
        try:
            res = requests.post(f"{api_url}/sendMessage", json=msg_data, timeout=20)
            res.raise_for_status()
            sent_messages[str(chat_id)] = res.json()["result"]["message_id"]
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")
            if "response" in locals() and hasattr(res, "text"):
                print(res.text)
            
    if not sent_messages:
        print("Could not send approval message to any chat ID. Aborting.")
        return False, current_quote, current_author, current_caption, None, None
        
    print("Waiting for configuration on Telegram...")
    
    offset = None
    waiting_for_input_type = None # "quote", "author", "caption"
    waiting_from_chat = None

    def update_all(text=None, kb=None):
        for cid, mid in sent_messages.items():
            payload = {"chat_id": cid, "message_id": mid}
            if text: payload["text"] = text
            if kb: payload["reply_markup"] = kb
            try: requests.post(f"{api_url}/editMessageText", json=payload)
            except: pass

    while True:
        try:
            updates_res = requests.get(f"{api_url}/getUpdates", params={"offset": offset, "timeout": 10}, timeout=15)
            updates_res.raise_for_status()
            updates = updates_res.json().get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                
                if "callback_query" in update:
                    query = update["callback_query"]
                    data = query.get("data")
                    query_id = query.get("id")
                    chat_id = str(query["message"]["chat"]["id"])
                    message_id = query["message"]["message_id"]
                    
                    is_main_msg = (chat_id in sent_messages and sent_messages[chat_id] == message_id)
                    is_font_msg = (chat_id in font_showcase_msgs and font_showcase_msgs.get(chat_id) == message_id)
                    
                    if is_main_msg or is_font_msg:
                        requests.post(f"{api_url}/answerCallbackQuery", json={"callback_query_id": query_id})
                        
                        if data == "generate_image":
                            update_all(f"✅ Generating Media...\n\nQuote: {current_quote}", kb={"inline_keyboard":[]})
                            final_font = available_fonts[selected_font_idx] if selected_font_idx is not None else None
                            final_music = available_music[selected_music_idx] if available_music and selected_music_idx is not None else None
                            return True, current_quote, current_author, current_caption, final_font, final_music
                            
                        elif data == "cancel_generation":
                            update_all(f"❌ Generation Cancelled.\n\nQuote: {current_quote}", kb={"inline_keyboard":[]})
                            return False, current_quote, current_author, current_caption, None, None
                            
                        elif data == "select_font":
                            img_path = generate_font_example_image(available_fonts)
                            update_all(text="🔠 Sent font examples below. Please choose a number.", kb={"inline_keyboard": []})
                            for cid in sent_messages.keys():
                                try:
                                    with open(img_path, "rb") as f:
                                        res = requests.post(
                                            f"{api_url}/sendPhoto",
                                            data={"chat_id": cid, "caption": "Choose a font number:", "reply_markup": json.dumps(get_font_keyboard())},
                                            files={"photo": f}
                                        )
                                        if res.status_code == 200:
                                            font_showcase_msgs[cid] = res.json()["result"]["message_id"]
                                except Exception as e:
                                    print(e)
                            
                        elif data.startswith("set_font_"):
                            val = data.replace("set_font_", "")
                            selected_font_idx = None if val == "random" else int(val)
                            
                            for cid, mid in font_showcase_msgs.items():
                                requests.post(f"{api_url}/deleteMessage", json={"chat_id": cid, "message_id": mid})
                            font_showcase_msgs.clear()
                            
                            update_all(text=get_main_text(), kb=get_main_keyboard())
                            
                        elif data == "select_music":
                            update_all(text="🎵 Select background music:", kb=get_music_keyboard())
                            
                        elif data == "upload_music":
                            waiting_for_input_type = "music"
                            waiting_from_chat = chat_id
                            prompt = "🎵 Please send an .mp3 audio file to this chat."
                            requests.post(f"{api_url}/editMessageText", json={
                                "chat_id": chat_id, "message_id": message_id, "text": prompt,
                                "reply_markup": {"inline_keyboard": [[{"text": "Cancel Edit", "callback_data": "cancel_edit"}]]}
                            })
                            
                        elif data.startswith("set_music_"):
                            val = data.replace("set_music_", "")
                            selected_music_idx = None if val == "none" else int(val)
                            update_all(text=get_main_text(), kb=get_main_keyboard())
                            
                        elif data == "back_to_main":
                            for cid, mid in font_showcase_msgs.items():
                                requests.post(f"{api_url}/deleteMessage", json={"chat_id": cid, "message_id": mid})
                            font_showcase_msgs.clear()
                            update_all(text=get_main_text(), kb=get_main_keyboard())
                            
                        elif data in ["edit_quote", "edit_author"]:
                            waiting_from_chat = chat_id
                            waiting_for_input_type = data.replace("edit_", "")
                            
                            prompt = f"✏️ Please reply to this message with the new {waiting_for_input_type}."
                            requests.post(f"{api_url}/editMessageText", json={
                                "chat_id": chat_id, "message_id": message_id, "text": prompt,
                                "reply_markup": {"inline_keyboard": [[{"text": "Cancel Edit", "callback_data": "cancel_edit"}]]}
                            })
                            
                        elif data == "edit_caption":
                            waiting_from_chat = chat_id
                            waiting_for_input_type = "caption"
                            first_name = query["from"].get("first_name", "Someone")
                            
                            for cid, mid in sent_messages.items():
                                if cid != chat_id:
                                    requests.post(f"{api_url}/editMessageText", json={
                                        "chat_id": cid, "message_id": mid,
                                        "text": f"✏️ {first_name} is currently editing the caption...",
                                        "reply_markup": {"inline_keyboard": []}
                                    })
                            
                            prompt = "✏️ Please reply to this message with the new caption."
                            requests.post(f"{api_url}/editMessageText", json={
                                "chat_id": chat_id, "message_id": message_id, "text": prompt,
                                "reply_markup": {"inline_keyboard": [[{"text": "Cancel Edit", "callback_data": "cancel_edit"}]]}
                            })
                            
                        elif data == "cancel_edit" and waiting_from_chat == chat_id:
                            waiting_from_chat = None
                            waiting_for_input_type = None
                            update_all(text=get_main_text(), kb=get_main_keyboard())

                elif "message" in update:
                    msg = update["message"]
                    chat_id = str(msg.get("chat", {}).get("id"))
                    
                    if chat_id in chat_ids:
                        # Global audio interceptor - if they send audio at ANY time, make it the selected music!
                        if "audio" in msg or "document" in msg or "voice" in msg:
                            file_info = msg.get("audio") or msg.get("document") or msg.get("voice")
                            # If it's a document, check if it's an audio format
                            mime = file_info.get("mime_type", "")
                            if "audio" in msg or "voice" in msg or mime.startswith("audio/"):
                                file_id = file_info["file_id"]
                                try:
                                    update_all(text="🎵 Downloading your uploaded music... Please wait.", kb={"inline_keyboard": []})
                                    f_res = requests.get(f"{api_url}/getFile?file_id={file_id}").json()
                                    file_path = f_res["result"]["file_path"]
                                    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                                    
                                    original_name = file_info.get("file_name", f"audio_{int(time.time())}.mp3")
                                    if not original_name.endswith(".mp3"): original_name += ".mp3"
                                    
                                    target_path = Path("music") / original_name
                                    target_path.parent.mkdir(exist_ok=True)
                                    
                                    with open(target_path, "wb") as f:
                                        f.write(requests.get(download_url).content)
                                        
                                    if available_music is not None:
                                        available_music.append(target_path)
                                        selected_music_idx = len(available_music) - 1
                                        
                                    if waiting_from_chat == chat_id and waiting_for_input_type == "music":
                                        waiting_from_chat = None
                                        waiting_for_input_type = None
                                        
                                    update_all(text=get_main_text(), kb=get_main_keyboard())
                                except Exception as e:
                                    print(f"Error downloading audio: {e}")
                                    update_all(text=get_main_text(), kb=get_main_keyboard())
                                    
                        elif waiting_from_chat == chat_id and "text" in msg:
                            reply_to = msg.get("reply_to_message")
                            if reply_to and reply_to.get("message_id") == sent_messages.get(chat_id):
                                new_text = msg["text"]
                                if waiting_for_input_type == "quote": current_quote = new_text
                                elif waiting_for_input_type == "author": current_author = new_text
                                elif waiting_for_input_type == "caption": current_caption = new_text
                                
                                waiting_from_chat = None
                                waiting_for_input_type = None
                                update_all(text=get_main_text(), kb=get_main_keyboard())

        except requests.exceptions.RequestException as e:
            time.sleep(2)
        time.sleep(2)


def ask_telegram_approval(public_url: str, caption: str) -> tuple[bool, str]:
    """
    Sends the generated image URL to multiple Telegram chat IDs with an Approve/Reject/Edit keyboard.
    Polls for a response and returns (is_approved, final_caption).
    First person to approve or reject decides for everyone.
    """
    load_dotenv()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_ids_raw = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not bot_token or not chat_ids_raw:
        print("Skipping Telegram approval: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return True, caption
        
    chat_ids = [cid.strip() for cid in chat_ids_raw.split(",") if cid.strip()]
    if not chat_ids:
        print("Skipping Telegram approval: No valid chat IDs found.")
        return True, caption

    api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def get_keyboard():
        return {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve & Post", "callback_data": "approve"},
                    {"text": "❌ Reject", "callback_data": "reject"}
                ],
                [
                    {"text": "✏️ Edit Caption", "callback_data": "edit_caption"}
                ]
            ]
        }
    
    sent_messages = {} # maps chat_id -> message_id
    
    is_video = public_url.lower().endswith(".mp4")
    endpoint = "/sendVideo" if is_video else "/sendPhoto"
    media_key = "video" if is_video else "photo"
    media_type_name = "Video" if is_video else "Image"
    
    print(f"Sending {media_type_name.lower()} to Telegram for approval...")
    for chat_id in chat_ids:
        msg_data = {
            "chat_id": chat_id,
            media_key: public_url,
            "caption": f"New {media_type_name} Ready to Post!\n\n{caption}",
            "reply_markup": get_keyboard()
        }
        try:
            res = requests.post(f"{api_url}{endpoint}", json=msg_data, timeout=20)
            res.raise_for_status()
            message_id = res.json()["result"]["message_id"]
            sent_messages[str(chat_id)] = message_id
        except Exception as e:
            print(f"Failed to send message to Telegram chat {chat_id}: {e}")
            if "response" in locals() and hasattr(res, "text"):
                print(res.text)
            
    if not sent_messages:
        print("Failed to send to any Telegram chats. Aborting.")
        return False, caption
        
    print("Waiting for a response on Telegram...")
    
    # Poll for updates
    offset = None
    waiting_for_new_caption_from = None
    current_caption = caption

    def update_all_messages(new_text: str, remove_keyboard: bool = False):
        """Helper to update all sent messages with a final status or new caption."""
        for cid, mid in sent_messages.items():
            payload = {
                "chat_id": cid,
                "message_id": mid,
                "caption": new_text
            }
            if not remove_keyboard:
                payload["reply_markup"] = get_keyboard()
                
            try:
                requests.post(f"{api_url}/editMessageCaption", json=payload)
            except Exception:
                pass # Ignore errors for individual chats

    while True:
        try:
            updates_res = requests.get(
                f"{api_url}/getUpdates", 
                params={"offset": offset, "timeout": 10}, 
                timeout=15
            )
            updates_res.raise_for_status()
            updates = updates_res.json().get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                
                # Check for callback queries (button clicks)
                if "callback_query" in update:
                    query = update["callback_query"]
                    data = query.get("data")
                    query_id = query.get("id")
                    from_user = query.get("from", {}).get("first_name", "Someone")
                    chat_id = str(query["message"]["chat"]["id"])
                    message_id = query["message"]["message_id"]
                    
                    if chat_id in sent_messages and sent_messages[chat_id] == message_id:
                        requests.post(f"{api_url}/answerCallbackQuery", json={"callback_query_id": query_id})
                        
                        if data == "approve":
                            final_text = f"✅ Approved by {from_user} and Posting!\n\n{current_caption}"
                            update_all_messages(final_text, remove_keyboard=True)
                            print(f"Post approved by {from_user} via Telegram!")
                            return True, current_caption
                            
                        elif data == "reject":
                            final_text = f"❌ Rejected by {from_user}! Not posting.\n\n{current_caption}"
                            update_all_messages(final_text, remove_keyboard=True)
                            print(f"Post rejected by {from_user} via Telegram.")
                            return False, current_caption
                            
                        elif data == "edit_caption":
                            waiting_for_new_caption_from = chat_id
                            
                            # Notify everyone else
                            for cid, mid in sent_messages.items():
                                if cid != chat_id:
                                    requests.post(f"{api_url}/editMessageCaption", json={
                                        "chat_id": cid,
                                        "message_id": mid,
                                        "caption": f"✏️ {from_user} is currently editing the caption...",
                                        "reply_markup": {"inline_keyboard": []}
                                    })
                            
                            requests.post(f"{api_url}/editMessageCaption", json={
                                "chat_id": chat_id,
                                "message_id": message_id,
                                "caption": f"✏️ Please reply to this message with your new caption.\n\nCurrent caption:\n{current_caption}",
                                "reply_markup": {"inline_keyboard": [[{"text": "Cancel Edit", "callback_data": "cancel_edit"}]]}
                            })
                            print(f"Waiting for new caption from {from_user} via Telegram reply...")
                            
                        elif data == "cancel_edit" and waiting_for_new_caption_from == chat_id:
                            waiting_for_new_caption_from = None
                            update_all_messages(f"New Image Ready to Post!\n\n{current_caption}")
                            print("Edit cancelled. Waiting for approval...")

                # Check for text messages (replies with new caption)
                elif "message" in update and waiting_for_new_caption_from:
                    msg = update["message"]
                    chat_id = str(msg.get("chat", {}).get("id"))
                    reply_to = msg.get("reply_to_message")
                    
                    if chat_id == waiting_for_new_caption_from and reply_to and "text" in msg:
                        if reply_to.get("message_id") == sent_messages.get(chat_id):
                            current_caption = msg["text"]
                            waiting_for_new_caption_from = None
                            
                            # Broadcast the new caption to all chats and restore keyboards
                            update_all_messages(f"New Image Ready to Post! (Caption edited)\n\n{current_caption}")
                            print("Received new caption. Waiting for approval...")

        except requests.exceptions.RequestException as e:
            print(f"Polling error: {e}, retrying...")
            time.sleep(2)
            
        time.sleep(2)

if __name__ == "__main__":
    # Test script
    print("Testing Telegram approval...")
    test_url = "https://placekitten.com/800/800"
    approved, caption = ask_telegram_approval(test_url, "Test caption")
    print(f"Result: Approved={approved}, Caption={caption}")
