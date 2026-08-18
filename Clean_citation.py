import os
import glob
import re

def clean_all_citations():
    html_files = glob.glob("*.html")
    
    if not html_files:
        print("No HTML files found in the current directory.")
        return

    # Properly defined regex pattern to catch full citations or partial/malformed ones
    cite_pattern = re.compile(r'\[\s*cite:\s*\d+(?:\.\s*தமிழ்)?.*?\]?|【cite:.*?】')

    modified_count = 0
    for filename in html_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if cite_pattern.search(content):
                cleaned_content = cite_pattern.sub('', content)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                
                print(f"[SUCCESS] Cleaned all citations from: {filename}")
                modified_count += 1
            else:
                print(f"[SKIPPED] No citations found in: {filename}")
                
        except Exception as e:
            print(f"[ERROR] Could not process {filename}: {e}")

    print(f"\nCleanup complete! Modified {modified_count} file(s).")

if __name__ == '__main__':
    print("Starting deep automated citation cleanup...")
    clean_all_citations()