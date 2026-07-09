from unittest.mock import patch, MagicMock
from zero.services.search import _clean_ddg_url, search_ddg, fetch_url_text

def test_clean_ddg_url():
    assert _clean_ddg_url("https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage") == "https://example.com/page"
    assert _clean_ddg_url("https://example.com") == "https://example.com"

@patch("urllib.request.urlopen")
def test_search_ddg_success(mock_urlopen):
    # Mock HTML response
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"""
    <html>
      <h2 class="result__title">
        <a class="result__link" href="/l/?uddg=https%3A%2F%2Fpython.org">Python Programming</a>
      </h2>
      <a class="result__snippet" href="/l/?uddg=https%3A%2F%2Fpython.org">Python is a programming language.</a>
    </html>
    """
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    
    results = search_ddg("python")
    assert len(results) == 1
    assert results[0]["title"] == "Python Programming"
    assert results[0]["url"] == "https://python.org"
    assert results[0]["snippet"] == "Python is a programming language."

@patch("urllib.request.urlopen")
def test_fetch_url_text(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"""
    <html>
      <head><style>body { color: red; }</style></head>
      <body>
        <script>console.log('test')</script>
        <header>Header content</header>
        <nav>Navigation</nav>
        <main>
          <h1>Main Title</h1>
          <p>This is the main readable content paragraph &mdash; with some &bull; bullet points.</p>
        </main>
        <footer>Footer info</footer>
      </body>
    </html>
    """
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    
    text = fetch_url_text("https://example.com")
    assert "Header content" not in text
    assert "Navigation" not in text
    assert "Footer info" not in text
    assert "Main Title" in text
    assert "This is the main readable content paragraph — with some • bullet points." in text
