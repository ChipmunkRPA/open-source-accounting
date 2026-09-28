"""Bounded EDGAR submissions metadata; never a filing-body or adoption parser."""
import json
import math
import re
import sys
from datetime import date, datetime
from urllib.parse import urlsplit
from .sec_core.core import canonical, digest
from .crossref_discovery import no_duplicate_keys

VERSION = 'sec-submissions-1'
MAX_ROWS = 10000
COLUMNS = {'accessionNumber','filingDate','reportDate','acceptanceDateTime','act','form','fileNumber',
           'filmNumber','items','core_type','size','isXBRL','isInlineXBRL','primaryDocument','primaryDocDescription'}
REQUIRED = {'accessionNumber','filingDate','reportDate','form','primaryDocument'}
ROOT_FIELDS = {'cik','entityType','sic','sicDescription','ownerOrg','insiderTransactionForOwnerExists',
    'insiderTransactionForIssuerExists','name','tickers','exchanges','ein','lei','description','website',
    'investorWebsite','category','fiscalYearEnd','stateOfIncorporation','stateOfIncorporationDescription',
    'addresses','phone','flags','formerNames','filings'}


def endpoint(url):
    p = urlsplit(url)
    match = re.fullmatch(r'/submissions/CIK([0-9]{10})(-submissions-[0-9]{3,})?\.json', p.path)
    if (p.scheme != 'https' or p.hostname != 'data.sec.gov' or p.username or p.password
            or p.port not in {None,443} or p.query or p.fragment or not match
            or '\\' in url or any(c.isspace() or ord(c)<32 for c in url) or int(match[1])==0):
        raise ValueError('Use an exact official SEC submissions JSON endpoint.')
    return match[1], bool(match[2])


def bounded(value, depth=0, count=None):
    count = count if count is not None else [0]
    count[0] += 1
    if depth>12 or count[0]>250000:
        raise ValueError('Metadata structure limit exceeded.')
    if isinstance(value,dict):
        for key, child in value.items():
            if len(key)>200:raise ValueError('Oversized key.')
            bounded(child,depth+1,count)
    elif isinstance(value,list):
        for child in value:bounded(child,depth+1,count)
    elif isinstance(value,float) and not math.isfinite(value):
        raise ValueError('Non-finite metadata number.')
    elif isinstance(value,str) and len(value)>10000:
        raise ValueError('Oversized metadata string.')


def text(value, maximum=300, empty=False):
    if not isinstance(value,str) or len(value)>maximum or (not empty and not value.strip()):
        raise ValueError('Invalid metadata string.')
    if any(ord(c)<32 for c in value):raise ValueError('Control character in metadata.')
    return value


def day(value, optional=False):
    if optional and value=='':return None
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',value):
        raise ValueError('Invalid date precision.')
    date.fromisoformat(value)
    return value


def extract(raw, base_url):
    cik, historical = endpoint(base_url)
    if len(raw)>16_000_000:raise ValueError('Oversized submissions snapshot.')
    def invalid_constant(_):raise ValueError('Non-finite JSON number.')
    data = json.loads(raw,object_pairs_hook=no_duplicate_keys,parse_constant=invalid_constant)
    bounded(data)
    if not isinstance(data,dict):raise ValueError('Expected submissions object.')
    company, older = None, []
    if historical:
        table, prefix = data, ''
    else:
        if set(data)-ROOT_FIELDS or type(data.get('cik')) not in {int,str}:
            raise ValueError('Unexpected submissions envelope.')
        reported_cik = str(data['cik'])
        if not reported_cik.isascii() or not reported_cik.isdigit() or int(reported_cik)!=int(cik):
            raise ValueError('Issuer CIK does not match the authorized endpoint.')
        company = text(data.get('name'))
        filings = data.get('filings')
        if not isinstance(filings,dict) or set(filings)!={'recent','files'}:
            raise ValueError('Missing recent filings or older-file inventory.')
        table, prefix = filings['recent'], '/filings/recent'
        files = filings['files']
        if not isinstance(files,list) or len(files)>1000:raise ValueError('Invalid older-file inventory.')
        seen = set()
        for n, entry in enumerate(files):
            if not isinstance(entry,dict) or set(entry)!={'name','filingCount','filingFrom','filingTo'}:
                raise ValueError('Invalid older-file descriptor.')
            name = text(entry['name'])
            url = 'https://data.sec.gov/submissions/'+name
            linked_cik, is_history = endpoint(url)
            if linked_cik!=cik or not is_history or name in seen:
                raise ValueError('Foreign, duplicate or non-history continuation.')
            seen.add(name)
            low, high = day(entry['filingFrom']), day(entry['filingTo'])
            if low>high or type(entry['filingCount']) is not int or not 0<=entry['filingCount']<=MAX_ROWS:
                raise ValueError('Invalid history range or reported count.')
            older.append({**entry,'url':url,'locator':f'/filings/files/{n}',
                          'status':'linked_not_acquired','reuse_authorized':False})
    if not isinstance(table,dict) or not REQUIRED<=set(table) or set(table)-COLUMNS:
        raise ValueError('Unsupported submissions columns.')
    if any(not isinstance(v,list) for v in table.values()):raise ValueError('Columns must be arrays.')
    total = len(table['accessionNumber'])
    if total>MAX_ROWS or any(len(v)!=total for v in table.values()):
        raise ValueError('Uneven or oversized submissions columns.')
    items, accessions = [], set()
    for n in range(total):
        row = {k:v[n] for k,v in table.items()}
        accession = text(row['accessionNumber'],20)
        if not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',accession) or accession in accessions:
            raise ValueError('Invalid or duplicate accession.')
        accessions.add(accession)
        form = text(row['form'],40)
        if not re.fullmatch(r'[A-Za-z0-9 /-]+',form):raise ValueError('Invalid form.')
        filed, period = day(row['filingDate']), day(row['reportDate'],True)
        accepted = row.get('acceptanceDateTime') or None
        if accepted is not None:
            text(accepted,50)
            stamp=datetime.fromisoformat(accepted.replace('Z','+00:00'))
            if stamp.tzinfo is None:raise ValueError('Acceptance timestamp needs a timezone.')
        name = text(row['primaryDocument'],255,True)
        if name and (not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*',name) or '..' in name):
            raise ValueError('Unsafe primary-document name.')
        for k in ('size','isXBRL','isInlineXBRL'):
            if k in row and (type(row[k]) is not int or row[k]<0 or (k!='size' and row[k] not in {0,1})):
                raise ValueError('Invalid size or XBRL indicator.')
        for k in set(row)-REQUIRED-{'size','isXBRL','isInlineXBRL','acceptanceDateTime'}:
            text(row[k],2000,True)
        directory=f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-", "")}/'
        items.append({'cik':cik,'company':company,'accession':accession,'form':form,
            'filed_on':filed,'period_end':period,'accepted_at':accepted,
            'primary_document':name or None,'url':directory+name if name else None,
            'index_url':directory+accession+'-index.html',
            'locator':f'{prefix}/accessionNumber/{n}','record_sha256':digest(canonical(row)),
            'metadata':row,'is_amendment':form.endswith('/A'),'amends_accession':None,
            'amendment_link_status':'unresolved' if form.endswith('/A') else 'not_asserted',
            'status':'unreviewed_filing_candidate','authority_type':'company_practice_not_gaap',
            'full_text_acquired':False,'reuse_authorized':False,'agent_eligible':False})
    return {'adapter_version':VERSION,'raw_sha256':digest(raw),'base_url':base_url,'cik':cik,
            'issuer_identity_basis':'endpoint_only' if historical else 'endpoint_and_reported_cik',
            'items':items,'older_files':older,'network_requests':0,
            'coverage_scope':'one submissions metadata snapshot; linked histories and filing bodies are separate',
            'complete_filing_history':False,'adoption_classification_performed':False}


def main():
    import resource
    resource.setrlimit(resource.RLIMIT_CPU,(15,15))
    if sys.platform!='darwin':resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
    sys.stdout.buffer.write(canonical(extract(sys.stdin.buffer.read(16_000_001),sys.argv[1])))


if __name__=='__main__':main()
