"""Tiny causal language-model experiment trained locally from random weights.

Summary next-token pretraining, then constrained yes/no next-token feature
generation distilled from cached teacher annotations. Narrow task, small data.
No pretrained weights or independent user-preference labels are used.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import sqlite3
import time

import numpy as np
import torch
from torch import nn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier

from recros_api.transfer_engine import FEATURES, ROOT, text_hash, validate_evidence

OUT=ROOT/'docs/milestone2/transfer/student'
ARTIFACT=ROOT/'ml/artifacts/tiny_student'
LOCAL=ROOT/'apps/api/data/scaled-transfer'
SPECIAL=['<pad>','<unk>','<bos>','<sep>','<eos>']+['<'+f+'>' for f in FEATURES]+['<yes>','<no>']


def normalize_title(title):
    return re.sub(r'[^\w]','',title.casefold())


def words(text):
    return re.findall(r'\w+|[^\w\s]',text.casefold())


class TinyLM(nn.Module):
    def __init__(self,vocab_size,dim=96,layers=2,context=192,small_initialization=False):
        super().__init__();self.context=context
        self.embedding=nn.Embedding(vocab_size,dim);self.position=nn.Embedding(context,dim)
        layer=nn.TransformerEncoderLayer(dim,4,dim*2,dropout=.1,activation='gelu',batch_first=True,norm_first=True)
        self.transformer=nn.TransformerEncoder(layer,layers,enable_nested_tensor=False)
        self.norm=nn.LayerNorm(dim);self.output=nn.Linear(dim,vocab_size,bias=False)
        self.output.weight=self.embedding.weight
        if small_initialization:
            nn.init.normal_(self.embedding.weight,mean=0,std=.02)
            nn.init.normal_(self.position.weight,mean=0,std=.02)

    def forward(self,x):
        n=x.shape[1]
        embedded=self.embedding(x)+self.position(torch.arange(n,device=x.device))[None,:,:]
        causal=torch.triu(torch.ones(n,n,device=x.device,dtype=torch.bool),diagonal=1)
        return self.output(self.norm(self.transformer(embedded,mask=causal,src_key_padding_mask=x==0)))


def tensor_batch(sequences,targets,device):
    size=max(len(s) for s in sequences)
    x=torch.zeros(len(sequences),size,dtype=torch.long)
    y=torch.full_like(x,-100)
    for n,(seq,label) in enumerate(zip(sequences,targets)):
        x[n,:len(seq)]=torch.tensor(seq);y[n,:len(label)]=torch.tensor(label)
    return x.to(device),y.to(device)


def feature_sequence(record,vocab,labels):
    ids=[vocab.get(w,1) for w in words(record['evidence_text'])][:120]
    seq=[vocab['<bos>']]+ids+[vocab['<sep>']];target=[-100]*len(seq)
    for feature,positive in zip(FEATURES,labels):
        seq.append(vocab['<'+feature+'>']);target.append(-100 if positive is None else vocab['<yes>'] if positive else vocab['<no>'])
        seq.append(vocab['<unk>'] if positive is None else vocab['<yes>'] if positive else vocab['<no>']);target.append(-100)
    return seq,target


@torch.no_grad()
def predict(model,records,vocab,device):
    model.eval();predictions=[]
    yes,no=vocab['<yes>'],vocab['<no>']
    for record in records:
        seq=[vocab['<bos>']]+[vocab.get(w,1) for w in words(record['evidence_text'])][:120]+[vocab['<sep>']]
        row=[]
        for f in FEATURES:
            seq.append(vocab['<'+f+'>'])
            logits=model(torch.tensor([seq],device=device))[0,-1,[no,yes]]
            positive=bool(logits.argmax().item());row.append(int(positive));seq.append(yes if positive else no)
        predictions.append(row)
    return np.array(predictions,dtype=int)


def metrics(actual,pred):
    tp=int(((actual==1)&(pred==1)).sum());fp=int(((actual==0)&(pred==1)).sum());fn=int(((actual==1)&(pred==0)).sum())
    precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
    return {'tp':tp,'fp':fp,'fn':fn,'precision':precision,'recall':recall,
            'micro_f1':2*precision*recall/(precision+recall) if precision+recall else 0}


def main(version='v1'):
    global OUT,ARTIFACT
    if version not in ('v1','v2'):raise ValueError('Unknown experiment version.')
    if version=='v2':OUT=OUT/'v2';ARTIFACT=ARTIFACT/'v2'
    OUT.mkdir(parents=True,exist_ok=True);ARTIFACT.mkdir(parents=True,exist_ok=True)
    if (OUT/'results.json').exists():
        raise ValueError('Student result already exists. Preserve it and use a new version for another run.')
    seed=20261014;random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.set_num_threads(2)
    device=torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    bank=json.loads((LOCAL/'annotated.json').read_text())
    evaluation=json.loads((ROOT/'demo/transfer/sources.json').read_text())['items']
    gold=json.loads((ROOT/'docs/milestone2/transfer/source_labels.json').read_text())
    excluded_titles={normalize_title(i['title']) for i in evaluation}
    pool=[i for i in bank['items'] if i.get('source_kind')=='recovered dataset summary'
          and 'annotation' in i and normalize_title(i['title']) not in excluded_titles]
    split_key=lambda i:normalize_title(i['title']) if version=='v2' else i['id']
    train=[i for i in pool if int(hashlib.sha256(split_key(i).encode()).hexdigest()[:8],16)%5!=0]
    validation=[i for i in pool if i not in train]
    if not train or not validation: raise ValueError('Need nonempty identity-separated splits.')
    val_ids={i['id'] for i in validation}
    excluded_pretrain_titles=excluded_titles|{normalize_title(i['title']) for i in validation}
    with sqlite3.connect(LOCAL/'narrative-catalog.db') as c:
        c.row_factory=sqlite3.Row
        corpus=[]
        for domain in ('movie','book'):
            rows=[dict(r) for r in c.execute('SELECT id,title,evidence_text FROM documents WHERE domain=?',(domain,))
                  if r['id'] not in val_ids and normalize_title(r['title']) not in excluded_pretrain_titles]
            random.shuffle(rows);corpus.extend(rows[:2000])
    # Neither validation-source texts nor evaluation works build the vocabulary.
    counts=Counter(w for r in corpus for w in words(r['evidence_text']))
    vocabulary=SPECIAL+[w for w,_ in counts.most_common(4096) if w not in SPECIAL]
    vocab={w:n for n,w in enumerate(vocabulary)}
    encoded=[[vocab['<bos>']]+[vocab.get(w,1) for w in words(r['evidence_text'])]+[vocab['<eos>']] for r in corpus]
    labels=lambda rows:np.array([[int(f in {v['feature'] for v in validate_evidence(i)[0]}) for f in FEATURES] for i in rows])
    y_train=labels(train);y_val=labels(validation)
    y_test=np.array([[int(f in gold['positive_labels'][i['id']]) for f in FEATURES] for i in evaluation])
    model=TinyLM(len(vocab),small_initialization=version=='v2').to(device)
    parameter_count=sum(p.numel() for p in model.parameters())
    protocol={'seed':seed,'architecture':'2-layer causal transformer, width 96, 4 attention heads, tied token embedding/output weights',
              'parameter_count':parameter_count,'vocabulary_size':len(vocab),'context':192,
              'initialization':'Random, no pretrained model weights downloaded.',
              'version':version,
              'pretraining_source_count':len(corpus),'pretraining_max_steps':1500 if version=='v2' else 300,'pretraining_wall_limit_seconds':240,
              'fine_tuning_max_steps':3000 if version=='v2' else 500,'fine_tuning_wall_limit_seconds':600,'batch_size':16,
              'split_unit':'Normalized work title' if version=='v2' else 'Source record ID',
              'embedding_initialization_std':.02 if version=='v2' else 1.,
              'augmentation':'Positive teacher quotation fragments; other feature targets masked as unknown.' if version=='v2' else 'None',
              'development_history':'v2 follows an inspected v1 result; these eighteen evaluation passages are development data, not a pristine independent test.' if version=='v2' else 'Initial exploratory run.',
              'train_ids':[i['id'] for i in train],'validation_ids':[i['id'] for i in validation],
              'evaluation_ids':[i['id'] for i in evaluation],'excluded_evaluation_title_keys':sorted(excluded_titles),
              'teacher_target':'Presence of provenance-accepted teacher claims, not absence of traits in complete works.',
              'fine_tuning':'Constrained yes/no next-token generation for each feature. Validation teacher-label F1 selects the checkpoint.',
              'evaluation':'The existing 18 development passages and single-analyst source labels. These texts/works are excluded from student training; the research team has already inspected them.',
              'scope':'Exploratory tiny task language model; no independently measured user utility or general-purpose SLM capability.',
              'device':str(device),'torch_version':torch.__version__,
              'teacher_bank_sha256':hashlib.sha256((LOCAL/'annotated.json').read_bytes()).hexdigest()}
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    optimizer=torch.optim.AdamW(model.parameters(),lr=.0008,weight_decay=.01)
    start=time.monotonic();phase_start=start;pre_losses=[];pre_steps=0
    model.train()
    for step in range(protocol['pretraining_max_steps']):
        if time.monotonic()-phase_start>protocol['pretraining_wall_limit_seconds']:break
        sequences=[];targets=[]
        for _ in range(16):
            doc=random.choice(encoded);offset=random.randrange(max(1,len(doc)-127));seq=doc[offset:offset+129]
            sequences.append(seq[:-1]);targets.append(seq[1:])
        x,y=tensor_batch(sequences,targets,device)
        loss=nn.functional.cross_entropy(model(x).reshape(-1,len(vocab)),y.reshape(-1),ignore_index=-100)
        optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step()
        pre_losses.append(float(loss.item()));pre_steps=step+1
        if step%50==0:print(json.dumps({'phase':'summary_language_pretraining','step':step,'loss':pre_losses[-1],'seconds':round(time.monotonic()-start,1)}),flush=True)
    pre_duration=time.monotonic()-phase_start
    optimizer=torch.optim.AdamW(model.parameters(),lr=.0003,weight_decay=.01)
    ft=[feature_sequence(r,vocab,label) for r,label in zip(train,y_train)]
    auxiliary=[]
    if version=='v2':
        for record in train:
            for claim in validate_evidence(record)[0]:
                target=[True if f==claim['feature'] else None for f in FEATURES]
                auxiliary.append(feature_sequence({'evidence_text':claim['quote']},vocab,target))
    best=-1;best_state=None;best_step=0;history=[];ft_steps=0;phase_start=time.monotonic()
    for step in range(protocol['fine_tuning_max_steps']):
        if time.monotonic()-phase_start>protocol['fine_tuning_wall_limit_seconds']:break
        model.train();batch=random.choices(ft,k=12)+random.choices(auxiliary,k=4) if auxiliary else random.choices(ft,k=16)
        x,y=tensor_batch([r[0] for r in batch],[r[1] for r in batch],device)
        logits=model(x);mask=y!=-100
        # The feature query is a token, and its following yes/no token is the
        # constrained continuation. No new classification head is introduced.
        target=(y[mask]==vocab['<yes>']).long()
        loss=nn.functional.cross_entropy(logits[mask][:,[vocab['<no>'],vocab['<yes>']]],target,
                                         weight=torch.tensor([1.,2.],device=device))
        optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step();ft_steps=step+1
        if step%(100 if version=='v2' else 50)==0 or step==protocol['fine_tuning_max_steps']-1:
            val=metrics(y_val,predict(model,validation,vocab,device));history.append({'step':step,'validation_teacher_f1':val['micro_f1'],'loss':float(loss.item())})
            print(json.dumps({'phase':'feature_generation','step':step,'validation_teacher_f1':val['micro_f1'],'seconds':round(time.monotonic()-start,1)}),flush=True)
            if val['micro_f1']>best:
                best=val['micro_f1'];best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()};best_step=step
    if best_state is None:raise RuntimeError('Fine tuning ended before a validation checkpoint.')
    model.load_state_dict(best_state);model.eval()
    inference_start=time.monotonic();pred=predict(model,evaluation,vocab,device);inference_seconds=time.monotonic()-inference_start
    # A cheap learned text baseline receives precisely the same train labels.
    vectorizer=TfidfVectorizer(ngram_range=(1,2),max_features=10000,min_df=1)
    linear=OneVsRestClassifier(LogisticRegression(C=1,class_weight='balanced',max_iter=1000))
    linear.fit(vectorizer.fit_transform(r['evidence_text'] for r in train),y_train)
    linear_pred=linear.predict(vectorizer.transform(r['evidence_text'] for r in evaluation))
    teacher=json.loads((ROOT/'demo/transfer/annotated.json').read_text())['items']
    teacher_by_id={i['id']:i for i in teacher}
    teacher_pred=labels([teacher_by_id[i['id']] for i in evaluation])
    results={'parameter_count':parameter_count,'device':str(device),'pretraining_steps':pre_steps,'pretraining_seconds':pre_duration,
             'pretraining_final_mean_loss':sum(pre_losses[-20:])/len(pre_losses[-20:]),
             'fine_tuning_steps':ft_steps,'fine_tuning_best_step':best_step,'validation_teacher_f1':best,
             'training_wall_seconds':time.monotonic()-start,'train_records':len(train),'validation_records':len(validation),
             'evaluation_records':len(evaluation),'evaluation_feature_decisions':len(evaluation)*len(FEATURES),
             'evaluation':{'tiny_causal_lm':metrics(y_test,pred),'tfidf_logistic_student':metrics(y_test,linear_pred),
                           'deepseek_teacher':metrics(y_test,teacher_pred)},
             'student_inference_seconds_for_18_records':inference_seconds,
             'by_domain':{d:metrics(y_test[[i['domain']==d for i in evaluation]],pred[[i['domain']==d for i in evaluation]]) for d in ('movie','book','music')},
             'predictions':[{'id':i['id'],'predicted_features':[f for f,b in zip(FEATURES,row) if b],
                             'source_label_features':gold['positive_labels'][i['id']]} for i,row in zip(evaluation,pred)],
             'validation_history':history,'scope':protocol['scope'],
             'limitations':['Small, query-selected, noisy teacher data.','Source-reading labels from one analyst; evaluation sample already used in development.',
                            'Movie/book student training, music transfer untrained.','No subjective experience or preference gain measured.']}
    torch.save({'state_dict':best_state,'vocab':vocab,'config':{'vocab_size':len(vocab),'dim':96,'layers':2,'context':192},'protocol':protocol},ARTIFACT/'checkpoint.pt')
    (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    # Offline student interpretation, with cached teacher passages as a separate
    # evidence gate. This cannot independently annotate an unseen new work.
    bank_pred=predict(model,bank['items'],vocab,device)
    gated=deepcopy(bank);kept=0;proposed=0
    for i,row in zip(gated['items'],bank_pred):
        requested={f for f,b in zip(FEATURES,row) if b};proposed+=len(requested)
        valid,_=validate_evidence(i);claims=[c for c in valid if c['feature'] in requested]
        kept+=len(claims)
        i['student_predicted_features']=sorted(requested)
        i['annotation']={'claims':claims,'evidence_sha256':text_hash(i['evidence_text']),'model':'local-tiny-causal-lm + cached teacher evidence gate'}
    gated['annotation_run']={'requested_model':'local-tiny-causal-lm-'+version,'parameter_count':parameter_count,
                             'scope':'Student feature proposals intersected with cached teacher source claims. Not independent quote generation.'}
    gated['student_gate']={'proposed_feature_count':proposed,'supported_by_cached_teacher_count':kept}
    (LOCAL/'student.annotated.json').write_text(json.dumps(gated,indent=2)+'\n')
    print(json.dumps({k:results[k] for k in ('parameter_count','device','train_records','validation_records','evaluation','training_wall_seconds')},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',default='v1',choices=['v1','v2'])
    main(parser.parse_args().version)
