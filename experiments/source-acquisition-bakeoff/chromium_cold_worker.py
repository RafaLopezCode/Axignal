from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--chrome", required=True)
    parser.add_argument("--timeout-ms", type=int, default=5000)
    args = parser.parse_args()

    payload: dict[str, object] = {
        "ok": False,
        "final_url": args.url,
        "status": None,
        "requests": [],
        "error": None,
    }
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=args.chrome,
                headless=True,
                args=["--disable-gpu", "--no-first-run", "--no-default-browser-check"],
            )
            context = browser.new_context()
            page = context.new_page()
            requests: list[str] = []
            page.on("request", lambda request: requests.append(request.url))
            response = page.goto(args.url, wait_until="load", timeout=args.timeout_ms)
            page.wait_for_timeout(150)
            Path(args.output).write_text(page.content(), encoding="utf-8")
            payload.update(
                {
                    "ok": True,
                    "final_url": page.url,
                    "status": None if response is None else response.status,
                    "requests": requests,
                }
            )
            context.close()
            browser.close()
    except Exception as exc:
        payload["error"] = f"{type(exc).__name__}:{str(exc)[:400]}"
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
