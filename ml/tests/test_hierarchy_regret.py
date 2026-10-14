from itertools import product
import random

import pytest

from recros_api.hierarchy_regret import pair_gap,propagate,flat_gap,recommend,corruption_bound


def completions(state,edges):
    for x in product((0,1),repeat=len(state)):
        if all(v is None or x[j]==v for j,v in enumerate(state)) and all(x[c]<=x[p] for c,p in edges):
            yield x


def exhaustive(chosen,challenger,lo,hi,edges):
    return max(sum((u if a>b else l)*(a-b) for a,b,l,u in zip(y,x,lo,hi))
               for x in completions(chosen,edges) for y in completions(challenger,edges))


def test_graph_cut_matches_exhaustive_signed_joint_uncertainty():
    rng=random.Random(731)
    for _ in range(240):
        m=rng.randint(1,5)
        edges=[(c,p) for c in range(m) for p in range(c) if rng.random()<.35]
        all_x=list(completions([None]*m,edges))
        x=rng.choice(all_x);y=rng.choice(all_x)
        a=[None if rng.random()<.7 else v for v in x]
        b=[None if rng.random()<.7 else v for v in y]
        lo=[rng.randint(-3,2) for _ in range(m)];hi=[l+rng.randint(0,3) for l in lo]
        gap=pair_gap(a,b,lo,hi,edges)
        assert gap.value==exhaustive(a,b,lo,hi,edges)
        assert gap.value==pair_gap(a,b,lo,hi,edges,backend='networkx').value
        assert gap.value<=flat_gap(propagate(a,edges),propagate(b,edges),lo,hi)
        assert sum(w*(v-u) for w,u,v in zip(gap.weights,gap.chosen_labels,gap.challenger_labels))==gap.value


def test_hierarchy_eliminates_an_impossible_negative_utility_world():
    # Broad genre +1, avoided subgenre -1; subgenre implies broad genre.
    edges=[(1,0)];unknown=[None,None];neutral=[0,0]
    assert flat_gap(unknown,neutral,[1,-1],[1,-1])==1
    assert pair_gap(unknown,neutral,[1,-1],[1,-1],edges).value==0
    assert recommend([unknown,neutral],[1,-1],[1,-1],edges)['max_regret']==0


def test_same_shared_weights_cancel_identical_complete_profiles():
    assert pair_gap([1,0],[1,0],[-2,-3],[5,4]).value==0


def test_self_regret_is_zero_even_if_all_labels_unknown():
    r=recommend([[None,None]],[-3,-2],[4,5],[(1,0)])
    assert r['max_regret']==0 and r['witness'] is None


def test_contradictory_labels_and_invalid_weight_models_fail():
    with pytest.raises(ValueError,match='Inconsistent'):pair_gap([0,1],[None,None],[1,1],[2,2],[(1,0)])
    with pytest.raises(ValueError,match='Reversed'):pair_gap([0],[1],[2],[1])
    with pytest.raises(ValueError,match='integer'):pair_gap([0],[1],[0.1],[0.2])


def test_known_propagation_and_cycles_do_not_invent_child_truth():
    assert propagate([1,None],[(1,0)])==(1,None)
    assert propagate([0,None],[(1,0)])==(0,0)
    assert propagate([None,1],[(1,0)])==(1,1)
    assert pair_gap([None,None],[None,None],[1,-2],[3,-1],[(0,1),(1,0)]).value==2


def test_structural_fault_budget_prevents_false_zero_regret_certificate():
    edges=[(1,0)];unknown=[None,None];neutral=[0,0];lo=hi=[1,-1]
    assert pair_gap(unknown,neutral,lo,hi,edges).value==0
    actual_bad_labels=[0,1]
    actual_gap=-sum(w*x for w,x in zip(lo,actual_bad_labels))
    bound=corruption_bound(unknown,neutral,lo,hi,edges,budget=1)
    assert actual_gap==1 and bound['bound']==1 and bound['attained']


def test_fault_bounds_cover_exhaustive_budgeted_worlds():
    rng=random.Random(113)
    for _ in range(90):
        m=rng.randint(1,4);edges=[(c,p) for c in range(m) for p in range(c) if rng.random()<.4]
        x=rng.choice(list(completions([None]*m,edges)));y=rng.choice(list(completions([None]*m,edges)))
        a=[None if rng.random()<.7 else v for v in x];b=[None if rng.random()<.7 else v for v in y]
        lo=[rng.randint(-3,2) for _ in range(m)];hi=[l+rng.randint(0,3) for l in lo];budget=rng.randint(1,3)
        values=[]
        for xc in completions(a,[]):
            for yc in completions(b,[]):
                violations=sum(int(xc[c]>xc[p])+int(yc[c]>yc[p]) for c,p in edges)
                if violations<=budget:values.append(sum((u if v>x else l)*(v-x) for x,v,l,u in zip(xc,yc,lo,hi)))
        result=corruption_bound(a,b,lo,hi,edges,budget)
        assert result['bound']>=max(values)
        if result['attained']:assert result['bound']==max(values)


def test_fault_budget_rejects_infeasible_fixed_observations():
    with pytest.raises(ValueError,match='No label completion'):
        corruption_bound([0,1,0,1],[0,0,0,0],[1]*4,[1]*4,[(1,0),(3,2)],budget=1)


def test_large_integer_endpoints_use_exact_fallback():
    huge=2**60
    assert pair_gap([None,None],[None,None],[huge,-huge],[huge,-huge],[(1,0)]).value==huge


def test_repeated_edges_do_not_count_as_multiple_structural_faults():
    result=corruption_bound([0,1],[0,0],[1,-1],[1,-1],[(1,0),(1,0)],budget=1)
    assert result['bound']==1 and result['attained'] and result['witness'].violations==1
