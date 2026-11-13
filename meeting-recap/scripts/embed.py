#!/usr/bin/env python3
"""Speaker embeddings for diarize.py identify. Runs in the MOSS venv, not stdlib Python:
it needs speechbrain (pip-installed next to MOSS, sharing its torch).

usage: embed.py <wav> [<wav> ...]   prints {"<wav>": [192 floats], ...} as JSON

Model: speechbrain/spkrec-ecapa-voxceleb, downloaded once into ~/.local/share/moss-transcribe-diarize. Audio never
leaves the machine; only the model weights come from Hugging Face.
"""
import json, os, sys
from speechbrain.inference.speaker import EncoderClassifier

SAVE = os.path.expanduser('~/.local/share/moss-transcribe-diarize/spkrec-ecapa-voxceleb')
clf = EncoderClassifier.from_hparams(source='speechbrain/spkrec-ecapa-voxceleb', savedir=SAVE)
out = {}
for p in sys.argv[1:]:
    wav = clf.load_audio(p)   # resamples to the model's 16 kHz
    out[p] = clf.encode_batch(wav.unsqueeze(0)).squeeze().tolist()
json.dump(out, sys.stdout)
