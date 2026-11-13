#!/usr/bin/env python3
"""Speaker-attributed transcript of a meeting recording, from a local MOSS-Transcribe-Diarize model.

Run every subcommand from the meeting's run directory (e.g. Output/Meetings/20261009_Kickoff/).
Per-meeting settings live in ./meeting.json:

  {"cast": ["Ana", "Ben", "Chen"],              names exactly as they should appear
   "anchors": ["my team", "I joined"],          extra phrases that identify a speaker
   "hotwords": ["Zephyr", "RTK"],               domain terms the model should spell right
   "speakers": {"S01": "Ana"},                  MOSS label -> name; written by the agent after the user confirms
   "fixes": [["\\\\bclock code\\\\b", "Claude Code"]],   regex mishearings seen in THIS recording
   "overrides": [[444.0, 462.0, "Chen", "why the words settle it"]]}

Pipeline (see references/diarization.md for when and why):
  prep <recording> [--chunk N]   16 kHz mono mp3 + chunks/c<offset>.mp3 (N s each, 1800 by default)
  transcribe [--only c0,...]     MOSS pass per chunk, resumable      -> moss/c<offset>.json
  anchors                        dump the transcript, <<< marks segments that name someone
  runs [--names S01,S02]         talk time per label + clean 3-10 s runs, to pick clips from
  clip <name> <start>            cut an enrolment clip               -> refs/<name>/<h-mm-ss>.wav
  identify                       propose names by voice (SpeechBrain) -> identify.json
  name <out.md>                  apply speakers and overrides        -> <out>.md + <out>.json
  fix <in.md> <out.md>           apply meeting.json fixes (free to re-run)
  spotcheck <out.md> <h:mm:ss-h:mm:ss[@label]> ...   re-transcribe a window to settle disputed words

Labels are S01, S02, ... for one chunk and c<offset>-S01 for several: a label is only consistent
within one request. Environment: MOSS_VENV (bin/mtd-subtitle, bin/python), MOSS_MODEL, MOSS_DEVICE,
MOSS_VLLM_URL. Needs ffmpeg/ffprobe on PATH. Stdlib only; the model and embed.py run in the MOSS venv.
"""
import argparse, glob, json, math, os, platform, re, shutil, subprocess, sys, tempfile, time
from collections import Counter, defaultdict

DEFAULT_PROMPT = ("Transcribe the audio. For each segment, start with the timestamp and speaker ID "
                  "([S01], [S02], [S03], ...), then the spoken text, and end with the segment timestamp.")
DEFAULT_VENV = '~/.local/share/moss-transcribe-diarize/repo/.venv'
DEFAULT_MODEL = 'OpenMOSS-Team/MOSS-Transcribe-Diarize'
MAX_TOKENS = 65536
CHUNK = 1800       # one 66-min pass stopped mid-word at 0:47 (context, not tokens); 30 min fits with room
AUDIO = 'audio-16k.mp3'
UNATTR = 'Unattributed'
THRESHOLD, MARGIN, AGREE = 0.45, 0.10, 0.75   # cosine; calibrated on real meetings, not derived
MIN_TALK, MIN_SEG, MAX_CLIP, BINS = 6.0, 2.0, 10.0, 12
EPS = 1e-9   # 0.60 - 0.50 is 0.0999..., which must still meet a 0.10 margin


# ---------- helpers ----------

def config():
    try:
        return json.load(open('meeting.json'))
    except FileNotFoundError:
        sys.exit('meeting.json not found: run from the meeting run directory')


def ts(x):
    return f"{int(x)//3600}:{int(x)//60 % 60:02d}:{int(x) % 60:02d}"


def secs(t):
    parts = [float(p) for p in t.split(':')]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def offset(path):
    return int(re.search(r'c(\d+)\.', os.path.basename(path)).group(1))


def ffmpeg(*args):
    try:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)
    except FileNotFoundError:
        sys.exit('ffmpeg not found on PATH')
    except subprocess.CalledProcessError:
        sys.exit(f"ffmpeg failed: ffmpeg {' '.join(args)}")


def duration(path):
    try:
        return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                                     path], capture_output=True, text=True, check=True).stdout)
    except FileNotFoundError:
        sys.exit('ffprobe not found on PATH')
    except (subprocess.CalledProcessError, ValueError):
        sys.exit(f'ffprobe could not read the duration of {path}')


def need_audio():
    if not os.path.exists(AUDIO):
        sys.exit(f'{AUDIO} not found: run prep from the meeting run directory first')


# ---------- MOSS ----------

def venv_bin(name):
    path = os.path.join(os.path.abspath(os.path.expanduser(os.environ.get('MOSS_VENV') or DEFAULT_VENV)), 'bin', name)
    if not os.path.exists(path):
        sys.exit(f'{path} not found: install MOSS-Transcribe-Diarize there or point MOSS_VENV at its venv')
    return path


def device():
    return os.environ.get('MOSS_DEVICE') or ('mps' if sys.platform == 'darwin' and platform.machine() == 'arm64' else 'auto')


def mtd_cmd(audio, out_dir, prompt, max_tokens):
    dev = device()
    cmd = [venv_bin('mtd-subtitle'), audio, '--model', os.environ.get('MOSS_MODEL') or DEFAULT_MODEL, '--device', dev,
           '--dtype', 'fp32' if dev == 'cpu' else 'bf16', '--max-new-tokens', str(max_tokens), '--prompt', prompt,
           '--out-dir', out_dir]
    if os.environ.get('MOSS_VLLM_URL'):
        cmd += ['--backend', 'vllm', '--vllm-base-url', os.environ['MOSS_VLLM_URL']]
    return cmd


def build_prompt(cfg):
    words = list(cfg.get('hotwords', [])) + list(cfg.get('cast', []))
    return DEFAULT_PROMPT + (' Hotwords: ' + ', '.join(words) if words else '')


def valid(s):
    sp = s.get('speaker') if isinstance(s, dict) else None
    return (isinstance(sp, str) and re.fullmatch(r'[\w-]+', sp) is not None and isinstance(s.get('text'), str)
            and all(isinstance(s.get(k), (int, float)) for k in ('start', 'end')) and s['start'] <= s['end'])


def read_result(path, dur):
    """(segments, '') or (None, why). The CLI writes whatever it parsed, so a token-limited run
    looks like success with the end of the meeting missing: the segments must reach the audio's end."""
    try:
        segs = json.load(open(path))
    except (OSError, ValueError) as e:
        return None, f'{path}: unreadable ({e})'
    if not isinstance(segs, list) or not all(valid(s) for s in segs):
        return None, f'{path}: not a list of segments with id/start/end/speaker/text'
    if not segs:
        return None, f'{path}: holds no segments'
    end, tol = max(s['end'] for s in segs), max(60, 0.05 * dur)
    if end < dur - tol:
        return None, f'truncated: ends at {ts(end)} of {ts(dur)}; raise --max-new-tokens or re-prep with --chunk'
    if end > dur + tol:
        return None, f'timestamps run past the audio: last segment ends at {ts(end)} of {ts(dur)}'
    return segs, ''


def run_mtd(audio, out_dir, prompt, max_tokens):
    """One mtd-subtitle run -> (segments or None, why, wall seconds). out_dir is wiped first so a
    failed run can never be judged by an earlier attempt's segments.json."""
    shutil.rmtree(out_dir, ignore_errors=True)
    t0 = time.time()
    try:
        r = subprocess.run(mtd_cmd(audio, out_dir, prompt, max_tokens), capture_output=True, text=True, errors='replace')
    except OSError as e:
        return None, f'could not run mtd-subtitle: {e}', time.time() - t0
    wall, tail = time.time() - t0, '\n'.join(r.stderr.splitlines()[-40:])
    if r.returncode:
        return None, f'mtd-subtitle exited {r.returncode}\n{tail}', wall
    segs, why = read_result(os.path.join(out_dir, 'segments.json'), duration(audio))
    return segs, f'{why}\n{tail}' if why else '', wall


def load_segs():
    """All segments on the recording's clock. Labels are per request: S01 for a single chunk,
    c<offset>-S01 for several, because S01 in c0 is not S01 in c540."""
    files = sorted(glob.glob('moss/c*.json'), key=offset)
    segs = []
    for p in files:
        off = offset(p)
        for s in json.load(open(p)):
            spk = f"c{off}-{s['speaker']}" if len(files) > 1 else s['speaker']
            segs.append({'start': s['start'] + off, 'end': s['end'] + off, 'spk': spk, 'text': s['text'].strip()})
    if not segs:
        sys.exit('moss/: no c*.json results: run transcribe first')
    return sorted(segs, key=lambda s: s['start'])


def check_complete():
    """A result set missing chunks would merge silently wrong, so every reader refuses it."""
    want = {os.path.basename(p)[:-4] for p in glob.glob('chunks/c*.mp3')}
    have = {os.path.basename(p)[:-5] for p in glob.glob('moss/c*.json')}
    if not want:
        sys.exit('no chunks/c*.mp3: run prep, then transcribe')
    if want - have:
        sys.exit(f"moss/ has no result for {', '.join(sorted(want - have, key=lambda c: int(c[1:])))}: "
                 'run transcribe (finished chunks are skipped)')


# ---------- text ----------

SPELLED = re.compile(r'(?<!\w)[A-Z](?: [A-Z])+(?!\w)')


def unspell(t):
    """MOSS spells acronyms as spaced capitals ("R T K"); join them, except runs of only I and A ("I I guess")."""
    return SPELLED.sub(lambda m: m.group(0) if set(m.group(0)) <= set('IA ') else m.group(0).replace(' ', ''), t)


def to_turns(segs, gap=15):
    """Merge same-speaker segments less than gap seconds apart. MOSS segments overlap, so a turn ends at its max end."""
    turns = []
    for s in segs:
        s = {**s, 'text': unspell(s['text'])}
        if turns and turns[-1]['spk'] == s['spk'] and s['start'] - turns[-1]['end'] < gap:
            turns[-1]['text'] += ' ' + s['text']
            turns[-1]['end'] = max(turns[-1]['end'], s['end'])
        else:
            turns.append(s)
    return turns


def talk_time(segs):
    """Seconds spoken per label: the sum of segment durations, not turn spans (a turn can bridge a long gap)."""
    talk = defaultdict(float)
    for s in segs:
        talk[s['spk']] += s['end'] - s['start']
    return dict(talk)


def write_md(turns, path):
    with open(path, 'w') as f:
        f.write('\n'.join(f"**[{ts(t['start'])}] {t['spk']}:** {t['text']}\n" for t in turns))


# ---------- voice identification ----------

def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n else v


def tally(seg_scores):
    """Mean score per name, the best name, and how many segments each name wins on its own."""
    names = sorted({n for s in seg_scores for n in s})
    mean = {n: sum(s.get(n, 0.0) for s in seg_scores) / len(seg_scores) for n in names}
    wins = Counter(max(sorted(s), key=s.get) for s in seg_scores)
    return mean, max(names, key=mean.get), wins


def decide(seg_scores, threshold=THRESHOLD, margin=MARGIN, agree=AGREE):
    """(name or None, reason) for one label's per-segment score dicts. A wrong name is worse than none, so a
    name needs a high mean, a clear lead over the runner-up, and most single segments agreeing with it."""
    if not any(seg_scores):
        return None, 'no scores'
    mean, best, wins = tally(seg_scores)
    rest = sorted((n for n in mean if n != best), key=lambda n: -mean[n])
    n = len(seg_scores)
    if mean[best] < threshold - EPS:
        return None, f'below threshold (best {best} {mean[best]:.2f})'
    if rest and mean[best] - mean[rest[0]] < margin - EPS:
        return None, f'too close: {best} {mean[best]:.2f} vs {rest[0]} {mean[rest[0]]:.2f}'
    if wins[best] / n < agree - EPS:
        return None, 'mixed: ' + ', '.join(f'{k} {v}/{n}' for k, v in wins.most_common(2))
    return best, 'ok' if rest else 'one enrolled name: no runner-up to compare against'


def overlapped(segs):
    """Indexes of segments that overlap another label's segment (segs sorted by start): two voices in one clip."""
    bad = set()
    for i, s in enumerate(segs):
        for j in range(i + 1, len(segs)):
            if segs[j]['start'] >= s['end']:
                break
            if segs[j]['spk'] != s['spk']:
                bad |= {i, j}
    return bad


def sample(segs, talk):
    """label -> up to BINS segments: the longest clean one (MIN_SEG s+, no other voice over it) of each of
    BINS equal time bins over the label's own span (its chunk, when chunked), so samples spread across
    everything the label covers. Labels with under MIN_TALK s are left out."""
    bad, out = overlapped(segs), {}
    for label, t in talk.items():
        if t < MIN_TALK:
            continue
        lo = min(s['start'] for s in segs if s['spk'] == label)
        span = max(s['end'] for s in segs if s['spk'] == label) - lo or 1
        best = {}
        for i, s in enumerate(segs):
            if s['spk'] != label or i in bad or s['end'] - s['start'] < MIN_SEG:
                continue
            b = min(BINS - 1, int(((s['start'] + s['end']) / 2 - lo) / span * BINS))
            if b not in best or s['end'] - s['start'] > best[b]['end'] - best[b]['start']:
                best[b] = s
        out[label] = [best[b] for b in sorted(best)]
    return out


def embed(wavs):
    """Voice vectors from embed.py, run once over every wav in the MOSS venv (it needs speechbrain)."""
    py = venv_bin('python')
    r = subprocess.run([py, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'embed.py'), *wavs],
                       capture_output=True, text=True, errors='replace')
    tail = '\n'.join(r.stderr.splitlines()[-40:])
    if r.returncode:
        sys.exit(f'embed.py failed (exit {r.returncode}); is speechbrain installed in {py}?\n{tail}')
    try:
        vecs = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        sys.exit(f'embed.py printed no JSON:\n{tail}')
    gone = [w for w in wavs if w not in vecs]
    if gone:
        sys.exit(f"embed.py returned no vector for {len(gone)} clip(s), e.g. {gone[0]}")
    return vecs


# ---------- subcommands ----------

def cmd_prep(a):
    stale = [p for p in (AUDIO, 'chunks', 'moss', 'ident') if os.path.exists(p)]
    if stale:
        sys.exit(f"refusing to prep: {', '.join(stale)} already exist. Old results must never be reused against "
                 're-cut audio: use a fresh run directory, or delete those by hand.')
    if a.chunk < 0:
        sys.exit('--chunk is 0 (one chunk for the whole recording) or a number of seconds')
    if not os.path.exists(a.recording):
        sys.exit(f'{a.recording}: no such file')
    try:
        ffmpeg('-i', a.recording, '-ac', '1', '-ar', '16000', '-c:a', 'libmp3lame', '-b:a', '32k', AUDIO)
        dur = duration(AUDIO)
        if dur <= 0:
            sys.exit(f'{a.recording}: no audio')
        offs = list(range(0, math.ceil(dur), a.chunk or math.ceil(dur)))
        if len(offs) > 1 and dur - offs[-1] < 2:   # a sliver of a tail would be an unscoreable chunk of its own
            offs.pop()
        os.makedirs('chunks')
        for i, off in enumerate(offs):   # the last chunk runs to the end of the audio
            span = ['-t', str(a.chunk)] if i < len(offs) - 1 else []
            ffmpeg('-ss', str(off), *span, '-i', AUDIO, '-c', 'copy', f'chunks/c{off}.mp3')
    except BaseException:   # a half-made run directory would block every retry
        shutil.rmtree('chunks', ignore_errors=True)
        if os.path.exists(AUDIO):
            os.remove(AUDIO)
        raise
    print(f"{ts(dur)} of audio, {len(offs)} chunk(s) in chunks/: {', '.join(f'c{o}' for o in offs)}")


def cmd_transcribe(a):
    venv_bin('mtd-subtitle')
    cfg = config()
    chunks = sorted(glob.glob('chunks/c*.mp3'), key=offset)
    if not chunks:
        sys.exit('no chunks/c*.mp3: run prep first')
    ids = [os.path.basename(c)[:-4] for c in chunks]
    only = {c.strip() for c in a.only.split(',')} if a.only else set(ids)
    if only - set(ids):
        sys.exit(f"--only: no such chunk {', '.join(sorted(only - set(ids)))} (chunks: {', '.join(ids)})")
    todo = [c for c, cid in zip(chunks, ids) if cid in only and not os.path.exists(f'moss/{cid}.json')]
    url, prompt = os.environ.get('MOSS_VLLM_URL'), build_prompt(cfg)
    where = f'vllm {url}' if url else f'device {device()}'
    print(f'{len(todo)} of {len(chunks)} chunks to transcribe ({where}, {a.max_new_tokens} max new tokens)', flush=True)
    os.makedirs('moss', exist_ok=True)
    failed = []
    for k, mp3 in enumerate(todo, 1):
        cid, audio_s = os.path.basename(mp3)[:-4], duration(mp3)
        segs, why, wall = run_mtd(mp3, f'moss/{cid}/', prompt, a.max_new_tokens)
        with open('moss/runs.jsonl', 'a') as f:
            f.write(json.dumps({'at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'chunk': cid, 'audio_s': round(audio_s, 1),
                                'wall_s': round(wall, 1), 'ok': segs is not None,
                                **({'backend': 'vllm'} if url else {'device': device()})}) + '\n')
        if segs is None:
            open(f'moss/{cid}.json.err', 'w').write(why.rstrip() + '\n')
            failed.append(cid)
            print(f'[{k}/{len(todo)}] {cid}: FAILED in {wall:.0f}s: {why.splitlines()[0]} (moss/{cid}.json.err)', flush=True)
            continue
        shutil.copyfile(f'moss/{cid}/segments.json', f'moss/{cid}.json.tmp')   # atomic: a half copy would count as done
        os.replace(f'moss/{cid}.json.tmp', f'moss/{cid}.json')
        if os.path.exists(f'moss/{cid}.json.err'):
            os.remove(f'moss/{cid}.json.err')
        print(f"[{k}/{len(todo)}] {cid}: {len(segs)} segs, speakers {','.join(sorted({s['speaker'] for s in segs}))} "
              f"in {wall:.0f}s", flush=True)
    if failed:
        sys.exit(f"{len(failed)} chunk(s) failed ({', '.join(failed)}), see moss/*.json.err; "
                 're-run the same command; finished chunks are skipped')


def cmd_anchors(a):
    cfg = config()
    check_complete()
    words = cfg.get('cast', []) + cfg.get('anchors', [])
    pat = re.compile(r'\b(' + '|'.join(re.escape(w) for w in words) + r')\b', re.I) if words else None
    for s in load_segs():
        mark = '  <<<' if pat and pat.search(s['text']) else ''
        print(f"[{ts(s['start'])}-{ts(s['end'])}] {s['spk']}: {s['text']}{mark}")


def cmd_runs(a):
    check_complete()
    segs = load_segs()
    talk = talk_time(segs)
    total = sum(talk.values()) or 1
    names = [n.strip() for n in a.names.split(',')] if a.names else sorted(talk, key=lambda n: -talk[n])
    if set(names) - set(talk):
        sys.exit(f"no such label: {', '.join(sorted(set(names) - set(talk)))} (labels: {', '.join(sorted(talk))})")
    runs = []
    for s in segs:
        if runs and runs[-1]['spk'] == s['spk'] and s['start'] - runs[-1]['end'] < 1.0:
            runs[-1]['end'] = max(runs[-1]['end'], s['end'])
            runs[-1]['text'] += ' ' + s['text']
        else:
            runs.append(dict(s))
    for n in names:
        mine = [r for r in runs if r['spk'] == n]
        good = sorted((r for r in mine if 3.0 <= r['end'] - r['start'] <= 10.0),
                      key=lambda r: r['start'] - r['end'])
        print(f"\n===== {n}  talk {talk[n]/60:.1f} min, {100*talk[n]/total:.0f}%  ({len(mine)} runs)")
        for r in good[:6]:
            print(f"  {ts(r['start'])} {r['start']:.1f}-{r['end']:.1f} ({r['end']-r['start']:.1f}s) {r['text'][:150]}")


def cmd_clip(a):
    if not 2 <= a.len <= 10:
        sys.exit('enrolment clips must be 2-10 s long')
    if not re.fullmatch(r'[^/\\.][^/\\]*', a.name):
        sys.exit(f'{a.name!r}: use the name exactly as it should appear (no slashes, not starting with a dot)')
    need_audio()
    start = secs(a.start)
    n = min(a.len, duration(AUDIO) - start)
    if start < 0 or n < 2:
        sys.exit(f'{a.start}: needs at least 2 s of audio from there; the recording is {ts(duration(AUDIO))} long')
    os.makedirs(f'refs/{a.name}', exist_ok=True)
    out = f'refs/{a.name}/{int(start)//3600}-{int(start)//60 % 60:02d}-{int(start) % 60:02d}.wav'
    ffmpeg('-ss', str(start), '-t', f'{n:.2f}', '-i', AUDIO, '-ac', '1', '-ar', '16000', out)
    print(f'{out} <- {a.start} +{n:.1f}s')


def cmd_identify(a):
    """Propose names by voice from refs/<Name>/*.wav. Writes identify.json only, never meeting.json."""
    check_complete()
    venv_bin('python')
    refs = {}
    for n in sorted(os.listdir('refs')) if os.path.isdir('refs') else []:
        wavs = sorted(glob.glob(os.path.join(glob.escape('refs'), glob.escape(n), '*.wav')))
        if wavs:
            refs[n] = wavs
    if not refs:
        sys.exit('no enrolment clips: cut some with `clip <name> <start>` (refs/<Name>/*.wav), at least one name')
    need_audio()
    th, mg, ag = (x if x is not None else d for x, d in ((a.threshold, THRESHOLD), (a.margin, MARGIN), (a.agree, AGREE)))
    cast = json.load(open('meeting.json')).get('cast') if os.path.exists('meeting.json') else None
    if cast and set(refs) - set(cast):
        print(f"WARNING: enrolled {', '.join(sorted(set(refs) - set(cast)))} not in meeting.json cast; "
              'a proposal is only as good as the spelling of the name')
    segs = load_segs()
    talk = talk_time(segs)
    total = sum(talk.values()) or 1
    samples = sample(segs, talk)
    shutil.rmtree('ident', ignore_errors=True)   # derived from the current results only
    for label, ss in samples.items():
        for s in ss:
            n = min(s['end'] - s['start'], MAX_CLIP)
            s['wav'] = f"ident/{label}/{s['start']:.2f}.wav"
            os.makedirs(os.path.dirname(s['wav']), exist_ok=True)
            ffmpeg('-ss', f"{(s['start'] + s['end'] - n) / 2:.2f}", '-t', f'{n:.2f}', '-i', AUDIO,
                   '-ac', '1', '-ar', '16000', s['wav'])
    wavs = [w for ws in refs.values() for w in ws] + [s['wav'] for ss in samples.values() for s in ss]
    vecs = embed(wavs) if any(samples.values()) else {}
    people = {n: unit([sum(c) / len(c) for c in zip(*(unit(vecs[w]) for w in ws))]) for n, ws in refs.items()} if vecs else {}
    labels = {}
    for label in sorted(talk, key=lambda l: -talk[l]):
        e = labels[label] = {'talk_s': round(talk[label], 1), 'share': round(talk[label] / total, 3), 'scores': {},
                             'proposed': None, 'reason': '', 'consistency': [0, 0], 'dissent': []}
        ss = samples.get(label, [])
        if talk[label] < MIN_TALK:
            e['reason'] = f'too short to score (under {MIN_TALK:g} s of talk)'
        elif not ss:
            e['reason'] = 'no clean sample'
        else:
            seg_scores = [{n: sum(x * y for x, y in zip(unit(vecs[s['wav']]), p)) for n, p in people.items()} for s in ss]
            mean, best, wins = tally(seg_scores)
            name, why = decide(seg_scores, th, mg, ag)
            e.update(scores={n: round(v, 3) for n, v in mean.items()}, proposed=name, reason=why,
                     consistency=[wins[best], len(ss)])
            if name:   # segments that individually vote for someone else: spot-check, or turn into overrides
                tops = [max(sorted(sc), key=sc.get) for sc in seg_scores]
                e['dissent'] = [[round(s['start'], 1), round(s['end'], 1), t, round(sc[t], 3)]
                                for s, sc, t in zip(ss, seg_scores, tops) if t != name]
    json.dump({'threshold': th, 'margin': mg, 'agree': ag, 'labels': labels}, open('identify.json', 'w'), indent=1)

    names = sorted(refs)
    print(f'threshold {th:g}  margin {mg:g}  agree {ag:g}  enrolled: {", ".join(names)}\n')
    print(f"{'label':12s} {'talk':>9s} {'share':>6s}  " + ' '.join(f'{n[:8]:>8s}' for n in names) + '  agree  proposed')
    for label, e in labels.items():
        sc = ' '.join(f"{e['scores'][n]:8.2f}" if n in e['scores'] else f"{'-':>8s}" for n in names)
        ag_ = f"{e['consistency'][0]}/{e['consistency'][1]}" if e['consistency'][1] else '-'
        print(f"{label:12s} {e['talk_s']/60:5.1f} min {100*e['share']:5.1f}%  {sc}  {ag_:>6s}  "
              f"{e['proposed'] or 'none'} ({e['reason']})")
    for label, e in labels.items():
        if e['dissent']:
            print(f"\ndissent in {label} (proposed {e['proposed']}): spot-check these, or turn them into overrides")
            for s0, s1, who, sc in e['dissent']:
                print(f'  [{ts(s0)}-{ts(s1)}] scores highest for {who} ({sc:.2f})')
    props = {l: e['proposed'] for l, e in labels.items() if e['proposed']}
    by = defaultdict(list)   # per chunk: the same person in two chunks is expected, within one chunk it is not
    for l, n in props.items():
        by[(l.rpartition('-')[0], n)].append(l)
    for (_, n), ls in by.items():
        if len(ls) > 1:
            print(f"\nFLAG: {n} is proposed for {len(ls)} labels in one request ({', '.join(ls)}): one voice split "
                  'in two, or a second person scoring close. Check the content of both before accepting.')
    if props:
        print('\nsuggested speakers, for meeting.json once the user confirms (meeting.json was not touched):')
        print('"speakers": ' + json.dumps(props))
    else:
        print('\nno label proposed: do not guess names; ask the user, or add clips with `clip` and re-run identify')


def cmd_name(a):
    cfg = config()
    check_complete()
    stem = os.path.splitext(a.out)[0]
    if stem + '.json' == a.out:
        sys.exit('the output must be a .md file (<out>.json is written next to it)')
    segs, speakers = load_segs(), cfg.get('speakers', {})
    stray = sorted(set(speakers) - {s['spk'] for s in segs})
    if stray:
        print(f"WARNING: speakers names labels that do not exist: {', '.join(stray)} "
              f"(labels are {', '.join(sorted({s['spk'] for s in segs}))}); those voices stay {UNATTR}")
    for s in segs:
        s['spk'] = speakers.get(s['spk']) or UNATTR
    overridden = 0
    for s in segs:
        mid = (s['start'] + s['end']) / 2
        for lo, hi, who, *_ in cfg.get('overrides', []):
            if lo <= mid <= hi:
                if s['spk'] != who:
                    s['spk'], overridden = who, overridden + 1
                break
    turns = to_turns(segs)
    json.dump(turns, open(stem + '.json', 'w'), indent=0)
    write_md(turns, a.out)
    talk = talk_time(segs)
    total = sum(talk.values()) or 1
    print(f'{len(turns)} turns, {len(segs)} segments, {overridden} overridden -> {a.out}')
    for k, v in sorted(talk.items(), key=lambda i: -i[1]):
        print(f'  {k:14s} {v/60:6.1f} min  {100*v/total:4.1f}%')
    open_ = [t for t in turns if t['spk'] == UNATTR and t['end'] - t['start'] >= 5]
    if open_:
        print(f'\nUnattributed turns of 5 s or more ({len(open_)}); ask the user about the ones that carry content:')
        for t in sorted(open_, key=lambda t: t['start'] - t['end'])[:15]:
            print(f"  [{ts(t['start'])}-{ts(t['end'])}] {t['text'][:110]}")


def cmd_fix(a):
    text = open(a.inp).read()
    for pat, rep in config().get('fixes', []):
        text, n = re.subn(pat, rep, text)
        print(f'  {n:3d}  {pat} -> {rep}' + ('   (no hits: drop it?)' if n == 0 else ''))
    open(a.out, 'w').write(text)


def cmd_spotcheck(a):
    """MOSS over one window, text only: labels are local to this run, so they say nothing about the main pass."""
    need_audio()
    prompt = DEFAULT_PROMPT if a.no_hotwords else build_prompt(config())
    wins = []
    for spec in a.windows:   # parse all before spending any inference
        rng, _, label = spec.partition('@')
        try:
            s, e = (secs(x) for x in rng.split('-'))
        except ValueError:
            sys.exit(f'{spec!r}: expected h:mm:ss-h:mm:ss[@label]')
        if not 0 <= s < e:
            sys.exit(f'{spec!r}: the window must end after it starts')
        wins.append((rng, label, s, e))
    failed = 0
    for rng, label, s, e in wins:
        with tempfile.TemporaryDirectory() as tmp:
            ffmpeg('-ss', f'{s:.2f}', '-t', f'{e - s:.2f}', '-i', AUDIO, '-c', 'copy', f'{tmp}/w.mp3')
            segs, why, _ = run_mtd(f'{tmp}/w.mp3', f'{tmp}/out/', prompt, MAX_TOKENS)
        if segs is None:
            failed += 1
            print(f'{rng} FAILED: {why}', file=sys.stderr)
            continue
        with open(a.out, 'a') as f:
            f.write(f'## {rng} {label}'.rstrip() + '\n\n')
            f.writelines(f"[{x['speaker']}] {x['text'].strip()}\n" for x in segs)
            f.write('\n')
        print(f'{rng} done: {len(segs)} segs')
    if failed:
        sys.exit(f'{failed} window(s) failed; nothing was written for them')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('prep'); p.add_argument('recording')
    p.add_argument('--chunk', type=int, default=CHUNK, help=f'seconds per chunk (default {CHUNK}); 0 = one request '
                   'for the whole recording, which keeps labels consistent but truncates past ~45 min')
    p = sub.add_parser('transcribe'); p.add_argument('--only', help='comma-separated chunk ids (c0,c540)')
    p.add_argument('--max-new-tokens', type=int, default=MAX_TOKENS)
    sub.add_parser('anchors')
    p = sub.add_parser('runs'); p.add_argument('--names', help='comma-separated labels')
    p = sub.add_parser('clip'); p.add_argument('name'); p.add_argument('start', help='h:mm:ss')
    p.add_argument('--len', type=float, default=9.5)
    p = sub.add_parser('identify')
    p.add_argument('--threshold', type=float); p.add_argument('--margin', type=float); p.add_argument('--agree', type=float)
    p = sub.add_parser('name'); p.add_argument('out')
    p = sub.add_parser('fix'); p.add_argument('inp'); p.add_argument('out')
    p = sub.add_parser('spotcheck'); p.add_argument('out'); p.add_argument('windows', nargs='+')
    p.add_argument('--no-hotwords', action='store_true', help='bare prompt, so hotwords cannot bias a disputed term')
    a = ap.parse_args()
    globals()['cmd_' + a.cmd](a)


if __name__ == '__main__':
    main()
