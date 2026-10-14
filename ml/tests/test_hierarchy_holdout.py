import numpy as np
import pandas as pd

from recros_ml.research.hierarchy_holdout import (
    background, eligible_users, fit_ease, lookup_cost, match_movies, regret_matrices,
    regret_order, split_frames,
)


def test_identity_matching_rejects_ambiguous_and_duplicate_items():
    items = [{'id':'movie: A (2000)','title':'A','domain':'movie'},
             {'id':'movie: B (2001)','title':'B','domain':'movie'},
             {'id':'movie: C (2002)','title':'C','domain':'movie'}]
    metadata = pd.DataFrame({'title':['A','B','B','C'], 'original_title':['A','B','B','C'],
                             'release_date':['2000-01-01','2001-01-01','2001-02-01','2002-01-01'],
                             'imdb_id':['tt0000001','tt0000002','tt0000003','tt0000004']})
    links = pd.DataFrame({'movieId':[10,20,30,40,41],'imdbId':[1,2,3,4,4]})
    matches, exclusions = match_movies(items,metadata,links)
    assert [m['movieId'] for m in matches] == [10]
    assert len(exclusions) == 2


def test_time_splits_and_background_do_not_use_future_or_evaluation_users():
    ratings=pd.DataFrame({'user':[1,2,1,2], 'item':[0,1,1,0],
                          'rating':[5,4,1,5], 'time':[10,20,30,40]})
    train,val,test=split_frames(ratings,20,30)
    assert train.time.max()==20 and list(val.time)==[30] and list(test.time)==[40]
    bg=background(train,2,{1})
    assert bg['counts'].tolist()==[0,1]
    assert bg['available'].tolist()==[False,True]
    ratings.loc[ratings.time>20,'rating']=0
    train2,_,_=split_frames(ratings,20,30)
    assert np.array_equal(background(train2,2,{1})['counts'],bg['counts'])


def test_ease_matches_constrained_ridge_normal_equations():
    gram=np.array([[10.,3.,2.],[3.,8.,1.],[2.,1.,6.]])
    regularization=5.; weights=fit_ease(gram,regularization)
    assert np.array_equal(np.diag(weights),np.zeros(3))
    for j in range(3):
        free=[i for i in range(3) if i!=j]
        expected=np.linalg.solve(gram[np.ix_(free,free)]+regularization*np.eye(2),gram[free,j])
        assert np.allclose(weights[free,j],expected)


def test_cohort_sampling_ignores_future_rating_values():
    history=pd.DataFrame({'user':[5]*20+[6]*20,'rating':[5]*40})
    future=pd.DataFrame({'user':[5]*5+[6]*5,'rating':[1]*10})
    before=eligible_users(history,future,'validation',128)
    future.rating=5
    assert eligible_users(history,future,'validation',128)==before
    assert before==([5],1)


def test_complete_fixed_weights_recover_ordinary_utility_ranking():
    labels=[[0,0],[1,0],[1,1]];weights=np.array([2,-3]);edges=[(1,0)]
    states,flat,exact=regret_matrices(labels,weights,weights,edges)
    assert np.array_equal(flat,exact)
    base=np.array([0,1,2])
    order,_=regret_order(exact,base,.5)
    utilities=base+.5*(np.array(labels)@weights)
    assert order==np.argsort(-utilities,kind='stable').tolist()
    zero_order,_=regret_order(exact,base,0)
    assert zero_order==[2,1,0]


def test_shared_lookup_sequence_cannot_cost_coherent_more_than_flat():
    observed=[[None,None],[0,0]];reference=np.array([[1,0],[0,0]])
    result=lookup_cost(observed,reference,np.array([1,-1]),np.array([1,-1]),[(1,0)],
                       np.array([.5,.5]),np.array([0,0]),gamma=1,threshold=.1,budget=4)
    assert result['hierarchy_certified'] and result['hierarchy_queries']==0
    assert result['flat_queries']>0
    assert result['hierarchy_queries']<=result['flat_queries']


def test_lookup_counts_uncertifiable_cases_without_false_certification():
    labels=[[0],[1]]
    result=lookup_cost(labels,np.array(labels),np.array([1]),np.array([1]),[],np.array([.5]),
                       np.array([0,0]),gamma=1,threshold=.1,budget=2)
    assert not result['flat_certified'] and not result['hierarchy_certified']
    assert result['flat_queries']==result['hierarchy_queries']==0
