"""Inspect a prepared Kaggle base/overlay without changing the base environment."""
import argparse
import gc
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import sys

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name


def check_profile(profile, facts):
    if facts.get('bnb_cuda_override') not in (None, '', '130'):
        raise RuntimeError('BNB_CUDA_VERSION override conflicts with prepared CUDA13 profile')
    if not SpecifierSet(profile['python_requires']).contains(facts['python_version']):
        raise RuntimeError('unsupported Python for prepared profile')
    if facts['torch_version'] != profile['torch_version'] or facts['torch_cuda'] != profile['torch_cuda']:
        raise RuntimeError('base torch/CUDA differs from prepared profile; stop without replacing PyTorch')
    for name, expected in profile['overlay_pins'].items():
        if facts['packages'].get(name) != expected:
            raise RuntimeError('overlay version mismatch: ' + name)


def check_dependencies(roots, distribution=metadata.distribution):
    """Check active (overlay-first) distributions, including default transitive deps."""
    pending = list(roots)
    seen, checked = set(), {}
    while pending:
        requirement = Requirement(pending.pop())
        if requirement.marker and not requirement.marker.evaluate({'extra': ''}):
            continue
        name = canonicalize_name(requirement.name)
        try:
            dist = distribution(name)
        except metadata.PackageNotFoundError:
            raise RuntimeError('missing active dependency: ' + name) from None
        if requirement.specifier and not requirement.specifier.contains(dist.version):
            raise RuntimeError('incompatible active dependency: ' + str(requirement) + ', found ' + dist.version)
        checked[name] = dist.version
        if name not in seen:
            seen.add(name)
            pending.extend(dist.requires or [])
    return checked


def environment_facts(torch):
    return {'python_version': platform.python_version(), 'python_executable': sys.executable,
            'python_prefix': sys.prefix, 'python_base_prefix': sys.base_prefix,
            'platform': platform.platform(), 'torch_version': torch.__version__,
            'torch_cuda': torch.version.cuda, 'bnb_cuda_override': os.environ.get('BNB_CUDA_VERSION'),
            'packages': {name: metadata.version(name) for name in
                         {canonicalize_name(d.metadata['Name']) for d in metadata.distributions()}}}


def verify_environment(profile, torch, overlay=None):
    facts = environment_facts(torch)
    # metadata.distribution resolves the active path, unlike a dictionary of
    # duplicate base/overlay installations. Never let the base copy win by order.
    facts['packages'] = {name: metadata.version(name) for name in profile['overlay_pins']}
    check_profile(profile, facts)
    if overlay:
        overlay = Path(overlay).resolve()
        facts['active_overlay_paths'] = {}
        for name in profile['overlay_pins']:
            path = Path(metadata.distribution(name).locate_file('')).resolve()
            if not path.is_relative_to(overlay):
                raise RuntimeError('dependency did not resolve from overlay: ' + name)
            facts['active_overlay_paths'][name] = str(path)
    facts['dependency_closure'] = check_dependencies(
        ['torch==' + profile['torch_version']] + profile['base_requirements']
        + [name + '==' + value for name, value in profile['overlay_pins'].items()])
    return facts


def gpu_preflight(torch, bnb, profile):
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable')
    name = torch.cuda.get_device_name(0)
    if profile['device_name_contains'] not in name:
        raise RuntimeError('prepared T4 profile does not match device: ' + name)
    free, total = torch.cuda.mem_get_info(0)
    if free < profile['minimum_free_bytes']:
        raise RuntimeError('insufficient actual free VRAM before preflight')
    a = torch.ones((16, 16), dtype=torch.float16, device='cuda:0')
    product = a @ a
    if not bool(torch.all(product == 16)):
        raise RuntimeError('GPU tensor operation failed')
    tensor = torch.randn((128, 128), dtype=torch.float16, device='cuda:0')
    packed, state = bnb.functional.quantize_4bit(tensor, quant_type='nf4', compress_statistics=True)
    restored = bnb.functional.dequantize_4bit(packed, state)
    if (restored.shape != tensor.shape or packed.device.type != 'cuda' or restored.device.type != 'cuda'
            or not bool(torch.isfinite(restored).all())):
        raise RuntimeError('GPU NF4 roundtrip failed')
    error = float((restored - tensor).abs().mean())
    if error > 0.3:
        raise RuntimeError('GPU NF4 roundtrip error is implausible')
    del a, product, tensor, packed, state, restored
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    free_after, _ = torch.cuda.mem_get_info(0)
    if free_after < profile['minimum_free_bytes']:
        raise RuntimeError('insufficient actual free VRAM after releasing preflight tensors')
    return {'device_name': name, 'physical_device': os.environ.get('CUDA_VISIBLE_DEVICES'),
            'free_vram_before': free, 'free_vram_after_release': free_after, 'total_vram': total,
            'tensor_operation': 'passed', 'gpu_nf4_roundtrip': 'passed', 'nf4_mean_absolute_error': error}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--overlay', type=Path, required=True)
    parser.add_argument('--device', type=int, choices=[0, 1], default=0)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError('environment report exists; preserve it')
    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.device)
    report = {'status': 'FAILED', 'execution_kind': 'environment_preflight_not_inference',
              'python_version': platform.python_version(), 'python_executable': sys.executable}
    try:
        import torch
        profile = json.loads(args.runtime.read_text(encoding='utf-8'))['environment_profile']
        report['environment'] = verify_environment(profile, torch, args.overlay)
        import bitsandbytes as bnb
        report['gpu'] = gpu_preflight(torch, bnb, profile)
        report['status'] = 'READY'
    except Exception as exc:
        report.update(error_type=type(exc).__name__, error=str(exc))
    with args.report.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps(report, indent=2))
    if report['status'] != 'READY':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
