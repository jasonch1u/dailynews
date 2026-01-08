import aiohttp
import asyncio
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime, timezone, timedelta
from api.llm_utils import translate_text

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/"
}

TZ_TW = timezone(timedelta(hours=8))

def get_tw_now():
    return datetime.now(TZ_TW)

def get_today_str():
    return get_tw_now().strftime("%Y-%m-%d")

def is_today_tw(date_iso_str):
    if not date_iso_str: return False
    try:
        if date_iso_str.endswith('Z'): date_iso_str = date_iso_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(date_iso_str).astimezone(TZ_TW)
        return dt.date() == get_tw_now().date()
    except:
        return False

async def fetch_url_with_retry(session, url, retries=2):
    """Fetch URL with retry mechanism."""
    for i in range(retries + 1):
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 404:
                    return None
        except Exception as e:
            if i == retries:
                print(f"Failed to fetch {url}: {e}")
            else:
                await asyncio.sleep(1)
    return None

async def process_article_link(session, db, title, link, source, content_selector, check_date=False):
    """
    Process a single article link:
    1. Check DB for content.
    2. If miss, scrape.
    3. Save to DB.
    """
    if db:
        cached = await db.get_article(link)
        if cached:
            # Enforce date check on cached articles to prevent "yesterday's news" from appearing today
            # If the article is cached but the date is not today, we treat it as expired for the purpose of "Daily Summary"
            cached_date = cached.get('published_date')
            if cached_date == get_today_str():
                # Return DB content
                return f"### {cached['title']}\n{cached['content']}\n出處: {source}\nLink: {link}"
            # If date doesn't match today, we skip returning it (and likely don't need to re-scrape if it's old)
            return None

    try:
        html = await fetch_url_with_retry(session, link)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            if check_date:
                # Basic check for meta tags
                is_valid = False
                # 1. Check Meta Tags
                for meta_prop in ['article:published_time', 'og:updated_time', 'datePublished']:
                    meta = soup.find('meta', property=meta_prop) or soup.find('meta', itemprop=meta_prop)
                    if meta and meta.get('content'):
                        c = meta.get('content')
                        if ("T" in c and is_today_tw(c)) or c.startswith(get_today_str()):
                            is_valid = True; break

                # 2. Check <time> tag (Common in modern sites like Cnyes, Anduril)
                if not is_valid:
                    time_tags = soup.find_all('time')
                    for t in time_tags:
                         datetime_val = t.get('datetime')
                         if datetime_val:
                              if ("T" in datetime_val and is_today_tw(datetime_val)) or datetime_val.startswith(get_today_str()):
                                   is_valid = True; break

                if not is_valid: return None

            container = soup.select_one(content_selector) if content_selector else soup.find('main')
            if not container: container = soup

            text = "\n".join([p.text.strip() for p in container.find_all('p') if len(p.text.strip()) > 10])
            content = text[:2000] + "..." if len(text) > 2000 else text

            if content:
                if db:
                    await db.save_article(link, title, content, source, get_today_str())
                return f"### {title}\n{content}\n出處: {source}\nLink: {link}"
    except Exception as e:
        if db: await db.log_error(f"scraper:{source}", f"Error processing {link}: {e}")

    return None

async def fetch_rss_feed(session, db, url, source_name, translate=False, allow_empty_content=False):
    """
    Generic RSS Fetcher.
    Fetches RSS XML, parses items, checks DB, returns formatted string.
    translate: If True, translates titles to Traditional Chinese.
    allow_empty_content: If True, uses title as content if description is missing (e.g. SeekingAlpha).
    """
    articles = []
    new_items = [] # (title, link, content) to be saved

    try:
        xml = await fetch_url_with_retry(session, url)
        if xml:
            try:
                soup = BeautifulSoup(xml, 'xml')
            except Exception:
                soup = BeautifulSoup(xml, 'html.parser')

            if not soup.find('item'):
                soup = BeautifulSoup(xml, 'html.parser')

            items = soup.find_all('item')
            for item in items[:10]: # Top 10
                title = item.title.text.strip() if item.title else "No Title"
                link = item.link.text.strip() if item.link else ""
                if not link and item.guid: link = item.guid.text.strip()

                # Check RSS PubDate
                pub_date_str = item.pubDate.text.strip() if item.pubDate else None
                if pub_date_str:
                    # RSS Date Format: "Tue, 06 Jan 2026 22:00:03 +0800" or similar
                    try:
                        # Try parsing common RSS formats
                        pd = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                        # Convert to TW time
                        pd_tw = pd.astimezone(TZ_TW)
                        if pd_tw.date() != get_tw_now().date():
                            continue # Skip if not today
                    except ValueError:
                        # If format doesn't match, we might skip strict check or try other formats
                        # For now, let's just log and proceed (or skip strict check to avoid losing data)
                        pass

                # Check DB first
                if db:
                    cached = await db.get_article(link)
                    if cached:
                        # Validate cached date
                        if cached.get('published_date') == get_today_str():
                            articles.append(f"### {cached['title']}\n{cached['content']}\n出處: {source_name}\nLink: {link}")
                        continue

                description = item.description.text.strip() if item.description else ""
                desc_soup = BeautifulSoup(description, 'html.parser')
                content = desc_soup.get_text().strip()

                # Fallback for empty content (e.g. SeekingAlpha)
                if not content and allow_empty_content and title:
                    content = title

                if content and link:
                    new_items.append({"title": title, "link": link, "content": content})

            # Batch Translate Titles if needed
            if translate and new_items:
                titles = [x['title'] for x in new_items]
                api_key = os.getenv("GEMINI_API_KEY")
                translated_titles = await translate_text(titles, api_key)

                # Update titles
                for i, t_title in enumerate(translated_titles):
                    if i < len(new_items):
                        new_items[i]['title'] = t_title

            # Save and Format
            for item in new_items:
                if db:
                    await db.save_article(item['link'], item['title'], item['content'], source_name, get_today_str())
                articles.append(f"### {item['title']}\n{item['content']}\n出處: {source_name}\nLink: {item['link']}")

    except Exception as e:
        print(f"{source_name} RSS Error: {e}")
        if db: await db.log_error(f"scraper:{source_name}", str(e))
    return articles

async def fetch_anduril_tw(session, db=None):
    url = "https://www.anduril.tw"
    tasks = []
    html = await fetch_url_with_retry(session, url)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('article', class_='gh-card')
        for card in cards:
            if len(tasks) >= 10: break
            time_tag = card.find('time')
            if time_tag and time_tag.get('datetime') != get_today_str(): continue
            link_tag = card.find('a', class_='gh-card-link')
            title_tag = card.find('h3', class_='gh-card-title')
            if link_tag and title_tag:
                title = title_tag.text.strip()
                link = link_tag.get('href')
                if not link.startswith('http'): link = url + link if link.startswith('/') else url + '/' + link
                if not any(x in link for x in ["tag", "category", "author"]):
                    # Changed source name to FOX per request
                    tasks.append(process_article_link(session, db, title, link, "FOX", "section.gh-content", False))
    return [x for x in await asyncio.gather(*tasks) if x]

async def fetch_blocktempo(session, db=None):
    url = "https://www.blocktempo.com/2026/"
    tasks = []
    html = await fetch_url_with_retry(session, url)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for h3 in soup.find_all('h3'):
            if len(tasks) >= 10: break
            a = h3.find('a')
            if a and a.get('href'):
                title = a.get('title') or a.text.strip()
                link = a.get('href')
                if len(title) > 5:
                    # Changed source name to 動區 per request
                    tasks.append(process_article_link(session, db, title, link, "動區", ".entry-content", True))
    return [x for x in await asyncio.gather(*tasks) if x]

async def fetch_cnyes_stock(session, db=None):
    # Use RSS feed to avoid client-side rendering issues and sidebar noise
    rss_url = "https://news.cnyes.com/rss/v1/news/category/wd_stock"
    tasks = []

    try:
        xml = await fetch_url_with_retry(session, rss_url)
        if xml:
            try:
                soup = BeautifulSoup(xml, 'xml')
            except:
                soup = BeautifulSoup(xml, 'html.parser')

            items = soup.find_all('item')
            for item in items[:10]: # Top 10 latest
                title = item.title.text.strip() if item.title else "No Title"
                link = item.link.text.strip() if item.link else ""
                if not link and item.guid: link = item.guid.text.strip()

                # Filter out "鉅亨速報" and "盤中速報"
                if "鉅亨速報" in title or "盤中速報" in title:
                    continue

                if link and title:
                    # We still fetch the full article content using process_article_link
                    # This ensures we get the full text, not just the RSS summary
                    # And process_article_link handles the <time> tag check
                    tasks.append(process_article_link(session, db, title, link, "Cnyes", "#article-container", True))

    except Exception as e:
        print(f"Cnyes RSS Error: {e}")
        if db: await db.log_error("scraper:cnyes", str(e))

    return [x for x in await asyncio.gather(*tasks) if x]

async def fetch_cnbc(session, db=None):
    # Enable Translation
    return await fetch_rss_feed(session, db, "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "CNBC", translate=True)

async def fetch_seeking_alpha(session, db=None):
    # SeekingAlpha RSS has empty descriptions and blocks scraping content.
    # We enable allow_empty_content=True to use the Title as the content, so the AI at least sees the headlines.
    return await fetch_rss_feed(session, db, "https://seekingalpha.com/market_currents.xml", "SeekingAlpha", translate=True, allow_empty_content=True)

async def fetch_marketwatch(session, db=None):
    return await fetch_rss_feed(session, db, "https://feeds.content.dowjones.io/public/rss/mw_topstories", "MarketWatch", translate=True)

# New fetch functions for additional sources
async def fetch_bbc(session, db=None):
    return await fetch_rss_feed(session, db, "http://feeds.bbci.co.uk/news/rss.xml", "BBC", translate=True)

async def fetch_cnn(session, db=None):
    return await fetch_rss_feed(session, db, "http://rss.cnn.com/rss/edition.rss", "CNN", translate=True)

async def fetch_techcrunch(session, db=None):
    return await fetch_rss_feed(session, db, "https://techcrunch.com/feed/", "TechCrunch", translate=True)

async def fetch_forbes(session, db=None):
    return await fetch_rss_feed(session, db, "https://www.forbes.com/most-popular/feed/", "Forbes", translate=True)

async def fetch_business_insider(session, db=None):
    return await fetch_rss_feed(session, db, "https://feeds.businessinsider.com/custom/all", "BusinessInsider", translate=True)

async def fetch_axios(session, db=None):
    return await fetch_rss_feed(session, db, "https://api.axios.com/feed/", "Axios", translate=True)

async def fetch_nyt(session, db=None):
    return await fetch_rss_feed(session, db, "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "NYT", translate=True)

async def fetch_reuters(session, db=None):
    # Reuters public RSS is deprecated. Using Google News RSS proxy for Reuters.
    url = "https://news.google.com/rss/search?q=site:reuters.com+when:1d&hl=en-US&gl=US&ceid=US:en"
    # Google News RSS items link to google redirects, but fetch_rss_feed stores the link.
    # process_article_link follows redirects usually? aiohttp follows redirects by default.
    return await fetch_rss_feed(session, db, url, "Reuters", translate=True)

async def run_all_scrapers(db_client=None, sources=None):
    """
    Run scrapers based on sources list.
    sources: list of strings
    """
    tasks = []
    # If sources is None or empty, we default to ALL sources
    # But for "Live Update" via API, the frontend might send specific sources.
    # We need to ensure new sources are included in the default set if sources is None.

    known_sources = {
        'anduril': fetch_anduril_tw,
        'blocktempo': fetch_blocktempo,
        'cnyes': fetch_cnyes_stock,
        'cnbc': fetch_cnbc,
        'seekingalpha': fetch_seeking_alpha,
        'marketwatch': fetch_marketwatch,
        'bbc': fetch_bbc,
        'cnn': fetch_cnn,
        'techcrunch': fetch_techcrunch,
        'forbes': fetch_forbes,
        'businessinsider': fetch_business_insider,
        'axios': fetch_axios,
        'nyt': fetch_nyt,
        'reuters': fetch_reuters
    }

    if not sources:
        sources = list(known_sources.keys())

    async with aiohttp.ClientSession() as session:
        for s in sources:
            if s in known_sources:
                tasks.append(known_sources[s](session, db_client))

        # Use return_exceptions=True so one failure doesn't crash the whole batch
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and filter out exceptions
        valid_results = []
        for res in results:
            if isinstance(res, Exception):
                print(f"Scraper Error: {res}")
                if db_client: await db_client.log_error("scraper:aggregator", str(res))
            elif isinstance(res, list):
                valid_results.extend(res)

        return valid_results
