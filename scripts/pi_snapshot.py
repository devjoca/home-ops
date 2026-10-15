"""Capture a small read-only Pi health snapshot through an existing SSH login."""
import argparse
import datetime
import json
import subprocess
from pathlib import Path

COMMANDS = {
    'host': 'date -Is; uptime; free -m; df -h /',
    'thermal': 'vcgencmd measure_temp; vcgencmd get_throttled',
    'docker': 'docker system df; docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Image}}"',
    'journal': 'journalctl --disk-usage',
    'processes': 'ps -eo comm,rss --sort=-rss | head -10',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, help='Existing SSH destination, USER@HOST')
    parser.add_argument('--output', type=Path, help='Private output path; otherwise prints JSON')
    args = parser.parse_args()
    if args.host.startswith('-') or any(char.isspace() for char in args.host):
        parser.error('--host must be a single SSH destination, not options')
    result = {'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checks': {}}
    for name, command in COMMANDS.items():
        try:
            run = subprocess.run(
                ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '--', args.host, command],
                capture_output=True, text=True, timeout=30,
            )
            result['checks'][name] = {'exit_code': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr}
        except (OSError, subprocess.TimeoutExpired) as error:
            result['checks'][name] = {'error': type(error).__name__}
    output = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
        args.output.chmod(0o600)
        print(f'Saved {len(result["checks"])} checks to {args.output}')
    else:
        print(output, end='')
    return 0 if all(check.get('exit_code') == 0 for check in result['checks'].values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
