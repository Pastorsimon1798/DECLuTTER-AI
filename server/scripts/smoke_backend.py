#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    path: str
    ok: bool
    status: int | None
    body: Any
    error: str | None = None


def fetch_json(base_url: str, path: str, timeout_seconds: float) -> CheckResult:
    url = base_url.rstrip('/') + path
    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
            status = response.status
            raw_body = response.read().decode('utf-8')
            try:
                body: Any = json.loads(raw_body)
            except json.JSONDecodeError:
                body = raw_body
            return CheckResult(path=path, ok=200 <= status < 300, status=status, body=body)
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode('utf-8', errors='replace')
        return CheckResult(path=path, ok=False, status=exc.code, body=raw_body, error=str(exc))
    except urllib.error.URLError as exc:
        return CheckResult(path=path, ok=False, status=None, body=None, error=str(exc.reason))
    except TimeoutError as exc:
        return CheckResult(path=path, ok=False, status=None, body=None, error=str(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description='Smoke-check a DECLuTTER-AI backend URL.')
    parser.add_argument('--url', required=True, help='Base URL, for example https://api.example.com')
    parser.add_argument('--timeout', type=float, default=5.0, help='Per-request timeout in seconds')
    parser.add_argument(
        '--require-production-ready',
        action='store_true',
        help='Fail unless /health/readiness reports ready_for_production=true.',
    )
    args = parser.parse_args()

    checks = [
        fetch_json(args.url, '/health/', args.timeout),
        fetch_json(args.url, '/health/readiness', args.timeout),
        fetch_json(args.url, '/launch/status', args.timeout),
        fetch_json(args.url, '/openapi.json', args.timeout),
    ]

    for result in checks:
        status = result.status if result.status is not None else 'ERR'
        print(f'{"PASS" if result.ok else "FAIL"} {result.path} status={status}')
        if result.error:
            print(f'  error={result.error}')

    failures = [result for result in checks if not result.ok]
    readiness = next(result for result in checks if result.path == '/health/readiness')
    if args.require_production_ready:
        ready = isinstance(readiness.body, dict) and readiness.body.get('ready_for_production') is True
        if not ready:
            failures.append(readiness)
            print('FAIL /health/readiness ready_for_production is not true')

    status = next(result for result in checks if result.path == '/launch/status')
    if isinstance(status.body, dict):
        limitations = status.body.get('limitations') or []
        if limitations:
            print('Launch limitations:')
            for limitation in limitations:
                print(f'  - {limitation}')

    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
