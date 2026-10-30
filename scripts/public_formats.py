"""Credential-free, native rule-set exports from one validated source generation."""
import hashlib
import ipaddress
import json

BASE_URL = 'https://raw.githubusercontent.com/Heibai0502/surge-rules/release/'
DATASETS = ('private', 'reject', 'proxy', 'direct', 'cn-ip')
FORMATS = {'surge': '.list', 'mihomo': '.yaml', 'sing-box': '.json'}
LOCAL = tuple(map(ipaddress.ip_network, (
    '0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
    '169.254.0.0/16', '172.16.0.0/12', '192.168.0.0/16', '224.0.0.0/4',
    '::/128', '::1/128', 'fc00::/7', 'fe80::/10', 'ff00::/8')))
SYNTHETIC = tuple(map(ipaddress.ip_network, ('198.18.0.0/15', 'fc00::/18', 'fd00:6152::/64')))


def public_china_networks(networks, minimum=1000):
    """Match the existing VpsCT public-CN filter, without exporting its deployment."""
    result = []
    for value in networks:
        network = ipaddress.ip_network(value, strict=True)
        if network in LOCAL:
            continue
        if any(network.version == item.version and network.overlaps(item)
               for item in LOCAL + SYNTHETIC):
            raise ValueError('china_ip_overlaps_local_or_synthetic_range')
        result.append(network)
    if any(sum(n.version == version for n in result) < minimum for version in (4, 6)):
        raise ValueError('china_ip_address_family_empty_or_truncated')
    return sorted(result, key=lambda n: (n.version, int(n.network_address), n.prefixlen))


def export(output, domain_groups, networks, generated_at):
    files, entries = {}, []
    for dataset in DATASETS:
        if dataset == 'cn-ip':
            payload = list(map(str, public_china_networks(networks)))
            lines = [('IP-CIDR6,' if ':' in value else 'IP-CIDR,') + value for value in payload]
            source = {'version': 3, 'rules': [{'ip_cidr': payload}]}
        else:
            exact, suffix = [sorted(set(values)) for values in domain_groups[dataset]]
            payload = exact + ['+.' + value for value in suffix]
            lines = ['DOMAIN,' + value for value in exact] + ['DOMAIN-SUFFIX,' + value for value in suffix]
            source = {'version': 3, 'rules': ([{'domain': exact}] if exact else [])
                      + ([{'domain_suffix': suffix}] if suffix else [])}
        contents = {
            'surge': '\n'.join(lines) + '\n',
            'mihomo': 'payload:\n' + ''.join('  - ' + json.dumps(value) + '\n' for value in payload),
            'sing-box': json.dumps(source, separators=(',', ':')) + '\n',
        }
        resources = {}
        for format_name, content in contents.items():
            name = format_name + '/' + dataset + FORMATS[format_name]
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode('utf-8'))
            files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            resources[format_name] = {'path': name, 'url': BASE_URL + name,
                                      'sha256': files[name], 'entries': len(payload)}
        entries.append({'id': dataset,
                        'action': 'REJECT' if dataset == 'reject' else 'PROXY' if dataset == 'proxy' else 'DIRECT',
                        'mihomo_behavior': 'ipcidr' if dataset == 'cn-ip' else 'domain',
                        'resources': resources})
    index = {
        'schema_version': 1, 'scope': 'public_routing_data_only',
        'generated_at_utc': generated_at, 'base_url': BASE_URL,
        'manifest_url': BASE_URL + 'manifest.json',
        'agent_guide_url': 'https://raw.githubusercontent.com/Heibai0502/surge-rules/master/AGENTS.md',
        'privacy_guide_url': 'https://github.com/Heibai0502/surge-rules/blob/master/docs/DNS-WEBRTC.md',
        'update_interval_seconds': 86400, 'max_source_age_seconds': 172800,
        'order': ['user-and-node-exceptions', 'lan', *DATASETS, 'final-proxy'],
        'datasets': entries,
        'credentials_required': False, 'contains_nodes': False,
        'dns_configuration_included': False, 'webrtc_protection_included': False,
    }
    path = output / 'index.json'
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    files['index.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files
