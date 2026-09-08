import requests
from bs4 import BeautifulSoup
import json
import os

TARGET_URL = "https://bookoutlet.com"
# This pulls your hidden Discord URL from GitHub's settings
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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(TARGET_URL, headers=headers)
        if response.status_code != 200:
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        already_seen = get_already_seen()
        new_books = []
        
        # Pulls the first 20 books available on the page grid
        book_elements = soup.find_all("div", class_="product-card")[:20] 
        
        for book in book_elements:
            try:
                title_tag = book.find("h3", class_="product-card__title") or book.find("div", class_="title")
                link_tag = book.find("a", href=True)
                price_tag = book.find("span", class_="product-card__price") or book.find("span", class_="price")
                
                title = title_tag.text.strip()
                book_url = "https://bookoutlet.com" + link_tag['href']
                price = price_tag.text.strip() if price_tag else "Price N/A"
                
                if book_url not in already_seen:
                    new_books.append({"title": title, "url": book_url, "price": price})
                    already_seen.add(book_url)
            except Exception:
                continue

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
                requests.post(DISCORD_WEBHOOK_URL, json=payload)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_book_outlet()
