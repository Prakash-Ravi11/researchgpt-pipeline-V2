"""Convert an actually executed JUnit report to compact reviewable evidence."""
import argparse
import importlib.metadata
import json
import platform
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("junit", type=Path)
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/test_results.json"))
    args = parser.parse_args()
    root = ET.parse(args.junit).getroot()
    packages = ["pydantic", "fastapi", "uvicorn", "requests", "PyMuPDF", "PyYAML", "tqdm", "chromadb",
                "sentence-transformers", "torch", "numpy", "rank-bm25", "pytest", "httpx"]
    cases = []
    for test in root.iter("testcase"):
        props = {p.get("name"): p.get("value") for p in test.findall("./properties/property")}
        cases.append({"module": test.get("classname"), "name": test.get("name"),
            "status": "FAILED" if test.find("failure") is not None or test.find("error") is not None else
                      "SKIPPED" if test.find("skipped") is not None else "PASSED",
            "seconds": float(test.get("time", 0)), **props})
    result = {"command": f'"{sys.executable}" -B -m pytest -p no:cacheprovider tests -q --junitxml={args.junit.as_posix()}',
              "environment": {"interpreter": sys.executable, "python": platform.python_version(), "platform": platform.platform(),
                              "packages": {p: importlib.metadata.version(p) for p in packages}},
              "scope": "contract/unit/connected synthetic fixtures; no real-model end-to-end pytest",
              "counts": {s: sum(t["status"] == s for t in cases) for s in ("PASSED", "FAILED", "SKIPPED")},
              "tests": cases}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["counts"]))


if __name__ == "__main__":
    main()
