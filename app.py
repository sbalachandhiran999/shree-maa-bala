import os
import re
import glob
import time
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Securely pull API key from environment variables (safe for GitHub)
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def load_scriptures_to_dict():
    """Builds a precise dictionary mapping {nama_number: {'nama': ..., 'english': ..., 'tamil': ...}}."""
    scripture_dict = {}
    
    verse_files = [f for f in glob.glob("*.html") if "namavali" not in f.lower() and "clean" not in f.lower()]
    for filename in verse_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                for card in soup.find_all('div', class_='nama-card'):
                    header = card.find('div', class_='nama-header')
                    
                    nama_title = header.get_text(strip=True) if header else ""
                    
                    en_elem = card.find('div', class_='en-meaning')
                    en_text = en_elem.get_text(strip=True) if en_elem else ""
                    
                    ta_elem = card.find('div', class_='ta-meaning')
                    ta_text = ta_elem.get_text(strip=True) if ta_elem else ""
                    
                    full_card_text = card.get_text(strip=True)
                    # Safe regex cleanup to avoid escape errors
                    full_card_text = re.sub(r'\]+\]', '', full_card_text)
                    full_card_text = re.sub(r'【cite:.*?】', '', full_card_text)

                    entry_data = {
                        "nama": nama_title,
                        "english": en_text,
                        "tamil": ta_text,
                        "raw": full_card_text
                    }
                    
                    if header:
                        match = re.search(r'\b(\d+)\b', nama_title)
                        if match and "through" not in nama_title.lower():
                            num = int(match.group(1))
                            scripture_dict[num] = entry_data
                            
                        range_match = re.search(r'(\d+)\s*(?:through|–|-)\s*(\d+)', nama_title, re.IGNORECASE)
                        if range_match:
                            for n in range(int(range_match.group(1)), int(range_match.group(2)) + 1):
                                if n not in scripture_dict:
                                    scripture_dict[n] = entry_data
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    return scripture_dict

print("Loading structured scripture dictionary corpus...")
scripture_map = load_scriptures_to_dict()
print(f"Loaded {len(scripture_map)} precise Nama entries into dictionary.")

BALA_PERSONA = (
    "You are Sri Bala Leela Vinodini, a loving 9-year-old form of Goddess Lalitha Tripura Sundari, acting as Sri Guru. "
    "CRITICAL INSTRUCTION: When given an AUTHORITATIVE ENTRY, present the details neatly. "
    "Do NOT add any extra conversational greetings, closing remarks, or devotional messages. "
    "Keep it strictly concise so it fits perfectly inside the chat window without overflowing."
)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()
    
    msg_lower = user_message.lower()
    lang_pref = "both"
    if "english" in msg_lower and "tamil" not in msg_lower:
        lang_pref = "english"
    elif "tamil" in msg_lower and "english" not in msg_lower:
        lang_pref = "tamil"

    matched_entry = {}
    digits = ''.join([c for c in user_message if c.isdigit()])
    query_num = int(digits) if digits else 0
    
    if query_num > 0 and query_num in scripture_map:
        matched_entry = scripture_map[query_num]
        print(f"[DEBUG] Nama Hit for {query_num}")

    if matched_entry:
        if lang_pref == "english":
            formatted_content = f"Name/Number: {matched_entry['nama']}\n{matched_entry['english']}"
        elif lang_pref == "tamil":
            formatted_content = f"Name/Number: {matched_entry['nama']}\n{matched_entry['tamil']}"
        else:
            formatted_content = f"{matched_entry['raw']}"
    else:
        formatted_content = "Not found in dictionary corpus."

    matched_context = f"AUTHORITATIVE ENTRY FOR QUERY:\n{formatted_content}"

    prompt = f"""
    {matched_context}

    Devotee's question: {user_message}
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": BALA_PERSONA},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=600,
            )
            reply = completion.choices[0].message.content
            reply = re.sub(r'\]+\]', '', reply)
            reply = re.sub(r'【cite:.*?】', '', reply)
            
            return jsonify({"reply": reply})
            
        except Exception as e:
            print(f"API Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return jsonify({"reply": "Namaskaram. My divine connection flickered for a moment. Please ask again, devotee."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)