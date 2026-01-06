import aiohttp
import os
import json

class SupabaseClient:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        # Check configuration explicitly for debugging
        self.is_configured = True
        if not self.supabase_url:
            self.is_configured = False
        if not self.supabase_key:
            self.is_configured = False

        if self.is_configured:
            # Normalize URL to ensure no trailing slash
            self.base_url = self.supabase_url.rstrip('/')
            self.headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }

    # --- Summary Cache Methods ---

    async def get_summary_by_date(self, date_str: str) -> str:
        """Fetch daily summary for a specific date."""
        if not self.is_configured: return None
        url = f"{self.base_url}/rest/v1/news_summaries"
        params = {"date": f"eq.{date_str}", "select": "content"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data[0].get("content") if data else None
                    else:
                        await self.log_error("db:read_summary", f"Status {response.status}: {await response.text()}")
        except Exception as e:
            print(f"DB Read Error: {e}")
        return None

    async def save_summary(self, date_str: str, content: str):
        """Save daily summary."""
        if not self.is_configured: return
        url = f"{self.base_url}/rest/v1/news_summaries"
        payload = {"date": date_str, "content": content}
        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, headers=headers, json=payload)
        except Exception as e:
            print(f"DB Save Error: {e}")

    async def get_available_dates(self):
        """Get list of dates with summaries."""
        if not self.is_configured: return []
        url = f"{self.base_url}/rest/v1/news_summaries"
        params = {"select": "date", "order": "date.desc"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [item['date'] for item in data]
        except Exception:
            pass
        return []

    # --- Article Cache Methods ---

    async def get_article(self, url_key: str):
        """Check if article exists. Returns dict {'content': ..., 'title': ...} or None."""
        if not self.is_configured: return None
        # URL might contain special chars, rely on params
        api_url = f"{self.base_url}/rest/v1/articles"
        params = {"url": f"eq.{url_key}", "select": "title,content,source"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data[0] if data else None
        except Exception:
            pass
        return None

    async def save_article(self, url: str, title: str, content: str, source: str, published_date: str):
        """Save individual article."""
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
                async with session.post(api_url, headers=headers, json=payload) as resp:
                    if resp.status not in [200, 201, 204]:
                         await self.log_error("db:save_article", f"Status {resp.status}")
        except Exception:
            pass

    # --- System ---

    async def log_error(self, source: str, message: str):
        """Log error to DB."""
        if not self.is_configured:
            print(f"[Local Log] {source}: {message}")
            return
        url = f"{self.base_url}/rest/v1/error_logs"
        payload = {"source": source, "message": str(message)[:1000]}
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, headers=self.headers, json=payload)
        except Exception:
            pass
