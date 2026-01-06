import aiohttp
import os
import json

class SupabaseClient:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        # Check if config is present, but don't crash if missing (graceful degradation)
        self.is_configured = bool(self.supabase_url and self.supabase_key)

        if self.is_configured:
            # Normalize URL to ensure no trailing slash
            self.base_url = self.supabase_url.rstrip('/')
            self.headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal" # For inserts, we don't need the object back usually
            }

    async def get_summary_by_date(self, date_str: str) -> str:
        """
        Fetch summary for a specific date (YYYY-MM-DD).
        Returns None if not found or not configured.
        """
        if not self.is_configured:
            print("Supabase not configured, skipping cache check.")
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
                        print(f"Supabase Read Error: {response.status} - {await response.text()}")
        except Exception as e:
            print(f"Supabase Connection Failed: {e}")

        print(f"Cache MISS for {date_str}")
        return None

    async def save_summary(self, date_str: str, content: str):
        """
        Save the summary to the database.
        Uses upsert logic (insert on conflict update) if possible,
        but standard REST 'POST' is Insert.
        To do upsert via REST, we add 'Prefer: resolution=merge-duplicates' header.
        """
        if not self.is_configured:
            print("Supabase not configured, skipping save.")
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
                        print(f"Supabase Write Error: {response.status} - {await response.text()}")
        except Exception as e:
            print(f"Supabase Save Failed: {e}")
