"""Offline reference checks; service-side validation remains a deployment requirement."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for p in (root/'adf').rglob('*.json'):
    data=json.loads(p.read_text())
    if p.name == 'publish_config.json':
        continue
    assert data['name']==p.stem,p
    def walk(obj):
        if isinstance(obj,dict):
            if obj.get('type') in ['LinkedServiceReference','DatasetReference']:
                folder='linkedService' if obj['type']=='LinkedServiceReference' else 'dataset'
                assert (root/'adf'/folder/(obj['referenceName']+'.json')).exists(),obj
            for v in obj.values():walk(v)
        elif isinstance(obj,list):
            for v in obj:walk(v)
    walk(data)
print('ADF JSON and resource references valid')
