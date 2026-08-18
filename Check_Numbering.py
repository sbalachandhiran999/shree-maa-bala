import os
import re
import glob
from bs4 import BeautifulSoup

def audit_scriptures():
    namavali_numbers = set()
    verse_numbers = set()
    
    # 1. Extract numbers from Namavali.html
    if os.path.exists("Namavali.html"):
        with open("Namavali.html", 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            for el in soup.find_all(['li', 'td', 'div', 'span', 'p']):
                text = el.get_text(strip=True)
                match = re.match(r'^(\d+)', text)
                if match:
                    namavali_numbers.add(int(match.group(1)))

    # 2. Extract numbers from Verse files (including verse_1_10.html)
    verse_files = glob.glob("*.html")
    for filename in verse_files:
        if "namavali" in filename.lower():
            continue
        with open(filename, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Check individual cards
            for card in soup.find_all('div', class_='nama-card'):
                header = card.find('div', class_='nama-header')
                if header:
                    header_text = header.get_text(strip=True)
                    # Handle single numbers or ranges (e.g., "1 - 5" or "1 through 5")
                    range_match = re.search(r'(\d+)\s*(?:through|–|-)\s*(\d+)', header_text, re.IGNORECASE)
                    if range_match:
                        for n in range(int(range_match.group(1)), int(range_match.group(2)) + 1):
                            verse_numbers.add(n)
                    else:
                        match = re.match(r'^(\d+)', header_text)
                        if match:
                            verse_numbers.add(int(match.group(1)))

    print(f"Total unique numbers found in Namavali: {len(namavali_numbers)}")
    print(f"Total unique numbers found in Verse files: {len(verse_numbers)}")
    
    # 3. Check for missing or extra numbers
    missing_in_verses = namavali_numbers - verse_numbers
    missing_in_namavali = verse_numbers - namavali_numbers
    
    if missing_in_verses:
        print(f"⚠️ Numbers in Namavali missing from Verse files: {sorted(list(missing_in_verses))[:20]}...")
    if missing_in_namavali:
        print(f"⚠️ Numbers in Verse files missing from Namavali: {sorted(list(missing_in_namavali))[:20]}...")
        
    if not missing_in_verses and not missing_in_namavali:
        print("✅ Perfect match! All numbers align correctly between Namavali and Verse files.")

if __name__ == '__main__':
    audit_scriptures()