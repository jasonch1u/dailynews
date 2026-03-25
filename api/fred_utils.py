import aiohttp
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

class FredClient:
    def __init__(self, db_client):
        self.api_key = os.getenv("FRED_API_KEY")
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        self.db_client = db_client

    async def fetch_series(self, series_id: str, start_date: str = "2025-12-01") -> List[Dict[str, Any]]:
        """
        Fetch series data from FRED API.
        Returns a list of dicts: {'date': 'YYYY-MM-DD', 'value': float}
        """
        if not self.api_key:
            print("FRED_API_KEY not set.")
            return []

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date
        }

        # Determine frequency to minimize data transfer if possible,
        # but FRED API 'frequency' param mainly aggregates.
        # For RRP (Daily), we might fetch all and filter later, or trust the caller.
        # WALCL and WDTGAL are Weekly (Wed).

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        observations = data.get("observations", [])
                        result = []
                        for obs in observations:
                            val = obs.get("value")
                            # FRED returns "." for missing values
                            if val and val != ".":
                                result.append({
                                    "date": obs.get("date"),
                                    "value": float(val)
                                })
                        return result
                    else:
                        print(f"Error fetching {series_id}: {resp.status}")
                        return []
            except Exception as e:
                print(f"Exception fetching {series_id}: {e}")
                return []

    async def update_market_liquidity(self):
        """
        Fetches WALCL, WDTGAL, RRPONTSYD, aligns them by Wednesday,
        calculates Net Liquidity, and saves to DB.
        """
        if not self.api_key:
            return {"status": "error", "message": "FRED_API_KEY missing"}

        print("Fetching FRED data...")
        # 1. Fetch all series
        # WALCL: Assets (Weekly, Wed) -> Unit: Millions
        # WDTGAL: TGA (Weekly, Wed) -> Unit: Millions (Usually)
        # RRPONTSYD: RRP (Daily) -> Unit: Billions (Usually! Need to verify units)

        # CHECK UNITS:
        # WALCL: Millions of U.S. Dollars
        # WDTGAL: Millions of U.S. Dollars
        # RRPONTSYD: Billions of U.S. Dollars (Wait, let's verify via Google or assumption)
        # RRPONTSYD on FRED says "Billions of U.S. Dollars".
        # WALCL/WDTGAL on FRED says "Millions of U.S. Dollars".
        # We need to normalize to Billions or Trillions for display, but for calculation:
        # Net Liquidity (Millions) = WALCL (Mil) - WDTGAL (Mil) - (RRP (Bil) * 1000)

        walcl_data, wdtgal_data, rrp_data = await asyncio.gather(
            self.fetch_series("WALCL"),
            self.fetch_series("WDTGAL"), # Or WTREGEN
            self.fetch_series("RRPONTSYD")
        )

        if not walcl_data:
            return {"status": "error", "message": "Failed to fetch WALCL"}

        # 2. Convert to lookup dicts for easier alignment
        # Structure: {'YYYY-MM-DD': value_in_millions}

        # WALCL is already in Millions
        walcl_map = {item['date']: item['value'] for item in walcl_data}

        # WDTGAL is already in Millions
        wdtgal_map = {item['date']: item['value'] for item in wdtgal_data}

        # RRP is in Billions -> Convert to Millions
        rrp_map = {item['date']: item['value'] * 1000 for item in rrp_data}

        # 3. Align based on WALCL dates (Wednesdays)
        # We iterate through WALCL dates. If a date exists in WALCL,
        # we look for it in WDTGAL and RRP.
        # Since RRP is daily, it should have the Wednesday date unless it's a holiday.
        # If holiday, FRED usually shifts the weekly release or the daily data point might be missing.
        # We'll skip points where data is incomplete or try to fill forward/zero?
        # Strict approach: skip if missing.

        processed_data = []

        # Sort dates to ensure order
        sorted_dates = sorted(walcl_map.keys())

        for date_str in sorted_dates:
            walcl_val = walcl_map[date_str]

            # Get TGA (expecting same date as it's Wednesday series)
            tga_val = wdtgal_map.get(date_str)

            # Get RRP (expecting same date)
            rrp_val = rrp_map.get(date_str)

            # RRP fallback: If RRP is missing on Wednesday (holiday),
            # maybe check prev day? For now, strict.
            # Note: RRP started later (2013). Before that RRP=0 effectively for this metric.
            if rrp_val is None:
                # If date is before 2014, assume 0 if we fetched back to 2002?
                # But we fetched from 2014.
                # If missing inside the range, it's a gap.
                pass

            if tga_val is not None and rrp_val is not None:
                net_liquidity = walcl_val - tga_val - rrp_val
                processed_data.append({
                    "date": date_str,
                    "walcl": walcl_val,     # Millions
                    "tga": tga_val,         # Millions
                    "rrp": rrp_val,         # Millions
                    "net_liquidity": net_liquidity # Millions
                })

        # 4. Save to DB
        # We will use upsert via db_client (need to add a method there)
        print(f"Computed {len(processed_data)} data points. Saving to DB...")
        await self.db_client.save_market_liquidity(processed_data)

        return {"status": "success", "count": len(processed_data)}

    async def update_economic_indicators(self):
        """
        Fetches additional economic indicators:
        - VIX (VIXCLS) - Daily
        - M2 (WM2NS) - Weekly
        - M1 (WM1NS) - Weekly
        - 10Y-2Y Spread (T10Y2Y) - Daily
        - Dollar Index (DTWEXBGS) - Daily (Weekly?) -> DTWEXBGS is Nominal Broad US Dollar Index (Daily)
        """
        if not self.api_key:
            return {"status": "error", "message": "FRED_API_KEY missing"}

        indicators = [
            {"id": "VIXCLS", "symbol": "VIX"},
            {"id": "WM2NS", "symbol": "M2"},
            {"id": "WM1NS", "symbol": "M1"},
            {"id": "T10Y2Y", "symbol": "10Y2Y"},
            {"id": "DTWEXBGS", "symbol": "DXY_BROAD"} # Broad Dollar Index
        ]

        total_saved = 0

        for ind in indicators:
            print(f"Fetching {ind['symbol']} ({ind['id']})...")
            # Fetch last 5 years to be safe, or just 2014 like liquidity
            data = await self.fetch_series(ind['id'], start_date="2014-01-01")

            if data:
                # Transform for DB: {date, symbol, value}
                formatted_data = [
                    {"date": item["date"], "symbol": ind["symbol"], "value": item["value"]}
                    for item in data
                ]
                await self.db_client.save_economic_indicators(formatted_data)
                total_saved += len(formatted_data)
            else:
                print(f"No data for {ind['symbol']}")

        # 2. Compute M1 & M2 YoY
        print("Computing M1/M2 YoY...")
        await self.update_m1_m2_yoy()

        return {"status": "success", "count": total_saved}

    async def update_m1_m2_yoy(self):
        """
        Calculates YoY Growth for M1 and M2 using stored data.
        Save as 'M1_YOY' and 'M2_YOY'.
        """
        for symbol in ["M1", "M2"]:
            # Fetch all data for the symbol
            data = await self.db_client.get_economic_indicators(symbol)
            if not data: continue

            # Sort by date
            data.sort(key=lambda x: x['date'])

            # Create a lookup for {date: value} for fast access
            # But dates are weekly, so we need to find "1 year ago".
            # Or simpler: for each point, look for a point ~365 days ago (within a margin).
            # M1/M2 are weekly.

            date_val_map = {d['date']: d['value'] for d in data}
            yoy_data = []

            for item in data:
                current_date_str = item['date']
                current_val = item['value']

                try:
                    current_dt = datetime.strptime(current_date_str, "%Y-%m-%d")
                    target_prev_year = current_dt - timedelta(days=365)

                    # Find closest date within a window (e.g., +/- 7 days) 1 year ago
                    # Because weekly data date might shift slightly.
                    found_prev_val = None

                    # Scan window
                    for offset in range(-7, 8):
                        check_date = (target_prev_year + timedelta(days=offset)).strftime("%Y-%m-%d")
                        if check_date in date_val_map:
                            found_prev_val = date_val_map[check_date]
                            break

                    if found_prev_val and found_prev_val != 0:
                        yoy_val = ((current_val - found_prev_val) / found_prev_val) * 100
                        yoy_data.append({
                            "date": current_date_str,
                            "symbol": f"{symbol}_YOY",
                            "value": round(yoy_val, 2)
                        })
                except Exception: continue

            if yoy_data:
                await self.db_client.save_economic_indicators(yoy_data)
                print(f"Saved {len(yoy_data)} points for {symbol}_YOY")
