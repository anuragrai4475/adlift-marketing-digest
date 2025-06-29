# ============================================================================== #
# FINAL SCRIPT – Adlift Marketing Digest (GitHub Version)
# ============================================================================== #

import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import telegram
import asyncio
import time
import os
from datetime import datetime
import nest_asyncio
nest_asyncio.apply()

# ============================================================================== #
# FUNCTION 1: Web Scraper
# ============================================================================== #
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

# ============================================================================== #
# FUNCTION 2: AI Summary with Grouping
# ============================================================================== #
def summarize_articles_with_ai_grouped(list_of_articles_with_sources):
    print("\n🤖 Asking the AI to perform a professional analysis...")
    try:
        my_gemini_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=my_gemini_key)

        combined_text = ""
        for item in list_of_articles_with_sources:
            combined_text += f"SOURCE_URL: {item['url']}\nCONTENT:\n{item['content']}\n\n---END OF ARTICLE---\n\n"

        prompt = f"""
You are a Senior Marketing Strategist AI. Your task is to analyze marketing articles and provide a high-level executive summary for a busy marketing team.

Format the output for Telegram in standard Markdown and follow this exact structure:

1. *📊 Executive Summary* — A one-paragraph overview of key marketing developments.
2. *🚀 Actionable Trends* — 3–4 insightful trends.

Each trend must have:
- 📌 *Bold Title*
- 2 sentence summary
- (Source: [URL])

ARTICLES TO ANALYZE:
{combined_text}
"""
        ai_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ AI issue: {e}")
        return "Could not summarize articles."

# ============================================================================== #
# FUNCTION 3: Telegram Message Sender (with chunking)
# ============================================================================== #
async def send_message_to_telegram(message):
    print("\n📬 Preparing to send the final report...")
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        bot = telegram.Bot(token=bot_token)

        if len(message) <= 4096:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', disable_web_page_preview=True)
        else:
            print("⚠️ Message too long, sending in chunks...")
            chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for chunk in chunks:
                await bot.send_message(chat_id=chat_id, text=chunk, parse_mode='Markdown', disable_web_page_preview=True)
                await asyncio.sleep(1)

        print("✅ Digest sent successfully.")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# ============================================================================== #
# MAIN RUNNER
# ============================================================================== #
def main():
    print("\n🚀 STARTING DAILY MARKETING DIGEST...")

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

        today = datetime.now().strftime("%B %d, %Y")
        title = f"*Hi Adlift Team!* ☀️\n\n*📢 Your Daily Marketing Trends Digest for {today} 📢*\n"
        divider = "------------------------------------\n\n"
        closing = "\n\n------------------------------------\n*Have a productive day!* — Your AI Analyst"

        final_message = title + divider + summary + closing
        asyncio.run(send_message_to_telegram(final_message))
        print("\n✅ JOB COMPLETE")
    else:
        print("\n❌ No new articles found.")

if __name__ == "__main__":
    main()
