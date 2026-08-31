#!/usr/bin/env python3
"""
Generate an Instagram-style motivational quote poster.

Requires:
    pip install requests pillow

Set:
    export POLLINATIONS_API_KEY="your_api_key"

Usage:
    python quote_poster.py
    python quote_poster.py --quote "Your custom quote"
    python quote_poster.py --theme "rainy city at night"
"""

from __future__ import annotations

import argparse
import os
import random
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote as urlquote
from dotenv import load_dotenv

from uploader import upload_image
from instagram import post_to_instagram

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

WIDTH, HEIGHT = 1080, 1350
POLLINATIONS_MODEL = "flux"
BRAND_HANDLE = "@romantic.notes.for.you"

def fetch_dynamic_quote() -> tuple[str, str]:
    # Fetch from a massive open-source database of 5000+ quotes
    url = "https://raw.githubusercontent.com/JamesFT/Database-Quotes-JSON/master/quotes.json"
    print("Fetching dynamic romantic quotes from database...")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        all_quotes = response.json()
        
        # Keywords that strongly indicate deep, personal romantic/relationship love
        keywords = ["romantic", "soulmate", "my love", "i love you", "kiss", "lovers", "in love", "true love", "together forever", "my heart", "your smile", "your eyes", "only you", "love of my life", "my whole world", "you are my everything", "you complete me", "in your arms", "forever with you", "holding you", "love", "romance"]
        
        # Words that indicate generic motivation, complex/archaic English, or broad philosophy (exclude these)
        blocklist = ["work", "business", "success", "fail", "win", "lose", "money", "career", "motivate", "enemy", "war", "friend", "society", "philosophy", "human", "mankind", "god", "religion", "politics", "spirituality", "animals", "science", "nature", "universe", "vanquish", "sectarianism", "banality", "eternity", "thou", "thy", "thee", "hath", "doth", "alas", "virtue", "sorrow", "abyss", "divine", "mortal", "immortal", "endeavor", "bestow"]
        
        import re
        
        romantic_quotes = []
        for q in all_quotes:
            text = q.get("quoteText", "")
            # Skip quotes that are too long (e.g. > 100 chars) so they fit perfectly in the image
            if len(text) > 100:
                continue
                
            text_lower = text.lower()
            
            # Extract pure words without punctuation for strict blocklist checking
            words_in_text = set(re.findall(r'\b\w+\b', text_lower))
            
            # Keywords can remain substring matches, but blocklist must be exact words
            if any(kw in text_lower for kw in keywords) and not any(bw in words_in_text for bw in blocklist):
                romantic_quotes.append(q)
                
        # Load previously used quotes to ensure we never repeat!
        used_quotes_file = Path("used_quotes.txt")
        used_quotes = set()
        if used_quotes_file.exists():
            used_quotes = set(used_quotes_file.read_text().splitlines())
            
        # Filter out already used quotes
        fresh_quotes = [q for q in romantic_quotes if q.get("quoteText", "") not in used_quotes]
        
        # If we exhausted all fresh quotes, reset the used quotes list
        if not fresh_quotes and romantic_quotes:
            if used_quotes_file.exists():
                used_quotes_file.unlink()
            fresh_quotes = romantic_quotes
        
        if fresh_quotes:
            chosen = random.choice(fresh_quotes)
            quote_text = chosen.get("quoteText", "")
            author = chosen.get("quoteAuthor") or "Unknown"
            
            # Save to history so it never loops
            with open(used_quotes_file, "a") as f:
                f.write(quote_text + "\n")
                
            return quote_text, author
            
    except Exception as e:
        print(f"Warning: Failed to fetch romantic quote. ({e})")
        
    # Beautiful romantic fallback
    return "I look at you and see the rest of my life in front of my eyes.", "Unknown"



ROMANTIC_FONTS = {
    "quote": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/greatvibes/GreatVibes-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/pacifico/Pacifico-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/alexbrush/AlexBrush-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/sacramento/Sacramento-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/parisienne/Parisienne-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/cookie/Cookie-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/tangerine/Tangerine-Bold.ttf"
    ],
    "author": ["https://raw.githubusercontent.com/google/fonts/main/ofl/crimsontext/CrimsonText-Italic.ttf"]
}


def font(kind: str, size: int):
    font_dir = Path("fonts")
    font_dir.mkdir(exist_ok=True)
    
    font_url = random.choice(ROMANTIC_FONTS[kind])
    font_filename = font_url.split("/")[-1]
    font_path = font_dir / font_filename
    
    if not font_path.exists():
        print(f"Downloading attractive {kind} font ({font_filename})...")
        try:
            response = requests.get(font_url, timeout=60)
            response.raise_for_status()
            font_path.write_bytes(response.content)
        except Exception as e:
            print(f"Warning: Failed to download font, using default. ({e})")
            return ImageFont.load_default()
            
    try:
        return ImageFont.truetype(str(font_path), size)
    except Exception:
        return ImageFont.load_default()


def generate_background(prompt: str, api_key: str, output_path: Path) -> None:
    encoded_prompt = urlquote(prompt, safe="")
    seed = random.randint(1, 99999999)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?model={POLLINATIONS_MODEL}&width={WIDTH}&height={HEIGHT}&nologo=True&seed={seed}"
    )

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.get(
        url,
        headers=headers,
        timeout=180,
    )
    response.raise_for_status()
    output_path.write_bytes(response.content)


def wrap_text(draw, text: str, chosen_font, max_width: int) -> str:
    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"
        box = draw.textbbox((0, 0), candidate, font=chosen_font)
        if box[2] - box[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return "\n".join(lines)


def get_text_dimensions(draw, text: str, chosen_font, max_width: int, spacing=16) -> tuple[int, int, str]:
    wrapped = wrap_text(draw, text, chosen_font, max_width)
    box = draw.multiline_textbbox((0, 0), wrapped, font=chosen_font, spacing=spacing, align="center")
    return box[2] - box[0], box[3] - box[1], wrapped


def find_best_y_position(image: Image.Image, text_height: int) -> int:
    # To place the text meaningfully, we find the "center of mass" of the image's details.
    # If the image is bottom-heavy (e.g., a person standing at the bottom), we place text at the top.
    # If the image is top-heavy, we place text at the bottom.
    # If balanced, we center it perfectly.
    
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    width, height = edges.size
    pixels = edges.load()
    
    total_weight = 0
    weighted_y_sum = 0
    
    # Calculate vertical center of mass of edge details
    for y in range(height):
        # Sample every 10th pixel for speed
        row_sum = sum(pixels[x, y] for x in range(0, width, 10))
        total_weight += row_sum
        weighted_y_sum += row_sum * y
        
    if total_weight == 0:
        return (height - text_height) // 2
        
    center_of_mass_y = weighted_y_sum / total_weight
    
    # Balance the composition:
    if center_of_mass_y > height * 0.55:
        # Subject is at the bottom, so place text beautifully in the top space
        return int(height * 0.18)
    elif center_of_mass_y < height * 0.45:
        # Subject is at the top, so anchor the text at the bottom
        return int(height * 0.82) - text_height
    else:
        # Image is evenly balanced, so place text directly in the center
        return (height - text_height) // 2


def center_text(draw, text, chosen_font, y, fill, max_width, spacing=16):
    wrapped = wrap_text(draw, text, chosen_font, max_width)
    box = draw.multiline_textbbox((0, 0), wrapped, font=chosen_font, spacing=spacing, align="center")
    width = box[2] - box[0]
    draw.multiline_text(
        ((WIDTH - width) / 2, y),
        wrapped,
        font=chosen_font,
        fill=fill,
        spacing=spacing,
        align="center",
    )
    return box[3] - box[1]


def build_poster(background_path: Path, quote: str, author: str, output_path: Path) -> None:
    image = Image.open(background_path).convert("RGBA").resize((WIDTH, HEIGHT))

    # Temporarily create a draw object for measurement
    temp_draw = ImageDraw.Draw(image)
    # Great Vibes is a cursive font, so we make it significantly larger to be highly readable and elegant
    quote_font = font("quote", 104)
    author_font = font("author", 34)
    maintainer_font = font("author", 26)
    
    # Calculate dimensions
    _, quote_height, _ = get_text_dimensions(temp_draw, quote, quote_font, max_width=920, spacing=24)
    
    # The total block consists of: quote + gap(55) + line(3) + gap(28) + author
    _, author_height, _ = get_text_dimensions(temp_draw, f"— {BRAND_HANDLE}", author_font, max_width=900, spacing=8)
    total_height = quote_height + 55 + 3 + 28 + author_height    
    # Find best placement using raw image
    best_y = find_best_y_position(image, total_height)

    # Dark translucent overlay for quote readability across the entire image.
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 90))
    image = Image.alpha_composite(image, overlay)

    draw = ImageDraw.Draw(image)

    actual_quote_height = center_text(
        draw,
        quote,
        quote_font,
        y=best_y,
        fill=(255, 255, 255, 250),
        max_width=920,
        spacing=24,
    )

    separator_y = best_y + actual_quote_height + 55
    draw.line(
        (WIDTH // 2 - 90, separator_y, WIDTH // 2 + 90, separator_y),
        fill=(255, 255, 255, 180),
        width=3,
    )

    actual_author_height = center_text(
        draw,
        f"— {BRAND_HANDLE}",
        author_font,
        y=separator_y + 28,
        fill=(255, 225, 220, 245),
        max_width=900,
        spacing=8,
    )

    maintainer_text = "Maintained by @vallarasu_kanthasamy"
    bbox = draw.textbbox((0, 0), maintainer_text, font=maintainer_font)
    maintainer_w = bbox[2] - bbox[0]
    maintainer_h = bbox[3] - bbox[1]
    margin_x, margin_y = 40, 40
    
    draw.text(
        (WIDTH - maintainer_w - margin_x, HEIGHT - maintainer_h - margin_y),
        maintainer_text,
        font=maintainer_font,
        fill=(255, 225, 220, 200),
    )

    image.convert("RGB").save(output_path, "PNG", optimize=True)
    print(f"Saved locally: {output_path}")

    # Upload to Meta compatibility layer
    try:
        from uploader import upload_image 
        public_url = upload_image(output_path)
        print(f"Public HTTPS URL for Meta API: {public_url}")
        
        # Post directly to Instagram
        if public_url:
            caption = f"\"{quote}\"\n\nFollow @romantic.notes.for.you 🤍\nMaintained by @vallarasu_kanthasamy ✨\n\n#lovequotes #romance #soulmate #quotes #aesthetic #lovers #romanticquotes #relationshipgoals #deepquotes"
            post_to_instagram(public_url, caption)
                
    except Exception as e:
        print(f"Warning: Failed to upload or post to Instagram. ({e})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quote", help="Custom quote text.")
    parser.add_argument("--author", help="Custom quote author.")
    parser.add_argument(
        "--theme",
        help="Custom theme prompt for the background image."
    )
    parser.add_argument("--out", default="quote_poster.png")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("POLLINATIONS_API_KEY")

    if args.quote:
        quote = args.quote
        author = args.author or "Unknown"
    else:
        quote, author = fetch_dynamic_quote()
        
    if args.theme:
        theme = args.theme
    else:
        # Intensely passionate and deeply romantic subjects with high diversity
        # We include objects, settings, and abstract representations of love, not just couples hugging
        subjects = [
            "two glasses of red wine on a table with candlelight",
            "beautiful bouquet of red roses",
            "path covered entirely in red rose petals",
            "pair of wedding rings resting on an open book",
            "cozy cabin with a warm fireplace and two armchairs",
            "romantic candlelit dinner setup under the stars",
            "handwritten love letter on vintage paper with a quill",
            "two coffee cups with heart-shaped latte art",
            "glowing neon sign that says love",
            "single red rose resting on piano keys",
            "two swans forming a heart shape in a serene lake",
            "heart drawn in the sand on a sunset beach",
            "small gift box with a beautiful red ribbon",
            "beautiful love lock on a bridge in Paris",
            "silhouette of a couple walking peacefully",
            "intertwined hands with a wedding ring"
        ]
        settings = [
            "under city streetlights in the rain", "at sunset by the ocean", "under a glowing starry night sky", 
            "in a dark moody forest", "on a snowy mountain peak", "by a cozy fireplace", 
            "during golden hour", "surrounded by floating lanterns", "in a blooming rose garden"
        ]
        
        # We don't track used themes because the AI uses a random SEED (1 in 100 million).
        # Even if "luxury sports car in the rain" is chosen 50 times, the seed ensures
        # that 50 completely different, unique images of cars will be generated!
        sub = random.choice(subjects)
        setg = random.choice(settings)
        chosen_subject = f"{sub} {setg}"
                
        theme = f"A breathtaking cinematic photography of {chosen_subject}, highly attractive, aesthetically pleasing, premium quality, visually stunning, no text, no watermark"

    with tempfile.TemporaryDirectory() as tmp_dir:
        background = Path(tmp_dir) / "background.jpg"
        final_output = Path(tmp_dir) / "final_poster.png"
        
        print(f"Generating background: {theme}")
        generate_background(theme, api_key, background)
        
        print("Building poster...")
        build_poster(background, quote, author, final_output)


if __name__ == "__main__":
    main()