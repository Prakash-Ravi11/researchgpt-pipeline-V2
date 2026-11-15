"""Download the official recovery wheel in checked ranges, verify index SHA256.

Optional workaround for a stalled single-stream CDN transfer; no third-party mirror.
"""
import concurrent.futures
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    filename = "torch-2.8.0+cu126-cp313-cp313-win_amd64.whl"
    index = "https://download.pytorch.org/whl/cu126/torch/"
    page = urllib.request.urlopen(index, timeout=30).read().decode()
    link = next(html.unescape(u) for u in re.findall(r'href="([^"]+)"', page)
                if urllib.parse.unquote(u.split("#")[0]).endswith(filename))
    expected = urllib.parse.parse_qs(urllib.parse.urlsplit(link).fragment)["sha256"][0]
    url = "https://download.pytorch.org/whl/cu126/" + urllib.parse.quote(filename)
    req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        total = int(response.headers["Content-Range"].split("/")[-1])
    folder = Path("outputs/recovery/wheels")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / filename
    partial = target.with_suffix(".whl.part")
    with partial.open("wb") as f:
        f.truncate(total)
    size = 16 * 1024 * 1024
    def fetch(start):
        end = min(start + size, total) - 1
        request = urllib.request.Request(url + f"?recovery_part={start}", headers={"Range": f"bytes={start}-{end}"})
        with urllib.request.urlopen(request, timeout=60) as r:
            if r.status != 206 or r.headers.get("Content-Range") != f"bytes {start}-{end}/{total}":
                raise ValueError("server did not honor exact byte range")
            data = r.read(end - start + 2)
        if len(data) != end - start + 1:
            raise ValueError("range size mismatch")
        with partial.open("r+b") as f:
            f.seek(start)
            f.write(data)
        return len(data)
    complete = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        tasks = [pool.submit(fetch, start) for start in range(0, total, size)]
        for future in concurrent.futures.as_completed(tasks):
            complete += future.result()
            print(f"Downloaded {complete}/{total} bytes ({complete / total:.1%})", flush=True)
    digest = hashlib.file_digest(partial.open("rb"), "sha256").hexdigest()
    if digest != expected:
        raise ValueError("official wheel hash mismatch")
    partial.replace(target)
    (folder / "wheel-verification.json").write_text(json.dumps({"url": url, "index": index,
        "filename": filename, "bytes": total, "expected_sha256": expected, "actual_sha256": digest}, indent=2) + "\n")
    print("Verified official wheel", target, flush=True)


if __name__ == "__main__":
    main()
