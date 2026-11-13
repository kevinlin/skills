#!/usr/bin/env python3
"""Rebuild everything generated under evals/fixtures. Standard library only.

  python3 build_manifests.py            write workspaces/ and refresh the script judges
  python3 build_manifests.py --check    exit 1 if anything on disk is out of date

Authored by hand:   src/base/            the shared workspace (rules, glossary, stakeholders,
                                         the earlier recap, the transcript)
                    src/clean-output/    a finished, clean recap (.md + .html) and the glossary
                                         as that recap leaves it
                    scripts/judge_*.py   judge-specific checks
                    judge_common.py      helpers every judge needs
Generated:          workspaces/<case>/   what skill-up uploads as each case's workspace
                    the COMMON and FIXTURE DATA regions of every judge: skill-up copies a judge
                    into a temp dir, so each one must be a single self-contained file. The fixture
                    data is the sha256 manifests the judges compare Input/ and Artefacts/ against.
Re-run this after any change under src/, judge_common.py or the defect list below.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC, WS, SCRIPTS = HERE / 'src', HERE / 'workspaces', HERE / 'scripts'
RECAP_DIR = 'Output/Meetings/20261105_Rollout-planning'
RECAP = RECAP_DIR + '/Rollout-planning-recap'
TRANSCRIPT = 'Input/Meetings/20261105_Rollout-planning/Rollout-planning-transcript.md'

# The four planted defects of the verify case. Each one is a single replacement per file, so a
# bad workspace with one defect differs from the clean one by exactly that mutation.
DEFECTS = {
    'banned name in a body line': {
        '.md': ('still carries the old programme name in half its headers',
                'still carries Project Kestrel in half its headers'),
        '.html': ('still carries the old programme name in half its headers',
                  'still carries Project Kestrel in half its headers')},
    'timestamp past the transcript end': {
        '.md': ('Mei-Ling (0:08:00).', 'Mei-Ling (0:48:12).'),
        '.html': ('Mei-Ling <span class="ts">0:08:00</span>.', 'Mei-Ling <span class="ts">0:48:12</span>.')},
    'quote attributed to the wrong person': {
        '.md': ('Tomasz: "Manifest sync has never once', 'Ingrid: "Manifest sync has never once'),
        '.html': ('Tomasz: \u201cManifest sync has never once', 'Ingrid: \u201cManifest sync has never once')},
    'broken relative link': {
        '.md': ('20261105_Rollout-planning/Rollout-planning-transcript.md>)',
                '20261105_Rollout-planning/Rollout-plan-transcript.md>)'),
        '.html': ('20261105_Rollout-planning/Rollout-planning-transcript.md"',
                  '20261105_Rollout-planning/Rollout-plan-transcript.md"')},
}


def apply_defect(name, ext, text):
    old, new = DEFECTS[name][ext]
    if text.count(old) != 1:
        sys.exit(f'defect "{name}" ({ext}): expected one occurrence of {old!r}, found {text.count(old)}')
    return text.replace(old, new)


def files_of(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob('*'))
            if p.is_file() and p.name != '.DS_Store'}


def workspace_files(case):
    files = files_of(SRC / 'base')
    if case != 'recap-from-transcript':
        files.update(files_of(SRC / 'clean-output'))
    if case == 'verify-planted-defects':
        for ext in ('.md', '.html'):
            text = files[RECAP + ext].decode('utf-8')
            for name in DEFECTS:
                text = apply_defect(name, ext, text)
            files[RECAP + ext] = text.encode('utf-8')
    return files


CASES = ['recap-from-transcript', 'verify-planted-defects', 'client-safe-copy']


def manifest(files, prefix):
    return {k: hashlib.sha256(v).hexdigest() for k, v in sorted(files.items()) if k.startswith(prefix)}


def transcript_end(files):
    turns = re.findall(r'^\*\*\[(\d+):(\d{2}):(\d{2})\] ', files[TRANSCRIPT].decode('utf-8'), re.M)
    return max(int(h) * 3600 + int(m) * 60 + int(s) for h, m, s in turns)


def fixture_data(case):
    files = workspace_files(case)
    data = {'transcript_end': transcript_end(files),
            'input': manifest(files, 'Input/'), 'artefacts': manifest(files, 'Artefacts/')}
    if case == 'recap-from-transcript':
        glossary = files['Glossary.md'].decode('utf-8')
        data['glossary_sha'] = hashlib.sha256(files['Glossary.md']).hexdigest()
        data['glossary_terms'] = re.findall(r'^\|\s*\*\*(.+?)\*\*\s*\|', glossary, re.M)
    elif case == 'verify-planted-defects':
        clean = workspace_files('client-safe-copy')
        data['md_sections'] = len(re.findall(r'^## ', clean[RECAP + '.md'].decode('utf-8'), re.M))
        data['html_sections'] = len(re.findall(r'<section\b', clean[RECAP + '.html'].decode('utf-8')))
    else:
        data['internal'] = manifest(files, RECAP_DIR + '/')
    return data


def common_body():
    text = (HERE / 'judge_common.py').read_text(encoding='utf-8')
    return text[text.index('import hashlib'):].rstrip() + '\n'


def stamp(judge_text, data):
    out, n = re.subn(r'(# >>> COMMON[^\n]*\n).*?(# <<< COMMON)',
                     lambda m: m.group(1) + common_body() + m.group(2), judge_text, flags=re.S)
    out, m = re.subn(r'(# >>> FIXTURE DATA[^\n]*\n).*?(# <<< FIXTURE DATA)',
                     lambda m: m.group(1) + 'FIXTURE = ' + json.dumps(data, indent=1, sort_keys=True) + '\n' + m.group(2),
                     out, flags=re.S)
    if (n, m) != (1, 1):
        sys.exit('a judge is missing its COMMON or FIXTURE DATA markers')
    return out


def judge_file(case):
    return SCRIPTS / f'judge_{case.replace("-", "_")}.py'


def check_anchors():
    """Every transcript turn a judge anchors a fact to must start at exactly that second."""
    turns = {int(h) * 3600 + int(m) * 60 + int(s) for h, m, s in
             re.findall(r'^\*\*\[(\d+):(\d{2}):(\d{2})\] ', (SRC / 'base' / TRANSCRIPT).read_text(encoding='utf-8'), re.M)}
    sources = [HERE / 'judge_common.py'] + [judge_file(c) for c in CASES]
    for src in sources:
        for group in re.findall(r'turns=\[([\d, ]+)\]', src.read_text(encoding='utf-8')):
            for t in (int(x) for x in group.split(',')):
                if t not in turns:
                    sys.exit(f'{src.name}: no transcript turn starts at {t} s')


def build(write):
    check_anchors()
    stale = []
    expected = {}
    for case in CASES:
        for rel, content in workspace_files(case).items():
            expected[WS / case / rel] = content
        judge = judge_file(case)
        expected[judge] = stamp(judge.read_text(encoding='utf-8'), fixture_data(case)).encode('utf-8')
    on_disk = {p for p in WS.rglob('*') if p.is_file()} if WS.exists() else set()
    for path in sorted(set(expected) | on_disk):
        if path not in expected:
            stale.append(f'{path.relative_to(HERE)} (no longer generated)')
        elif not path.exists() or path.read_bytes() != expected[path]:
            stale.append(f'{path.relative_to(HERE)} (out of date)')
    if write:
        for path in on_disk - set(expected):
            path.unlink()
        for path, content in expected.items():
            if not path.exists() or path.read_bytes() != content:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        for d in sorted((p for p in WS.rglob('*') if p.is_dir()), reverse=True):
            if not any(d.iterdir()):
                d.rmdir()
        for judge in (judge_file(c) for c in CASES):
            judge.chmod(0o755)
        print(f'rebuilt {len(expected)} files ({len(stale)} changed)')
    return stale


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='report out-of-date files instead of writing')
    stale = build(write=not ap.parse_args().check)
    if stale and '--check' in sys.argv:
        print('out of date, run build_manifests.py:\n  ' + '\n  '.join(stale))
        sys.exit(1)


if __name__ == '__main__':
    main()
