"""Emit allowlisted P4000 evidence as JSON; never copy raw log text."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

IDS = ('qwen35-9b-q4', 'qwen35-4b-q4', 'qwen35-2b-q8',
       'phi4-mini-38b-q4', 'llama32-3b-q4')
CAPS = {'general.chat', 'content.write', 'content.summarize'}


def require(value, message):
    if not value:
        raise ValueError(message)


def provenance(path):
    data = path.read_bytes()
    return {'sha256': hashlib.sha256(data).hexdigest(), 'sizeBytes': len(data)}


def summarize(directory, platform, hwinfo=None):
    state = json.loads((directory / 'status.json').read_text(encoding='utf-8'))
    require(state['status'] == 'completed' and state['finalUnload'] == 'verified', 'incomplete-run')
    require(set(state['models']) == set(IDS), 'unexpected-model-set')
    expected_os = {'windows': 'Windows 11 Pro 10.0.26200',
                   'ubuntu': 'Ubuntu 26.04.1 LTS, Linux 7.0.0-31-generic'}[platform]
    driver = {'windows': '582.78', 'ubuntu': '580.178.04'}[platform]
    require(state['profile'] == dict(gpu='NVIDIA Quadro P4000', memoryMiB=8192,
            driver=driver, os=expected_os, backend='CUDA', runtime='0.32.14'), 'unexpected-profile')
    models = []
    system_memory = state['models'][IDS[0]]['core'][0]['evidence']['systemMemoryGiB']
    require(isinstance(system_memory, (int, float)) and math.isfinite(system_memory)
            and 0 < system_memory < 1024, 'invalid-memory')
    for mid in IDS:
        item = state['models'][mid]
        require(item['status'] == 'passed' and item['elapsedSoakSeconds'] >= 1800, 'incomplete-model')
        digest = item['manifestDigest']
        require(len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), 'invalid-digest')
        require(len(item['core']) == 3 and {c['evidence']['capability'] for c in item['core']} == CAPS, 'core-coverage')
        totals = {}
        for phase in ('core', 'soak'):
            count = 0
            require(bool(item[phase]), 'empty-phase')
            for cell in item[phase]:
                m, e = cell['metrics'], cell['evidence']
                require(cell['outcome'] == 'passed' and cell['errorCode'] is None, 'failed-cell')
                require(m['samplesAttempted'] == m['samplesPassed'] == m['unloadPasses'] == 3
                        and m['samplesFailed'] == 0, 'sample-mismatch')
                require(e['modelId'] == mid and e['manifestDigest'] == digest
                        and e['systemMemoryGiB'] == system_memory and e['usableGpuMemoryGiB'] == 8
                        and e['providerVersion'] == '0.32.14' and e['backendMode'] == 'cuda'
                        and e['capability'] in CAPS and e['capabilityPassed'] is True
                        and e['platformFamily'] == ('linux' if platform == 'ubuntu' else 'windows'), 'binding-mismatch')
                count += 3
            totals[phase + 'SamplesPassed'] = count
        models.append(dict(modelId=mid, manifestDigest=digest, status='passed', **totals,
                           elapsedSoakSeconds=item['elapsedSoakSeconds']))
    rows = [json.loads(line) for line in (directory/'telemetry.jsonl').read_text().splitlines()]
    telemetry = {}
    for field in ('temperatureC', 'powerW'):
        values = [r[field] for r in rows if r[field] is not None]
        require(values and all(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0 for v in values), 'invalid-telemetry')
        telemetry[field] = dict(samples=len(values), unavailable=len(rows)-len(values),
                                minimum=min(values), maximum=max(values), arithmeticMean=round(mean(values), 3))
    sources = {name: provenance(directory/name) for name in ('status.json', 'telemetry.jsonl')}
    if hwinfo:
        sources['rawHwinfo'] = provenance(hwinfo)
    return dict(schemaVersion=1, kind='haven42-p4000-bounded-inference-evidence',
                observedDate='2026-09-09', platform=platform, operatingSystem=expected_os,
                accelerator='NVIDIA Quadro P4000 8 GB', driverVersion=driver,
                systemMemoryGiB=round(system_memory, 3),
                runtime='Ollama 0.32.14', backend='CUDA', models=models,
                samplesPassed=sum(m['coreSamplesPassed']+m['soakSamplesPassed'] for m in models),
                samplesFailed=0, finalUnload='verified', telemetry=telemetry,
                telemetryMethod='nvidia-smi checkpoints before three-response cells and model preflight; not sustained-load or time-weighted averages',
                powerScope='GPU board only, not wall power; no energy estimate',
                sourceProvenance=sources,
                codingAgent='not-run', nativePackageReview='not-run',
                automaticDefaultChangeAllowed=False, automaticSupportChangeAllowed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--platform', choices=('windows', 'ubuntu'), required=True)
    parser.add_argument('--hwinfo', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.results, args.platform, args.hwinfo), indent=2))
