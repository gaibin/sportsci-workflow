"""Zotero access through the local HTTP API of the desktop app (no web API key needed). Zotero must be running.

Capabilities of the local API (Zotero 7) — verified, so do not waste time on the rest:
    GET  /connector/ping                                    200  alive
    GET  /api/users/0/items?q=<text>&limit=<n>              200  search the library
    GET  /api/users/0/items/<KEY>?format=csljson            200  full CSL record (returns a LIST: take [0])
    GET  /api/users/0/collections                           200  all collections
    GET  /api/users/0/collections/<KEY>/items               200  items of a collection
    POST /connector/saveItems                               201  create items (land in the collection SELECTED in the UI)
    DELETE / PATCH / PUT items                              501  not implemented -> the API cannot delete or edit
Never write "test" items into a real library to probe write access: they cannot be deleted through the API.

Numeric itemIDs (needed in citation payloads) are not exposed by the API; `item_ids()` reads them from a COPY of
zotero.sqlite (+ -wal / -journal, otherwise the latest changes are missing). Never write to zotero.sqlite.
If an MCP Zotero connector is available in the agent session it can replace this module; "configured" is not
"connected" — check that its tools are actually present, otherwise use this module.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import urllib.parse
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .config import RefConfig, load_config
from .doi import clean_doi, title_similarity
from .net import HTTPFailure, fetch


class ZoteroUnavailable(RuntimeError):
    pass


class ZoteroLocal:
    def __init__(self, cfg: Optional[RefConfig] = None):
        self.cfg = cfg or load_config()
        self.base = self.cfg.zotero_api

    # ------------------------------------------------------------------ transport (always bypasses proxies)
    def _get(self, path: str, raw: bool = False):
        try:
            b = fetch(self.base + path, local=True, timeout=20, headers={"Zotero-API-Version": "3"})
        except HTTPFailure as e:
            if e.status is None:
                raise ZoteroUnavailable("Zotero 本地接口无响应：请确认 Zotero 桌面端已打开（设置 → 高级 → 允许其他应用通信）。") from e
            raise
        return b if raw else json.loads(b.decode("utf-8"))

    def status(self) -> Dict:
        """Diagnose reachability. A 502 means a proxy intercepted the call — Zotero itself is not running."""
        try:
            fetch(self.base + "/connector/ping", local=True, timeout=5, tries=1)
            api = True
            try:
                self._get("/api/users/0/items?limit=1")
            except Exception:
                api = False
            return dict(running=True, local_api=api, message="Zotero 正在运行" + ("" if api else "，但本地 API 未开启：设置 → 高级 → 勾选“允许此计算机上的其他应用程序与 Zotero 通信”"))
        except HTTPFailure as e:
            msg = "Zotero 未运行或端口 23119 未监听，请打开 Zotero 桌面端。"
            if e.status == 502:
                msg += "（502 来自本机代理，不代表 Zotero 故障。）"
            return dict(running=False, local_api=False, message=msg, error=str(e))

    # ------------------------------------------------------------------ reads
    def search(self, q: str, limit: int = 25) -> List[Dict]:
        return [self._slim(it) for it in self._get(f"/api/users/0/items?q={urllib.parse.quote(q)}&limit={limit}")]

    def collections(self) -> List[Dict]:
        return [dict(key=c["key"], name=c["data"]["name"], parent=c["data"].get("parentCollection") or None, n=c.get("meta", {}).get("numItems"))
                for c in self._get("/api/users/0/collections?limit=200")]

    def collection_key(self, name_or_key: str) -> str:
        cols = self.collections()
        hit = [c for c in cols if c["key"] == name_or_key or c["name"] == name_or_key]
        if not hit:
            raise KeyError(f"collection '{name_or_key}' not found; available: {[c['name'] for c in cols][:30]}")
        return hit[0]["key"]

    def collection_items(self, coll: str) -> List[Dict]:
        key = self.collection_key(coll)
        out, start = [], 0
        while True:
            page = self._get(f"/api/users/0/collections/{key}/items/top?limit=100&start={start}")
            out += [self._slim(it) for it in page if it.get("data", {}).get("itemType") not in ("attachment", "note")]
            if len(page) < 100:
                return out
            start += 100

    def csl(self, key: str) -> Dict:
        d = self._get(f"/api/users/0/items/{key}?format=csljson")
        return d[0] if isinstance(d, list) else d

    @staticmethod
    def _slim(it: Dict) -> Dict:
        d = it.get("data", {})
        return dict(key=it.get("key") or d.get("key"), type=d.get("itemType"), title=(d.get("title") or "").strip(), doi=clean_doi(d.get("DOI") or ""),
                    year=(d.get("date") or "")[:4], journal=(d.get("publicationTitle") or "").strip())

    # ------------------------------------------------------------------ writes (explicit, never automatic)
    def save_items(self, items: List[Dict], uri: str = "https://doi.org/") -> int:
        """Create items via the connector endpoint. They land in the collection currently SELECTED in Zotero.
        Items use Zotero's connector format (itemType, title, creators, DOI, ...). Returns the HTTP status."""
        import uuid
        body = json.dumps({"sessionID": uuid.uuid4().hex[:12], "uri": uri, "items": items}).encode("utf-8")
        fetch(self.base + "/connector/saveItems", local=True, data=body, method="POST", headers={"Content-Type": "application/json"}, tries=1)
        return 201

    def uri(self, key: str) -> str:
        if not self.cfg.zotero_user_id:
            raise ValueError("ZOTERO_USER_ID is not set (config/local.toml [refs] zotero_user_id, or env var); it is the number shown at zotero.org/settings/keys")
        return f"http://zotero.org/users/{self.cfg.zotero_user_id}/items/{key}"

    # ------------------------------------------------------------------ itemIDs from a copy of the database
    def item_ids(self, keys: Iterable[str]) -> Dict[str, int]:
        if not self.cfg.zotero_data_dir:
            return {}
        src = Path(self.cfg.zotero_data_dir) / "zotero.sqlite"
        if not src.exists():
            raise FileNotFoundError(f"{src} not found (check ZOTERO_DATA_DIR)")
        tmp = Path(tempfile.mkdtemp(prefix="zotero_copy_"))
        try:
            for suf in ("", "-wal", "-journal"):  # copy the WAL too, or recent changes are missing
                f = src.with_name(src.name + suf)
                if f.exists():
                    shutil.copy2(f, tmp / f.name)
            con = sqlite3.connect(tmp / src.name)
            keys = list(keys)
            rows = con.execute(f"SELECT key, itemID FROM items WHERE libraryID = 1 AND key IN ({','.join('?' * len(keys))})", keys).fetchall() if keys else []
            con.close()
            return {k: int(i) for k, i in rows}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def match(refs: List[Dict], items: List[Dict], threshold: float = 0.90) -> Dict:
    """Match parsed references (CSL dicts with title / DOI) to Zotero items. DOI first, then title similarity.

    Returns {mapping: {ref_id: {key, how, score}}, unmatched: [ref_id], unused: [zotero items not matched]}.
    Low-confidence title matches (< 0.97) are listed for manual review.
    """
    used, mapping, unmatched, review = set(), {}, [], []
    for r in refs:
        rid = str(r.get("id"))
        hit = None
        rd = clean_doi(r.get("DOI", "")).lower()
        if rd:
            hit = next(((z, "DOI", 1.0) for z in items if z["key"] not in used and z["doi"].lower() == rd), None)
        if not hit:
            best = max(((z, title_similarity(r.get("title", ""), z["title"])) for z in items if z["key"] not in used), key=lambda t: t[1], default=(None, 0))
            if best[0] is not None and best[1] >= threshold:
                hit = (best[0], "title", best[1])
        if hit:
            z, how, sc = hit
            used.add(z["key"])
            mapping[rid] = dict(key=z["key"], how=how, score=round(sc, 3), zotero_title=z["title"], ref_title=r.get("title", ""))
            if how == "title" and sc < 0.97:
                review.append(rid)
        else:
            unmatched.append(rid)
    return dict(mapping=mapping, unmatched=unmatched, review=review, unused=[z for z in items if z["key"] not in used])
