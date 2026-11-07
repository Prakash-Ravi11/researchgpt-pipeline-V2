"""Capture isolated native imports and the existing smoke without global changes."""
import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interpreter", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "interpreter": str(args.interpreter.resolve()), "probes": {}}
    probes = {
        "numpy": "import sys; print(sys.executable,flush=True); import numpy; print(numpy.__version__,flush=True)",
        "torch": "import sys; print(sys.executable,flush=True); print('before torch',flush=True); import torch; print(torch.__version__,torch.version.cuda,torch.cuda.is_available(),flush=True)",
    }
    if args.smoke:
        path = (args.output / "fresh-chroma").resolve()
        project = "legacy-reproduction-" + uuid.uuid4().hex
        # Same documented smoke and real encoder, only database/project are
        # redirected to new storage to avoid touching existing collections.
        probes["documented_smoke_isolated_index"] = (
            "from scripts import smoke_live as s; original=s.ChromaIndex; "
            f"s.ChromaIndex=lambda project_id,path,encoder: original({project!r},{str(path)!r},encoder); "
            "import sys; sys.argv=['scripts.smoke_live','--model']; s.main()")
        report["isolated_reproduction_project"] = project
    for name, code in probes.items():
        result = subprocess.run([str(args.interpreter.resolve()), "-B", "-c", code],
                                capture_output=True, text=True, timeout=180)
        (args.output / (name + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
        (args.output / (name + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
        report["probes"][name] = {"returncode": result.returncode, "command": [str(args.interpreter.resolve()), "-B", "-c", code],
                                   "stdout": result.stdout, "stderr": result.stderr}
    old_base = Path("C:/Users/Praka/miniconda3")
    report["openmp_dlls"] = [{"path": str(p), "bytes": p.stat().st_size,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in (
            old_base / "Library/bin/libiomp5md.dll", old_base / "Lib/site-packages/torch/lib/libiomp5md.dll") if p.exists()]
    (args.output / "diagnosis.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"interpreter": report["interpreter"], "exit_codes": {k: v["returncode"] for k,v in report["probes"].items()},
                      "output": str(args.output.resolve())}, indent=2))


if __name__ == "__main__":
    main()
