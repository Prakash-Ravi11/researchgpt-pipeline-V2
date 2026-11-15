"""Validate the exact recovered interpreter, native imports and actual CUDA math."""
import importlib.metadata
import json
import os
import sys
from pathlib import Path

if os.getenv("KMP_DUPLICATE_LIB_OK", "").upper() in ("TRUE", "1"):
    raise RuntimeError("unsafe duplicate-OpenMP override is not permitted for this validation")

import numpy as np
import torch
import chromadb
import onnxruntime
import psutil
from sentence_transformers import SentenceTransformer


def main():
    versions = {}
    for p in ["torch", "numpy", "mkl", "mkl-service", "intel-openmp", "sentence-transformers", "transformers",
              "tokenizers", "FlagEmbedding", "onnxruntime", "onnxruntime-gpu", "chromadb"]:
        try: versions[p] = importlib.metadata.version(p)
        except importlib.metadata.PackageNotFoundError: versions[p] = None
    result = {"interpreter": sys.executable, "python": sys.version, "base_prefix": sys.base_prefix,
        "system_site_packages_inherited": any("miniconda" in p.lower() for p in sys.path), "versions": versions,
        "torch_cuda_build": torch.version.cuda, "cuda_available": torch.cuda.is_available(),
        "onnx_providers": onnxruntime.get_available_providers(), "numpy_build": np.show_config(mode="dicts"),
        "unsafe_openmp_override": False}
    if torch.cuda.is_available():
        before = torch.cuda.mem_get_info()
        x = torch.arange(16, dtype=torch.float32, device="cuda").reshape(4,4)
        product = x @ x.T
        torch.cuda.synchronize()
        assert torch.equal(product.cpu(), torch.arange(16,dtype=torch.float32).reshape(4,4) @ torch.arange(16,dtype=torch.float32).reshape(4,4).T)
        result["cuda_operation"] = {"device": str(x.device), "gpu": torch.cuda.get_device_name(),
            "capability": list(torch.cuda.get_device_capability()), "matrix_product_verified": True,
            "free_bytes_before": before[0], "total_bytes": before[1]}
        del x, product
        torch.cuda.empty_cache()
        result["cuda_operation"]["allocated_after_release"] = torch.cuda.memory_allocated()
    result["loaded_openmp_dlls"] = sorted({m.path for m in psutil.Process().memory_maps() if "iomp" in m.path.lower()})
    out = Path("outputs/recovery/recovered-environment-probe.json")
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ["interpreter","versions","cuda_available","loaded_openmp_dlls"]},indent=2))


if __name__ == "__main__":
    main()
