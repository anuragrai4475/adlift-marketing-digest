# ========================================================================
# FINAL SCRIPT – FOR CLOUD DEPLOYMENT (GitHub Actions / Render / Replit)
# ========================================================================

import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import telegram
import asyncio
import time
import os
from datetime import datetime
import pytz
import nest_asyncio
nest_asyncio.apply()

# ========================================================================
# FUNCTION 1: Article Scraper
# ========================================================================
def get_articles_from_website(url):
    print(f"\n🔍 Scanning for articles on: {url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    articles_with_sources = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = set()

        for a in soup.find_all('a', href=True):
            href = a['href']
            if not href.startswith('http'):
                base_url = "https://" + url.split('/')[2]
                href = base_url + href if href.startswith('/') else base_url + '/' + href
            if url.split('/')[2] in href and 'author' not in href and 'category' not in href:
                links.add(href)

        print(f"✅ Found {len(links)} potential links. Reading the first 3...")
        for link in list(links)[:3]:
            try:
                art = requests.get(link, headers=headers, timeout=10)
                s = BeautifulSoup(art.content, 'html.parser')
                paragraphs = [p.get_text() for p in s.find_all('p')]
                content = "\n".join(paragraphs)
                if len(content) > 300:
                    articles_with_sources.append({'url': link, 'content': content})
            except Exception:
                pass
        return articles_with_sources
    except Exception as e:
        print(f"⚠️ Error while fetching from {url}: {e}")
        return []

# ========================================================================
# FUNCTION 2: AI Summarizer
# ========================================================================
def summarize_articles_with_ai_grouped(list_of_articles_with_sources):
    print("\n🤖 Asking the AI to perform a professional analysis...")
    try:
        my_gemini_key = os.environ.get('GEMINI_API_KEY')
        genai.configure(api_key=my_gemini_key)

        combined_text = ""
        for item in list_of_articles_with_sources:
            combined_text += f"SOURCE_URL: {item['url']}\nCONTENT:\n{item['content']}\n\n---END OF ARTICLE---\n\n"

        prompt = f"""
You are a Senior Marketing Strategist AI. Analyze the following full marketing articles and generate a professional digest.

Format using basic Telegram Markdown:

📊 *Executive Summary*  
(Write a 2–3 sentence summary of overall trends in the articles)

🚀 *Actionable Trends*  
Then, for each trend:
- Start with 📌 *Title of the trend*  
- Write 2-sentence description of the insight  
- Add (Source: [URL])

ARTICLES TO ANALYZE:
{combined_text}
        """

        ai_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"  > AI issue: {e}")
        return "Could not summarize articles."

# ========================================================================
# FUNCTION 3: Telegram Sender
# ========================================================================
async def send_message_to_telegram(message):
    print("\n📬 Preparing to send the final report...")
    try:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        bot = telegram.Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', disable_web_page_preview=True)
        print("✅ Message sent!")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# ========================================================================
# FUNCTION 4: Main Logic
# ========================================================================
def main():
    print("\n🚀 STARTING FULL DAILY MARKETING DIGEST")

    websites = [
        "https://blog.hubspot.com/marketing", "https://moz.com/blog", "https://contentmarketinginstitute.com/blog/",
        "https://www.searchenginejournal.com/", "https://www.socialmediaexaminer.com/", "https://neilpatel.com/blog/",
        "https://backlinko.com/blog", "https://ahrefs.com/blog", "https://www.marketingprofs.com/", "https://copyblogger.com/blog/"
    ]

    all_articles = []
    for site in websites:
        all_articles.extend(get_articles_from_website(site))
        time.sleep(1)

    if all_articles:
        print(f"\n✅ Scraped {len(all_articles)} full articles.")
        summary = summarize_articles_with_ai_grouped(all_articles)

        # 📅 Format today's date in IST
        ist = pytz.timezone('Asia/Kolkata')
        today_date = datetime.now(ist).strftime("%B %d, %Y")

        # 📝 Build Telegram Message
        title = f"*Hi Adlift Team! ☀️*\n\n*📢 Your Daily Marketing Trends Digest for {today_date} 📢*\n\n"
        closing = "\n\n------------------------------------\n*Have a productive day!* — Your AI Analyst"
        final_message = title + summary + closing

        asyncio.run(send_message_to_telegram(final_message))
        print("✅ Digest sent successfully.")
    else:
        print("❌ No articles found.")

# ========================================================================
# ENTRY POINT
# ========================================================================
if __name__ == "__main__":
    main()
