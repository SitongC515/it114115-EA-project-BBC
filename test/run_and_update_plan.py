import unittest
import re
import os
import sys
import importlib.util
from pathlib import Path

# Ensure project root is on sys.path so tests can `import app` etc.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

PHASES = {n: f'test/test_phase{n}.py' for n in range(6)}


def load_module_from_path(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'Cannot load spec for {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_phase(test_path):
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2)
    try:
        abs_path = os.path.abspath(test_path)
        module_name = f'project_{os.path.basename(abs_path).replace(".py","")}'
        module = load_module_from_path(abs_path, module_name)
        suite = loader.loadTestsFromModule(module)
    except Exception as e:
        return {'status': 'error', 'reason': str(e)}
    result = runner.run(suite)
    if result.errors or result.failures:
        if result.skipped and (len(result.skipped) == (result.testsRun if result.testsRun else 0)):
            return {'status': 'skipped'}
        return {'status': 'failed', 'failures': len(result.failures) + len(result.errors)}
    if result.skipped:
        return {'status': 'skipped'}
    return {'status': 'passed'}


def update_plan(phase_results, plan_path='MOVING_TO_BBC_PLAN.md'):
    p = Path(plan_path)
    text = p.read_text(encoding='utf-8')
    for n, res in phase_results.items():
        test_path = f'test/test_phase{n}.py'
        # find line that contains this test path
        pattern = re.compile(r'^([ \t\-]*\[.\])\s*`' + re.escape(test_path) + r'`.*$', re.M)
        replacement_box = {
            'passed': '[x]',
            'failed': '[ ]',
            'skipped': '[ ]',
            'error': '[ ]'
        }[res['status']]
        # Also prepare status text
        status_text = res['status'].capitalize()
        new_line = f'- {replacement_box} `{test_path}` — {status_text}'
        # If the line exists, replace it; otherwise insert under the Phase header
        if pattern.search(text):
            text = pattern.sub(new_line, text)
        else:
            # try to find Phase header and insert a Tests: block
            header = f'## Phase {n} '
            idx = text.find(header)
            if idx != -1:
                # find next newline after header and insert Tests block
                insert_at = text.find('\n', idx)
                insert_text = '\n  - Tests:\n    ' + new_line + '\n'
                text = text[:insert_at+1] + insert_text + text[insert_at+1:]
    p.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    results = {}
    for n, module in PHASES.items():
        print(f'Running Phase {n} tests ({module})...')
        results[n] = run_phase(module)
        print(f'Phase {n} result: {results[n]}\n')
    print('Updating MOVING_TO_BBC_PLAN.md with results...')
    update_plan(results)
    print('Update complete.')
