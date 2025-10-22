#!/usr/bin/env python3
"""
Dual-purpose Cesium Ion proxy + cache (final fixed version)
------------------------------------------------------------
• Serves local imagery from ./tiles/
• Dynamically fetches Cesium Ion terrain endpoint
• Caches and serves quantized-mesh terrain from ./terrain/
• Adds CORS headers for CesiumJS viewer access
"""

import os, sys, aiohttp, aiofiles, asyncio
from aiohttp import web
from pathlib import Path

TOKEN = os.getenv("CESIUM_ION_TOKEN")
ASSET_ID = os.getenv("CESIUM_ASSET_ID")

if not TOKEN or not ASSET_ID:
    print("❌ Please set CESIUM_ION_TOKEN and CESIUM_ASSET_ID.")
    sys.exit(1)

IMAGERY_DIR = Path("tiles")
TERRAIN_DIR = Path("terrain")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

IMAGERY_DIR.mkdir(exist_ok=True)
TERRAIN_DIR.mkdir(exist_ok=True)

BASE_URL = None
ASSET_TOKEN = None


# ────────────────────────────────────────────────
async def resolve_endpoint():
    """Query Cesium Ion for the correct terrain endpoint."""
    global BASE_URL, ASSET_TOKEN
    api_url = f"https://api.cesium.com/v1/assets/{ASSET_ID}/endpoint"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    print(f"🔎 Resolving Cesium Ion endpoint → {api_url}")

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"❌ Failed to resolve endpoint ({resp.status}): {text[:200]}")
            info = await resp.json()
            BASE_URL = info.get("url", "").rstrip("/")
            ASSET_TOKEN = info.get("accessToken", TOKEN)
            print(f"✅ Endpoint resolved: {BASE_URL}")
            return BASE_URL


# ────────────────────────────────────────────────
async def fetch_and_cache(rel_path: str) -> bytes | None:
    """Fetch missing terrain tiles or layer.json from Cesium Ion."""
    global BASE_URL, ASSET_TOKEN
    if not BASE_URL:
        await resolve_endpoint()

    # Normalize URL path
    base = BASE_URL.rstrip("/")
    path = rel_path.lstrip("/")
    url = f"{base}/{path}" if path else f"{base}/layer.json"

    headers = {"Authorization": f"Bearer {ASSET_TOKEN}"}
    cache_path = TERRAIN_DIR / (path if path else "layer.json")
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🌐 Fetching from Cesium Ion → {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.read()
                async with aiofiles.open(cache_path, "wb") as f:
                    await f.write(data)
                print(f"✅ Cached {rel_path or 'layer.json'}")
                return data
            else:
                text = await resp.text()
                print(f"❌ Ion returned {resp.status} for {rel_path or 'layer.json'}: {text[:120]}")
                # Try /layers/ fallback (some Ion terrain assets use /layers/layer.json)
                if rel_path == "" and "NoSuchKey" in text:
                    alt_url = f"{base}/layers/layer.json"
                    print(f"🔁 Retrying alternate path → {alt_url}")
                    async with session.get(alt_url, headers=headers) as alt_resp:
                        if alt_resp.status == 200:
                            data = await alt_resp.read()
                            async with aiofiles.open(cache_path, "wb") as f:
                                await f.write(data)
                            print("✅ Cached (from /layers/ fallback)")
                            return data
                        else:
                            print(f"❌ Alternate path failed: {alt_resp.status}")
                return None


# ────────────────────────────────────────────────
async def handle_terrain(request: web.Request):
    """Serve terrain files from cache or Cesium Ion."""
    rel_path = request.match_info.get("tail", "")
    local_path = TERRAIN_DIR / (rel_path if rel_path else "layer.json")

    if local_path.exists():
        return web.FileResponse(local_path)

    data = await fetch_and_cache(rel_path)
    if data:
        return web.Response(body=data)
    raise web.HTTPNotFound(text=f"Terrain file not found: {rel_path or 'layer.json'}")


# ────────────────────────────────────────────────
async def handle_imagery(request: web.Request):
    """Serve local imagery from ./tiles/"""
    rel_path = request.match_info.get("tail", "")
    local_path = IMAGERY_DIR / rel_path
    if not local_path.exists():
        raise web.HTTPNotFound(text=f"Imagery tile not found: {rel_path}")
    return web.FileResponse(local_path)


# ────────────────────────────────────────────────
async def on_prepare(request, response):
    """Add CORS headers"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"


# ────────────────────────────────────────────────
async def start_app():
    await resolve_endpoint()
    app = web.Application()
    app.on_response_prepare.append(on_prepare)
    app.router.add_get("/tiles/{tail:.*}", handle_imagery)
    app.router.add_get("/terrain/{tail:.*}", handle_terrain)

    print(f"🚀 Proxy running on http://localhost:{PORT}/")
    print(f"• Imagery from {IMAGERY_DIR.resolve()}")
    print(f"• Terrain cache at {TERRAIN_DIR.resolve()} (Ion asset {ASSET_ID})")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    while True:
        await asyncio.sleep(3600)


# ────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        asyncio.run(start_app())
    except KeyboardInterrupt:
        print("\n🛑 Proxy stopped.")
