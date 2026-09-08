import requests
from bs4 import BeautifulSoup
import json
import os

# Updated to use Book Outlet's direct, default US region catalog link
TARGET_URL = "https://bookoutlet.com"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL") 
CACHE_FILE = "stored_books.txt"

def get_already_seen():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def save_new_inventory(seen_set):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(seen_set))

def scrape_book_outlet():
    # Enriched headers to mimic a normal browser request completely
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://bookoutlet.com/"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers)
        print(f"[DEBUG] Website responded with status code: {response.status_code}")
        
        if response.status_code != 200:
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        already_seen = get_already_seen()
        new_books = []
        
        # Broadened selectors to catch any alternative grid tags Book Outlet uses
        book_elements = soup.find_all("div", class_="product-card") or soup.find_all("div", class_="grid-item")
        print(f"[DEBUG] Total items found on page grid: {len(book_elements)}")
        
        for book in book_elements:
            try:
                title_tag = book.find("h3", class_="product-card__title") or book.find("div", class_="title") or book.find("h3")
                link_tag = book.find("a", href=True)
                price_tag = book.find("span", class_="product-card__price") or book.find("span", class_="price")
                
                if not title_tag or not link_tag:
                    continue
                    
                title = title_tag.text.strip()
                book_url = "https://bookoutlet.com" + link_tag['href']
                price = price_tag.text.strip() if price_tag else "Price N/A"
                
                if book_url not in already_seen:
                    new_books.append({"title": title, "url": book_url, "price": price})
                    already_seen.add(book_url)
            except Exception as e:
                print(f"[DEBUG] Individual book parsing skip: {e}")
                continue

        print(f"[DEBUG] New books being sent to Discord: {len(new_books)}")

        if new_books:
            save_new_inventory(already_seen)
            for item in new_books:
                payload = {
                    "embeds": [{
                        "title": "📖 New Fiction Listed!",
                        "description": f"**[{item['title']}]({item['url']})** is now live.",
                        "color": 3447003,
                        "fields": [{"name": "Price", "value": item['price'], "inline": True}]
                    }]
                }
                res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
                print(f"[DEBUG] Discord Response: {res.status_code}")
                
    except Exception as e:
        print(f"[DEBUG] Error details: {e}")

if __name__ == "__main__":
    scrape_book_outlet()
