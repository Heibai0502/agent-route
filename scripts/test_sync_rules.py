import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from sync_rules import operate, selected, locked, validate_manifest, get, compare, parse_integration
from unittest.mock import patch, MagicMock

def change(version, kind='docs'):
    return {'version':version,'date':'2026-10-31','class':kind,'summary':'s','action':'a'}

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)/'cache'
        self.sha = 'a'*40; self.bad = None; self.age = 0
    def tearDown(self): self.temp.cleanup()
    def fetch(self, url):
        if self.bad == 'offline': raise OSError('offline')
        if url.endswith('/commits/release'): return json.dumps({'sha':self.sha}).encode()
        date=(datetime.now(timezone.utc)-timedelta(hours=self.age)).isoformat()
        # Stable within a download transaction.
        if url.endswith('/manifest.json'):
            self.data={n:b'payload' for n in selected('all')}
            self.data['index.json']=json.dumps({'schema_version':1,'generated_at_utc':date}).encode()
            self.manifest={'schema_version':1,'scope':'domestic_direct_and_adblock','generated_at_utc':date,'files':{n:hashlib.sha256(v).hexdigest() for n,v in self.data.items()}}
            if self.bad=='path': self.manifest['files']['../escape']='0'*64
            return json.dumps(self.manifest).encode()
        name=url.split('/'+self.sha+'/')[1]
        if self.bad=='interrupt': raise KeyboardInterrupt()
        return b'corrupt' if self.bad=='hash' else self.data[name]
    def sync(self): return operate('sync',self.root,fetch=self.fetch)
    def test_lifecycle_and_local_rollback(self):
        self.assertEqual(self.sync()['status'],'updated')
        self.assertEqual(self.sync()['status'],'unchanged')
        self.sha='b'*40;self.sync();self.bad='offline'
        self.assertEqual(operate('rollback',self.root)['generation'],'a'*40+'-all')
        self.assertEqual(operate('verify',self.root)['status'],'verified')
    def test_failed_updates_preserve_pointer(self):
        self.sync();before=(self.root/'current.json').read_bytes();self.sha='b'*40
        for bad in ('offline','path','hash','interrupt'):
            self.bad=bad
            with self.subTest(bad=bad),self.assertRaises((ValueError,OSError,KeyboardInterrupt)):self.sync()
            self.assertEqual((self.root/'current.json').read_bytes(),before)
        self.bad=None;self.age=49
        with self.assertRaises(ValueError):self.sync()
        self.assertEqual((self.root/'current.json').read_bytes(),before)
    def test_corruption_detected(self):
        result=self.sync();(Path(result['directory'])/'surge/direct.list').write_bytes(b'bad')
        with self.assertRaises(ValueError):operate('verify',self.root)
    def test_missing_cache_and_rollback(self):
        for command in ('verify','status','rollback'):
            with self.assertRaises(ValueError):operate(command,self.root)
    def test_lock_exclusion_and_crash_release(self):
        script="from pathlib import Path; from sync_rules import locked; import sys,time;\nwith locked(Path(sys.argv[1])):\n print('locked',flush=True); time.sleep(30)"
        p=subprocess.Popen([sys.executable,'-B','-c',script,str(self.root)],cwd=Path(__file__).parent,stdout=subprocess.PIPE,text=True)
        try:
            self.assertEqual(p.stdout.readline().strip(),'locked')
            with self.assertRaises(ValueError):self.sync()
        finally:p.kill();p.wait();p.stdout.close()
        self.assertEqual(self.sync()['status'],'updated')
    def test_two_generations_retained(self):
        for x in 'abc':self.sha=x*40;self.sync()
        self.assertEqual(len(list((self.root/'generations').iterdir())),2)
    def test_corrupt_current_cannot_replace_valid_previous(self):
        self.sync();self.sha='b'*40;second=self.sync()
        (Path(second['directory'])/'index.json').write_bytes(b'corrupt')
        before=(self.root/'current.json').read_bytes();self.sha='c'*40
        with self.assertRaises(ValueError):self.sync()
        self.assertEqual((self.root/'current.json').read_bytes(),before)
        self.assertEqual(operate('rollback',self.root)['generation'],'a'*40+'-all')
    def test_pointer_replace_failure_preserves_current(self):
        self.sync(); before=(self.root/'current.json').read_bytes(); self.sha='b'*40
        with patch('sync_rules.atomic',side_effect=OSError('write denied')):
            with self.assertRaises(OSError): self.sync()
        self.assertEqual((self.root/'current.json').read_bytes(),before)
    def test_future_publication_rejected(self):
        self.age=-1
        with self.assertRaises(ValueError):self.sync()
        self.assertFalse((self.root/'current.json').exists())
    def test_truncated_http_response_rejected(self):
        response=MagicMock();response.__enter__.return_value=response
        response.status=200;response.url='https://raw.githubusercontent.com/example/file'
        response.headers={'Content-Length':'100'};response.read.return_value=b'short'
        with patch('urllib.request.urlopen',return_value=response):
            with self.assertRaises(ValueError):get(response.url)
    def test_corrupt_previous_refuses_rollback(self):
        first=self.sync();self.sha='b'*40;self.sync()
        before=(self.root/'current.json').read_bytes()
        (Path(first['directory'])/'index.json').write_bytes(b'corrupt')
        with self.assertRaises(ValueError):operate('rollback',self.root)
        self.assertEqual((self.root/'current.json').read_bytes(),before)
    def test_compare_classifies_pending_changes(self):
        channel={'version':3,'changes':[change(3,'config'),change(2,'tool'),change(1)]}
        self.assertEqual(compare(channel,None)['status'],'not_initialized')
        self.assertEqual(compare(channel,3)['status'],'up_to_date')
        result=compare(channel,1)
        self.assertEqual((result['status'],result['highest_class']),('update_available','config'))
        self.assertEqual([c['version'] for c in result['changes']],[2,3])
        channel['changes'][0]['class']='breaking'
        self.assertEqual(compare(channel,2)['status'],'action_required')
    def test_compare_refuses_regression_and_gaps(self):
        self.assertEqual(compare({'version':2,'changes':[change(2)]},5)['status'],'upstream_version_regressed')
        result=compare({'version':5,'changes':[change(5),change(4)]},1)
        self.assertEqual((result['status'],result['highest_class']),('action_required','breaking'))
    def test_parse_integration_rejects_unknown_class_and_oversized_text(self):
        for bad in ({**change(1),'class':'run'},{**change(1),'summary':'x'*401}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                parse_integration(json.dumps({'schema_version':1,'version':1,'changes':[bad]}))
    def bundle_fetch(self,version=2,kinds=('docs','config')):
        channel=json.dumps({'schema_version':1,'version':version,'changes':[change(i+1,kinds[i]) for i in range(version)][::-1]}).encode()
        extra={'integration.json':channel,'docs/UPDATES.md':b'guide','examples/full/mihomo.yaml':b'template','scripts/sync_rules.py':b'tool','sing-box/non-cn-ip.json':b'helper'}
        def fetch(url):
            if url.endswith('/commits/release'):return json.dumps({'sha':self.sha}).encode()
            if url.endswith('/manifest.json'):
                date=datetime.now(timezone.utc).isoformat()
                self.data={**{n:b'payload' for n in selected('all')},**extra}
                self.data['index.json']=json.dumps({'schema_version':1,'generated_at_utc':date}).encode()
                return json.dumps({'schema_version':1,'scope':'domestic_direct_and_adblock','generated_at_utc':date,'files':{n:hashlib.sha256(v).hexdigest() for n,v in self.data.items()}}).encode()
            return self.data[url.split('/'+self.sha+'/')[1]]
        return fetch
    def test_check_then_ack_cycle_writes_only_local_state(self):
        fetch=self.bundle_fetch()
        self.assertEqual(operate('check',self.root,fetch=fetch)['status'],'not_initialized')
        self.assertEqual(operate('ack',self.root,version=1)['applied_version'],1)
        result=operate('check',self.root,fetch=fetch)
        self.assertEqual((result['status'],result['highest_class'],result['tool_update_available']),('update_available','config',True))
        self.assertEqual(json.loads((self.root/'update-status.json').read_text())['latest_version'],2)
        operate('ack',self.root,version=2)
        self.assertEqual(operate('check',self.root,fetch=fetch)['status'],'up_to_date')
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),['.lock','agentroute-state.json','update-status.json'])
    def test_ack_refuses_silent_downgrade(self):
        operate('ack',self.root,version=3)
        with self.assertRaises(ValueError):operate('ack',self.root,version=2)
        self.assertEqual(operate('ack',self.root,version=2,allow_lower=True)['previous_version'],3)
        with self.assertRaises(ValueError):operate('ack',self.root)
    def test_failed_check_records_status_and_keeps_applied_version(self):
        operate('ack',self.root,version=1);self.bad='offline'
        with self.assertRaises(OSError):operate('check',self.root,fetch=self.fetch)
        self.assertEqual(json.loads((self.root/'update-status.json').read_text())['status'],'failed')
        self.assertEqual(json.loads((self.root/'agentroute-state.json').read_text())['applied_version'],1)
    def test_integration_hash_mismatch_rejected(self):
        fetch=self.bundle_fetch()
        def tampered(url):
            return b'{"schema_version":1,"version":99,"changes":[]}' if url.endswith('/integration.json') else fetch(url)
        with self.assertRaises(ValueError):operate('check',self.root,fetch=tampered)
    def test_sync_caches_bundle_and_honours_format(self):
        result=operate('sync',self.root,'surge',fetch=self.bundle_fetch())
        self.assertIn('examples/full/mihomo.yaml',result['files'])
        self.assertNotIn('sing-box/non-cn-ip.json',result['files'])
        self.assertEqual((Path(result['directory'])/'docs/UPDATES.md').read_bytes(),b'guide')
        self.assertEqual(operate('verify',self.root)['status'],'verified')
    def test_cache_from_older_tool_stays_valid_after_upgrade(self):
        result=self.sync();path=Path(result['directory'])/'cache.json'
        self.assertEqual(json.loads(path.read_text())['files'],selected('all'))
        self.assertEqual(operate('verify',self.root)['status'],'verified')
        self.sha='b'*40;self.assertEqual(operate('sync',self.root,fetch=self.bundle_fetch())['status'],'updated')
    def test_tampered_cached_template_detected(self):
        result=operate('sync',self.root,fetch=self.bundle_fetch())
        (Path(result['directory'])/'examples/full/mihomo.yaml').write_bytes(b'changed')
        with self.assertRaises(ValueError):operate('verify',self.root)
    def test_optimized_parser_rejects_invalid_input(self):
        code="from build_rules import domains; domains('not a domain')"
        p=subprocess.run([sys.executable,'-O','-B','-c',code],cwd=Path(__file__).parent,capture_output=True)
        self.assertNotEqual(p.returncode,0)

if __name__=='__main__':unittest.main()
