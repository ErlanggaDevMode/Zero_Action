"""Service containing search and page reading utilities backed by the standard library."""

import re
import urllib.parse
import urllib.request
from typing import List, Dict, Any
from zero.services.logging import logger

def _urlopen_safe(req: urllib.request.Request, timeout: int) -> Any:
    """Perform urlopen with default SSL context, falling back to unverified context on SSL failures."""
    import ssl
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except Exception as e:
        err_str = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in err_str or "certificate verify failed" in err_str:
            logger.bind(category="search").debug("SSL certificate verify failed, retrying with unverified context.")
            unverified_ctx = ssl._create_unverified_context()
            return urllib.request.urlopen(req, timeout=timeout, context=unverified_ctx)
        raise e

def _clean_ddg_url(url: str) -> str:
    """Extract destination URL from DuckDuckGo redirect link."""
    if "//duckduckgo.com/l/?uddg=" in url or "/l/?uddg=" in url:
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if "uddg" in params:
                return params["uddg"][0]
        except Exception as e:
            logger.debug(f"Failed to parse DDG redirect URL {url}: {e}")
    return url

def search_ddg(query: str) -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo HTML interface.
    Returns list of dicts with keys: 'title', 'url', 'snippet'.
    """
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
    )
    
    html = ""
    try:
        logger.bind(category="search").debug(f"Querying DuckDuckGo for: {query}")
        with _urlopen_safe(req, timeout=8) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.bind(category="search").warning(f"DuckDuckGo direct search failed: {e}. Trying DoH fallback.")
        
    # Check if blocked by Internet Positif or failed
    if not html or "Internet Positif" in html or "internetpositif" in html:
        logger.bind(category="search").info("DuckDuckGo blocked or failed. Resolving via DNS-over-HTTPS fallback.")
        try:
            doh_url = "https://dns.google/resolve?name=html.duckduckgo.com&type=A"
            doh_req = urllib.request.Request(doh_url)
            with _urlopen_safe(doh_req, timeout=5) as doh_resp:
                import json
                doh_data = json.loads(doh_resp.read().decode("utf-8"))
            ips = [ans["data"] for ans in doh_data.get("Answer", []) if ans.get("type") == 1]
            if ips:
                ip = ips[0]
                fallback_url = f"https://{ip}/html/?q={urllib.parse.quote(query)}"
                req_fallback = urllib.request.Request(
                    fallback_url,
                    headers={
                        "Host": "html.duckduckgo.com",
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        )
                    }
                )
                with _urlopen_safe(req_fallback, timeout=8) as response:
                    html = response.read().decode("utf-8", errors="replace")
        except Exception as e_fallback:
            logger.bind(category="search").warning(f"DoH fallback failed: {e_fallback}")

    if not html:
        return [{"title": "Error", "url": "", "snippet": "Search failed: No connection or blocked by provider."}]
        
    if "Internet Positif" in html or "internetpositif" in html:
        return [{"title": "Error", "url": "", "snippet": "Search failed: Blocked by Internet Positif DNS."}]

    results = []
    
    # Locate result titles/links and snippets
    # DuckDuckGo HTML nests anchor under .result__title, and snippet is .result__snippet.
    link_pattern = re.compile(
        r'<h2 class="result__title">\s*<a[^>]*class="(?:result__a|result__link)"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL
    )
    snippet_pattern = re.compile(r'<a class="result__snippet"[^>]*>(.*?)</a>', re.DOTALL)

    links = list(link_pattern.finditer(html))
    snippets = list(snippet_pattern.finditer(html))

    # Zip lists safely
    for link_match, snippet_match in zip(links, snippets):
        href = _clean_ddg_url(link_match.group(1))
        # Ensure url starts with https:// if it has been cleaned to a relative link
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://duckduckgo.com" + href
        
        # Clean HTML tags from match strings
        title = re.sub(r'<[^>]+>', '', link_match.group(2)).strip()
        snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
        
        results.append({
            "title": title,
            "url": href,
            "snippet": snippet
        })
        
    return results[:8]

def fetch_url_text(url: str) -> str:
    """
    Fetch raw HTML from target URL and convert it to stripped, readable text context.
    Capped at 10,000 characters to prevent prompt context bloat.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
    )
    
    try:
        logger.bind(category="search").debug(f"Fetching URL contents: {url}")
        with _urlopen_safe(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.bind(category="search").warning(f"Failed to fetch webpage {url}: {e}")
        return f"Error reading URL: {e}"

    # Extract clean text from HTML body
    # 1. Remove scripts, styles, header, footer, and navigation sections
    cleaned = re.sub(r'<(script|style|header|footer|nav|noscript)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Strip all remaining HTML tags
    cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
    
    # 3. Unescape HTML entities (e.g., &mdash; -> —, &bull; -> •)
    import html
    cleaned = html.unescape(cleaned)
    
    # 4. Collapse whitespace and normalise spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Return capped content
    return cleaned[:10000]
