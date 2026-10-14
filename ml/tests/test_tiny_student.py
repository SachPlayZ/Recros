import pytest

torch=pytest.importorskip('torch')
from recros_ml.research.tiny_student import SPECIAL,TinyLM,feature_sequence


def test_causal_language_model_cannot_see_future_feature_answers():
    torch.manual_seed(7)
    model=TinyLM(40,dim=16,layers=1,context=20,small_initialization=True).eval()
    before=torch.tensor([[2,12,13,14,15]])
    after=torch.tensor([[2,12,13,30,31]])
    with torch.no_grad():
        assert torch.allclose(model(before)[:,:3],model(after)[:,:3],atol=1e-5)


def test_auxiliary_quote_supervision_keeps_other_criteria_unknown():
    vocab={word:n for n,word in enumerate(SPECIAL)}
    seq,target=feature_sequence({'evidence_text':'Synthetic fixture text'},vocab,[True,None,None,None])
    assert sum(y!=-100 for y in target)==1
    assert vocab['<yes>'] in target
    assert vocab['<no>'] not in target
