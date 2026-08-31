import requests
import json
import argparse

def fetch_soft_love_songs(limit=15):
    print(f"🎵 Searching for {limit} soft romantic songs for your background...")
    
    url = "https://itunes.apple.com/search"
    # Search for lofi, cinematic, or soft romantic tracks
    params = {
        "term": "lofi love romance soft instrumental",
        "media": "music",
        "limit": limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            print("No songs found.")
            return

        print("\n=== 💖 Top Soft Romantic Tracks 💖 ===")
        for i, track in enumerate(results, 1):
            title = track.get("trackName", "Unknown Title")
            artist = track.get("artistName", "Unknown Artist")
            preview_url = track.get("previewUrl", "")
            
            print(f"{i}. {title} by {artist}")
            if preview_url:
                print(f"   Download Audio: {preview_url}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error fetching songs: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch trending soft love music from iTunes")
    parser.add_argument("--limit", type=int, default=15, help="Number of songs to fetch")
    args = parser.parse_args()
    
    fetch_soft_love_songs(args.limit)
