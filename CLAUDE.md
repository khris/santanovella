# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Santanovella is a simple web browser implementation based on the [Web Browser Engineering](https://browser.engineering/) book. It's built in Python (requires >=3.14) using tkinter for the UI and implements HTTP/HTTPS protocols from scratch.

## Development Commands

### Running the Browser
```bash
# Using uv
uv run santanovella <url>

# Or using the script directly
python run_santanovella.py <url>
```

### Package Management
This project uses `uv` for package management. Dependencies are defined in `pyproject.toml`.

## Architecture

### Protocol System

The browser uses a plugin-style URL protocol system where different schemes are handled by different classes:

- **Base abstraction**: `Url` (in `protocol/common.py`) is an abstract base class with a `subclass_map` that automatically registers URL handlers for different schemes
- **Supported schemes**: HTTP, HTTPS, file://, data:, view-source:
- **Implementation pattern**: Each protocol handler inherits from `Url` and implements `_allowed_schemes()` and `request()` methods
  - `PlainHttpUrl` and `HttpsUrl` in `protocol/http.py`
  - `FileUrl` in `protocol/file.py`
  - `DataUrl` in `protocol/data.py`
  - `ViewSourceUrl` in `protocol/view_source.py` (wraps another URL and returns plain text)

The `protocol/__init__.py` auto-imports all protocol handlers so they self-register on module import.

### HTTP Implementation

HTTP is implemented from scratch without using urllib or requests:

- **Connection pooling**: `SocketPool` (singleton in `net/__init__.py`) manages persistent connections with keep-alive support
- **Response caching**: `TtlCache` (in `ds/__init__.py`) implements time-based response caching with cache-control header support
- **Compression**: Supports gzip and deflate encoding via `PayloadReader` classes in `protocol/payload_reader.py`
- **Redirection**: Browser follows up to `MAX_REDIRECTION` (2) redirects automatically

### Rendering Pipeline

1. **URL parsing** → `Url.create_from()` determines the appropriate protocol handler
2. **Request/Response** → Protocol handler's `request()` returns a `Response` object
3. **Content processing**:
   - HTML: `html.lex()` parses HTML entities and strips tags, returning plain text
   - JSON: Pretty-printed using `json.dumps()`
   - Text: Displayed as-is
4. **Layout** → `Browser.layout()` positions characters in a grid with word wrapping
5. **Rendering** → `Browser.draw()` uses tkinter Canvas to display visible characters

The browser uses a simple character-based layout system (no CSS) with:
- Character grid positioning (`Vec2` coordinates)
- Display list of `Char` objects (position + character)
- Scrolling support (keyboard arrows and mouse wheel)
- Dynamic canvas resizing

### Data Structures

- `SimpleKV`: Generic key-value pair (used for parsing HTTP headers)
- `TtlCache`: Time-based cache with expiration (for HTTP response caching)
- `Header`: Multi-value HTTP header container with case-insensitive keys

### HTML Parsing

The `html.lex()` function is a state-machine parser that:
- Strips HTML tags
- Decodes HTML entities (both named entities from `entities.json` and numeric codepoints)
- Returns plain text for rendering

## Code Patterns

### URL Handler Registration

New protocol handlers automatically register themselves via `__init_subclass__`:

```python
class MyProtocolUrl(Url):
    @classmethod
    def _allowed_schemes(cls):
        return (Scheme.MY_PROTOCOL,)

    def request(self) -> Response:
        # Implementation
```

### Response Creation

Always return a `Response` object with appropriate fields:
- `status_code`: HTTP status (default: 200)
- `content_type`: `MimeType` object
- `body`: bytes
- `should_redirect`: bool for 3xx redirects
- `redirect_path`: absolute URL for redirects

### Connection Management

The `SocketPool` singleton manages connections. Connections are:
- Keyed by `(host, port, is_secure)` tuple
- Reused when alive (checked via `MSG_PEEK`)
- Reconnected automatically on `ConnectionResetError` (up to `MAX_RETRIES`)
- Support both plain TCP and TLS-wrapped sockets