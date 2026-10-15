"""Read Linux host and HA process metrics without Docker memory accounting."""
import datetime
import json
import os
from pathlib import Path

CACHE = Path(os.environ.get('HA_RESOURCE_CACHE', '/config/.ha-resource-sample.json'))


def sample():
    cpu = [int(v) for v in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
    total, idle = sum(cpu), cpu[3] + cpu[4]
    mem = {line.split(':')[0]: int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()}
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            args = (directory / 'cmdline').read_bytes().split(b'\0')
            if not any(args[i:i+2] == [b'-m', b'homeassistant'] for i in range(len(args)-1)):
                continue
            fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
            ticks = int(fields[11]) + int(fields[12])
            start = int(fields[19])
            status = (directory / 'status').read_text().splitlines()
            rss = int(next(line.split()[1] for line in status if line.startswith('VmRSS:')))
            break
        except (OSError, ValueError, StopIteration):
            continue
    else:
        raise RuntimeError('Home Assistant process not found')
    identity = f"{Path('/proc/sys/kernel/random/boot_id').read_text().strip()}:{directory.name}:{start}"
    current = {'total': total, 'idle': idle, 'ticks': ticks, 'identity': identity}
    try:
        previous = json.loads(CACHE.read_text())
    except (OSError, ValueError):
        previous = {}
    # A valid JSON document can still have the wrong shape or partial fields.
    # Treat this disposable cache as a first sample and rebuild it.
    if (
        not isinstance(previous, dict)
        or not isinstance(previous.get('identity'), str)
        or any(type(previous.get(key)) is not int or previous[key] < 0
               for key in ('total', 'idle', 'ticks'))
        or previous['idle'] > previous['total']
    ):
        previous = {}
    delta = total - previous.get('total', total)
    same_process = previous.get('identity') == identity
    host_cpu = ha_cpu = None
    if delta > 0 and same_process:
        host_cpu = round(max(0, min(100, 100 * (1 - (idle - previous['idle']) / delta))), 2)
        ha_cpu = round(max(0, min(100, 100 * (ticks - previous['ticks']) / delta)), 2)
    temporary = CACHE.with_suffix('.tmp')
    temporary.write_text(json.dumps(current))
    temporary.replace(CACHE)
    result = {
        'sample_time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'pi_cpu': host_cpu,
        'ha_cpu': ha_cpu,
        'ha_memory': round(rss / 1024, 1),
        'pi_memory': round((mem['MemTotal'] - mem['MemAvailable']) / 1024, 1),
        'pi_memory_percent': round(100 * (1 - mem['MemAvailable'] / mem['MemTotal']), 1),
        'pi_memory_available': round(mem['MemAvailable'] / 1024, 1),
        'pi_memory_total': round(mem['MemTotal'] / 1024, 1),
        'ha_uptime_hours': round((float(Path('/proc/uptime').read_text().split()[0]) - start / os.sysconf('SC_CLK_TCK')) / 3600, 2),
    }
    thermal = Path('/sys/class/thermal/thermal_zone0/temp')
    result['pi_temperature'] = round(int(thermal.read_text()) / 1000, 1) if thermal.exists() else None
    try:
        rollup = (directory / 'smaps_rollup').read_text().splitlines()
        result['ha_pss'] = round(int(next(line.split()[1] for line in rollup if line.startswith('Pss:'))) / 1024, 1)
    except (OSError, StopIteration):
        result['ha_pss'] = None
    return result


if __name__ == '__main__':
    print(json.dumps(sample()))
