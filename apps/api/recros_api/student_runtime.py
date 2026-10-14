"""Lazy local tiny-LM inference, followed by an explicitly teacher-dependent gate."""
from copy import deepcopy
from functools import lru_cache
import time

from .transfer_engine import FEATURES,ROOT,text_hash,validate_evidence


@lru_cache(maxsize=1)
def loaded_model():
    import torch
    from recros_ml.research.tiny_student import TinyLM
    checkpoint=ROOT/'ml/artifacts/tiny_student/v2/checkpoint.pt'
    state=torch.load(checkpoint,map_location='cpu',weights_only=True)
    torch.set_num_threads(2)
    model=TinyLM(**state['config'])
    model.load_state_dict(state['state_dict']);model.eval()
    return model,state['vocab'],torch.device('cpu'),state['protocol']['parameter_count']


def interpret(items):
    from recros_ml.research.tiny_student import predict
    started=time.perf_counter()
    model,vocab,device,parameters=loaded_model()
    proposed=predict(model,items,vocab,device)
    result=deepcopy(items);counts={'proposed':0,'retained':0}
    for item,row in zip(result,proposed):
        features={f for f,bit in zip(FEATURES,row) if bit}
        valid,_=validate_evidence(item)
        claims=[c for c in valid if c['feature'] in features]
        counts['proposed']+=len(features);counts['retained']+=len(claims)
        item['annotation']={'claims':claims,'evidence_sha256':text_hash(item['evidence_text']),
                            'model':'local-tiny-lm-v2 with cached teacher evidence gate'}
    return result,{'parameter_count':parameters,'device':'cpu','wall_ms':round((time.perf_counter()-started)*1000,2),
                   'first_load_may_be_included':True,**counts}
