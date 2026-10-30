"""Offline native format checks. Never start a proxy or change an active profile."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from public_formats import BASE_URL, DATASETS


def checked(command):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True, timeout=90)
    output = result.stdout + result.stderr
    if result.returncode or re.search(r'\b(WARN(?:ING)?|ERROR|FATAL|deprecated)\b', output, re.I):
        raise RuntimeError('native validation failed: ' + output[:3000])


def validate(generated, mihomo, sing_box, surge=None):
    import yaml  # Validation only; the data builder has no third-party dependencies.
    examples = Path(__file__).resolve().parents[1] / 'examples'
    # Shadowrocket has no local native validator: check only the portable fragment.
    shadow_lines = [line.strip() for line in (examples / 'shadowrocket.conf').read_text().splitlines()
                    if line.strip() and not line.startswith(('#', '['))]
    expected = ['RULE-SET,' + BASE_URL + 'surge/' + name + '.list,'
                + ('REJECT' if name == 'reject' else 'PROXY' if name == 'proxy' else 'DIRECT')
                for name in DATASETS] + ['FINAL,PROXY']
    if shadow_lines != expected:
        raise ValueError('shadowrocket_fragment_order_or_url_invalid')
    with tempfile.TemporaryDirectory(prefix='routing-native-') as folder:
        work = Path(folder)
        for dataset in DATASETS:
            behavior = 'ipcidr' if dataset == 'cn-ip' else 'domain'
            checked([mihomo, 'convert-ruleset', behavior, 'yaml', generated / ('mihomo/' + dataset + '.yaml'), work / (dataset + '.mrs')])
            checked([sing_box, 'rule-set', 'compile', '--output', work / (dataset + '.srs'), generated / ('sing-box/' + dataset + '.json')])

        config = yaml.safe_load((examples / 'mihomo.yaml').read_text())
        config.update({'mode': 'rule', 'proxies': [{'name': 'PROXY', 'type': 'socks5', 'server': '127.0.0.1', 'port': 9}]})
        for provider in config['rule-providers'].values():
            source = generated / provider['url'].removeprefix(BASE_URL)
            destination = work / provider['path']
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            provider['type'] = 'file'
            provider.pop('url'); provider.pop('proxy'); provider.pop('interval')
        path = work / 'mihomo.yaml'
        path.write_text(yaml.safe_dump(config, sort_keys=False))
        checked([mihomo, '-t', '-d', work, '-f', path])

        config = json.loads((examples / 'sing-box.json').read_text())
        config['outbounds'] = [{'type': 'direct', 'tag': 'DIRECT'},
                               {'type': 'socks', 'tag': 'PROXY', 'server': '127.0.0.1', 'server_port': 9}]
        config['experimental']['cache_file']['path'] = str(work / 'cache.db')
        remote = work / 'sing-box-remote.json'
        remote.write_text(json.dumps(config))
        checked([sing_box, 'check', '-c', remote])
        for rule_set in config['route']['rule_set']:
            rule_set['path'] = str(generated / rule_set.pop('url').removeprefix(BASE_URL))
            rule_set['type'] = 'local'
            rule_set.pop('http_client'); rule_set.pop('update_interval')
        path = work / 'sing-box-local.json'
        path.write_text(json.dumps(config))
        checked([sing_box, 'check', '-c', path])
        if surge:
            content = (examples / 'surge.conf').read_text().replace(BASE_URL, str(generated) + '/')
            path = work / 'surge.conf'
            path.write_text('[General]\nloglevel = notify\n[Proxy]\nPROXY = socks5, 127.0.0.1, 9\n' + content)
            checked([surge, '--check', path])
    return {'mihomo_datasets': 5, 'sing_box_datasets': 5, 'example_checks': 3 + bool(surge),
            'surge_checked': bool(surge), 'shadowrocket': 'structure_only', 'live_client_changed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generated', type=Path, default=Path('generated'))
    parser.add_argument('--mihomo', required=True)
    parser.add_argument('--sing-box', required=True)
    parser.add_argument('--surge')
    args = parser.parse_args()
    print(json.dumps(validate(args.generated.resolve(), args.mihomo, args.sing_box, args.surge)))


if __name__ == '__main__':
    main()
