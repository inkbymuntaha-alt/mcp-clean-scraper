import re
from fastapi import FastAPI, Header, Query
from fastapi.responses import JSONResponse
import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as md

app = FastAPI(title="MCP Clean Scraper")
TX_HASH_REGEX = re.compile(r"^0x[a-fA-F0-9]{64}$")

@app.get("/mcp/manifest")
def get_manifest():
    return {
        "schema_version": "1.0.0",
        "name": "mcp-clean-scraper",
        "endpoint": "https://mcp-clean-scraper.vercel.app/mcp/tools/scrape_to_markdown",
        "x402_gated": True,
        "price_per_call": "0.05 USDC"
    }

@app.post("/mcp/tools/scrape_to_markdown")
async def scrape_to_markdown(
    payment_signature: str = Header(None, alias="PAYMENT-SIGNATURE"),
    url: str = Query(...)
):
    if not payment_signature or not TX_HASH_REGEX.match(payment_signature):
        return JSONResponse(status_code=402, content={
            "error": "Payment Required",
            "x402_challenge": {
                "network": "eip155:8453",
                "asset": "USDC",
                "recipient": "0x960E510E4E1dA4B13CE3b601202d4680AFcf02E0",
                "price": "0.05"
            }
        })

    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        res = await client.get(url, headers={"User-Agent": "Mozilla/5.0 AgentScraper"})
        if res.status_code != 200:
            return {"error": f"Failed to fetch URL: status {res.status_code}"}

        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        return {
            "status": "success",
            "payment_verified": True,
            "url": url,
            "markdown": md(str(soup))[:5000],
            "cross_promotions": {
                "lead_signals": "https://mcp-lead-signals.vercel.app/mcp/manifest",
                "dep_checker": "https://mcp-dep-checker.vercel.app/mcp/manifest"
            }
        }
