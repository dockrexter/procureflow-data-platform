"""Verify a complete source batch and land it locally or via Azure CLI/Entra auth."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path


def verify(path):
    path=Path(path)
    raw=(path/'manifest.json').read_bytes()
    if (path/'_SUCCESS').read_text().strip()!=hashlib.sha256(raw).hexdigest():
        raise ValueError('Invalid completion marker')
    m=json.loads(raw)
    if not re.fullmatch(r'[A-Z0-9_]+',m['source']) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',m['batch_date']):
        raise ValueError('Invalid source or date')
    for name,meta in m['files'].items():
        if not re.fullmatch(r'[a-z_]+\.csv',name):raise ValueError('Unsafe file name')
        f=path/name
        if hashlib.sha256(f.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError(f'Hash mismatch: {name}')
        with f.open(newline='') as stream:
            rows=sum(1 for _ in csv.DictReader(stream))
        if rows!=meta['rows']:raise ValueError(f'Row count mismatch: {name}')
    expected=set(m['files'])|{'manifest.json','_SUCCESS'}
    if {p.name for p in path.iterdir()}!=expected:raise ValueError('Unexpected batch contents')
    return m


def az(*args):
    return subprocess.run(['az',*args,'--only-show-errors'],check=True,capture_output=True,text=True).stdout


def land(source, root=None, account=None):
    source=Path(source);m=verify(source)
    prefix=f"{m['source']}/{m['batch_date']}"
    names=sorted(m['files'])+['manifest.json','_SUCCESS']
    if root is not None:
        dest=Path(root)/prefix
        if dest.exists():
            if any(not (dest/n).exists() or (dest/n).read_bytes()!=(source/n).read_bytes() for n in names):
                raise ValueError('Landing conflict')
            verify(dest);return str(dest)
        dest.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
            stage=Path(tmp)/'batch';stage.mkdir()
            for n in names:(stage/n).write_bytes((source/n).read_bytes())
            verify(stage);stage.rename(dest)
        return str(dest)
    if not account or not re.fullmatch('[a-z0-9]{3,24}',account):raise ValueError('Invalid storage account')
    common=['--account-name',account,'--container-name','landing','--auth-mode','login']
    # Compare before writing. Never overwrite a different blob; interrupted uploads can resume.
    for n in names:
        blob=f'{prefix}/{n}'
        exists=json.loads(az('storage','blob','exists',*common,'--name',blob))['exists']
        if exists:
            with tempfile.TemporaryDirectory() as tmp:
                downloaded=Path(tmp)/n
                az('storage','blob','download',*common,'--name',blob,'--file',str(downloaded),'--no-progress')
                if downloaded.read_bytes()!=(source/n).read_bytes():raise ValueError(f'Landing conflict: {blob}')
    for n in names:
        blob=f'{prefix}/{n}'
        exists=json.loads(az('storage','blob','exists',*common,'--name',blob))['exists']
        if not exists:az('storage','blob','upload',*common,'--name',blob,'--file',str(source/n),'--overwrite','false','--no-progress')
        with tempfile.TemporaryDirectory() as tmp:
            downloaded=Path(tmp)/n
            az('storage','blob','download',*common,'--name',blob,'--file',str(downloaded),'--no-progress')
            if downloaded.read_bytes()!=(source/n).read_bytes():raise ValueError(f'Read-back mismatch: {blob}')
    return f'https://{account}.dfs.core.windows.net/landing/{prefix}'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('batch')
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--local-root');group.add_argument('--account')
    a=p.parse_args();print(land(a.batch,a.local_root,a.account))
