"""Scale cached evidence using already recovered datasets, without label fabrication.

Full text retrieval indexes available movie/book summaries. A bounded, explicitly
query-selected candidate pool receives hosted annotations. It is not a preference
benchmark or a claim to annotate every work in the 222,896-item catalog.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from recros_api.transfer_engine import FEATURES, ROOT, text_hash, validate_evidence
from .commandcode import DEFAULT_MODEL, complete_json
from .transfer_build import PROMPT, QUERIES, canonical_hash

LOCAL=ROOT/'apps/api/data/scaled-transfer'
SOURCE_DB=ROOT/'apps/api/data/familiar-catalog.db'
INDEX=LOCAL/'narrative-catalog.db'
SOURCES={'movie':'https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset',
         'book':'https://www.kaggle.com/datasets/dylanjcastillo/7k-books-with-metadata'}


def build_index():
    LOCAL.mkdir(parents=True,exist_ok=True)
    if INDEX.exists():
        with sqlite3.connect(INDEX) as c:
            return json.loads(c.execute('SELECT payload FROM provenance').fetchone()[0])
    source=sqlite3.connect(SOURCE_DB); source.row_factory=sqlite3.Row
    staging=INDEX.with_suffix('.building.db')
    if staging.exists(): staging.unlink()
    with sqlite3.connect(staging) as c:
        c.execute('CREATE TABLE documents (id TEXT PRIMARY KEY,domain TEXT,title TEXT,creators TEXT,evidence_text TEXT)')
        rows=source.execute("SELECT id,domain,title,creators,description FROM works WHERE domain IN ('movie','book') AND length(trim(description))>=60 AND lower(trim(description)) NOT IN ('nan','none','null')").fetchall()
        c.executemany('INSERT INTO documents VALUES (?,?,?,?,?)',[tuple(r) for r in rows])
        c.execute('CREATE VIRTUAL TABLE text_search USING fts5(title,creators,evidence_text,content=documents,content_rowid=rowid,tokenize="porter unicode61 remove_diacritics 2")')
        c.execute("INSERT INTO text_search(text_search) VALUES ('rebuild')")
        counts=dict(c.execute('SELECT domain,count(*) FROM documents GROUP BY domain').fetchall())
        provenance={'input':'apps/api/data/familiar-catalog.db','input_sha256':hashlib.sha256(SOURCE_DB.read_bytes()).hexdigest(),
                    'counts':counts,'eligibility':'Movie/book summaries of at least 60 characters.',
                    'music_note':'Spotify records have acoustic metadata but no narrative summary; not included in this text index.'}
        c.execute('CREATE TABLE provenance(payload TEXT)');c.execute('INSERT INTO provenance VALUES (?)',(json.dumps(provenance),))
    source.close();staging.replace(INDEX)
    return provenance


def prepare(per_query=24,batch_size=24):
    provenance=build_index()
    selected={}; retrieval=[]
    with sqlite3.connect(INDEX) as c:
        c.row_factory=sqlite3.Row
        for domain in ('movie','book'):
            for feature,query in QUERIES.items():
                match=' OR '.join('"'+term+'"' for term in re.findall(r'[a-z]+',query))
                rows=c.execute('SELECT d.*,bm25(text_search,0.5,0.0,1.0) AS score FROM text_search '
                               'JOIN documents d ON text_search.rowid=d.rowid WHERE text_search MATCH ? '
                               'AND d.domain=? ORDER BY score,d.id LIMIT ?',(match,domain,per_query)).fetchall()
                retrieval.append({'domain':domain,'criterion':feature,'count':len(rows),'query':query,
                                  'ids':[r['id'] for r in rows]})
                for row in rows:
                    selected[row['id']]={k:row[k] for k in ('id','domain','title','creators','evidence_text')}
                    selected[row['id']]['evidence_text']=row['evidence_text'][:1400]
                    selected[row['id']].update(source_url=SOURCES[domain],source_kind='recovered dataset summary',
                                              evidence_kind='dataset summary, first 1400 characters',checked_at='2026-10-14')
    items=[selected[k] for k in sorted(selected)]
    protocol={'created_at':datetime.now(timezone.utc).isoformat(),'model':DEFAULT_MODEL,
              'index_provenance':provenance,'selection':'Top fixed BM25/FTS results for four criteria in each narrative domain; union of IDs.',
              'per_query_limit':per_query,'batch_size':batch_size,'pool_size':len(items),
              'retrieval':retrieval,'source_records_sha256':canonical_hash(items),
              'scope':'Query-selected evidence bank, no independent preference labels or representative-sampling claim.'}
    path=LOCAL/'protocol.json'
    if path.exists():
        old=json.loads(path.read_text())
        if any(old[k]!=protocol[k] for k in protocol if k!='created_at'):
            raise ValueError('Pool selection changed; preserve the existing pool and start a versioned directory.')
        protocol=old
    else: path.write_text(json.dumps(protocol,indent=2)+'\n')
    (LOCAL/'sources.json').write_text(json.dumps({'items':items},indent=2)+'\n')
    return items,protocol


def run(allow_calls=False):
    items,protocol=prepare()
    cache_dir=LOCAL/'model_calls';cache_dir.mkdir(exist_ok=True)
    failed=[];calls=[];unannotated=0
    for start in range(0,len(items),protocol['batch_size']):
        batch=items[start:start+protocol['batch_size']]
        data=[{'id':i['id'],'text':i['evidence_text']} for i in batch]
        # Use the same definitions as the development comparison. Only the quote
        # length limit changes for concise excerpts from recovered summaries.
        prompt=PROMPT+'For this batch keep each quotation at most 12 words.\n'+json.dumps(data)
        key=canonical_hash({'prompt':prompt,'model':DEFAULT_MODEL})
        path=cache_dir/(key+'.json')
        cached_before=path.exists()
        if cached_before:
            cached=json.loads(path.read_text())
            if cached['prompt']!=prompt: raise ValueError('Cache prompt mismatch.')
        elif allow_calls:
            try:
                response,prov=complete_json(prompt,DEFAULT_MODEL)
                cached={'prompt':prompt,'response':response,'provenance':prov,'prompt_sha256':text_hash(prompt)}
                path.write_text(json.dumps(cached,indent=2)+'\n')
            except Exception as exc:
                failed.append({'start':start,'count':len(batch),'error_type':type(exc).__name__})
                print(json.dumps({'batch':start,'status':'failed','error_type':type(exc).__name__}),flush=True)
                continue
        else:
            unannotated+=len(batch);continue
        calls.append(cached['provenance'])
        predictions=cached['response'].get('items',[])
        ids=[r.get('id') for r in predictions if isinstance(r,dict)]
        if len(predictions)!=len(batch) or len(ids)!=len(set(ids)) or set(ids)!={i['id'] for i in batch}:
            failed.append({'start':start,'count':len(batch),'error_type':'invalid_id_schema'});continue
        by_id={r['id']:r for r in predictions}
        for item in batch:
            raw=by_id[item['id']].get('claims')
            if not isinstance(raw,list) or len(raw)>4:
                failed.append({'id':item['id'],'error_type':'invalid_claim_schema'});continue
            # Overlong spans remain rejected and recorded rather than silently
            # edited into an apparently successful model response.
            item['annotation']={'claims':raw,'evidence_sha256':text_hash(item['evidence_text']),'model':DEFAULT_MODEL}
            item['annotation']['overlong_quotes']=[c for c in raw if isinstance(c,dict) and
                                                  isinstance(c.get('quote'),str) and len(c['quote'].split())>12]
        print(json.dumps({'batch':start,'items':len(batch),'status':'cached' if cached_before else 'complete'}),flush=True)
    small=json.loads((ROOT/'demo/transfer/annotated.json').read_text())
    # Prefer the inspected official-source record when a title occurs twice.
    existing={(i['domain'],i['title'].casefold()) for i in small['items']}
    combined=small['items']+[i for i in items if (i['domain'],i['title'].casefold()) not in existing]
    rejected=[];accepted=Counter();status=Counter()
    for item in combined:
        valid,bad=validate_evidence(item)
        # Enforce concise spans for dataset records only; original paraphrase
        # annotations remain exactly as in their frozen benchmark.
        if item.get('source_kind')=='recovered dataset summary' and item.get('annotation'):
            raw=item['annotation']['claims']
            item['annotation']['claims']=[c for c in raw if not isinstance(c,dict) or not isinstance(c.get('quote'),str) or len(c['quote'].split())<=12]
            valid,bad=validate_evidence(item)
            bad.extend({'claim':c,'reason':'Quote exceeds the frozen twelve-word budget.'} for c in item['annotation']['overlong_quotes'])
        accepted.update(c['feature'] for c in valid)
        status[item['domain']]+=len(valid)>0
        rejected.extend({'id':item['id'],**r} for r in bad)
    audit={'generated_at':datetime.now(timezone.utc).isoformat(),'index':protocol['index_provenance'],
           'annotation_pool':len(items),'combined_items':len(combined),
           'combined_domains':dict(Counter(i['domain'] for i in combined)),
           'items_with_supported_features_by_domain':dict(status),'accepted_features':dict(accepted),
           'accepted_claims':sum(accepted.values()),'rejected_claims':rejected,'failed_batches_or_items':failed,
           'unannotated_records_due_to_missing_cache':unannotated,'model_calls':calls,
           'unannotated_records_total':sum('annotation' not in i for i in combined),
           'scope':protocol['scope'],'evaluation_note':'No held-out preference or source-label accuracy measured on this scaled bank.'}
    payload={'schema':'recros-scaled-transfer-v1','selection':protocol['scope'],'items':combined,
             'pipeline_counts':{'searchable_catalog':222896,'indexed_narrative_records':sum(protocol['index_provenance']['counts'].values()),
                                'annotation_pool':len(items),'evidence_bank':len(combined)},
             'annotation_run':{'requested_model':DEFAULT_MODEL,'scope':'Composite bank; per-batch calls retained locally.'}}
    if failed: print(json.dumps({'warning':'Failed entries remain unannotated; inspect audit.'}),flush=True)
    (LOCAL/'annotated.json').write_text(json.dumps(payload,indent=2)+'\n')
    (LOCAL/'AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
    # Publish aggregate counts only, not the licensed raw records/cache.
    public={k:v for k,v in audit.items() if k not in ('rejected_claims','model_calls')}
    public['model_call_count']=len(calls); public['rejected_claim_count']=len(rejected)
    (ROOT/'docs/milestone2/transfer/SCALE_AUDIT.json').write_text(json.dumps(public,indent=2)+'\n')
    print(json.dumps(public,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-model',action='store_true');p.add_argument('--prepare-only',action='store_true')
    args=p.parse_args()
    if args.prepare_only:
        items,protocol=prepare();print(json.dumps({'pool':len(items),'index':protocol['index_provenance']},indent=2))
    else: run(args.run_model)
