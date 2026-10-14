import bz2

import numpy as np
import pandas as pd
import pytest

from recros_ml.research.domain_holdout import (
    BOOK_ALIASES, BOOK_EDGES, closures_for, load_song_labels,
    sample_song_users, song_targets, song_window,
)


def test_book_taxonomy_keeps_secondary_themes_separate_from_genres():
    features=set(BOOK_ALIASES)|{v for edge in BOOK_EDGES for v in edge}
    closures=closures_for(features,BOOK_EDGES)
    assert {'urban-fantasy','fantasy','speculative-fiction','fiction'}<=set(closures['urban-fantasy'])
    assert {'historical-romance','romance','historical-fiction','fiction'}<=set(closures['historical-romance'])
    assert closures['theme:magic']==['theme:magic']
    assert 'published:before2000' in closures['published:before1900']
    with pytest.raises(ValueError):closures_for(['a','b'],[('a','b'),('b','a')])


def test_song_labels_are_recording_level_and_preserve_source_hierarchy(tmp_path):
    source=tmp_path/'genres.tsv.bz2'
    with bz2.open(source,'wt') as f:
        f.write('recordingmbid\treleasegroupmbid\tgenre1\tgenre2\tgenre3\n')
        f.write('recording-A\talbum-A\trock---indie\t\t\n')
        f.write('recording-B\talbum-A\tpop\tpop---ballad\t\n')
    labels,edges,features=load_song_labels(source)
    assert labels['recording-a']=={'rock','rock---indie'}
    assert ('rock---indie','rock') in edges
    assert 'album-A' not in labels and 'genre1' not in features


def test_song_play_strength_never_uses_future_counts():
    events=pd.DataFrame({'user':[1]*5,'item':[0,0,1,0,1],'time':[1,2,3,20,30]})
    history=song_window(events,10).set_index('item')
    assert history.loc[0,'plays']==2 and history.loc[1,'plays']==1
    assert history.loc[0,'rating']==pytest.approx(4+np.log1p(2))
    mutated=pd.concat([events,pd.DataFrame({'user':[1]*100,'item':[0]*100,'time':[40]*100})])
    assert song_window(mutated,10).equals(song_window(events,10))
    assert set(song_targets(events,10,25).item)=={0}


def test_song_cohorts_require_unseen_future_recordings_in_background_catalog():
    history=pd.DataFrame({'user':[1]*20,'item':list(range(20))})
    future=pd.DataFrame({'user':[1]*6,'item':[0,20,21,22,23,24]})
    assert sample_song_users(history,future,set(range(25)),'test',320)==[1]
    assert sample_song_users(history,future,set(range(24)),'test',320)==[]
    assert sample_song_users(history,future,set(range(25)),'validation',128)==[]
