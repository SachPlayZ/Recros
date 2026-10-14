# Tiny local language-model experiment

October 14, 2026. This is an actual trained causal language model, distinct from
the repository's original nineteen-feature LightGBM classifier.

The model has **562,464 trainable parameters**: two causal transformer layers,
width 96, four attention heads, context length 192 and a capped word vocabulary.
Token embeddings and output weights are tied. We trained random initial weights
on this Mac CPU; no pretrained weights or Ollama model was downloaded. PyTorch
is a software dependency, not a downloaded pretrained model.

Version 2 used 4,000 local movie/book summaries for next-token pretraining, then
135 teacher-labelled training records and 33 validation records for constrained
yes/no next-token feature generation. Positive quotation fragments supplied an
auxiliary objective with other features masked as unknown. Normalized titles
separate training and validation groups, and the eighteen evaluation titles were
excluded from training and vocabulary preparation. Training took approximately
115 seconds. The validation-selected checkpoint is step 700.

| Interpretation on eighteen development passages | TP | FP | FN | F1 |
|---|---:|---:|---:|---:|
| TF-IDF logistic student | 2 | 0 | 23 | 0.148 |
| Tiny causal LM v2 | 3 | 8 | 22 | 0.167 |
| DeepSeek teacher | 21 | 0 | 4 | 0.913 |
| Tiny LM intersected with cached teacher claims | 3 | 0 | 22 | 0.214 |

The references were authored by the Codex assistant. Version 1 reached F1 0.211;
v2 did not improve that development outcome. Inspecting these results influenced
development, so they are not independent held-out accuracy. Neither the training
volume nor pretraining resources are matched to the hosted teacher. Music was
not in training. See [label provenance](LABEL_PROVENANCE.md).

The subsequent [human reading pilot](HUMAN_READING_PILOT.md) matched zero of seven
positive labels for this student, compared with six for DeepSeek. The filtered
student retained zero positives. The conclusion is a failed compact-extraction
trial, with a working implementation and reproducible evidence, rather than a
successful large-model replacement.

`/explore` can now load the saved v2 checkpoint and run CPU inference on the fixed
shortlist. Its displayed evidence is the intersection of local proposals and
cached teacher claims. This requires teacher evidence and is not independent
verification. A runtime example can work on bank records related to training;
that does not overturn the evaluation failure. DeepSeek remains the default.

Checkpoint: `ml/artifacts/tiny_student/v2/checkpoint.pt` (local, ignored by Git).
SHA-256: `8c67d01e2aa65fa12f9f557816354a2a9f124c912c333111819a783885b7dcb7`.
Results and protocol: `student/v2/results.json` and `student/v2/protocol.json`.
The checkpoint loads with `weights_only=True`; two contract tests verify causal
attention and masking of unknown auxiliary labels.

To reproduce v2 training, inspect `tiny_student.py --help` and the frozen protocol.
To run the saved checkpoint, install `ml/requirements.student.txt` in the research
environment and use `/explore`'s experimental local-model selection. No training
or hosted call is required during presentation.
