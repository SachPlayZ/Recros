from recros_api.bridges import description_hash
from recros_api.contrast_audit import audit


def inputs():
    items=[{'id':str(i),'domain':'music','title':str(i),'description':'','genres':'',
            'identity_status':'matched','preference_label':label}
           for i,label in enumerate(('like','like','dislike'))]
    return {'items':items},{'items':items}


def test_identical_representation_opposite_labels_has_unavoidable_error():
    p,c=inputs(); a=audit(p,c)
    for view in a['representations'].values():
        assert view['unavoidable_label_errors']==1
        assert view['conflicts'][0]['positive_ids']==['0','1']
        assert view['conflicts'][0]['negative_ids']==['2']
    # Exhaust all possible constant binary classifiers on this one feature vector.
    assert min(sum(pred!=(r['preference_label']=='like') for r in p['items']) for pred in (False,True))==1


def test_pending_identity_is_excluded_instead_of_silently_confirmed():
    p,c=inputs(); p['items'][-1]['identity_status']='pending'
    a=audit(p,c)
    assert a['pending_identity_ids']==['2']
    assert a['representations']['domain_and_concepts']['unavoidable_label_errors']==0
    assert a['representations']['domain_and_concepts']['observed_records']==2


def test_supported_feature_can_resolve_collision_but_stale_annotation_cannot():
    p,c=inputs(); item=c['items'][-1]
    item['description']='A friendship survives many tests.'
    item['annotation']={'description_sha256':description_hash(item['description']),
                         'facets':[{'concept':'friendship','quote':'A friendship survives'}]}
    a=audit(p,c)
    assert a['representations']['domain_only']['unavoidable_label_errors']==1
    assert a['representations']['domain_and_concepts']['unavoidable_label_errors']==0
    item['description']='Now the source has changed.'
    assert audit(p,c)['representations']['domain_and_concepts']['unavoidable_label_errors']==1


def test_changed_profile_description_cannot_reuse_old_cached_evidence():
    from copy import deepcopy
    p,c=inputs()
    c=deepcopy(c)
    c['items'][-1]['description']='A friendship survives many tests.'
    c['items'][-1]['annotation']={'description_sha256':description_hash(c['items'][-1]['description']),
                                 'facets':[{'concept':'friendship','quote':'A friendship survives'}]}
    assert audit(p,c)['representations']['domain_and_concepts']['unavoidable_label_errors']==1


def test_creator_conflict_needs_resolved_nonempty_same_domain_creator():
    p,c=inputs()
    p['items'][0]['creators']='Synthetic Artist'
    p['items'][2]['creators']='synthetic artist'
    assert len(audit(p,c)['same_creator_with_opposite_labels'])==1
    p['items'][2]['identity_status']='pending'
    assert audit(p,c)['same_creator_with_opposite_labels']==[]
    p['items'][2]['identity_status']='matched'
    p['items'][2]['domain']='book'
    assert audit(p,c)['same_creator_with_opposite_labels']==[]
