"""Offline updater regressions. Fixtures remain in temp/update-tests for inspection."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('updater', ROOT / 'skills/update/scripts/update.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)


def metadata(version='0.5.0', episode='15-2', legacy=False):
    data = {'bundle_version': version, 'latest_ep': episode.split('-')[0]}
    if not legacy:
        data['latest_episode'] = episode
    return {k: v for k, v in data.items() if v is not None}


def snapshot(version='0.5.0', episode='15-2', legacy=False):
    fields = metadata(version, episode, legacy)
    source = '---\n' + ''.join(f'{k}: {v}\n' for k, v in fields.items()) + '---\n'
    return {name: source.encode() if name == 'SOURCES.md' else f'{version}/{episode}/{name}\n'.encode()
            for name in u.KNOWLEDGE_FILES}


def archive(payload, version='0.5.0'):
    stream = io.BytesIO()
    members = {f'package/{u.KNOWLEDGE_REL}/{name}': data for name, data in payload.items()}
    members['package/package.json'] = json.dumps({'version': version}).encode()
    members['package/skills/ask/SKILL.md'] = b'new skill body'
    with tarfile.open(fileobj=stream, mode='w:gz') as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name); info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return stream.getvalue()


class UpdateTests(unittest.TestCase):
    def setUp(self):
        base = ROOT / 'temp/update-tests'
        base.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(dir=base))
        self.write_local()

    def write_local(self, version='0.4.4', episode='12', legacy=True):
        for name, data in snapshot(version, episode, legacy).items():
            path = self.root / u.KNOWLEDGE_REL / name
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        (self.root / 'skills/ask/SKILL.md').write_text('old skill body')

    def run_main(self, blob=None, apply=True):
        out = io.StringIO()
        args = ['update.py', '--root', str(self.root), '--json', '--apply' if apply else '--check']
        with patch.object(sys, 'argv', args), patch.object(u, 'fetch_tarball', return_value=blob), \
             patch.object(u, 'remote_from_sources', return_value=None), \
             patch.object(u, 'remote_from_api', return_value=None), contextlib.redirect_stdout(out):
            code = u.main()
        return code, json.loads(out.getvalue())

    def test_versions_and_episodes(self):
        cases = [
            (metadata('0.4.4','12',True), metadata(), 'behind'),
            (metadata('0.5.0','15-1'), metadata('0.5.1','15-2'), 'behind'),
            (metadata('0.5.0'), metadata('0.5.1'), 'behind'),
            (metadata(), metadata(), 'latest'),
            (metadata('0.6.0'), metadata(), 'ahead'),
            (metadata('0.4.4','16'), metadata(), 'conflict'),
            (metadata('0.6.0','14'), metadata(), 'conflict'),
            (metadata('0.5.0','15-1'), metadata(), 'conflict'),
            (metadata(None,'15-1'), metadata(None,'15-2'), 'behind'),
            (metadata(None,'12',True), metadata(None,'14',True), 'behind'),
            (metadata('0.4.4','15',True), metadata(), 'behind'),
            ({}, {}, 'unknown'),
        ]
        for local, remote, state in cases:
            with self.subTest(local=local, remote=remote):
                self.assertEqual(u.compare_metadata(local,remote)[0],state)

    def test_valid_versions(self):
        self.assertIsNone(u.version_key('garbage'))
        self.assertIsNone(u.version_key('0.5'))
        self.assertIsNone(u.version_key('0.5.0-01'))
        self.assertLess(u.version_key('0.5.0-rc.2'),u.version_key('0.5.0-rc.10'))
        self.assertLess(u.version_key('0.5.0-rc.10'),u.version_key('0.5.0'))

    def test_upgrade_and_repeat(self):
        payload=snapshot(); blob=archive(payload)
        code,result=self.run_main(blob)
        self.assertEqual((code,result['state']),(10,'latest'))
        self.assertEqual(len(result['applied']),6)
        self.assertEqual(result['skill_files_differ'],['skills/ask/SKILL.md'])
        self.assertEqual((self.root/'skills/ask/SKILL.md').read_text(),'old skill body')
        for name,data in payload.items():
            self.assertEqual((self.root/u.KNOWLEDGE_REL/name).read_bytes(),data)
        code,result=self.run_main(blob)
        self.assertEqual((code,result['state'],result['applied']),(0,'latest',[]))

    def test_same_episode_revision(self):
        self.write_local('0.5.0','15-2',False)
        code,result=self.run_main(archive(snapshot('0.5.1'), '0.5.1'))
        self.assertEqual((code,result['state']),(10,'latest'))

    def test_multipart_upgrade(self):
        self.write_local('0.4.9','15-1',False)
        code,result=self.run_main(archive(snapshot()))
        self.assertEqual((code,result['state']),(10,'latest'))

    def test_downgrade_and_conflict_do_not_write(self):
        for version,ep,state,exit_code in [('0.6.0','16','ahead',0),('0.4.3','16','conflict',20)]:
            self.write_local(version,ep,False)
            before=(self.root/u.KNOWLEDGE_REL/'SOURCES.md').read_bytes()
            code,result=self.run_main(archive(snapshot()))
            self.assertEqual((code,result['state']),(exit_code,state))
            self.assertEqual((self.root/u.KNOWLEDGE_REL/'SOURCES.md').read_bytes(),before)

    def test_missing_file_rejected_before_writes(self):
        payload=snapshot(); payload.pop('pc-checkup.md')
        before=(self.root/u.KNOWLEDGE_REL/'INDEX.md').read_bytes()
        code,result=self.run_main(archive(payload))
        self.assertEqual((code,result['state']),(20,'failed'))
        self.assertEqual((self.root/u.KNOWLEDGE_REL/'INDEX.md').read_bytes(),before)

    def test_write_failure_keeps_old_metadata_and_can_retry(self):
        original=u.write_atomic
        def fail(path,data):
            if path.name=='pc-checkup.md': raise OSError('simulated write failure')
            original(path,data)
        with patch.object(u,'write_atomic',side_effect=fail):
            code,result=self.run_main(archive(snapshot()))
        self.assertEqual((code,result['state']),(20,'failed'))
        self.assertEqual(u.read_frontmatter(self.root/u.KNOWLEDGE_REL/'SOURCES.md')['bundle_version'],'0.4.4')
        code,result=self.run_main(archive(snapshot()))
        self.assertEqual((code,result['state']),(10,'latest'))

    def test_download_failure_and_corrupt_archive(self):
        for blob in (None,b'invalid archive'):
            code,result=self.run_main(blob)
            self.assertEqual((code,result['state']),(20,'unknown'))

    def test_raw_download_failure_is_not_partial_install(self):
        before=(self.root/u.KNOWLEDGE_REL/'SOURCES.md').read_bytes()
        payload=snapshot()
        def get(url):
            name=url.rsplit('/',1)[-1]
            if name=='pc-checkup.md': raise OSError('simulated download failure')
            return payload[name]
        with patch.object(u,'http_get',side_effect=get):
            with self.assertRaises(OSError): u.apply_from_raw(self.root,metadata())
        self.assertEqual((self.root/u.KNOWLEDGE_REL/'SOURCES.md').read_bytes(),before)

    def test_check_is_read_only(self):
        code,result=self.run_main(archive(snapshot()),False)
        self.assertEqual((code,result['state'],result['applied']),(10,'behind',[]))

    def test_mismatched_snapshot_rejected(self):
        with self.assertRaises(ValueError):
            u.install_knowledge(snapshot(),self.root,{'version':'0.6.0'})

    def test_body_digest_mismatch_rejected(self):
        payload=snapshot()
        payload['SOURCES.md'] += b'| `so101-guide.md` | guide | source | 1 | 1 | `000000000000` |\n'
        with self.assertRaises(ValueError):
            u.install_knowledge(payload,self.root,metadata())

    def test_package_metadata_mismatch_rejected(self):
        self.assertIsNone(u.remote_from_tarball(archive(snapshot(), '0.6.0')))

    def test_timeout_is_unknown(self):
        with patch.object(u,'http_get',side_effect=subprocess.TimeoutExpired('curl',30)):
            self.assertIsNone(u.fetch_tarball(None))


if __name__=='__main__': unittest.main()
