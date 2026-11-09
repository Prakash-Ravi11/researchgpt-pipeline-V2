"""Standard-library-only trusted notebook bootstrap; embedded verbatim in v4."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import zipfile

PAYLOADS = {'packet.json', 'request.json', 'runtime.json', 'code.zip'}
MAX_PAYLOAD_BYTES = 32_000_000


def bootstrap_input(input_root, work_root, expected_sha, attempt='03'):
    """Restore transported ZIP bytes, validate, then stage/extract into fresh paths.

    A mounted code/ directory is never executable input. code.zip.bin is only a
    transport name for the original manifest's code.zip bytes, not a new archive.
    Nothing is deleted or reused, including partial staging from a failed call.
    """
    if not re.fullmatch(r'[a-f0-9]{64}', expected_sha) or not re.fullmatch(r'[A-Za-z0-9_-]{1,32}', attempt):
        raise ValueError('invalid retained SHA or attempt identifier')
    digest = lambda data: hashlib.sha256(data).hexdigest()
    matches = [p for p in Path(input_root).rglob('input-manifest.json')
               if not p.is_symlink() and p.stat().st_size <= 1_000_000
               and digest(p.read_bytes()) == expected_sha]
    if len(matches) != 1:
        raise ValueError('expected exactly one matching mounted manifest; found ' + str(len(matches)))
    mounted = matches[0].parent
    manifest_bytes = matches[0].read_bytes()
    manifest = json.loads(manifest_bytes)
    if set(manifest.get('files', {})) != PAYLOADS:
        raise ValueError('unexpected input manifest file set')
    if not re.fullmatch(r'[a-f0-9]{40}', manifest.get('code_commit', '')):
        raise ValueError('invalid source commit')
    blobs, transports = {}, {}
    for name in sorted(PAYLOADS):
        candidates = [mounted / name]
        if name == 'code.zip':
            candidates = [mounted / 'code.zip.bin', mounted / 'code.zip']
        existing = [p for p in candidates if p.is_file() and not p.is_symlink()]
        if not existing:
            raise FileNotFoundError('missing payload: ' + name + '; expanded code/ is not a substitute')
        entry = manifest['files'][name]
        if type(entry.get('bytes')) is not int or not 0 <= entry['bytes'] <= MAX_PAYLOAD_BYTES:
            raise ValueError('unsafe payload size: ' + name)
        for path in existing:
            if path.stat().st_size != entry['bytes']:
                raise ValueError('payload size mismatch: ' + path.name)
            data = path.read_bytes()
            if digest(data) != entry['sha256']:
                raise ValueError('payload hash mismatch: ' + path.name)
        blobs[name] = existing[0].read_bytes()
        transports[name] = existing[0].name
    archive = zipfile.ZipFile(io.BytesIO(blobs['code.zip']))
    with archive:
        members = archive.infolist()
        if sum(i.file_size for i in members) > MAX_PAYLOAD_BYTES:
            raise ValueError('code archive is too large')
        names = set()
        for info in members:
            name = info.filename
            path = PurePosixPath(name)
            if (not name or not path.parts or '\x00' in name or '\\' in name or path.is_absolute()
                    or '..' in path.parts or PureWindowsPath(name).drive
                    or stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK
                    or name.rstrip('/').casefold() in names):
                raise ValueError('unsafe code archive member: ' + name)
            names.add(name.rstrip('/').casefold())
        if archive.testzip() is not None:
            raise ValueError('code archive CRC failure')
        work = Path(work_root).resolve(strict=True)
        staged = work / ('rgpt-staged-input-' + attempt)
        source = work / ('rgpt-source-' + manifest['code_commit'][:7] + '-' + attempt)
        if staged.exists() or source.exists():
            raise FileExistsError('staged/source path exists; preserve it and use a fresh session or attempt identifier')
        staged.mkdir()
        for name, data in blobs.items():
            (staged / name).write_bytes(data)
        (staged / 'input-manifest.json').write_bytes(manifest_bytes)
        source.mkdir()
        for info in members:
            target = source.joinpath(*PurePosixPath(info.filename).parts)
            if not target.resolve().is_relative_to(source):
                raise ValueError('archive path escaped source directory')
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info))
    record = {'package_id': manifest['package_id'], 'input_manifest_sha256': expected_sha,
              'mounted_input': str(mounted), 'staged_input': str(staged), 'source': str(source),
              'code_commit': manifest['code_commit'], 'transport_names': transports,
              'code_zip_sha256': digest(blobs['code.zip'])}
    return staged, source, record
