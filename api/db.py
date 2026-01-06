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
            print("❌ Error: SUPABASE_URL environment variable is missing.")
            self.is_configured = False
        if not self.supabase_key:
            print("❌ Error: SUPABASE_KEY environment variable is missing.")
            self.is_configured = False

        if self.is_configured:
            print(f"✅ Supabase Client configured for URL: {self.supabase_url[:8]}...")
            # Normalize URL to ensure no trailing slash
            self.base_url = self.supabase_url.rstrip('/')
            self.headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }

    async def get_summary_by_date(self, date_str: str) -> str:
        """
        Fetch summary for a specific date (YYYY-MM-DD).
        """
        if not self.is_configured:
            return None

        url = f"{self.base_url}/rest/v1/news_summaries"
        params = {
            "date": f"eq.{date_str}",
            "select": "content"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            print(f"Cache HIT for {date_str}")
                            return data[0].get("content")
                    else:
                        await self.log_error("db:read", f"Status {response.status}: {await response.text()}")
        except Exception as e:
            print(f"Supabase Connection Failed: {e}")

        print(f"Cache MISS for {date_str}")
        return None

    async def save_summary(self, date_str: str, content: str):
        """
        Save the summary to the database.
        """
        if not self.is_configured:
            return

        url = f"{self.base_url}/rest/v1/news_summaries"
        payload = {
            "date": date_str,
            "content": content
        }

        # Prefer: resolution=merge-duplicates enables UPSERT based on Primary Key
        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status in [200, 201, 204]:
                        print(f"Successfully saved summary for {date_str}")
                    else:
                        await self.log_error("db:write", f"Status {response.status}: {await response.text()}")
        except Exception as e:
            print(f"Supabase Save Failed: {e}")

    async def get_available_dates(self):
        """
        Get a list of dates that have summaries.
        Returns a list of strings ["2024-05-20", "2024-05-19", ...]
        """
        if not self.is_configured:
            return []

        url = f"{self.base_url}/rest/v1/news_summaries"
        params = {
            "select": "date",
            "order": "date.desc"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [item['date'] for item in data]
                    else:
                        await self.log_error("db:history", f"Status {response.status}: {await response.text()}")
        except Exception as e:
             print(f"Supabase History Fetch Failed: {e}")

        return []

    async def log_error(self, source: str, message: str):
        """
        Log an error to the error_logs table.
        """
        if not self.is_configured:
            print(f"[Local Log] {source}: {message}")
            return

        url = f"{self.base_url}/rest/v1/error_logs"
        payload = {
            "source": source,
            "message": str(message)[:1000] # Truncate if too long
        }

        try:
            # Fire and forget-ish (we await but catch all)
            async with aiohttp.ClientSession() as session:
                await session.post(url, headers=self.headers, json=payload)
        except Exception as e:
            print(f"Failed to log error to Supabase: {e}")
