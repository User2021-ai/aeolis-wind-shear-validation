"""Integration tests using real AeoLiS initialization and model.update calls.

First run --baseline FILE with the clean audited source. Then run --reference
FILE --output REPORT with the patched source. Generated fixtures are temporary.
"""

import argparse
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from aeolis.model import AeoLiS
from aeolis import wind, shear


REFERENCE = None
FIELDS = ('tau', 'ustar', 'qs', 'qn', 'Ct', 'mass', 'zb')


def make_model(directory, adaptive=False, fractions=1, process_shear=True,
               method='fft', speed=12.):
    directory = Path(directory)
    x, y = np.meshgrid(np.arange(12.) * 2, np.arange(8.) * 2)
    for name, data in [('x', x), ('y', y), ('bed', 2 + .05 * np.cos(2*np.pi*x/24))]:
        np.savetxt(directory / (name + '.txt'), data)
    np.savetxt(directory / 'wind.txt', [[0, speed, 260], [10, speed, 260]])
    options = {
        'xgrid_file': directory / 'x.txt', 'ygrid_file': directory / 'y.txt',
        'bed_file': directory / 'bed.txt', 'wind_file': directory / 'wind.txt',
        'dx': 2, 'dy': 2, 'dt': .1, 'tstop': 1, 'output_times': .1,
        'process_shear': 'T' if process_shear else 'F', 'method_shear': method,
        'method_roughness': 'mean_grainsize_adaptive' if adaptive else 'constant',
        'k': '0.00001', 'grain_size': '0.0003' if fractions == 1 else '0.0002 0.0004',
        'grain_dist': '1.0' if fractions == 1 else '0.5 0.5',
        'visualization': 'F', 'process_separation': 'F',
    }
    # Forward slashes avoid ambiguity in configuration file paths.
    config = directory / 'aeolis.txt'
    config.write_text('\n'.join(f'{key} = {str(value).replace(chr(92), chr(47))}'
                                for key, value in options.items()) + '\n')
    model = AeoLiS(str(config))
    model.initialize()
    return model


def evolve(model):
    initial = model.s['zb'].copy()
    for _ in range(3):
        model.update(.1)
    arrays = {key: model.s[key].copy() for key in FIELDS}
    arrays['initial_zb'] = initial
    arrays['time'] = np.array(model.t)
    return arrays


class FullModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_scalar_full_run_matches_unpatched(self):
        result = evolve(make_model(self.tmp.name))
        with np.load(REFERENCE) as baseline:
            for key, actual in result.items():
                self.assertTrue(np.isfinite(actual).all(), key)
                np.testing.assert_array_equal(actual, baseline[key], err_msg=key)
        self.assertGreater(np.max(np.abs(result['qs'])), 0.)
        self.assertGreater(np.max(np.abs(result['zb'] - result['initial_zb'])), 0.)

    def test_uniform_adaptive_full_run_matches_scalar(self):
        adaptive = evolve(make_model(self.tmp.name, adaptive=True))
        with np.load(REFERENCE) as baseline:
            for key, actual in adaptive.items():
                self.assertTrue(np.isfinite(actual).all(), key)
                np.testing.assert_allclose(actual, baseline[key], rtol=1e-12, atol=1e-14,
                                           err_msg=key)

    def test_uniform_adaptive_change_refreshes_fft(self):
        model = make_model(self.tmp.name, adaptive=True, fractions=2)
        old = model.s['shear'].z0
        total = model.s['mass'][:, :, 0, :].sum(axis=-1)
        model.s['mass'][:, :, 0, 0] = total
        model.s['mass'][:, :, 0, 1] = 0
        model.update(.1)
        self.assertNotEqual(old, model.s['shear'].z0)
        self.assertAlmostEqual(model.s['shear'].z0, .0002 / 30)
        np.testing.assert_allclose(model.s['ustar0'],
                                   12 * model.p['kappa'] / np.log(model.p['z']/(.0002/30)))

    def test_varying_adaptive_update_rejected_before_bed_change(self):
        model = make_model(self.tmp.name, adaptive=True, fractions=2)
        total = model.s['mass'][0, 0, 0, :].sum()
        model.s['mass'][0, 0, 0, :] = [total, 0]
        bed, mass, time = model.s['zb'].copy(), model.s['mass'].copy(), model.t
        with self.assertRaisesRegex(NotImplementedError, 'Spatially varying'):
            model.update(.1)
        np.testing.assert_array_equal(model.s['zb'], bed)
        np.testing.assert_array_equal(model.s['mass'], mass)
        self.assertEqual(model.t, time)

    def test_zero_wind_refreshes_roughness(self):
        model = make_model(self.tmp.name, speed=0)
        model.p['k'] *= 2
        model.update(.1)
        self.assertEqual(model.s['shear'].z0, model.p['k'])
        np.testing.assert_array_equal(model.s['tau'], 0.)

    def test_disabled_shear_allows_varying_roughness(self):
        model = make_model(self.tmp.name, adaptive=True, fractions=2, process_shear=False)
        model.s['mass'][0, 0, 0, :] = [model.s['mass'][0, 0, 0, :].sum(), 0]
        model.update(.1)
        self.assertGreater(model.t, 0)
        self.assertTrue(np.isfinite(model.s['tau']).all())

    def test_direct_shear_refreshes(self):
        model = make_model(self.tmp.name)
        wind.interpolate(model.s, model.p, 0)
        model.p['k'] *= 2
        wind.shear(model.s, model.p)
        self.assertEqual(model.s['shear'].z0, model.p['k'])

    def test_non_fft_shear_accepts_adaptive_update(self):
        model = make_model(self.tmp.name, adaptive=True, fractions=2, method='duna2d')
        model.s['mass'][0, 0, 0, :] = [model.s['mass'][0, 0, 0, :].sum(), 0]
        model.update(.1)
        self.assertGreater(model.t, 0)
        self.assertTrue(np.isfinite(model.s['tau']).all())

    def test_direct_constructor_rejects_varying_field(self):
        x, y = np.meshgrid(np.arange(8.), np.arange(8.))
        with self.assertRaises(NotImplementedError):
            shear.WindShear(x, y, x*0, 1., 1., 100., 10., .001+x*.0001, 10.)

    def test_direct_compute_rejects_changed_field_at_zero_wind(self):
        model = make_model(self.tmp.name)
        obj = model.s['shear']
        obj.igrid = {'z': model.s['zb']}
        obj.z0 = .001 + model.s['x'] * .0001
        with self.assertRaises(NotImplementedError):
            obj.compute_shear(0.)


def main():
    global REFERENCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.baseline:
        with tempfile.TemporaryDirectory() as folder:
            np.savez(args.baseline, **evolve(make_model(folder)))
        print('Saved original full-run baseline:', args.baseline)
        return
    if not args.reference or not args.output:
        parser.error('--reference and --output are required for integration tests')
    REFERENCE = args.reference
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(FullModelTests))
    summary = {'scope': 'Synthetic 12x8 grid, real initialize/update, three 0.1 s steps for equivalence',
               'tests_run': result.testsRun, 'failures': len(result.failures),
               'errors': len(result.errors), 'passed': result.wasSuccessful(),
               'failure_details': [str(test) + '\n' + detail for test, detail
                                   in result.failures + result.errors]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
