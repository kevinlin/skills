#!/usr/bin/env python3
"""Checks for scripts/diarize.py: pure rules, refusals, then an offline round trip against a fake MOSS venv.
Run: python3 tests/test_diarize.py"""
import contextlib, io, json, os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # importing diarize must not leave scripts/__pycache__ in the shipped skill
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import diarize
from diarize import DEFAULT_PROMPT, UNATTR, decide, read_result, talk_time, to_turns, unspell

for k in [k for k in os.environ if k.startswith('MOSS_')]:
    del os.environ[k]   # a developer's real MOSS setup must not leak into the checks

# ---------- helpers ----------


def cli(*argv):
    """diarize.main() in-process: (exit code, everything it printed)."""
    out, code, old = io.StringIO(), 0, sys.argv
    sys.argv = ['diarize.py', *map(str, argv)]
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            diarize.main()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else int(e.code is not None)
        if isinstance(e.code, str):
            out.write(e.code + '\n')
    finally:
        sys.argv = old
    return code, out.getvalue()


@contextlib.contextmanager
def rundir(**env):
    """A scratch run directory (the cwd) with MOSS_* set for the block."""
    here, saved, tmp = os.getcwd(), dict(os.environ), tempfile.mkdtemp()
    os.chdir(tmp)
    os.environ.update(env)
    try:
        yield tmp
    finally:
        os.chdir(here)
        os.environ.clear()
        os.environ.update(saved)
        shutil.rmtree(tmp, ignore_errors=True)


def stub_run(chunks, **cfg):
    """A run directory whose chunks are already transcribed: chunks = {offset: [(start, end, 'S01', text)]}."""
    os.makedirs('chunks'), os.makedirs('moss')
    for off, segs in chunks.items():
        open(f'chunks/c{off}.mp3', 'wb').close()
        json.dump([{'id': i, 'start': a, 'end': b, 'speaker': s, 'text': t} for i, (a, b, s, t) in enumerate(segs)],
                  open(f'moss/c{off}.json', 'w'))
    json.dump(cfg, open('meeting.json', 'w'))


def named(out='out.md'):
    code, text = cli('name', out)
    assert code == 0, text
    return [(t['start'], t['end'], t['spk']) for t in json.load(open(os.path.splitext(out)[0] + '.json'))]


# A MOSS venv stand-in. bin/mtd-subtitle writes a two-speaker segments.json covering the audio; markers/ holds its
# switches (fail-<chunk>: exit 3, trunc-<chunk>: exit 0 but segments end at 30 s) and logs every call's argv.
# bin/python stands in for the interpreter that runs embed.py: deterministic vectors keyed on the wav path.
FAKE_MTD = r'''
import json, os, subprocess, sys
mk = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'markers')
a = sys.argv[1:]
chunk = os.path.basename(a[0]).rsplit('.', 1)[0]
open(os.path.join(mk, 'calls.log'), 'a').write(json.dumps(a) + '\n')
on = lambda kind: os.path.exists(os.path.join(mk, f'{kind}-{chunk}'))
if on('fail'):
    sys.stderr.write('boom: out of memory\n')
    sys.exit(3)
if on('none'):      # exits 0 and writes nothing
    sys.exit(0)
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a[0]],
                           capture_output=True, text=True).stdout)
end = 30.0 if on('trunc') else dur
segs, t, i = [], 0.0, 0
while t < end:
    e = end if end - (t + 10) < 1 else t + 10
    segs.append({'id': i, 'start': t, 'end': e, 'speaker': 'S01' if i % 2 == 0 else 'S02',
                 'text': 'the R T K query' if i == 0 else f'segment {i}'})
    t, i = e, i + 1
out = a[a.index('--out-dir') + 1]
os.makedirs(out, exist_ok=True)
json.dump(segs, open(os.path.join(out, 'segments.json'), 'w'))
open(os.path.join(out, 'raw_transcript.txt'), 'w').write('raw')
'''

FAKE_PY = r'''
import json, os, sys
mk = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'markers')
open(os.path.join(mk, 'embed.log'), 'a').write(json.dumps(sys.argv[1:]) + '\n')
vecs = {}
for p in sys.argv[2:]:      # argv[1] is embed.py, which this stand-in ignores
    v = [0.0] * 192
    v[0 if ('/Ana/' in p or 'S01/' in p) else 1] = 1.0
    v[2] = (sum(map(ord, p)) % 7) * 0.01
    vecs[p] = v
json.dump(vecs, sys.stdout)
'''


@contextlib.contextmanager
def fake_venv():
    root = tempfile.mkdtemp()
    os.makedirs(f'{root}/bin'), os.makedirs(f'{root}/markers')
    for name, body in (('mtd-subtitle', FAKE_MTD), ('python', FAKE_PY)):
        open(f'{root}/bin/{name}', 'w').write(f'#!{sys.executable}\n{body}')
        os.chmod(f'{root}/bin/{name}', 0o755)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def log(venv, name):
    p = f'{venv}/markers/{name}.log'
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def mark(venv, kind, chunk, on=True):
    p = f'{venv}/markers/{kind}-{chunk}'
    open(p, 'w').close() if on else os.remove(p)


def arg(argv, flag):
    return argv[argv.index(flag) + 1]


def sine(path, seconds):
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'sine=duration={seconds}:sample_rate=16000', path],
                   check=True)


# ---------- pure rules ----------

# MOSS spells acronyms as spaced capitals; a run of only I/A is a sentence ("I I guess"), not an acronym
assert unspell('R T K query') == 'RTK query'
assert unspell('the C C gateway') == 'the CC gateway'
assert unspell('I I guess') == 'I I guess' and unspell('I A') == 'I A'
assert unspell('A B test') == 'AB test'      # B is not I or A, so the run joins
assert unspell('see M F E and Ana B Test') == 'see MFE and Ana B Test'


def rows(n, **scores):
    return [dict(scores) for _ in range(n)]


def d(seg_scores):
    return decide(seg_scores, 0.45, 0.10, 0.75)


assert d(rows(12, Ana=0.8, Ben=0.1))[0] == 'Ana'
assert d(rows(12, Ana=0.31, Ben=0.05)) == (None, 'below threshold (best Ana 0.31)')
assert d(rows(12, Ana=0.52, Ben=0.49)) == (None, 'too close: Ana 0.52 vs Ben 0.49')
# 8 of 12 segments say Ana, 4 say Ben: the means look fine but agreement 0.67 is under 0.75
assert d(rows(8, Ana=0.8, Ben=0.1) + rows(4, Ana=0.3, Ben=0.9)) == (None, 'mixed: Ana 8/12, Ben 4/12')
assert d(rows(9, Ana=0.8, Ben=0.1) + rows(3, Ana=0.3, Ben=0.4))[0] == 'Ana'   # exactly 0.75 passes
name, why = d(rows(5, Ana=0.7))
assert name == 'Ana' and 'one enrolled name' in why     # no runner-up to check the margin against
assert d(rows(5, Ana=0.3))[0] is None                   # but the threshold still applies
assert d([])[0] is None

# truncation: the CLI writes whatever it parsed, so a token-limited run looks like success
with tempfile.TemporaryDirectory() as t:
    def res(segs, dur):
        json.dump(segs, open(f'{t}/s.json', 'w'))
        return read_result(f'{t}/s.json', dur)
    seg = lambda a, b: {'id': 0, 'start': a, 'end': b, 'speaker': 'S01', 'text': 'x'}
    assert res([seg(0, 2470)], 3946)[1] == ('truncated: ends at 0:41:10 of 1:05:46; '
                                             'raise --max-new-tokens or re-prep with --chunk')
    assert res([seg(0, 3800)], 3946)[1] == ''            # within 5% (197 s)
    assert res([seg(0, 250)], 300)[1] == ''              # short chunks get 60 s
    assert res([seg(0, 200)], 300)[1].startswith('truncated')
    assert res([], 300)[1] and res([seg(0, 10), {'start': 0}], 10)[1]
    open(f'{t}/s.json', 'w').write('{not json')
    assert read_result(f'{t}/s.json', 10)[1] and read_result(f'{t}/missing.json', 10)[1]

# turns: segments overlap in MOSS output, so a merged turn ends at the max of the ends
turns = to_turns([{'start': 0, 'end': 10, 'spk': 'Ana', 'text': 'a'}, {'start': 2, 'end': 4, 'spk': 'Ana', 'text': 'b'}])
assert [(t['start'], t['end'], t['text']) for t in turns] == [(0, 10, 'a b')], turns
assert [t['text'] for t in to_turns([{'start': 0, 'end': 2, 'spk': 'Ana', 'text': 'the R T K'},
                                     {'start': 40, 'end': 41, 'spk': 'Ana', 'text': 'later'}])] == ['the RTK', 'later']
# talk time is the sum of segment durations, not the span of the turn they merge into
two = [{'start': 0, 'end': 1, 'spk': 'Ana', 'text': 'a'}, {'start': 14, 'end': 15, 'spk': 'Ana', 'text': 'b'}]
assert talk_time(two) == {'Ana': 2} and to_turns(two)[0]['end'] == 15

# sampling: longest clean segment per time bin; short, overlapped and under-6 s labels are left out
sg = lambda spk, a, b: {'spk': spk, 'start': a, 'end': b, 'text': ''}
segs = sorted([sg('A', 0, 3), sg('A', 4, 9), sg('A', 20, 26), sg('A', 30, 31.5), sg('A', 60, 66), sg('A', 100, 102),
               sg('B', 22, 23), sg('B', 110, 120), sg('C', 40, 42), sg('D', 50, 58), sg('E', 52, 54)],
              key=lambda s: s['start'])
picked = diarize.sample(segs, talk_time(segs))
assert {k: [s['start'] for s in v] for k, v in picked.items()} == {'A': [4, 60, 100], 'B': [110], 'D': []}, picked
# A's [20,26] is overlapped by B; C has 2 s of talk; D has 8 s but all of it is under E's voice (no clean sample)
# bins span the label's own stretch: a label living in the last chunk (c3600-) still gets 12 samples
late = [sg('c0-S01', 0, 3)] + [sg('c3600-S01', 3600 + 30 * i, 3603 + 30 * i) for i in range(12)]
assert len(diarize.sample(late, talk_time(late))['c3600-S01']) == 12

# ---------- refusals and labels ----------

for stale in ('audio-16k.mp3', 'chunks', 'moss', 'ident'):     # old results must never meet re-cut audio
    with rundir():
        open('rec.wav', 'wb').close()
        if stale.endswith('.mp3'):
            open(stale, 'w').close()
        else:
            os.makedirs(stale)
        code, text = cli('prep', 'rec.wav')
        assert code != 0 and stale in text, (stale, text)
        assert sorted(os.listdir('.')) == sorted(['rec.wav', stale])    # nothing created or changed

with rundir(MOSS_VENV='/nonexistent/venv'):
    stub_run({0: [(0, 5, 'S01', 'hello')]})
    code, text = cli('transcribe')
    assert code != 0 and '/nonexistent/venv/bin/mtd-subtitle' in text, text
    os.makedirs('refs/Ana'), open('refs/Ana/a.wav', 'wb').close()
    code, text = cli('identify')
    assert code != 0 and '/nonexistent/venv/bin/python' in text, text

with rundir():   # labels: S01 for one chunk, c<off>-S01 when several (labels are per request)
    stub_run({0: [(0, 5, 'S01', 'a')]})
    assert {s['spk'] for s in diarize.load_segs()} == {'S01'}
with fake_venv() as venv, rundir(MOSS_VENV=venv):
    stub_run({0: [(0, 5, 'S01', 'a')], 1800: [(0, 5, 'S01', 'b')]})
    assert [(s['spk'], s['start']) for s in diarize.load_segs()] == [('c0-S01', 0), ('c1800-S01', 1800)]
    os.remove('moss/c1800.json')
    for argv in (['anchors'], ['runs'], ['identify'], ['name', 'out.md']):
        code, text = cli(*argv)
        assert code != 0 and 'c1800' in text and not os.path.exists('out.md'), (argv, text)

# ---------- name ----------

with rundir():
    stub_run({0: [(0, 5, 'S01', 'hello'), (2, 8, 'S02', 'hi'), (12, 14, 'S03', 'who'), (20, 22, 'S02', 'bye')]},
             speakers={'S01': 'Ana', 'S02': 'Ben'},
             overrides=[[4, 10, 'Chen', 'the words settle it']])
    # by midpoint: [0,5] ends inside the window but its midpoint 2.5 is outside; [2,8] starts outside, midpoint 5 inside
    assert named() == [(0, 5, 'Ana'), (2, 8, 'Chen'), (12, 14, UNATTR), (20, 22, 'Ben')]
    assert '**[0:00:12] Unattributed:** who' in open('out.md').read()
with rundir():
    stub_run({0: [(0, 5, 'S01', 'a')], 1800: [(0, 5, 'S01', 'b')]}, speakers={'c0-S01': 'Ana', 'c1800-S01': 'Ben'})
    assert named() == [(0, 5, 'Ana'), (1800, 1805, 'Ben')]            # different voices, different labels
    json.dump({'speakers': {'S01': 'Ana'}}, open('meeting.json', 'w'))
    assert named() == [(0, 5, UNATTR), (1800, 1805, UNATTR)]          # an unscoped key matches nothing

# ---------- anchors and runs ----------

with rundir():
    stub_run({0: [(0, 3, 'S01', 'Hi I am Ana here'), (3, 6, 'S02', 'My team ships it'), (6, 9, 'S01', 'banana split'),
                  (10, 14, 'S02', 'ok'), (20, 24, 'S01', 'x'), (24.5, 28, 'S01', 'y'), (40, 42, 'S01', 'short')]},
             cast=['Ana'], anchors=['my team'])
    lines = cli('anchors')[1].splitlines()
    assert [l.endswith('<<<') for l in lines[:3]] == [True, True, False], lines   # word-bounded: banana is not Ana
    text = cli('runs')[1]
    assert '20.0-28.0 (8.0s)' in text and '40.0-42.0' not in text, text         # gap under 1 s merges; 2 s is too short
    assert cli('runs', '--names', 'S09')[0] != 0                                 # unknown label is a refusal

# ---------- environment -> command line ----------

with fake_venv() as venv:
    with rundir(MOSS_VENV=venv, MOSS_DEVICE='mps', MOSS_VLLM_URL='http://gpu:8000', MOSS_MODEL='x/y'):
        cmd = diarize.mtd_cmd('a.mp3', 'o', 'p', 7)
        assert arg(cmd, '--dtype') == 'bf16' and arg(cmd, '--model') == 'x/y'
        i = cmd.index('--backend')
        assert cmd[i:i + 4] == ['--backend', 'vllm', '--vllm-base-url', 'http://gpu:8000']
    with rundir(MOSS_VENV=venv, MOSS_DEVICE='cpu'):
        cmd = diarize.mtd_cmd('a.mp3', 'o', 'p', 7)
        assert arg(cmd, '--dtype') == 'fp32' and '--backend' not in cmd

# ---------- round trips (need ffmpeg) ----------


def round_trip():
    """prep -> transcribe (a failed and a truncated chunk, then resume) -> clip -> identify -> name -> fix -> spotcheck."""
    with fake_venv() as venv, rundir(MOSS_VENV=venv, MOSS_DEVICE='cpu'):
        sine('rec.wav', 600)
        json.dump({'cast': ['Ana', 'Ben'], 'hotwords': ['Zephyr'], 'fixes': [[r'\bquery\b', 'request']]},
                  open('meeting.json', 'w'))
        assert cli('prep', 'rec.wav', '--chunk', 540)[0] == 0
        assert sorted(os.listdir('chunks')) == ['c0.mp3', 'c540.mp3'] and os.path.exists('audio-16k.mp3')
        assert cli('prep', 'rec.wav')[0] != 0                  # a re-prep never reuses or overwrites

        assert cli('transcribe', '--only', 'c99')[0] != 0 and log(venv, 'calls') == []

        # c540 dies, c0 comes back truncated (ends at 30 s of 540 s): neither may be cached as a result
        mark(venv, 'fail', 'c540'), mark(venv, 'trunc', 'c0')
        assert cli('transcribe')[0] != 0
        assert not os.path.exists('moss/c0.json') and not os.path.exists('moss/c540.json')
        assert 'truncated' in open('moss/c0.json.err').read()
        assert 'out of memory' in open('moss/c540.json.err').read()

        # c0 recovers while c540 keeps failing: the finished chunk is kept, the exit stays non-zero
        mark(venv, 'trunc', 'c0', False)
        assert cli('transcribe')[0] != 0
        assert os.path.exists('moss/c0.json') and not os.path.exists('moss/c0.json.err')
        assert os.path.exists('moss/c540.json.err') and not os.path.exists('moss/c540.json')
        for argv in (['anchors'], ['runs'], ['identify'], ['name', 'out.md']):
            code, text = cli(*argv)
            assert code != 0 and 'c540' in text, (argv, text)
        assert not any(os.path.exists(p) for p in ('identify.json', 'ident', 'out.md'))

        # after the cause is fixed a re-run transcribes only the missing chunk
        mark(venv, 'fail', 'c540', False)
        before = len(log(venv, 'calls'))
        assert cli('transcribe')[0] == 0
        assert [os.path.basename(c[0]) for c in log(venv, 'calls')[before:]] == ['c540.mp3']
        assert os.path.exists('moss/c540.json') and not os.path.exists('moss/c540.json.err')
        assert cli('transcribe')[0] == 0 and len(log(venv, 'calls')) == before + 1    # nothing left to do

        attempts = [json.loads(l) for l in open('moss/runs.jsonl')]
        assert [(r['chunk'], r['ok']) for r in attempts] == [
            ('c0', False), ('c540', False), ('c0', True), ('c540', False), ('c540', True)]
        assert all({'at', 'audio_s', 'wall_s'} <= set(r) and r['device'] == 'cpu' for r in attempts)
        call = log(venv, 'calls')[0]
        assert call[0] == 'chunks/c0.mp3' and arg(call, '--out-dir') == 'moss/c0/'
        assert arg(call, '--model') == 'OpenMOSS-Team/MOSS-Transcribe-Diarize'
        assert (arg(call, '--device'), arg(call, '--dtype'), arg(call, '--max-new-tokens')) == ('cpu', 'fp32', '65536')
        assert arg(call, '--prompt') == DEFAULT_PROMPT + ' Hotwords: Zephyr, Ana, Ben'

        segs = diarize.load_segs()
        assert {s['spk'] for s in segs} == {'c0-S01', 'c0-S02', 'c540-S01', 'c540-S02'}
        code, text = cli('anchors')
        assert code == 0 and len(text.strip().splitlines()) == len(segs)
        assert cli('runs')[0] == 0

        # enrol, then identify: it proposes and never writes meeting.json
        assert cli('clip', 'Ana', '0:00:05')[0] == 0 and cli('clip', 'Ben', '0:00:15')[0] == 0
        assert os.path.exists('refs/Ana/0-00-05.wav') and os.path.exists('refs/Ben/0-00-15.wav')
        assert abs(diarize.duration('refs/Ana/0-00-05.wav') - 9.5) < 0.2
        assert cli('clip', 'Ana', '0:00:05', '--len', 11)[0] != 0 and cli('clip', 'Ana', '0:09:59')[0] != 0
        snapshot = open('meeting.json').read()
        code, text = cli('identify')
        assert code == 0, text
        assert open('meeting.json').read() == snapshot
        ident = json.load(open('identify.json'))
        assert (ident['threshold'], ident['margin'], ident['agree']) == (0.45, 0.10, 0.75)
        labels = ident['labels']
        want = {'c0-S01': 'Ana', 'c0-S02': 'Ben', 'c540-S01': 'Ana', 'c540-S02': 'Ben'}
        assert {k: v['proposed'] for k, v in labels.items()} == want, labels
        for v in labels.values():
            assert v['consistency'][0] == v['consistency'][1] >= 1 and v['dissent'] == []
            assert v['talk_s'] >= 6 and set(v['scores']) == {'Ana', 'Ben'}
        starts = sorted(float(f[:-4]) for f in os.listdir('ident/c0-S01'))
        assert len(starts) >= 10 and starts[-1] - starts[0] > 400, starts    # spread over the whole meeting
        wavs = [os.path.join(r, f) for top in ('refs', 'ident') for r, _, fs in os.walk(top) for f in fs]
        (embed_call,) = log(venv, 'embed')                                   # one embed run over every wav
        assert embed_call[0].endswith('embed.py') and sorted(embed_call[1:]) == sorted(wavs), embed_call

        # the agent writes speakers after the user confirms; then name -> fix
        cfg = json.load(open('meeting.json'))
        cfg['speakers'] = {k: v['proposed'] for k, v in labels.items()}
        json.dump(cfg, open('meeting.json', 'w'))
        code, text = cli('name', 'body-raw.md')
        assert code == 0, text
        turns = json.load(open('body-raw.json'))
        assert len(turns) == len(segs) and {t['spk'] for t in turns} == {'Ana', 'Ben'}
        assert turns[0]['text'] == 'the RTK query' and (turns[0]['start'], turns[0]['spk']) == (0, 'Ana')
        assert any(t['start'] == 540 and t['spk'] == 'Ana' for t in turns)
        assert '**[0:00:00] Ana:** the RTK query' in open('body-raw.md').read()
        assert cli('fix', 'body-raw.md', 'body.md')[0] == 0
        body = open('body.md').read()
        assert body.count('the RTK request') == 2 and 'query' not in body

        # spotcheck: hotwords unless told otherwise, one [Sxx] line per segment, appended
        assert cli('spotcheck', 'spot.md', '0:00:10-0:00:40@c0-S01', '--no-hotwords')[0] == 0
        assert arg(log(venv, 'calls')[-1], '--prompt') == DEFAULT_PROMPT
        assert cli('spotcheck', 'spot.md', '0:01:00-0:01:30')[0] == 0
        assert arg(log(venv, 'calls')[-1], '--prompt').endswith(' Hotwords: Zephyr, Ana, Ben')
        spot = open('spot.md').read()
        assert spot.startswith('## 0:00:10-0:00:40 c0-S01\n') and '\n## 0:01:00-0:01:30\n' in spot
        assert re.findall(r'^\[(S0\d)\] ', spot, re.M) == ['S01', 'S02', 'S01'] * 2

        # a run that exits 0 and writes nothing must not be vouched for by the last run's segments.json
        os.remove('moss/c0.json')
        mark(venv, 'none', 'c0')
        assert cli('transcribe')[0] != 0 and not os.path.exists('moss/c0.json') and os.path.exists('moss/c0.json.err')


def short_recordings():
    """--chunk 0 is one chunk; a tail under 2 s joins the last chunk instead of becoming an unscoreable one."""
    with rundir():
        sine('rec.wav', 7)
        assert cli('prep', 'rec.wav')[0] == 0 and os.listdir('chunks') == ['c0.mp3']
        assert abs(diarize.duration('chunks/c0.mp3') - 7) < 0.2
    with rundir():
        sine('rec.wav', 7)
        assert cli('prep', 'rec.wav', '--chunk', 3)[0] == 0 and sorted(os.listdir('chunks')) == ['c0.mp3', 'c3.mp3']
        assert abs(diarize.duration('chunks/c3.mp3') - 4) < 0.2


if shutil.which('ffmpeg') and shutil.which('ffprobe'):
    round_trip()
    short_recordings()
else:
    print('ffmpeg not found: skipped the round trips')

help_ = subprocess.run([sys.executable, os.path.join(HERE, '..', 'scripts', 'diarize.py'), '-h'],
                       capture_output=True, text=True).stdout
assert re.search(r'\{(.*?)\}', help_).group(1) == 'prep,transcribe,anchors,runs,clip,identify,name,fix,spotcheck'
print('ok')
