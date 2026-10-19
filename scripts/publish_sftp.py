"""Publish an immutable verified batch using host-key checked SFTP and atomic rename."""
import argparse
import errno
import os
from pathlib import Path
import tempfile
from landing import verify


def exists(client,path):
    try:client.stat(path);return True
    except OSError as exc:
        if exc.errno==errno.ENOENT:return False
        raise


def publish(client,batch):
    batch=Path(batch);m=verify(batch)
    root='/outbound/'+m['source']
    # The dedicated SFTP account must already have a writable /outbound root.
    if not exists(client,root):client.mkdir(root)
    target=root+'/'+m['batch_date']
    names=sorted(m['files'])+['manifest.json','_SUCCESS']
    if exists(client,target):
        if set(client.listdir(target))!=set(names):raise ValueError('Existing remote batch differs')
        for name in names:
            with client.open(target+'/'+name,'rb') as stream:
                if stream.read()!=(batch/name).read_bytes():raise ValueError('Remote batch conflict: '+name)
        return target
    staging=root+'/.pending-'+m['batch_date']+'-'+(batch/'_SUCCESS').read_text().strip()[:16]
    if not exists(client,staging):client.mkdir(staging)
    for name in names:
        dest=staging+'/'+name
        client.put(str(batch/name),dest,confirm=True)
        with client.open(dest,'rb') as stream:
            if stream.read()!=(batch/name).read_bytes():raise ValueError('Remote checksum mismatch: '+name)
    client.rename(staging,target)
    return target


def main():
    import paramiko
    p=argparse.ArgumentParser();p.add_argument('batch');a=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        key=Path(tmp)/'key';key.write_text(os.environ['SFTP_PRIVATE_KEY']);key.chmod(0o600)
        known=Path(tmp)/'known_hosts';known.write_text(os.environ['SFTP_KNOWN_HOSTS'])
        client=paramiko.SSHClient();client.load_host_keys(str(known))
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        try:
            client.connect(os.environ['SFTP_HOST'],port=int(os.environ.get('SFTP_PORT','22')),
                           username=os.environ['SFTP_USER'],key_filename=str(key),look_for_keys=False,
                           allow_agent=False,timeout=30,banner_timeout=30,auth_timeout=30)
            with client.open_sftp() as sftp:
                sftp.get_channel().settimeout(60)
                print(publish(sftp,a.batch))
        finally:client.close()
if __name__=='__main__':main()
