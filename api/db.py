import aiohttp
import os
import json

class SupabaseClient:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        self.is_configured = True
        if not self.supabase_url: self.is_configured = False
        if not self.supabase_key: self.is_configured = False

        if self.is_configured:
            self.base_url = self.supabase_url.rstrip('/')
            self.headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }

    # --- Summary Cache ---

    async def get_summary_by_date(self, date_str: str) -> str:
        if not self.is_configured: return None
        url = f"{self.base_url}/rest/v1/news_summaries"
        # Get the LATEST version (order by version desc limit 1)
        params = {"date": f"eq.{date_str}", "select": "content", "order": "version.desc", "limit": "1"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data[0].get("content") if data else None
        except Exception: pass
        return None

    async def save_summary(self, date_str: str, content: str, prompt: str = None):
        if not self.is_configured: return
        url = f"{self.base_url}/rest/v1/news_summaries"

        # 1. Get current max version for this date
        max_version = 0
        try:
            async with aiohttp.ClientSession() as session:
                params = {"date": f"eq.{date_str}", "select": "version", "order": "version.desc", "limit": "1"}
                async with session.get(url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data:
                            max_version = data[0].get('version', 0) or 0
        except Exception as e:
            print(f"Error getting max version: {e}")

        # 2. Insert new version
        new_version = max_version + 1
        payload = {
            "date": date_str,
            "content": content,
            "version": new_version,
            "prompt": prompt
        }

        # We use POST to insert a new row (since PK is date+version)
        # We do NOT use merge-duplicates resolution because we want a new row
        headers = self.headers.copy()
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, headers=headers, json=payload)
        except Exception: pass

    async def get_available_dates(self):
        if not self.is_configured: return []
        url = f"{self.base_url}/rest/v1/news_summaries"
        params = {"select": "date", "order": "date.desc"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Deduplicate while preserving order (Python 3.7+ dicts preserve insertion order)
                        dates = [item['date'] for item in data]
                        return list(dict.fromkeys(dates))
        except Exception: pass
        return []

    # --- Articles ---

    async def get_article(self, url_key: str):
        if not self.is_configured: return None
        api_url = f"{self.base_url}/rest/v1/articles"
        params = {"url": f"eq.{url_key}", "select": "title,content,source,published_date"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data[0] if data else None
        except Exception: pass
        return None

    async def save_article(self, url: str, title: str, content: str, source: str, published_date: str):
        if not self.is_configured: return
        api_url = f"{self.base_url}/rest/v1/articles"
        payload = {
            "url": url,
            "title": title,
            "content": content,
            "source": source,
            "published_date": published_date
        }
        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(api_url, headers=headers, json=payload)
        except Exception: pass

    async def get_articles_by_date(self, date_str: str):
        """Fetch list of articles for a given date."""
        if not self.is_configured: return []
        api_url = f"{self.base_url}/rest/v1/articles"
        # Select title, url, source, and published_date.
        # Note: We don't fetch 'content' to keep the list response light.
        params = {
            "published_date": f"eq.{date_str}",
            "select": "title,url,source,published_date",
            "order": "created_at.desc"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data
        except Exception: pass
        return []

    # --- Logs ---

    async def log_error(self, source: str, message: str):
        if not self.is_configured:
            print(f"[Local Log] {source}: {message}")
            return
        url = f"{self.base_url}/rest/v1/error_logs"
        payload = {"source": source, "message": str(message)[:1000]}
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, headers=self.headers, json=payload)
        except Exception: pass

    # --- Market Liquidity ---

    async def save_market_liquidity(self, data_list: list):
        """
        Upserts market liquidity data points.
        data_list: List of dicts with keys: date, walcl, tga, rrp, net_liquidity
        """
        if not self.is_configured or not data_list: return
        url = f"{self.base_url}/rest/v1/market_liquidity"

        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"

        # Supabase allows bulk upsert
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, headers=headers, json=data_list)
        except Exception as e:
            print(f"Error saving market liquidity: {e}")

    async def get_market_liquidity(self):
        """Fetch all market liquidity data ordered by date."""
        if not self.is_configured: return []
        url = f"{self.base_url}/rest/v1/market_liquidity"
        params = {
            "select": "date,net_liquidity,walcl,tga,rrp",
            "order": "date.asc"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            print(f"Error fetching market liquidity: {e}")
        return []

    # --- Economic Indicators ---

    async def save_economic_indicators(self, data_list: list):
        """
        Upserts economic indicators.
        data_list: List of dicts with keys: date, symbol, value
        """
        if not self.is_configured or not data_list: return
        url = f"{self.base_url}/rest/v1/economic_indicators"

        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"

        try:
            async with aiohttp.ClientSession() as session:
                # Supabase limits bulk insert size? Split if too large?
                # 5 years daily ~ 1800 rows. Should be fine.
                await session.post(url, headers=headers, json=data_list)
        except Exception as e:
            print(f"Error saving economic indicators: {e}")

    async def get_economic_indicators(self, symbol: str = None):
        """
        Fetch economic indicators.
        If symbol provided, filter by it.
        """
        if not self.is_configured: return []
        url = f"{self.base_url}/rest/v1/economic_indicators"
        params = {
            "select": "date,symbol,value",
            "order": "date.asc"
        }
        if symbol:
            params["symbol"] = f"eq.{symbol}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            print(f"Error fetching economic indicators: {e}")
        return []
