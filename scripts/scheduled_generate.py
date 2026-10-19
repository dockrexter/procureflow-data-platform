import os
import subprocess
from datetime import datetime,timezone,date
batch=os.environ.get('BATCH_DATE') or datetime.now(timezone.utc).date().isoformat()
date.fromisoformat(batch)
mode=os.environ.get('BATCH_MODE') or 'daily'
subprocess.run(['python','data-generator/generate.py',mode,'--date',batch],check=True)
