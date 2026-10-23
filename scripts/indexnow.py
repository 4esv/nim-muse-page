#!/usr/bin/env python3
"""
indexnow.py - submit the site's URLs to IndexNow after a publish.

IndexNow is the shared indexing protocol behind Bing, Yandex, and
others: one POST to api.indexnow.org distributes the URL list to
every participating engine. Ownership is proven by the key file at
the site root: <key>.txt containing the key itself. That file ships
with the site and must be live before a submission validates, so
this runs after the deploy rsync, never before it.

URLs come from sitemap.xml, the same list crawlers get. No URLs are
invented here.

Usage: python3 scripts/indexnow.py [--dry-run]
Python 3 standard library only.
"""
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "nim.aesv.io"
ENDPOINT = "https://api.indexnow.org/indexnow"


def find_key():
    pats = sorted(glob.glob(os.path.join(ROOT, "*.txt")))
    for path in pats:
        name = os.path.basename(path)[:-4]
        if re.fullmatch(r"[0-9a-f]{32}", name):
            with open(path, encoding="utf-8") as fh:
                if fh.read().strip() == name:
                    return name
    return None


def sitemap_urls():
    with open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8") as fh:
        return re.findall(r"<loc>([^<]+)</loc>", fh.read())


def main(argv):
    dry = "--dry-run" in argv[1:]
    unknown = [a for a in argv[1:] if a != "--dry-run"]
    if unknown:
        sys.stderr.write("usage: python3 scripts/indexnow.py [--dry-run]\n")
        return 2
    key = find_key()
    if not key:
        sys.stderr.write("indexnow: no <key>.txt key file at the site root\n")
        return 1
    urls = sitemap_urls()
    if not urls:
        sys.stderr.write("indexnow: sitemap.xml lists no URLs\n")
        return 1
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": "https://%s/%s.txt" % (HOST, key),
        "urlList": urls,
    }
    if dry:
        print("dry run: %d URLs would go to %s" % (len(urls), ENDPOINT))
        for u in urls:
            print("  " + u)
        return 0
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
    except OSError as e:
        # NOTE: URLError, plus raw timeouts the proxy can raise mid-read.
        sys.stderr.write("indexnow: request failed: %s\n" % e)
        return 1
    # NOTE: 200 means accepted, 202 means accepted pending key validation.
    if status in (200, 202):
        print("indexnow: %d URLs submitted, HTTP %d" % (len(urls), status))
        return 0
    sys.stderr.write("indexnow: HTTP %d submitting %d URLs\n" % (status, len(urls)))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
