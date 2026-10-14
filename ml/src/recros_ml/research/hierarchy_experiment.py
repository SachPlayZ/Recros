"""Frozen structural benchmark of joint uncertainty on public LTO annotations.

This is not a human preference study. Unlisted ontology tags are treated as zero
only inside this declared closed-world benchmark, then facts are masked. The
request weights are scripted, never inferred personal preference judgments.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import random
import re
import time
import zipfile

import networkx as nx
import numpy as np
from scipy.optimize import Bounds,LinearConstraint,milp
from scipy.sparse import coo_matrix

from recros_api.hierarchy_regret import pair_gap,propagate,flat_gap,independent_utility_gap,corruption_bound

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'docs/milestone2/hierarchy'
DATA=ROOT/'apps/api/data/literary-theme-ontology/theming-v2026.04.zip'


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def blocks(text):
    for block in re.split(r'(?m)(?=^[^\n]+\n=+\n)',text):
        lines=block.splitlines()
        if len(lines)<2 or not re.fullmatch(r'=+',lines[1]):continue
        sections={};key=None
        for line in lines[2:]:
            if line.startswith(':: '):key=line[3:].strip();sections[key]=[]
            elif key and line.strip():sections[key].append(line.strip())
        yield lines[0].strip(),sections


def load_lto():
    themes={};aliases={};raw=[]
    with zipfile.ZipFile(DATA) as archive:
        for path in archive.namelist():
            if path.endswith(('/themes/primary.th.txt','/themes/timeperiod.th.txt')):
                for name,fields in blocks(archive.read(path).decode('utf-8')):
                    themes[name]=fields;aliases[name.casefold()]=name
                    for alias in fields.get('Aliases',[]):aliases[alias.casefold()]=name
        edges=[];unresolved=[]
        for child,fields in themes.items():
            for parent in fields.get('Parents',[]):
                canonical=aliases.get(parent.casefold())
                if canonical:edges.append((child,canonical))
                else:unresolved.append({'child':child,'parent':parent})
        graph=nx.DiGraph();graph.add_nodes_from(themes);graph.add_edges_from(edges)
        closures={tag:{tag}|nx.descendants(graph,tag) for tag in themes}
        unmapped=set()
        for path in archive.namelist():
            if '/notes/stories/' not in path or not path.endswith('.txt'):continue
            for name,fields in blocks(archive.read(path).decode('utf-8')):
                if not name.startswith(('movie:','novel:')):continue
                tags=set()
                for section,lines in fields.items():
                    if section not in ('Choice Themes','Major Themes','Minor Themes'):continue
                    for line in lines:
                        literal=re.split(r'\s*[\[<]',line)[0].strip()
                        tag=aliases.get(literal.casefold())
                        if tag:tags.add(tag)
                        elif '[' in line:unmapped.add(literal)
                if not tags:continue
                all_tags=set().union(*(closures[t] for t in tags))
                title=re.sub(r' \([^)]*\)$','',name.split(': ',1)[1])
                raw.append({'id':name,'title':title,'domain':'movie' if name.startswith('movie:') else 'book',
                            'tags':sorted(tags),'closure':sorted(all_tags),
                            'source_file':path.split('/notes/')[1]})
    items={r['id']:r for r in raw}
    return themes,edges,closures,list(items.values()),{'unresolved_parent_references':unresolved,'unmapped_story_terms':sorted(unmapped)}


def freeze():
    if (OUT/'protocol.json').exists():raise RuntimeError('Protocol already exists; choose a separate experiment directory for revisions.')
    themes,edges,closures,items,issues=load_lto();rng=random.Random(20261014)
    books=sorted((i for i in items if i['domain']=='book'),key=lambda i:i['id'])
    films=sorted((i for i in items if i['domain']=='movie'),key=lambda i:i['id'])
    sources=books+rng.sample(films,len(books))
    sources.sort(key=lambda i:i['id']);states=[];skipped=[]
    for source in sources:
        source_tags=set(source['closure'])
        options=[(c,p) for c,p in edges if p in source_tags and c not in source_tags]
        rng.shuffle(options);pairs=[];parents=set()
        for child,parent in options:
            if parent not in parents:pairs.append((child,parent));parents.add(parent)
            if len(pairs)==4:break
        if len(pairs)<2:skipped.append(source['id']);continue
        selected=set(x for pair in pairs for x in pair)
        # Preserve all ancestor paths; do not invent a direct implication.
        active=set().union(*(closures[t] for t in selected));names=sorted(active);index={t:n for n,t in enumerate(names)}
        active_edges=[(index[c],index[p]) for c,p in edges if c in active and p in active]
        midpoint=[0]*len(names)
        for child,parent in pairs:midpoint[index[parent]]+=2;midpoint[index[child]]-=2
        target='movie' if source['domain']=='book' else 'book'
        pool=[i for i in items if i['domain']==target and i['title'].casefold()!=source['title'].casefold()]
        # Fixed, observable source-theme retrieval; same candidates for all methods.
        def overlap(i):
            tags=set(i['closure']);return len(tags&source_tags)/max(len(tags|source_tags),1)
        candidates=sorted(pool,key=lambda i:(-overlap(i),i['id']))[:8]
        references=[[int(t in set(i['closure'])) for t in names] for i in candidates]
        for missing in (.25,.50,.75):
            observed=[[None if rng.random()<missing else x for x in row] for row in references]
            for uncertainty in (0,1):
                lo=[v-uncertainty if v else 0 for v in midpoint];hi=[v+uncertainty if v else 0 for v in midpoint]
                states.append({'id':f'{len(states):04d}','source':{k:source[k] for k in ('id','title','domain','source_file')},
                               'target_domain':target,'source_themes':source['tags'],
                               'request_pairs':[{'prefer':p,'avoid':c} for c,p in pairs],
                               'features':names,'edges':active_edges,'lower':lo,'upper':hi,'midpoint':midpoint,
                               'missing_fraction':missing,'weight_width':uncertainty,
                               'candidates':[{k:i[k] for k in ('id','title','domain','source_file')} for i in candidates],
                               'observed':observed,'reference':references})
    scales=[];scale_rng=random.Random(90210)
    for m in (32,128,512,2048):
        for replicate in range(3):
            hierarchy=[(c,scale_rng.randrange(c)) for c in range(1,m)]
            # Feasible random binary profiles on a tree.
            def reference():
                values=[scale_rng.randrange(2)]
                for c,p in hierarchy:values.append(values[p]*scale_rng.randrange(2))
                return values
            a=[None if scale_rng.random()<.8 else v for v in reference()]
            b=[None if scale_rng.random()<.8 else v for v in reference()]
            lo=[scale_rng.randint(-3,2) for _ in range(m)];hi=[l+scale_rng.randint(0,3) for l in lo]
            scales.append({'facets':m,'replicate':replicate,'edges':hierarchy,'chosen':a,'challenger':b,'lower':lo,'upper':hi})
    protocol={'version':1,'created_utc':datetime.now(timezone.utc).isoformat(),'data_source':'https://zenodo.org/records/19367236',
              'data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),'ontology_facets':len(themes),'ontology_edges':len(edges),
              'annotated_movies':len(films),'annotated_books':len(books),'unique_source_works':len(sources)-len(skipped),
              'skipped_sources':skipped,'states':len(states),'candidates_per_state':8,
              'mask_fractions':[.25,.50,.75],'weight_widths':[0,1],'random_seed':20261014,
              'primary':'Exact joint-uncertainty gap and witness agreement; paired bound slack after sound unary propagation.',
              'secondary':'Conditional bound coverage at normalized regret thresholds; runtime against a general MILP oracle.',
              'scope':'Scripted preferences and artificially masked closed-world LTO tag references. No human enjoyment, extraction correctness, or trained SLM improvement is measured.',
              'reference_rule':'Listed tags and their ancestors are 1; unlisted active tags are 0 only within this controlled structural test.',
              'scale_seed':90210,'scale_cases':len(scales),'scale_oracle_time_limit_seconds':15,
              'corruption_probe':'A declared subgenre-parent counterexample and exhaustive small-budget tests; structural implication faults only.',
              'data_issues':issues,'states_sha256':digest(states),'scales_sha256':digest(scales)}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'states.json').write_text(json.dumps(states,indent=2)+'\n');(OUT/'scales.json').write_text(json.dumps(scales,indent=2)+'\n')
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    print(json.dumps({'frozen_protocol_sha256':digest(protocol),'states':len(states),'sources':protocol['unique_source_works'],'features':len(themes),'movies':len(films),'books':len(books),'unresolved_parents':len(issues['unresolved_parent_references'])}),flush=True)


def milp_gap(chosen,challenger,lo,hi,edges,time_limit=15):
    """Independent general MILP oracle with the full binary conjunction hull."""
    m=len(lo);objective=-np.array([*lo,*lo,*[u-l for l,u in zip(lo,hi)]],dtype=float)
    lower=np.zeros(3*m);upper=np.ones(3*m)
    for j,(a,b) in enumerate(zip(challenger,chosen)):
        if a is not None:lower[j]=upper[j]=a
        if b is not None:lower[m+j]=upper[m+j]=1-b
    rows=[];cols=[];values=[];limits=[]
    def row(terms,rhs):
        n=len(limits)
        for k,v in terms:rows.append(n);cols.append(k);values.append(v)
        limits.append(rhs)
    for c,p in edges:row([(c,1),(p,-1)],0);row([(m+p,1),(m+c,-1)],0)
    for j in range(m):
        row([(2*m+j,1),(j,-1)],0);row([(2*m+j,1),(m+j,-1)],0)
        row([(j,1),(m+j,1),(2*m+j,-1)],1)
    matrix=coo_matrix((values,(rows,cols)),shape=(len(limits),3*m)).tocsc()
    result=milp(objective,integrality=np.ones(3*m),bounds=Bounds(lower,upper),
                constraints=LinearConstraint(matrix,-np.inf,np.array(limits)),
                options={'time_limit':time_limit,'mip_rel_gap':0})
    if result.status!=0:raise RuntimeError(f'MILP not optimal: {result.status}, {result.message}')
    value=-float(result.fun)-sum(lo)
    if abs(value-round(value))>1e-6:raise RuntimeError('Unexpected noninteger oracle objective.')
    return round(value)


def run(result_name=None):
    protocol=json.loads((OUT/'protocol.json').read_text());states=json.loads((OUT/'states.json').read_text());scales=json.loads((OUT/'scales.json').read_text())
    assert digest(states)==protocol['states_sha256'] and digest(scales)==protocol['scales_sha256']
    records=[];demo_candidates=[];started=time.perf_counter()
    for n,state in enumerate(states):
        rows=[propagate(x,state['edges']) for x in state['observed']];count=len(rows)
        exact=np.zeros((count,count),dtype=int);flat=exact.copy();independent=exact.copy();witnesses={};elapsed=0.
        for i in range(count):
            for j in range(count):
                if i==j:continue
                clock=time.perf_counter();gap=pair_gap(rows[i],rows[j],state['lower'],state['upper'],state['edges']);elapsed+=time.perf_counter()-clock
                exact[i,j]=gap.value;flat[i,j]=flat_gap(rows[i],rows[j],state['lower'],state['upper'])
                independent[i,j]=independent_utility_gap(rows[i],rows[j],state['lower'],state['upper'])
                assert exact[i,j]<=flat[i,j]<=independent[i,j]
                witnesses[i,j]=gap
        emax=exact.max(axis=1);fmax=flat.max(axis=1);imax=independent.max(axis=1)
        selected=int(np.argmin(emax));fs=int(np.argmin(fmax));is_=int(np.argmin(imax));challenger=int(np.argmax(exact[selected]))
        scale=sum(max(abs(l),abs(u)) for l,u in zip(state['lower'],state['upper'])) or 1
        actual=np.array(state['reference'])@np.array(state['midpoint'])
        for i in range(count):assert int(actual.max()-actual[i])<=int(emax[i])
        rec={'id':state['id'],'source_domain':state['source']['domain'],'target_domain':state['target_domain'],
             'missing_fraction':state['missing_fraction'],'weight_width':state['weight_width'],'facets':len(state['features']),
             'known_before':sum(v is not None for row in state['observed'] for v in row),'known_after':sum(v is not None for row in rows for v in row),
             'normalization':scale,'selected':selected,'flat_selected':fs,'interval_selected':is_,
             'exact_mmr':int(emax[selected]),'flat_bound_same_item':int(fmax[selected]),'interval_bound_same_item':int(imax[selected]),
             'flat_selection_coherent_regret':int(emax[fs]),'interval_selection_coherent_regret':int(emax[is_]),
             'exact_bounds':emax.tolist(),'flat_bounds':fmax.tolist(),'interval_bounds':imax.tolist(),
             'max_regret_challenger':challenger,'cut_runtime_seconds':elapsed,'cuts':count*(count-1),
             'reference_midpoint_regret':int(actual.max()-actual[selected])}
        records.append(rec)
        if fmax[selected]>emax[selected]:
            rec['illustration_witness']=asdict(witnesses.get((selected,challenger))) if selected!=challenger else None
            demo_candidates.append((int(fmax[selected]-emax[selected]),n))
        if (n+1)%24==0:print(json.dumps({'completed_states':n+1,'total':len(states)}),flush=True)
    # Select the illustrations after measurement and label this selection explicitly.
    top=sorted(demo_candidates,reverse=True)[:8]
    demos=[{'state':states[n],'result':records[n],'selection':'Post hoc largest bound-gap illustrations; not independently held-out examples.'} for _,n in top]
    timings=[];milp_failures=[]
    # Both methods get one discarded warm-up before timing. Time model construction too.
    warm=scales[0];pair_gap(warm['chosen'],warm['challenger'],warm['lower'],warm['upper'],warm['edges'])
    milp_gap(warm['chosen'],warm['challenger'],warm['lower'],warm['upper'],warm['edges'])
    for case in scales:
        args=(case['chosen'],case['challenger'],case['lower'],case['upper'],case['edges'])
        begin=time.perf_counter();gap=pair_gap(*args);cut_time=time.perf_counter()-begin
        begin=time.perf_counter();python_gap=pair_gap(*args,backend='networkx');python_time=time.perf_counter()-begin
        assert gap.value==python_gap.value
        begin=time.perf_counter()
        try:oracle=milp_gap(*args);oracle_time=time.perf_counter()-begin
        except RuntimeError as error:milp_failures.append({'facets':case['facets'],'replicate':case['replicate'],'error':str(error)});continue
        assert gap.value==oracle,(case['facets'],gap.value,oracle)
        timings.append({'facets':case['facets'],'replicate':case['replicate'],'value':gap.value,'cut_seconds':cut_time,
                        'milp_seconds':oracle_time,'networkx_seconds':python_time,'nodes':gap.graph_nodes,'edges':gap.graph_edges,'equal':True})
        print(json.dumps({'scale_facets':case['facets'],'replicate':case['replicate'],'equal':True}),flush=True)
    normalized=lambda key:[r[key]/r['normalization'] for r in records]
    coverage=[]
    for threshold in (0,.05,.10,.20,.30,.50):
        coverage.append({'threshold':threshold,'exact_count':sum(v<=threshold+1e-12 for v in normalized('exact_mmr')),
                         'flat_count_same_recommendation':sum(v<=threshold+1e-12 for v in normalized('flat_bound_same_item')),
                         'independent_count_same_recommendation':sum(v<=threshold+1e-12 for v in normalized('interval_bound_same_item'))})
    toy={'chosen':[None,None],'challenger':[0,0],'lower':[1,-1],'upper':[1,-1],'edges':[[1,0]]}
    hard=pair_gap(toy['chosen'],toy['challenger'],toy['lower'],toy['upper'],toy['edges'])
    robust=corruption_bound(toy['chosen'],toy['challenger'],toy['lower'],toy['upper'],toy['edges'],budget=1)
    result={'protocol_sha256':digest(protocol),'states':len(records),'unique_source_works':protocol['unique_source_works'],
            'exact_cut_count':sum(r['cuts'] for r in records),'bound_order_failures':0,'reference_bound_failures':0,
            'states_with_strict_hierarchy_tightening':sum(r['flat_bound_same_item']>r['exact_mmr'] for r in records),
            'mean_exact_normalized_mmr':float(np.mean(normalized('exact_mmr'))),
            'mean_flat_normalized_bound_same_item':float(np.mean(normalized('flat_bound_same_item'))),
            'mean_independent_normalized_bound_same_item':float(np.mean(normalized('interval_bound_same_item'))),
            'mean_flat_selection_coherent_regret':float(np.mean(normalized('flat_selection_coherent_regret'))),
            'mean_interval_selection_coherent_regret':float(np.mean(normalized('interval_selection_coherent_regret'))),
            'coverage':coverage,'scale_timings':timings,'milp_failures':milp_failures,
            'cut_total_seconds':sum(r['cut_runtime_seconds'] for r in records),'total_seconds':time.perf_counter()-started,
            'structural_fault_counterexample':{'assumed_hierarchy_gap':hard.value,'one_fault_upper_bound':robust['bound'],
                                              'actual_violating_labels':[0,1],'actual_gap':1},
            'scope':protocol['scope'],'demo_selection':'Post hoc largest bound-gap cases; descriptive illustrations only.'}
    result['implementation']='Native SciPy integer max flow, with NetworkX exact fallback for large capacities. Native optimization added after the initial Python-backend run; same frozen states retained.'
    suffix='-'+result_name if result_name else ''
    for name,data in [('results',result),('per_state',records),('demo',demos)]:
        path=OUT/(name+suffix+'.json')
        if path.exists():raise RuntimeError('Preserve completed runs; choose a new result name.')
        path.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','run']);parser.add_argument('--result-name');args=parser.parse_args()
    if args.result_name and not re.fullmatch(r'[a-z0-9-]+',args.result_name):parser.error('Use a simple result name.')
    freeze() if args.action=='freeze' else run(args.result_name)
