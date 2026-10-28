"""Run with unittest discovery; includes comparison with the real FFT operator."""

import unittest

import numpy as np

from b01_roughness_guard import scalar_fft_roughness
from b01_roughness_reproducer import evaluate


class RoughnessGuardTests(unittest.TestCase):
    def test_scalar_and_zero_dimensional(self):
        for value in (0.001, np.array(0.001)):
            with self.subTest(value=value):
                self.assertEqual(scalar_fft_roughness(value, (64, 64)), 0.001)

    def test_uniform_grid_preserves_original_shear(self):
        baseline = evaluate(0.001)
        field = np.full((64, 64), 0.001)
        actual = evaluate(scalar_fft_roughness(field, field.shape))
        for before, after in zip(baseline, actual):
            self.assertTrue(np.isfinite(after).all())
            np.testing.assert_array_equal(before, after)
        np.testing.assert_array_equal(field, np.full((64, 64), 0.001))

    def test_variable_grid_rejected(self):
        field = np.full((64, 64), 0.001)
        field[0, 0] = 0.002
        with self.assertRaisesRegex(NotImplementedError, "Spatially varying"):
            scalar_fft_roughness(field, field.shape)

    def test_even_small_variation_is_not_averaged(self):
        field = np.full((64, 64), 0.001)
        field[0, 0] = np.nextafter(0.001, np.inf)
        with self.assertRaises(NotImplementedError):
            scalar_fft_roughness(field, field.shape)

    def test_wrong_shapes_rejected(self):
        for field in (np.full((32, 64), 0.001), np.array([0.001]), np.array([])):
            with self.subTest(shape=field.shape):
                with self.assertRaises(ValueError):
                    scalar_fft_roughness(field, (64, 64))

    def test_invalid_values_rejected(self):
        for value in (0., -0.001, np.nan, np.inf, -np.inf, True, "0.001", 0.001j):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    scalar_fft_roughness(value, (64, 64))
        for value in (0., np.nan, np.inf):
            field = np.full((64, 64), 0.001)
            field[0, 0] = value
            with self.subTest(array_value=value):
                with self.assertRaises(ValueError):
                    scalar_fft_roughness(field, field.shape)


if __name__ == "__main__":
    unittest.main()
