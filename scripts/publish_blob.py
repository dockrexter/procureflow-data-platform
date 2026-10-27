"""Validate a generated batch and replace its fixed filenames in outbound."""
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


def publish(source, account):
    source = Path(source)
    m = verify(source)
    if not re.fullmatch('[a-z0-9]{3,24}', account):
        raise ValueError('Invalid storage account')
    names = sorted(m['files']) + ['manifest.json', '_SUCCESS']
    container = 'outbound'
    common = ['--account-name', account, '--container-name', container, '--auth-mode', 'login']
    # Outbound is a replaceable source folder, not a historical archive.
    prefix=m['source']
    marker=f'{prefix}/_SUCCESS'
    existing=json.loads(az('storage','blob','list',*common,'--prefix',prefix+'/', '--query','[].name'))
    if marker in existing:
        az('storage','blob','delete',*common,'--name',marker)
    # Remove stale files, including the former dated layout, only in this source.
    expected={f'{prefix}/{n}' for n in names}
    for blob in existing:
        if blob not in expected:
            az('storage','blob','delete',*common,'--name',blob)
    for n in names:
        blob=f'{prefix}/{n}'
        az('storage','blob','upload',*common,'--name',blob,'--file',str(source/n),'--overwrite','true','--no-progress')
        with tempfile.TemporaryDirectory() as tmp:
            downloaded=Path(tmp)/n
            az('storage','blob','download',*common,'--name',blob,'--file',str(downloaded),'--no-progress')
            if downloaded.read_bytes()!=(source/n).read_bytes():
                if n == '_SUCCESS':
                    az('storage','blob','delete',*common,'--name',marker)
                raise ValueError(f'Read-back mismatch: {blob}')
    return f'https://{account}.blob.core.windows.net/{container}/{prefix}'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch')
    parser.add_argument('--account', required=True)
    args = parser.parse_args()
    print(publish(args.batch, args.account))
