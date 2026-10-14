"""Public, read-only demonstrations of the declared hierarchical uncertainty model."""
from dataclasses import asdict
from functools import lru_cache
import json
from pathlib import Path
import time

from fastapi import APIRouter,HTTPException,Query

from .hierarchy_regret import pair_gap,propagate,corruption_bound

router=APIRouter(prefix='/api/hierarchy',tags=['hierarchy-research'])
OUT=Path(__file__).resolve().parents[3]/'docs/milestone2/hierarchy'


@lru_cache(maxsize=1)
def demos():
    path=OUT/'demo-native.json'
    if not path.exists():raise HTTPException(503,'Run the frozen hierarchy experiment first.')
    return json.loads(path.read_text())


@router.get('/summary')
def summary():
    path=OUT/'results-native.json'
    if not path.exists():raise HTTPException(503,'Experiment results are unavailable.')
    result=json.loads(path.read_text())
    return {'results':result,'cases':[{'id':d['state']['id'],'source':d['state']['source'],
                                      'target_domain':d['state']['target_domain'],
                                      'missing_fraction':d['state']['missing_fraction']} for d in demos()],
            'scope':'Controlled masks and scripted preference intervals on public LTO annotations. These are not personal recommendations or independently verified semantic labels.',
            'selection':'Cases are post hoc illustrations selected for large bound gaps.'}


@router.get('/toy')
def toy(budget:int=Query(0,ge=0,le=2)):
    chosen=[None,None];neutral=[0,0];lo=hi=[1,-1];edges=[(1,0)]
    exact=pair_gap(chosen,neutral,lo,hi,edges)
    flat=pair_gap(chosen,neutral,lo,hi)
    robust=corruption_bound(chosen,neutral,lo,hi,edges,budget)
    return {'flat_gap':flat.value,'coherent_gap':exact.value,'fault_bound':robust['bound'],
            'budget':budget,'attained':robust['attained'],'flat_witness':asdict(flat),
            'scope':'Analytical construction: prefer a broad theme (+1), avoid its subtype (-1). Candidate A unknown, B both labels absent. Utility is conditional matching, not enjoyment.'}


@router.get('/case/{case_id}')
def case(case_id:str,budget:int=Query(0,ge=0,le=2)):
    example=next((d for d in demos() if d['state']['id']==case_id),None)
    if example is None:raise HTTPException(404,'Unknown public demonstration case.')
    state=example['state'];edges=state['edges'];lo=state['lower'];hi=state['upper'];rows=state['observed']
    propagated=[propagate(x,edges) for x in rows]
    results=[];started=time.perf_counter()
    for i,row in enumerate(rows):
        exact=0;flat=0;fault=0;flat_witness=None;exact_witness=None
        for j,other in enumerate(rows):
            if i==j:continue
            hg=pair_gap(row,other,lo,hi,edges)
            fg=pair_gap(propagated[i],propagated[j],lo,hi)
            if hg.value>exact:exact=hg.value;exact_witness={'challenger':j,**asdict(hg)}
            if fg.value>flat:
                flat=fg.value
                broken=[{'child':state['features'][c],'parent':state['features'][p],'item':'chosen' if fg.chosen_labels[c]>fg.chosen_labels[p] else 'challenger'}
                        for c,p in edges if fg.chosen_labels[c]>fg.chosen_labels[p] or fg.challenger_labels[c]>fg.challenger_labels[p]]
                flat_witness={'challenger':j,**asdict(fg),'broken_hierarchy_relations':broken}
            fg_bound=hg.value if budget==0 else corruption_bound(row,other,lo,hi,edges,budget)['bound']
            fault=max(fault,fg_bound)
        results.append({**state['candidates'][i],'index':i,'exact_regret':exact,'flat_bound':flat,'fault_bound':fault,
                        'known_labels':sum(v is not None for v in rows[i]),'total_labels':len(row),
                        'flat_witness':flat_witness,'coherent_witness':exact_witness})
    selected=min(range(len(results)),key=lambda i:(results[i]['fault_bound'],i))
    return {'source':state['source'],'target_domain':state['target_domain'],'request_pairs':state['request_pairs'],
            'features':state['features'],'edges':edges,'lower':lo,'upper':hi,'observed':rows,'candidates':results,
            'selected':selected,'budget':budget,'normalization':sum(max(abs(l),abs(u)) for l,u in zip(lo,hi)) or 1,
            'runtime_ms':1000*(time.perf_counter()-started),
            'scope':'Public LTO reference annotations, closed-world active-tag references, artificial masking and scripted preferences. No satisfaction claim.',
            'selection':example['selection']}
