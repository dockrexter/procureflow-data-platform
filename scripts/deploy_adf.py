"""Publish reviewed ADF JSON, no trigger creation or execution."""
import argparse
import json
import subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--subscription',required=True);p.add_argument('--group',required=True);p.add_argument('--factory',required=True);a=p.parse_args()
base=f'https://management.azure.com/subscriptions/{a.subscription}/resourceGroups/{a.group}/providers/Microsoft.DataFactory/factories/{a.factory}'
for folder,kind in [('linkedService','linkedservices'),('dataset','datasets'),('pipeline','pipelines')]:
    for file in sorted(Path('adf',folder).glob('*.json')):
        name=json.loads(file.read_text())['name']
        subprocess.run(['az','rest','--method','put','--url',f'{base}/{kind}/{name}?api-version=2018-06-01','--body','@'+str(file),'--output','none'],check=True)
        print('Published',kind,name)
