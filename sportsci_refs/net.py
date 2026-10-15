"""HTTP helpers with the proxy rule that matters on machines running Clash / V2Ray style local proxies:

    external APIs (Crossref, Europe PMC, OpenAlex, doi.org)  -> use the system proxy (often the only way out)
    the Zotero local API (127.0.0.1:23119)                     -> bypass the proxy

Going through the proxy to 127.0.0.1 returns "502 Bad Gateway" from the proxy when Zotero is not running,
which looks like a broken Zotero instead of a closed one. `local_opener()` avoids that.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from .config import load_config


def external_opener():
    return urllib.request.build_opener()


def local_opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


class HTTPFailure(RuntimeError):
    def __init__(self, url: str, status: Optional[int], reason: str):
        super().__init__(f"{status or ''} {reason} <- {url}".strip())
        self.url, self.status, self.reason = url, status, reason


def fetch(url: str, local: bool = False, timeout: float = 25, tries: int = 2, headers: Optional[Dict[str, str]] = None,
          data: Optional[bytes] = None, method: Optional[str] = None) -> bytes:
    op = local_opener() if local else external_opener()
    h = {"User-Agent": load_config().user_agent}
    h.update(headers or {})
    last: Exception = RuntimeError("no attempt")
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=h, data=data, method=method)
            with op.open(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404, 501):
                raise HTTPFailure(url, e.code, e.reason)
            last = HTTPFailure(url, e.code, str(e.reason))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = HTTPFailure(url, None, type(e).__name__ + ": " + str(getattr(e, "reason", e)))
        if i < tries - 1:
            time.sleep(1.0 + i)
    raise last


def get_json(url: str, local: bool = False, **kw) -> Any:
    return json.loads(fetch(url, local=local, **kw).decode("utf-8", "replace"))
