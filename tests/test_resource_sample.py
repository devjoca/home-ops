import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('collector', Path(__file__).resolve().parents[1] / 'scripts/resource_sample.py')
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


class ResourceSampleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.write('/proc/stat', 'cpu 1000 0 100 5000 0 0 0 0 0 0\n')
        self.write('/proc/meminfo', 'MemTotal: 4000000 kB\nMemAvailable: 3000000 kB\n')
        self.write('/proc/71/cmdline', 'python3\x00-P\x00-m\x00homeassistant\x00--config\x00/config\x00')
        self.write('/proc/71/stat', self.process_stat(100))
        self.write('/proc/71/status', 'VmRSS: 409600 kB\n')
        self.write('/proc/71/smaps_rollup', 'Pss: 400000 kB\n')
        self.write('/proc/sys/kernel/random/boot_id', 'fixture-boot')
        self.write('/proc/uptime', '1000 0\n')
        self.write('/sys/class/thermal/thermal_zone0/temp', '60000')
        cache = self.root / 'config/cache.json'
        cache.parent.mkdir()
        self.cache_patch = patch.object(collector, 'CACHE', cache)
        self.path_patch = patch.object(collector, 'Path', lambda value: self.root / str(value).lstrip('/'))
        self.cache_patch.start()
        self.path_patch.start()
        self.addCleanup(self.cache_patch.stop)
        self.addCleanup(self.path_patch.stop)

    def write(self, name, content):
        destination = self.root / name.lstrip('/')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)

    @staticmethod
    def process_stat(ticks):
        fields = ['0'] * 22
        fields[0], fields[11], fields[19] = 'S', str(ticks), '100'
        return '71 (python3) ' + ' '.join(fields)

    def test_first_sample_and_total_capacity_cpu(self):
        first = collector.sample()
        self.assertIsNone(first['pi_cpu'])
        self.assertIsNone(first['ha_cpu'])
        self.assertEqual(first['ha_memory'], 400)
        self.assertEqual(first['pi_memory_percent'], 25)
        self.write('/proc/stat', 'cpu 1020 0 110 5070 0 0 0 0 0 0\n')
        self.write('/proc/71/stat', self.process_stat(110))
        second = collector.sample()
        self.assertEqual(second['pi_cpu'], 30)
        self.assertEqual(second['ha_cpu'], 10)

    def test_bad_cache_recovers_current_telemetry(self):
        for bad in ['not json', '[]', 'null', '{"identity":"fixture-boot:71:100","total":0}', '{"identity":"x","total":2,"idle":3,"ticks":1}']:
            with self.subTest(cache=bad):
                collector.CACHE.write_text(bad)
                sample = collector.sample()
                self.assertIsNone(sample['ha_cpu'])
                self.assertEqual(sample['ha_memory'], 400)
                self.assertEqual(sample['pi_temperature'], 60)
                self.assertIsInstance(json.loads(collector.CACHE.read_text()), dict)

    def test_process_identity_change_resets_cpu(self):
        collector.sample()
        self.write('/proc/sys/kernel/random/boot_id', 'new-fixture-boot')
        self.write('/proc/stat', 'cpu 1020 0 110 5070 0 0 0 0 0 0\n')
        self.assertIsNone(collector.sample()['ha_cpu'])

    def test_pss_is_optional(self):
        (self.root / 'proc/71/smaps_rollup').unlink()
        sample = collector.sample()
        self.assertIsNone(sample['ha_pss'])
        self.assertEqual(sample['ha_memory'], 400)


if __name__ == '__main__':
    unittest.main()
