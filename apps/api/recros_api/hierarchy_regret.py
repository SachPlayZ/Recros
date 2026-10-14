"""Exact joint preference/label uncertainty for an implication-only facet model.

Weights are integer endpoints of independent intervals; multiply rational inputs
by a common denominator first. Labels are 0, 1, or None (unknown). A child tag
implies a parent tag. No calibrated enjoyment or semantic correctness is implied.
The reduction uses the established maximum-weight-closure/min-cut construction.
"""
from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from typing import Sequence

@dataclass(frozen=True)
class Gap:
    value: int
    chosen_labels: tuple[int, ...]
    challenger_labels: tuple[int, ...]
    weights: tuple[int, ...]
    graph_nodes: int
    graph_edges: int
    violations: int = 0
    unpenalized_value: int | None = None


def propagate(labels: Sequence[int | None], implications: Sequence[tuple[int, int]]) -> tuple[int | None, ...]:
    """Propagate only sound implications, including false-parent contraposition."""
    state=list(labels)
    if any(v not in (0, 1, None) for v in state):
        raise ValueError('Labels must be 0, 1, or unknown.')
    for child,parent in implications:
        if not (0 <= child < len(state) and 0 <= parent < len(state)):
            raise ValueError('Implication index outside the label vector.')
    changed=True
    while changed:
        changed=False
        for child,parent in implications:
            if state[child]==1:
                if state[parent]==0:raise ValueError('Inconsistent child/parent labels.')
                if state[parent] is None:state[parent]=1;changed=True
            if state[parent]==0:
                if state[child]==1:raise ValueError('Inconsistent child/parent labels.')
                if state[child] is None:state[child]=0;changed=True
    return tuple(state)


def pair_gap(chosen: Sequence[int | None], challenger: Sequence[int | None],
             lower: Sequence[int], upper: Sequence[int],
             implications: Sequence[tuple[int, int]] = (), *, _penalty: int | None = None,
             backend: str = 'native') -> Gap:
    """Maximize u(challenger)-u(chosen) over one shared weight vector.

    The two arguments denote distinct items whose unknown labels can differ.
    Never call this for an item against itself; its gap is identically zero.
    Returned witnesses attain the exact value within this declared model.
    """
    m=len(lower)
    implications=tuple(dict.fromkeys(tuple(edge) for edge in implications))
    if any(len(edge)!=2 or not all(isinstance(v,Integral) and 0<=v<m for v in edge) for edge in implications):
        raise ValueError('Implication index outside the label vector.')
    if len(upper)!=m or len(chosen)!=m or len(challenger)!=m:
        raise ValueError('Label and interval dimensions must match.')
    if any(not isinstance(v,Integral) for v in (*lower,*upper)):
        raise ValueError('Use integer-scaled rational weight endpoints.')
    lo=tuple(map(int,lower));hi=tuple(map(int,upper))
    if any(l>u for l,u in zip(lo,hi)):
        raise ValueError('Reversed preference interval.')
    if _penalty is not None and (not isinstance(_penalty,Integral) or _penalty<0):
        raise ValueError('Implication penalties must be nonnegative integers.')
    chosen=propagate(chosen,implications if _penalty is None else ())
    challenger=propagate(challenger,implications if _penalty is None else ())
    # a = challenger labels, y = 1 - chosen labels.
    # max_w w*(a-b) = l*a + l*y + (u-l)*a*y - l.
    source=3*m;sink=source+1;node_count=3*m+2
    weights={}
    for j,(l,u) in enumerate(zip(lo,hi)):
        weights[j]=l;weights[m+j]=l;weights[2*m+j]=u-l
    infinity=sum(abs(w) for w in weights.values())+2*len(implications)*(_penalty or 0)+1
    positive=0;arcs=[]
    def add_arc(a,b,capacity):
        if capacity:arcs.append((a,b,capacity))
    for node,w in weights.items():
        if w>0:add_arc(source,node,w);positive+=w
        elif w<0:add_arc(node,sink,-w)
    def force(node,value):
        if value==1:add_arc(source,node,infinity)
        elif value==0:add_arc(node,sink,infinity)
    for j in range(m):
        force(j,challenger[j]);force(m+j,None if chosen[j] is None else 1-chosen[j])
        # Positive auxiliary reward obtains a*y without any disjunction.
        add_arc(2*m+j,j,infinity);add_arc(2*m+j,m+j,infinity)
    for child,parent in implications:
        capacity=infinity if _penalty is None else int(_penalty)
        add_arc(child,parent,capacity);add_arc(m+parent,m+child,capacity)
    # C-level integer max flow avoids Python flow overhead. For large capacities,
    # fall back to Python arbitrary-precision integers rather than risk overflow.
    if backend not in ('native','networkx'):raise ValueError('Unknown max-flow backend.')
    if backend=='native' and (infinity>2**29 or any(c>2**29 for _,_,c in arcs)):
        backend='networkx'
    if backend=='native':
        import numpy as np
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import maximum_flow,breadth_first_order
        rows=[a for a,_,_ in arcs];cols=[b for _,b,_ in arcs];values=[c for _,_,c in arcs]
        capacity=coo_matrix((np.array(values,dtype=np.int64),(rows,cols)),shape=(node_count,node_count)).tocsr()
        # Multiple hard and unary arcs can share endpoints. Their sum exceeds a
        # single capacity; check this too before the bounded native computation.
        if capacity.nnz and int(capacity.data.max())>2**30:
            return pair_gap(chosen,challenger,lo,hi,implications,_penalty=_penalty,backend='networkx')
        flow=maximum_flow(capacity,source,sink,method='dinic');cut=int(flow.flow_value)
        residual=capacity-flow.flow;residual.data=(residual.data>0).astype(np.int8);residual.eliminate_zeros()
        selected=set(map(int,breadth_first_order(residual,source,directed=True,return_predecessors=False)))
        arc_count=capacity.nnz
    else:
        import networkx as nx
        graph=nx.DiGraph();graph.add_nodes_from(range(node_count))
        for a,b,c in arcs:graph.add_edge(a,b,capacity=c+graph.get_edge_data(a,b,{}).get('capacity',0))
        cut,(selected,_)=nx.minimum_cut(graph,source,sink,flow_func=nx.algorithms.flow.preflow_push)
        arc_count=graph.number_of_edges()
    value=positive-int(cut)-sum(lo)
    a=tuple(int(j in selected) for j in range(m))
    b=tuple(1-int(m+j in selected) for j in range(m))
    w=tuple(hi[j] if a[j]>b[j] else lo[j] for j in range(m))
    actual=sum(wj*(aj-bj) for wj,aj,bj in zip(w,a,b))
    violations=sum(int(a[c]>a[p])+int(b[c]>b[p]) for c,p in implications)
    assert actual-(_penalty or 0)*violations==value
    if _penalty is None:assert violations==0
    assert all(v is None or v==b[j] for j,v in enumerate(chosen))
    assert all(v is None or v==a[j] for j,v in enumerate(challenger))
    return Gap(value,b,a,w,node_count,int(arc_count),violations,actual)


def corruption_bound(chosen,challenger,lower,upper,implications=(),budget=0,penalties=None):
    """Upper-bound the gap if <=budget implications can fail across both items.

    This is a Lagrangian upper bound, not generally the exact budgeted optimum.
    It keeps observed facts fixed; it does not protect against incorrect observed
    facts or arbitrary user-model errors. The penalized witness may exceed budget.
    """
    if not isinstance(budget,Integral) or budget<0:raise ValueError('Invalid violation budget.')
    if budget==0:
        gap=pair_gap(chosen,challenger,lower,upper,implications)
        return {'bound':gap.value,'penalty':None,'witness':gap,'attained':True,'budget':0}
    m=len(lower)
    feasibility=pair_gap(chosen,challenger,[0]*m,[0]*m,implications,_penalty=1)
    if -feasibility.value>budget:raise ValueError('No label completion fits the violation budget.')
    if penalties is None:
        stop=2*sum(max(abs(l),abs(u)) for l,u in zip(lower,upper))+1
        penalties=[0];p=1
        while p<stop:penalties.append(p);p*=2
        penalties.append(stop)
    if not penalties:raise ValueError('Provide at least one nonnegative penalty.')
    candidates=[]
    for penalty in penalties:
        gap=pair_gap(chosen,challenger,lower,upper,implications,_penalty=penalty)
        candidates.append((gap.value+int(penalty)*int(budget),int(penalty),gap))
    bound,penalty,gap=min(candidates,key=lambda x:(x[0],x[1]))
    return {'bound':bound,'penalty':penalty,'witness':gap,
            'attained':gap.violations<=budget and gap.unpenalized_value==bound,'budget':int(budget)}


def flat_gap(chosen,challenger,lower,upper):
    """Common-weight baseline after unary propagation, without unknown coupling."""
    return sum(max(w*(a-b) for a in ((0,1) if av is None else (av,))
                   for b in ((0,1) if bv is None else (bv,)) for w in (l,u))
               for bv,av,l,u in zip(chosen,challenger,lower,upper))


def independent_utility_gap(chosen,challenger,lower,upper):
    """Conservative ablation: lets each item have a different weight vector."""
    return sum(max(w*a for a in ((0,1) if av is None else (av,)) for w in (l,u))
               -min(w*b for b in ((0,1) if bv is None else (bv,)) for w in (l,u))
               for bv,av,l,u in zip(chosen,challenger,lower,upper))


def recommend(labels,lower,upper,implications=()):
    """Deterministic minimax-regret selection for a finite list of distinct items."""
    if not labels:raise ValueError('At least one candidate is required.')
    states=[propagate(x,implications) for x in labels]
    regrets=[];witnesses=[]
    for i,x in enumerate(states):
        worst=0;witness=None
        for j,y in enumerate(states):
            if i==j:continue
            gap=pair_gap(x,y,lower,upper,implications)
            if gap.value>worst:worst=gap.value;witness=(j,gap)
        regrets.append(worst);witnesses.append(witness)
    selected=min(range(len(labels)),key=lambda i:(regrets[i],i))
    return {'selected':selected,'regrets':regrets,'max_regret':regrets[selected],
            'witness':witnesses[selected]}
