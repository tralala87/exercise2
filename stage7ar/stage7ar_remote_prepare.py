from __future__ import annotations
import argparse, csv, hashlib, json, os, shutil, tempfile, time, urllib.request, zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import numpy as np
import pandas as pd

MANIFEST_PATH = Path(__file__).with_name('DATASET_CANDIDATES.json')
MANIFEST = json.loads(MANIFEST_PATH.read_text())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def stable_json(x: Any) -> str:
    return json.dumps(x,sort_keys=True,separators=(',',':'),default=str,allow_nan=False)

def atomic_json(path: Path, x: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+'.tmp'); t.write_text(json.dumps(x,indent=2,sort_keys=True,default=str,allow_nan=False)+'\n'); t.replace(path)

def atomic_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+'.tmp'); frame.to_csv(t,index=False); t.replace(path)

def download(url: str, dst: Path, retries: int=4) -> Path:
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists() and dst.stat().st_size>0: return dst
    err=None
    for k in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'stage7ar-github-actions/1.0'})
            with urllib.request.urlopen(req,timeout=180) as r, tempfile.NamedTemporaryFile(dir=dst.parent,delete=False) as f:
                shutil.copyfileobj(r,f); tmp=Path(f.name)
            if tmp.stat().st_size<=0: raise IOError('empty download')
            tmp.replace(dst); return dst
        except Exception as e:
            err=e; time.sleep(2**k)
    raise RuntimeError(f'download failed: {url}: {err}')

def interp(v: np.ndarray) -> np.ndarray:
    v=np.asarray(v,float); ok=np.isfinite(v)
    if ok.all(): return v.copy()
    if not ok.any(): return np.zeros_like(v)
    x=np.arange(len(v)); return np.interp(x,x[ok],v[ok])

def parse_wide(path: Path, c: Mapping[str,Any]):
    df=pd.read_csv(path); drop={str(x).lower() for x in c.get('drop_columns',[])}
    names=[]; arr=[]
    for col in df.columns:
        if str(col).lower() in drop: continue
        v=pd.to_numeric(df[col],errors='coerce').to_numpy(float)
        if np.isfinite(v).sum()<max(12,int(.6*len(v))) or float(np.nanstd(v))<1e-12: continue
        names.append(str(col)); arr.append(v)
    if len(arr)<2: raise ValueError('fewer than two numeric channels')
    return tuple(names),np.column_stack(arr),'native_wide_chronology'

def parse_panel_long(path: Path, c: Mapping[str,Any]):
    df=pd.read_csv(path)
    entity=str(c['entity_column']); time_col=str(c['time_column']); value=str(c['value_column'])
    missing=[x for x in (entity,time_col,value) if x not in df.columns]
    if missing: raise ValueError(f'missing panel columns {missing}')
    work=df[[entity,time_col,value]].copy()
    work[value]=pd.to_numeric(work[value],errors='coerce')
    work=work.dropna(subset=[entity,time_col,value])
    if work.empty: raise ValueError('no usable long-panel rows')
    pivot=work.pivot_table(index=time_col,columns=entity,values=value,aggfunc='mean')
    try: pivot=pivot.sort_index()
    except Exception: pivot=pivot.sort_index(key=lambda x:x.astype(str))
    return tuple(str(x) for x in pivot.columns),pivot.to_numpy(float),'native_entity_time_panel'

@dataclass
class TSeries:
    attrs: dict[str,str]
    values: np.ndarray

def parse_tsf(path: Path):
    attrs=[]; rows=[]; in_data=False
    with path.open('r',encoding='utf-8',errors='replace') as f:
        for raw in f:
            line=raw.strip()
            if not line or line.startswith('#'): continue
            if not in_data:
                if line.lower()=='@data': in_data=True; continue
                if line.lower().startswith('@attribute'):
                    p=line.split()
                    if len(p)>=3: attrs.append((p[1],p[2].lower()))
                continue
            p=line.split(':')
            if len(p)!=len(attrs)+1: continue
            meta={attrs[i][0]:p[i] for i in range(len(attrs))}
            try: v=np.array([np.nan if z.strip() in {'?','','nan','NaN'} else float(z) for z in p[-1].split(',')],float)
            except Exception: continue
            if np.isfinite(v).sum()>=12: rows.append(TSeries(meta,v))
    if not rows: raise ValueError('no usable TSF series')
    return rows

def stamp(a: Mapping[str,str]) -> str:
    for k in ('start_timestamp','start_time','start_date','timestamp'):
        if k in a: return str(a[k])
    return ''

def align_tsf(rows, minimum: int):
    groups=defaultdict(list)
    for r in rows: groups[(stamp(r.attrs),len(r.values))].append(r)
    good=[g for (s,_),g in groups.items() if s and len(g)>=minimum]
    if not good: raise ValueError('no explicit shared-calendar aligned block; relative-index alignment forbidden')
    g=max(good,key=lambda q:(len(q),len(q[0].values)))
    names=[]
    for i,r in enumerate(g): names.append(str(r.attrs.get('series_name') or r.attrs.get('series_id') or f'series_{i:05d}'))
    return tuple(names),np.column_stack([r.values for r in g]),'calendar_start_and_length_aligned'

def shape_hash(values: np.ndarray) -> str:
    x=np.asarray(values,float); n=min(len(x),256); ix=np.linspace(0,len(x)-1,n).round().astype(int); z=x[ix]
    hs=[]
    for j in range(z.shape[1]):
        v=interp(z[:,j]); v=(v-v.mean())/max(float(v.std()),1e-6); v=np.clip(v,-8,8).astype(np.float32)
        hs.append(sha256_bytes(np.ascontiguousarray(v).tobytes()))
    return sha256_bytes('|'.join(sorted(hs)).encode())

def prepare_one(c: Mapping[str,Any], cache: Path, minimum: int):
    kind=c['kind']
    if kind=='wide_csv':
        url=str(c['url']); raw=download(url,cache/'raw'/f"{c['id']}.csv"); names,values,mode=parse_wide(raw,c); source=url
    elif kind=='panel_long_csv':
        url=str(c['url']); raw=download(url,cache/'raw'/f"{c['id']}.csv"); names,values,mode=parse_panel_long(raw,c); source=url
    elif kind=='zenodo_tsf':
        if c.get('alignment_contract')!='explicit_shared_calendar_start_and_length': raise ValueError('missing alignment contract')
        rid=int(c['record_id']); stem=str(c['file_stem']); url=f'https://zenodo.org/record/{rid}/files/{stem}.zip'
        raw=download(url,cache/'raw'/f"{c['id']}.zip"); ext=cache/'extracted'/c['id']; ext.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(raw) as z: z.extractall(ext)
        matches=list(ext.rglob('*.tsf'))
        if not matches: raise ValueError('zip has no TSF')
        names,values,mode=align_tsf(parse_tsf(matches[0]),minimum); source=url
    else: raise ValueError(f'unsupported kind {kind}')
    values=np.asarray(values,float)
    keep=[j for j in range(values.shape[1]) if np.isfinite(values[:,j]).sum()>=12 and np.nanstd(values[:,j])>1e-12]
    values=values[:,keep]; names=tuple(names[j] for j in keep)
    if len(names)<minimum: raise ValueError(f'only {len(names)} valid series')
    good=np.isfinite(values).sum(axis=1)>=minimum
    if not good.any(): raise ValueError('no rows with enough active series')
    lo=int(np.argmax(good)); hi=int(len(good)-np.argmax(good[::-1])); values=values[lo:hi]
    if c['partition']=='training' and len(values)<int(MANIFEST['selection_policy']['training_minimum_length']): raise ValueError(f'training chronology too short {len(values)}')
    if c['partition']=='locked' and len(values)<int(MANIFEST['selection_policy']['locked_minimum_length']): raise ValueError(f'locked chronology too short {len(values)}')
    parsed=sha256_bytes(np.ascontiguousarray(np.nan_to_num(values,nan=9.87654321e37),dtype=np.float64).tobytes())
    return dict(candidate_id=c['id'],partition=c['partition'],source_family=c['source_family'],names=list(names),values=values,
                alignment_mode=mode,raw_path=str(raw),raw_sha256=sha256_file(raw),parsed_sha256=parsed,source_url=source,
                license=c.get('license','unspecified'),chronology_length=len(values),series_count=values.shape[1],missing_fraction=float(np.mean(~np.isfinite(values))))

def main(root: Path):
    policy=MANIFEST['selection_policy']; minimum=int(policy['minimum_active_series']); cache=root/'data'; cache.mkdir(parents=True,exist_ok=True)
    need={p:int(policy[p+'_required']) for p in ('training','development','locked')}; selected={p:[] for p in need}; failures=[]
    exact=set(); shapes=set(); families=set()
    for c in MANIFEST['candidates']:
        p=c['partition']
        if len(selected[p])>=need[p]: continue
        try:
            full=prepare_one(c,cache,minimum)
            if full['source_family'] in families: raise ValueError('source family overlap')
            values=full.pop('values')
            sh=shape_hash(values)
            if full['parsed_sha256'] in exact: raise ValueError('exact duplicate')
            if sh in shapes: raise ValueError('normalized-shape duplicate')
            panel=cache/'panels'/f"{c['id']}.npz"; panel.parent.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(panel,values=values,names=np.array(full['names'],dtype=str))
            full['snapshot_path']=str(panel); full['snapshot_sha256']=sha256_file(panel); full['normalized_shape_sha256']=sh
            selected[p].append(full); exact.add(full['parsed_sha256']); shapes.add(sh); families.add(full['source_family'])
            print('SELECTED',p,c['id'],full['chronology_length'],full['series_count'],flush=True)
        except Exception as e:
            failures.append(dict(candidate_id=c['id'],partition=p,error=f'{type(e).__name__}: {e}'))
            print('FAILED',p,c['id'],type(e).__name__,e,flush=True)
    counts={p:len(selected[p]) for p in need}; shortages={p:max(0,need[p]-counts[p]) for p in need}
    flat=[r for p in ('training','development','locked') for r in selected[p]]
    lock=dict(stage='7A-R',manifest_version=MANIFEST['manifest_version'],selection_policy=policy,partition_counts=counts,
              shortages=shortages,selected=flat,failures=failures,source_family_disjoint=len(families)==len(flat),
              relative_index_alignment_forbidden=True,created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    lock['data_lock_sha256']=sha256_bytes(stable_json({k:v for k,v in lock.items() if k!='created_utc'}).encode())
    atomic_json(root/'FROZEN_DATASET_CANDIDATES.json',MANIFEST); atomic_json(root/'DATA_LOCK.json',lock)
    atomic_csv(root/'DATA_SELECTION.csv',pd.DataFrame(flat)); atomic_csv(root/'DATA_FAILURES.csv',pd.DataFrame(failures))
    print(json.dumps({'data_lock_sha256':lock['data_lock_sha256'],'partition_counts':counts,'shortages':shortages},indent=2))
    if any(shortages.values()): raise SystemExit(3)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); a=ap.parse_args(); main(a.root)
