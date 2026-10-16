#!/usr/bin/env python3
"""Localhost bridge between the Playwright MCP browser and this machine.

The Playwright MCP `browser_run_code_unsafe` sandbox cannot spawn processes or
write files, but it *can* make HTTP requests (page.request.*). This bridge lets
institution scripts:
  * optionally read 1Password fields (via `op`) without secrets entering the agent
    transcript -- only when the `op` CLI is installed and unlocked; otherwise the
    login falls back to the user signing in manually
  * save downloaded/generated statement files into the output directory

Subcommands
-----------
  bridge.py list
      List supported institutions (directories under ../institutions/).

  bridge.py find <institution> [--query TEXT ...]
      Check whether 1Password is usable and, if so, search Login items whose
      title/URLs match the institution's portal domain + `op_match` keywords
      (plus any --query terms). Never fails and never prints secrets:
        {"op": "available"|"not_installed"|"no_account"|"locked"|"error",
         "detail": str, "items": [{"id","title","vault","urls"}...]}
      Nothing about item titles or vaults is configured anywhere; items are
      discovered at runtime and the user picks one if several match.

  bridge.py serve <institution> [--op-item ID] [--out DIR] [--since YYYY-MM-DD] [--ttl SEC]
      --op-item is optional. If it is omitted or 1Password can't be read, the
      bridge still starts with has_credentials=false (manual login).
      Start the bridge (run it in async/background mode). Prints one JSON line:
        {"bridge": URL, "run": {"login": CODE, "download": CODE}, "out": DIR, ...}
      Each `run.*` value is a one-line loader to pass verbatim as the `code`
      argument of `browser_run_code_unsafe`; it fetches the institution's JS
      (with the bridge URL baked in) from the bridge and evaluates it.

Endpoints (all under the random-token URL)
------------------------------------------
  GET  /script/<name>     -> institution JS (<name>.js) with bridge URL substituted
  GET  /config            -> {"institution","out","since","has_credentials","has_otp"}
  GET  /secret/<key>      -> field value by purpose/id/label (each served once)
  GET  /otp               -> current TOTP code (fresh every call)
  PUT  /file?path=<rel>   -> write request body to <out>/<rel> (no traversal)
  POST /log               -> append a line to <out>/.bridge.log
  GET  /close             -> shut down
"""
import argparse
import http.server
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import urllib.parse
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
INST_DIR = SKILL_DIR / "institutions"
DEFAULT_OUT = Path.home() / "Documents" / "statements"


class OpError(Exception):
    def __init__(self, kind, detail):
        super().__init__(detail)
        self.kind, self.detail = kind, detail


def op(*args, timeout=90):
    """Run the 1Password CLI. Raises OpError instead of exiting so callers can fall back."""
    if not shutil.which("op"):
        raise OpError("not_installed", "1Password CLI (`op`) is not installed")
    try:
        return subprocess.run(["op", *args], check=True, capture_output=True, text=True, timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        raise OpError("locked", "`op` timed out (1Password locked or waiting for approval)")
    except subprocess.CalledProcessError as e:
        msg = (e.stderr or "").strip().splitlines()[-1:] or ["unknown error"]
        kind = "locked" if any(w in msg[0].lower() for w in ("signed in", "sign in", "locked", "unauthorized", "authoriz")) else "error"
        raise OpError(kind, msg[0])


def op_status():
    """Return (status, detail). Never raises."""
    try:
        accounts = json.loads(op("account", "list", "--format", "json", timeout=20) or "[]")
    except OpError as e:
        return e.kind, e.detail
    except json.JSONDecodeError:
        accounts = []
    if not accounts:
        return "no_account", "`op` is installed but no 1Password account is configured"
    try:
        # Desktop-app integration may show an unlock prompt here; that's expected.
        op("vault", "list", "--format", "json")
    except OpError as e:
        return e.kind, e.detail
    return "available", "1Password CLI is installed and unlocked"


def load_institution(name):
    d = INST_DIR / name
    meta = d / "institution.json"
    if name.startswith("_") or not meta.is_file():
        avail = ", ".join(sorted(p.name for p in INST_DIR.iterdir() if (p / "institution.json").is_file() and not p.name.startswith("_")))
        sys.exit(f"Unknown institution '{name}'. Available: {avail}")
    return d, json.loads(meta.read_text())


def cmd_list(_):
    out = []
    for p in sorted(INST_DIR.iterdir()):
        m = p / "institution.json"
        if m.is_file() and not p.name.startswith("_"):
            j = json.loads(m.read_text())
            out.append({"id": p.name, "name": j.get("name"), "portal": j.get("login_url"), "formats": j.get("formats")})
    print(json.dumps(out, indent=2))


def match_terms(meta, extra=()):
    terms = {h.lower() for h in meta.get("op_match", [])} | {t.lower() for t in extra if t}
    host = urllib.parse.urlsplit(meta.get("login_url", "")).hostname or ""
    parts = host.split(".")
    if len(parts) >= 2:
        terms.add(".".join(parts[-2:]))  # registrable-ish domain, e.g. cibc.com
    return sorted(t for t in terms if t)


def cmd_find(a):
    _, meta = load_institution(a.institution)
    status, detail = op_status()
    result = {"op": status, "detail": detail, "items": []}
    if status == "available":
        terms = match_terms(meta, a.query or [])
        try:
            items = json.loads(op("item", "list", "--categories", "Login", "--format", "json") or "[]")
        except (OpError, json.JSONDecodeError) as e:
            result.update(op="error", detail=getattr(e, "detail", str(e)))
            items = []
        for i in items:
            urls = [u.get("href", "") for u in i.get("urls", [])]
            hay = (i.get("title", "") + " " + " ".join(urls)).lower()
            if any(t in hay for t in terms):
                result["items"].append({"id": i["id"], "title": i.get("title"),
                                        "vault": (i.get("vault") or {}).get("name"), "urls": urls})
        result["matched_on"] = terms
    print(json.dumps(result, indent=2))


def cmd_serve(a):
    inst_dir, meta = load_institution(a.institution)
    out = Path(os.path.expanduser(a.out)).resolve() / a.institution
    out.mkdir(parents=True, exist_ok=True)

    fields, otp, cred_note = {}, False, "no --op-item: manual login"
    item = {}
    if a.op_item:
        try:
            item = json.loads(op("item", "get", a.op_item, "--format", "json"))
            cred_note = "1Password item loaded"
        except (OpError, json.JSONDecodeError) as e:
            cred_note = f"1Password unavailable ({getattr(e, 'detail', e)}): manual login"
        for f in item.get("fields", []):
            if f.get("type") == "OTP":
                otp = True
            elif f.get("value") is not None:
                for k in filter(None, {(f.get("purpose") or "").lower(), f.get("id"), f.get("label")}):
                    fields.setdefault(k, f["value"])

    token = secrets.token_urlsafe(24)
    served = set()
    log_path = out / ".bridge.log"

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _route(self):
            u = urllib.parse.urlsplit(self.path)
            parts = u.path.strip("/").split("/", 1)
            if len(parts) != 2 or not secrets.compare_digest(parts[0], token):
                return None, None
            return parts[1], urllib.parse.parse_qs(u.query)

        def _send(self, body, code=200, ctype="text/plain"):
            b = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            route, _ = self._route()
            if route is None:
                return self.send_error(404)
            if route == "config":
                return self._send(json.dumps({
                    "institution": a.institution, "out": str(out), "since": a.since,
                    "has_credentials": bool(fields), "has_otp": otp,
                }), ctype="application/json")
            if route.startswith("script/") and route[len("script/"):] in scripts:
                src = (inst_dir / f"{route[len('script/'):]}.js").read_text().replace("__BRIDGE_URL__", url)
                return self._send(src, ctype="application/javascript")
            if route == "otp":
                if not otp:
                    return self.send_error(404, "no otp")
                try:
                    return self._send(op("item", "get", item["id"], "--otp").strip())
                except OpError as e:
                    return self.send_error(503, f"otp unavailable: {e.kind}")
            if route.startswith("secret/"):
                key = urllib.parse.unquote(route[len("secret/"):])
                if key in fields and key not in served:
                    served.add(key)
                    return self._send(fields[key])
                return self.send_error(404, "unavailable")
            if route == "close":
                self._send("bye")
                return threading.Thread(target=srv.shutdown).start()
            self.send_error(404)

        def _body(self):
            return self.rfile.read(int(self.headers.get("Content-Length") or 0))

        def do_PUT(self):
            route, q = self._route()
            if route != "file" or "path" not in q:
                return self.send_error(404)
            dest = (out / q["path"][0]).resolve()
            if out not in dest.parents:
                return self.send_error(400, "path escapes output dir")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(self._body())
            self._send(json.dumps({"saved": str(dest)}), ctype="application/json")

        def do_POST(self):
            route, _ = self._route()
            if route != "log":
                return self.send_error(404)
            with log_path.open("a") as fh:
                fh.write(self._body().decode(errors="replace").rstrip() + "\n")
            self._send("ok")

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), H)
    url = f"http://127.0.0.1:{srv.server_port}/{token}"

    # Scripts are re-read on every request so edits apply without restarting the bridge.
    scripts = [js.stem for js in sorted(inst_dir.glob("*.js"))]
    loader = ("async (page) => {{ const r = await page.request.get('{u}/script/{n}'); "
              "if (!r.ok()) throw new Error('bridge unreachable: ' + r.status()); "
              "return await eval(await r.text())(page); }}")
    threading.Timer(a.ttl, srv.shutdown).start()
    print(json.dumps({"bridge": url, "run": {n: loader.format(u=url, n=n) for n in scripts}, "out": str(out),
                      "login_url": meta.get("login_url"), "has_credentials": bool(fields), "has_otp": otp,
                      "credentials": cred_note,
                      "ttl": a.ttl}), flush=True)
    srv.serve_forever()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    f = sub.add_parser("find")
    f.add_argument("institution")
    f.add_argument("--query", nargs="*", help="extra search terms (e.g. a domain or word the user gave)")
    f.set_defaults(fn=cmd_find)
    s = sub.add_parser("serve")
    s.add_argument("institution")
    s.add_argument("--op-item", help="optional 1Password item id chosen from `find`; omit for manual login")
    s.add_argument("--out", default=str(DEFAULT_OUT))
    s.add_argument("--since", help="YYYY-MM-DD: download every statement period on/after this date (default: latest only)")
    s.add_argument("--ttl", type=int, default=900, help="seconds before the bridge exits (default 900)")
    s.add_argument("--port", type=int, default=0)
    s.set_defaults(fn=cmd_serve)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
