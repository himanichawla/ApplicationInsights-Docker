#
# ApplicationInsights-Docker
# Copyright (c) Microsoft Corporation
# All rights reserved.
#
# MIT License
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the ""Software""), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

__author__ = 'galha'
import unittest
from appinsights import dockerconvertors


class TestDockerConvertors(unittest.TestCase):
    def test_get_total_blkio_when_total_exists(self):
        expected = 40
        stat = {'blkio_stats': {'io_service_bytes_recursive': [{'op': 'Total', 'value': expected}]}}
        actual = dockerconvertors.get_total_blkio(stat)
        self.assertEqual(expected, actual)

    def test_get_total_blkio_when_total_not_exists(self):
        expected = 0
        stat = {'blkio_stats': {'io_service_bytes_recursive': []}}
        actual = dockerconvertors.get_total_blkio(stat)
        self.assertEqual(expected, actual)

    def test_get_cpu_metric(self):
        samples = [(0, 0), (1, 2), (2, 4), (4, 100)]
        expected_avg = 34.0277778
        expected_min = 2.0833333
        expected_max = 50
        expected_std = 27.6647004
        stats = [(system, {'cpu_stats': {'cpu_usage': {'total_usage': cpu}, 'system_cpu_usage': system}}) for
                 cpu, system in samples]
        metric = dockerconvertors.get_cpu_metric(stats)
        self.assertEqual('% Processor Time', metric['name'])
        self.assertEqual(len(samples) - 1, metric['count'])
        self.assertAlmostEqual(expected_avg, metric['value'], delta=0.01)
        self.assertAlmostEqual(expected_min, metric['min'], delta=0.01)
        self.assertAlmostEqual(expected_max, metric['max'], delta=0.01)
        self.assertAlmostEqual(expected_std, metric['std'], delta=0.01)

    def test_get_cpu_metric_trows_when_stats_is_none(self):
        self.assertRaises(AssertionError, dockerconvertors.get_cpu_metric, None)

    def test_get_cpu_metric_trows_when_stats_is_has_only_one_stat(self):
        stat = [(0, {'cpu_stats': {'cpu_usage': {'total_usage': 0}, 'system_cpu_usage': 0}})]
        self.assertRaises(AssertionError, dockerconvertors.get_cpu_metric, stat)

    def test_get_cpu_metric_trows_when_stats_is_empty(self):
        stat = []
        self.assertRaises(AssertionError, dockerconvertors.get_cpu_metric, stat)

    def test_per_second_metric(self):
        samples = [(0, 1), (1, 2), (2, 3), (3, 10)]
        expected_metric = {'name': 'm1', 'count': len(samples) - 1, 'value': 3, 'min': 1, 'max': 7, 'std': 3.464101615}
        actual_metric = dockerconvertors.get_per_second_metric('m1', lambda s: s, samples)
        self._assert_metrics_equals(expected_metric=expected_metric, actual_metric=actual_metric)

    def test_per_second_metric_rais_when_metric_is_none(self):
        self.assertRaises(AssertionError, dockerconvertors.get_per_second_metric, None, lambda s: s, [(0, 1), (2, 3)])

    def test_per_second_metric_rais_when_func_is_none(self):
        self.assertRaises(AssertionError, dockerconvertors.get_per_second_metric, "metric1", None, [(0, 1), (2, 3)])

    def test_per_second_metric_rais_when_stats_has_only_one_stats(self):
        self.assertRaises(AssertionError, dockerconvertors.get_per_second_metric, 'm1', lambda s: s, [(0, 0)])

    def test_per_second_metric_rais_when_stats_has_zero_stats(self):
        self.assertRaises(AssertionError, dockerconvertors.get_per_second_metric, 'm1', lambda s: s, [])

    def test_get_simple_metric(self):
        samples = [(0, 123), (1, 2321), (3, 2312), (4, -234)]
        expected_metric = {'name': 'm1', 'value': 1130.5, 'count': len(samples), 'min': -234, 'max': 2321,
                           'std': 1377.213249}
        actual_metric = dockerconvertors.get_simple_metric('m1', lambda s: s, samples)
        self._assert_metrics_equals(expected_metric=expected_metric, actual_metric=actual_metric)

    def test_get_simple_metric_rais_when_metric_is_none(self):
        self.assertRaises(AssertionError, dockerconvertors.get_simple_metric, None, lambda s: s, [(0, 1), (2, 3)])

    def test_get_simple_metric_rais_when_func_is_none(self):
        self.assertRaises(AssertionError, dockerconvertors.get_simple_metric, "metric1", None, [(0, 1), (2, 3)])

    def test_get_simple_metric_rais_when_stats_has_only_one_stats(self):
        self.assertRaises(AssertionError, dockerconvertors.get_simple_metric, 'm1', lambda s: s, [(0, 0)])

    def test_get_simple_metric_rais_when_stats_has_zero_stats(self):
        self.assertRaises(AssertionError, dockerconvertors.get_simple_metric, 'm1', lambda s: s, [])

    def _assert_metrics_equals(self, expected_metric, actual_metric):
        self.assertEqual(expected_metric['name'], actual_metric['name'])
        self.assertEqual(expected_metric['count'], actual_metric['count'])
        self.assertAlmostEqual(expected_metric['value'], actual_metric['value'], delta=0.001)
        self.assertAlmostEqual(expected_metric['min'], actual_metric['min'], delta=0.001)
        self.assertAlmostEqual(expected_metric['max'], actual_metric['max'], delta=0.001)
        self.assertAlmostEqual(expected_metric['std'], actual_metric['std'], delta=0.001)

    def test_convert_to_metrics(self):
        time_samples = [0, 10, 20, 30, 40, 50, 60]
        cpu_samples = [0, 1, 2, 5, 9, 19, 22]
        system_samples = [0, 10, 20, 30, 40, 50, 60]
        blkio_samples = [0, 1, 20, 30, 200, 350, 700]
        rx_samples = [0, 0, 0, 101, 120, 120, 230]
        tx_samples = [0, 0, 10, 10, 200, 250, 260]
        memory_samples = [1000000, 1000000, 2000000, 2020000, 3000000, 2000000, 1000000]
        memory_limit = 8000000

        samples = [(time, {'cpu_stats': {'cpu_usage': {'total_usage': cpu}, 'system_cpu_usage': system},
                    'memory_stats': {'limit': memory_limit, 'usage': mem}, 'network': {'rx_bytes': rx, 'tx_bytes': tx},
                    'blkio_stats': {'io_service_bytes_recursive': [{'op': 'Total', 'value': blkio}]}})
                   for time, cpu, system, blkio, rx, tx, mem in
                   zip(time_samples, cpu_samples, system_samples, blkio_samples, rx_samples, tx_samples,
                       memory_samples)]

        expected_metrics = {
            '% Processor Time': {'name': '% Processor Time', 'count': 6, 'value': 36.66666667, 'min': 10, 'max': 100, 'std': 33.26659987},
            'Available Bytes': {'name': 'Available Bytes', 'count': 7, 'value': 6282857.142857143, 'min': 5000000,
             'max': 7000000, 'std': 757225.5121101482},
            'Docker RX Bytes':{'name': 'Docker RX Bytes', 'count': 6, 'value': 3.833333333, 'min': 0, 'max': 11, 'std': 5.262192192},
            'Docker TX Bytes': {'name': 'Docker TX Bytes', 'count': 6, 'value': 4.333333333, 'min': 0, 'max': 19, 'std': 7.420691792},
            'Docker Blkio Bytes': {'name': 'Docker Blkio Bytes', 'count': 6, 'value': 11.66666667, 'min': 0.1, 'max': 35, 'std': 13.61582413}}

        actual_metrics = dockerconvertors.convert_to_metrics(samples)

        for metric in actual_metrics:
            self.assertTrue(metric['name'] in expected_metrics)
            self._assert_metrics_equals(expected_metrics[metric['name']], metric)

    def test_get_container_properties_from_inspect(self):
        expected = {'Docker host': 'host1', 'Docker image': 'image1', 'Docker container id': 'c1', 'Docker container name': 'container1'}
        inspect = {'Name':expected['Docker container name'], 'Id':expected['Docker container id'], 'Config':{'Image': expected['Docker image']}}
        properties = dockerconvertors.get_container_properties_from_inspect(inspect, expected['Docker host'])
        self.assertDictEqual(expected, properties)