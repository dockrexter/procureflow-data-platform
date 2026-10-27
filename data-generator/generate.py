"""Deterministic simplified SAP procurement extracts. Python standard library only."""
import argparse
import csv
import hashlib
import io
import json
import random
import re
import shutil
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

VERSION = 1
SCHEMAS = {
 'companies': 'BUKRS BUTXT WAERS', 'plants': 'WERKS BUKRS NAME1',
 'purchasing_organizations': 'EKORG BUKRS EKOTX', 'suppliers': 'LIFNR NAME1 LAND1',
 'materials': 'MATNR MAKTX MEINS', 'exchange_rates': 'GDATU FCURR TCURR UKURS',
 'po_headers': 'EBELN BUKRS EKORG LIFNR BEDAT WAERS',
 'po_items': 'EBELN EBELP MATNR WERKS MENGE MEINS NETPR NETWR',
 'goods_receipts': 'MBLNR EBELN EBELP BUDAT MENGE',
 'invoice_headers': 'BELNR EBELN BUKRS LIFNR BLDAT WAERS RMWWR',
 'invoice_items': 'BELNR BUZEI EBELN EBELP MENGE WRBTR',
 'payments': 'PAYMENT_ID BELNR BUKRS BUDAT WAERS WRBTR',
 'po_history': 'EVENT_ID EBELN EBELP VGABE BUDAT MENGE WRBTR',
}
KEYS = {t: fields.split()[:1] for t, fields in SCHEMAS.items()}
KEYS.update(po_items=['EBELN','EBELP'], invoice_items=['BELNR','BUZEI'],
            exchange_rates=['GDATU','FCURR','TCURR'])
CURRENCIES = ['EUR','USD','GBP','SEK','PLN']

def money(cents):
    return format(Decimal(cents) / 100, '.2f')

def load_config(path):
    c = json.loads(Path(path).read_text())
    date.fromisoformat(c['epoch'])
    for k in ['seed','bootstrap_pos','daily_pos','history_days','suppliers','materials']:
        if type(c[k]) is not int or c[k] < (0 if k == 'seed' else 1):
            raise ValueError(f'Invalid {k}')
    if c['bootstrap_pos'] > 999999 or c['daily_pos'] > 999999:
        raise ValueError('Maximum 999999 POs per cohort')
    if c.get('adapter', c.get('source')) != 'SAP_S4HANA':
        raise ValueError('Unsupported source adapter')
    return c

def snapshot(c, as_of):
    epoch = date.fromisoformat(c['epoch'])
    if as_of < epoch:
        raise ValueError('as-of precedes epoch')
    tables = {t: [] for t in SCHEMAS}
    def add(t, *values):
        row = dict(zip(SCHEMAS[t].split(), map(str, values), strict=True))
        tables[t].append(row)
        return row
    for i in range(5):
        company = f'{1000+i}'
        add('companies',company,f'Synthetic Company {i+1}',CURRENCIES[i])
        for j in range(4):
            add('plants',f'{i*4+j+1:04}',company,f'Synthetic Plant {i*4+j+1}')
        for j in range(2):
            add('purchasing_organizations',f'{i*2+j+1:04}',company,f'Purchasing {i*2+j+1}')
    for i in range(1,c['suppliers']+1):
        add('suppliers',f'{i:010}',f'Synthetic Supplier {i:04}', ['FI','DE','US','SE','PL'][i%5])
    for i in range(1,c['materials']+1):
        add('materials',f'{i:018}',f'Synthetic Material {i:05}','EA')
    first = epoch - timedelta(days=c['history_days']-1)
    for day in range((as_of-first).days+1):
        d = first + timedelta(days=day)
        for currency, base in zip(CURRENCIES,[1000000,920000,1180000,89000,230000]):
            # Synthetic rates expressed as EUR per one unit of source currency.
            noise = 0 if currency=='EUR' else random.Random(f"{c['seed']}:fx:{d}:{currency}").randint(-1000,1000)
            add('exchange_rates',d,currency,'EUR',format(Decimal(base+noise)/1000000,'.6f'))
    def order(cohort, index, created):
        rng = random.Random(f"{VERSION}:{c['seed']}:{cohort}:{index}")
        po = f'{cohort}{index:06}'
        comp = rng.randrange(5)
        company, currency = str(1000+comp), CURRENCIES[comp]
        supplier = f"{rng.randint(1,c['suppliers']):010}"
        add('po_headers',po,company,f'{comp*2+rng.randrange(2)+1:04}',supplier,created,currency)
        inv_date = created+timedelta(days=3+rng.randrange(5))
        payment_date = inv_date+timedelta(days=30)
        invoice = 'I'+po
        total = 0
        for line in range(1, rng.randint(2,4)+1):
            item = f'{line*10:05}'
            qty, price = rng.randint(2,100), rng.randint(100,100000)
            value = qty*price
            total += value
            add('po_items',po,item,f"{rng.randint(1,c['materials']):018}",f'{comp*4+rng.randrange(4)+1:04}',qty,'EA',money(price),money(value))
            # Two partial receipts, never exceeding the ordered quantity.
            for part, received in enumerate([qty//2,qty-qty//2],1):
                receipt_date = created+timedelta(days=part)
                if receipt_date <= as_of:
                    rid = f'R{po}-{item}-{part}'
                    add('goods_receipts',rid,po,item,receipt_date,received)
                    add('po_history',rid,po,item,'1',receipt_date,received,money(received*price))
            if inv_date <= as_of:
                add('invoice_items',invoice,item,po,item,qty,money(value))
                add('po_history',f'{invoice}-{item}',po,item,'2',inv_date,qty,money(value))
        if inv_date <= as_of:
            add('invoice_headers',invoice,po,company,supplier,inv_date,currency,money(total))
        if payment_date <= as_of:
            add('payments','P'+po,invoice,company,payment_date,currency,money(total))
    for i in range(c['bootstrap_pos']):
        created = first + timedelta(days=i % c['history_days'])
        order('B',i+1,created)
    for offset in range(1,(as_of-epoch).days+1):
        created = epoch + timedelta(days=offset)
        for i in range(c['daily_pos']):
            order(created.strftime('%Y%m%d'),i+1,created)
    return tables

def validate(t):
    def require(ok, message):
        if not ok: raise ValueError(message)
    for name, fields in SCHEMAS.items():
        keys = [tuple(r[k] for k in KEYS[name]) for r in t[name]]
        require(len(keys)==len(set(keys)),f'Duplicate key: {name}')
        require(all(set(r)==set(fields.split()) for r in t[name]),f'Schema: {name}')
    companies = {r['BUKRS']:r for r in t['companies']}
    plants = {r['WERKS']:r for r in t['plants']}
    orgs = {r['EKORG']:r for r in t['purchasing_organizations']}
    suppliers = {r['LIFNR'] for r in t['suppliers']}
    materials = {r['MATNR'] for r in t['materials']}
    pos = {r['EBELN']:r for r in t['po_headers']}
    items = {(r['EBELN'],r['EBELP']):r for r in t['po_items']}
    invoices = {r['BELNR']:r for r in t['invoice_headers']}
    fx = {(r['GDATU'],r['FCURR'],r['TCURR']) for r in t['exchange_rates']}
    for r in t['plants']+t['purchasing_organizations']:
        require(r['BUKRS'] in companies,'Master company relationship')
    for r in t['exchange_rates']:
        require(Decimal(r['UKURS'])>0,'FX positive')
    for r in pos.values():
        require(r['BUKRS'] in companies and r['LIFNR'] in suppliers,'PO master relationship')
        require(orgs[r['EKORG']]['BUKRS']==r['BUKRS'],'PO organization company')
        require(r['WAERS']==companies[r['BUKRS']]['WAERS'],'PO currency')
        require((r['BEDAT'],r['WAERS'],'EUR') in fx,'Missing FX rate')
    for k,r in items.items():
        require(r['EBELN'] in pos and r['MATNR'] in materials,'PO item relationship')
        require(plants[r['WERKS']]['BUKRS']==pos[k[0]]['BUKRS'],'Plant company')
        require(int(r['MENGE'])>0 and Decimal(r['NETPR'])>0,'Positive quantity and price')
        require(Decimal(r['NETWR'])==int(r['MENGE'])*Decimal(r['NETPR']),'PO amount')
    receipts, receipt_dates = {}, {}
    expected_history = []
    for r in t['goods_receipts']:
        k=(r['EBELN'],r['EBELP'])
        require(k in items,'Receipt relationship')
        require(r['BUDAT']>=pos[k[0]]['BEDAT'],'Receipt chronology')
        require(int(r['MENGE'])>0,'Receipt quantity')
        receipts[k]=receipts.get(k,0)+int(r['MENGE'])
        receipt_dates[k]=max(receipt_dates.get(k,''),r['BUDAT'])
        expected_history.append(dict(zip(SCHEMAS['po_history'].split(),[r['MBLNR'],*k,'1',r['BUDAT'],r['MENGE'],format(Decimal(items[k]['NETPR'])*int(r['MENGE']),'.2f')])))
    require(all(q<=int(items[k]['MENGE']) for k,q in receipts.items()),'Over receipt')
    totals, billed = {}, {}
    for r in t['invoice_items']:
        k=(r['EBELN'],r['EBELP'])
        require(k in items and r['BELNR'] in invoices,'Invoice item relationship')
        h=invoices[r['BELNR']]
        require(h['EBELN']==k[0] and h['BLDAT']>=receipt_dates[k],'Invoice chronology or PO')
        require(int(r['MENGE'])>0,'Invoice quantity')
        billed[k]=billed.get(k,0)+int(r['MENGE'])
        require(Decimal(r['WRBTR'])==int(r['MENGE'])*Decimal(items[k]['NETPR']),'Invoice line amount')
        totals[r['BELNR']]=totals.get(r['BELNR'],Decimal(0))+Decimal(r['WRBTR'])
        expected_history.append(dict(zip(SCHEMAS['po_history'].split(),[f"{r['BELNR']}-{r['EBELP']}",*k,'2',h['BLDAT'],r['MENGE'],r['WRBTR']])))
    require(all(q<=receipts.get(k,0) for k,q in billed.items()),'Over invoice')
    for r in invoices.values():
        p=pos[r['EBELN']]
        require(all(r[k]==p[k] for k in ['BUKRS','LIFNR','WAERS']),'Invoice header relationship')
        require(totals.get(r['BELNR'])==Decimal(r['RMWWR']),'Invoice total')
    paid={}
    for r in t['payments']:
        require(r['BELNR'] in invoices,'Payment relationship')
        h=invoices[r['BELNR']]
        require(r['BUDAT']>=h['BLDAT'],'Payment chronology')
        require(r['BUKRS']==h['BUKRS'] and r['WAERS']==h['WAERS'],'Payment company/currency')
        require(Decimal(r['WRBTR'])>0,'Payment positive')
        paid[r['BELNR']]=paid.get(r['BELNR'],Decimal(0))+Decimal(r['WRBTR'])
    require(all(v<=Decimal(invoices[k]['RMWWR']) for k,v in paid.items()),'Over payment')
    require(sorted(expected_history,key=lambda r:r['EVENT_ID'])==sorted(t['po_history'],key=lambda r:r['EVENT_ID']),'History reconciliation')

def batch(c, as_of, mode):
    full=snapshot(c,as_of)
    validate(full)
    if mode=='bootstrap':
        if as_of.isoformat()!=c['epoch']: raise ValueError('Bootstrap must use epoch date')
        return full
    if as_of<=date.fromisoformat(c['epoch']): raise ValueError('Daily must follow epoch')
    date_fields={'exchange_rates':'GDATU','po_headers':'BEDAT','goods_receipts':'BUDAT','invoice_headers':'BLDAT','payments':'BUDAT','po_history':'BUDAT'}
    result={t:[] for t in SCHEMAS}
    for t,field in date_fields.items():
        result[t]=[r for r in full[t] if r[field]==as_of.isoformat()]
    new_pos={r['EBELN'] for r in result['po_headers']}
    new_inv={r['BELNR'] for r in result['invoice_headers']}
    result['po_items']=[r for r in full['po_items'] if r['EBELN'] in new_pos]
    result['invoice_items']=[r for r in full['invoice_items'] if r['BELNR'] in new_inv]
    return result

def build_files(c, as_of, mode):
    tables=batch(c,as_of,mode)
    files={}
    manifest={'schema_version':VERSION,'source':c['source'],'batch_date':as_of.isoformat(),'mode':mode,'config':c,'files':{}}
    for t,rows in tables.items():
        stream=io.StringIO(newline='')
        writer=csv.DictWriter(stream,fieldnames=SCHEMAS[t].split(),lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
        data=stream.getvalue().encode()
        files[t+'.csv']=data
        manifest['files'][t+'.csv']={'rows':len(rows),'sha256':hashlib.sha256(data).hexdigest()}
    files['manifest.json']=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    files['_SUCCESS']=(hashlib.sha256(files['manifest.json']).hexdigest()+'\n').encode()
    return files

def write_batch(c, as_of, mode, root):
    files=build_files(c,as_of,mode)
    target=Path(root)/c['source']/as_of.isoformat()
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if {p.name:p.read_bytes() for p in target.iterdir() if p.is_file()}!=files:
            raise ValueError('Existing batch differs; refusing overwrite')
        return target
    stage=Path(tempfile.mkdtemp(prefix='.batch-',dir=target.parent))
    try:
        for name,data in files.items(): (stage/name).write_bytes(data)
        stage.rename(target)
    finally:
        if stage.exists(): shutil.rmtree(stage)
    return target

def source_config(source, as_of, config_dir=None):
    if not re.fullmatch(r'[A-Z][A-Z0-9_]*', source):
        raise ValueError('Datasource must use uppercase letters, numbers and underscores')
    config_dir = Path(config_dir) if config_dir else Path(__file__).resolve().parents[1] / 'config'
    path = config_dir / (source.lower() + '.json')
    if not path.is_file():
        raise ValueError(f'No datasource configuration: {path.name}')
    config = load_config(path)
    if config['source'] != source:
        raise ValueError('Datasource name does not match its configuration')
    epoch = date.fromisoformat(config['epoch'])
    if as_of < epoch:
        raise ValueError(f'Date must be on or after {epoch}')
    return config, 'bootstrap' if as_of == epoch else 'daily'


def business_date(value):
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError('Date must use YYYY-MM-DD')
    return parsed


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source', required=True)
    p.add_argument('--date', required=True, type=business_date)
    p.add_argument('--output', default='data/outbound')
    a=p.parse_args()
    try:
        config, mode = source_config(a.source, a.date)
    except ValueError as error:
        p.error(str(error))
    print(write_batch(config, a.date, mode, a.output))
