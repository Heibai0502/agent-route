#!/usr/bin/env python3
"""Build one verified routing-data generation; never copy upstream templates."""
import datetime
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import time
import urllib.request
from public_formats import export

SOURCES = {
    'china_domains': 'https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/direct-list.txt',
    'foreign_domains': 'https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/proxy-list.txt',
    'private_domains': 'https://raw.githubusercontent.com/Loyalsoldier/domain-list-custom/release/private.txt',
    'china_ip': 'https://raw.githubusercontent.com/Loyalsoldier/geoip/release/text/cn.txt',
    'advertising_domains': 'https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/reject-list.txt',
}
LOCAL_NETWORKS = [
    '0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
    '169.254.0.0/16', '172.16.0.0/12', '192.168.0.0/16',
    '224.0.0.0/4', '::/128', '::1/128', 'fc00::/7', 'fe80::/10', 'ff00::/8',
]
DOMAIN = re.compile(r'^[-_a-zA-Z0-9]+(?:\.[-_a-zA-Z0-9]+)*$')


def fetch(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'vpsct-direct-rules-builder'})
            with urllib.request.urlopen(request, timeout=30) as response:
                limit = 16 * 1024 * 1024
                data = response.read(limit + 1)
                assert response.status == 200 and data
                if len(data) > limit:
                    raise ValueError('rule_source_too_large')
                return data.decode('utf-8')
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def domains(text):
    exact, suffix = set(), set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(('#', '//')):
            continue
        if line.startswith(('regexp:', 'keyword:')):
            continue
        target = exact if line.startswith('full:') else suffix
        if line.startswith(('full:', 'domain:')):
            line = line.split(':', 1)[1]
        if line.startswith('.'):
            line = line[1:]
            target = suffix
        assert DOMAIN.fullmatch(line), 'invalid_domain_source_line'
        target.add(line.lower())
    return exact, suffix


def parents(domain):
    parts = domain.split('.')
    return ['.'.join(parts[index:]) for index in range(len(parts))]


def exclude_foreign(exact, suffix, foreign_exact, foreign_suffix):
    foreign_parents = {parent for domain in foreign_exact | foreign_suffix for parent in parents(domain)}
    exact = {domain for domain in exact if domain not in foreign_exact
             and not any(parent in foreign_suffix for parent in parents(domain))}
    # A positive suffix cannot express a foreign child exception. Remove such
    # broad entries (including the .cn umbrella); specific domestic domains and
    # China IPs still match the same DIRECT dataset, with proxy DNS for IP lookup.
    suffix = {domain for domain in suffix if domain not in foreign_parents
              and not any(parent in foreign_suffix for parent in parents(domain))}
    return exact, suffix


def matches(domain, exact, suffix):
    return domain in exact or any(parent in suffix for parent in parents(domain))


def advertising_domains(text):
    exact, suffix = domains(text)
    if not 1000 <= len(exact) + len(suffix) <= 500000:
        raise ValueError('advertising_dataset_empty_or_oversized')
    for name in exact | suffix:
        if '.' not in name or name in {'com.cn', 'net.cn', 'org.cn', 'co.uk', 'com.au', 'co.jp'}:
            raise ValueError('advertising_domain_too_broad')
        try:
            ipaddress.ip_address(name)
        except ValueError:
            pass
        else:
            raise ValueError('advertising_ip_forbidden')
    for host in ('www.baidu.com', 'www.qq.com', 'login.weixin.qq.com', 'www.taobao.com', 'www.jd.com',
                 'www.google.com', 'api.github.com', 'www.apple.com', 'login.microsoftonline.com',
                 'huoshua.net', 'claude.ai', 'anthropic.com', 'claude.com'):
        if matches(host, exact, suffix):
            raise ValueError('advertising_blocks_protected_site')
    if not matches('ad.doubleclick.net', exact, suffix):
        raise ValueError('advertising_coverage_lost')
    return sorted(exact), sorted(suffix)


def private_domains(text):
    exact, suffix = domains(text)
    local_tlds = {'internal', 'localdomain', 'example', 'invalid', 'localhost', 'test', 'local', 'lan'}
    if not 1 <= len(exact) + len(suffix) <= 10000:
        raise ValueError('private_dataset_empty_or_oversized')
    for name in exact | suffix:
        if ('.' not in name and name not in local_tlds) or name in {'com.cn', 'net.cn', 'org.cn', 'co.uk', 'com.au', 'co.jp'}:
            raise ValueError('private_domain_too_broad')
    for host in ('www.google.com', 'api.github.com', 'www.apple.com', 'icloud.com',
                 'huoshua.net', 'claude.ai', 'anthropic.com', 'claude.com'):
        if matches(host, exact, suffix):
            raise ValueError('private_overrides_public_service')
    return exact, suffix


def build(raw, output):
    ad_exact, ad_suffix = advertising_domains(raw['advertising_domains'])
    exact, suffix = domains(raw['china_domains'])
    assert len(exact) + len(suffix) > 1000, 'china_domain_dataset_empty_or_truncated'
    foreign_exact, foreign_suffix = domains(raw['foreign_domains'])
    assert len(foreign_exact) + len(foreign_suffix) > 1000, 'foreign_domain_dataset_empty_or_truncated'
    before_domain_count = len(exact) + len(suffix)
    exact, suffix = exclude_foreign(exact, suffix, foreign_exact, foreign_suffix)
    excluded_count = before_domain_count - len(exact) - len(suffix)
    assert not any(matches(domain, exact, suffix) for domain in
                   ('www.gstatic.com', 'www.google.com', 'www.wikipedia.org', 'api.github.com')), 'foreign_domain_would_be_direct'
    assert all(matches(domain, exact, suffix) for domain in
               ('www.baidu.com', 'www.qq.com', 'www.taobao.com', 'www.jd.com')), 'domestic_domain_would_be_proxied'
    private_exact, private_suffix = private_domains(raw['private_domains'])
    exact.update(private_exact)
    suffix.update(private_suffix | {'local', 'lan', 'home.arpa'})
    exact.add('localhost')
    networks = set(LOCAL_NETWORKS)
    china_network_count = 0
    for line in raw['china_ip'].splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        network = ipaddress.ip_network(line, strict=False)
        assert network.prefixlen != 0, 'universal_direct_route_forbidden'
        networks.add(str(network))
        china_network_count += 1
    assert china_network_count > 1000, 'china_ip_dataset_empty_or_truncated'
    ordered_networks = sorted(networks, key=lambda n: (ipaddress.ip_network(n).version,
                                                      int(ipaddress.ip_network(n).network_address),
                                                      ipaddress.ip_network(n).prefixlen))
    output = Path(output)
    output.mkdir(exist_ok=True)
    rules = ['# Domestic and local DIRECT dataset. Other traffic uses the client proxy.']
    rules += ['DOMAIN,' + name for name in sorted(exact)]
    rules += ['DOMAIN-SUFFIX,' + name for name in sorted(suffix)]
    rules += [('IP-CIDR6' if ':' in network else 'IP-CIDR') + ',' + network
              for network in ordered_networks]
    (output / 'direct.list').write_text('\n'.join(rules) + '\n')
    (output / 'direct.domains').write_text('\n'.join(sorted(exact) + ['.' + name for name in sorted(suffix)]) + '\n')
    (output / 'private.domains').write_text('\n'.join(sorted(private_exact) + ['.' + name for name in sorted(private_suffix)]) + '\n')
    # Preserve the exact foreign input used for conflict removal in this build.
    # Consumers must not combine this generation with a moving upstream branch.
    (output / 'proxy-source.txt').write_text(raw['foreign_domains'])
    (output / 'direct.ipcidr').write_text('\n'.join(
        ('IP-CIDR6' if ':' in network else 'IP-CIDR') + ',' + network for network in ordered_networks) + '\n')
    source = {'version': 3, 'rules': [{'domain': sorted(exact)},
                                     {'domain_suffix': sorted(suffix)},
                                     {'ip_cidr': ordered_networks}]}
    (output / 'direct.json').write_text(json.dumps(source, separators=(',', ':')) + '\n')
    (output / 'reject.domains').write_text('\n'.join(ad_exact + ['.' + name for name in ad_suffix]) + '\n')
    (output / 'reject.list').write_text('\n'.join(['DOMAIN,' + name for name in ad_exact] +
                                                ['DOMAIN-SUFFIX,' + name for name in ad_suffix]) + '\n')
    ad_conditions = ([{'domain': ad_exact}] if ad_exact else []) + ([{'domain_suffix': ad_suffix}] if ad_suffix else [])
    (output / 'reject.json').write_text(json.dumps({'version': 3, 'rules': ad_conditions}, separators=(',', ':')) + '\n')
    generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    public_files = export(output, {
        'direct': (exact, suffix), 'proxy': (foreign_exact, foreign_suffix),
        'private': (private_exact, private_suffix), 'reject': (ad_exact, ad_suffix),
    }, ordered_networks, generated_at)
    manifest = {
        'generated_at_utc': generated_at,
        'scope': 'domestic_direct_and_adblock', 'sources': SOURCES,
        'source_sha256': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in raw.items()},
        'counts': {'exact_domains': len(exact), 'suffix_domains': len(suffix), 'ip_prefixes': len(networks),
                   'adblock_domains': len(ad_exact) + len(ad_suffix),
                   'private_domains': len(private_exact) + len(private_suffix)},
        'excluded_overseas_domain_entries': excluded_count,
        'files': {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                  for name in ['direct.list', 'direct.json', 'direct.domains', 'direct.ipcidr',
                               'reject.domains', 'reject.list', 'reject.json', 'private.domains', 'proxy-source.txt']},
        'application_or_country_groups_generated': False,
        'client_templates_generated': False,
        'public_formats_version': 1,
    }
    manifest['files'].update(public_files)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    assert {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()} == set(manifest['files']) | {'manifest.json'}
    return manifest


def main():
    raw = {name: fetch(url) for name, url in SOURCES.items()}
    manifest = build(raw, Path('generated'))
    print(json.dumps(manifest['counts']))


if __name__ == '__main__':
    main()
