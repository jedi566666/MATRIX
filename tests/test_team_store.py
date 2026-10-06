# Copyright 2026 MATRIX contributors
# SPDX-License-Identifier: Apache-2.0
# Modified for the standalone public distribution, October 2026.
import tempfile
import unittest
from pathlib import Path
from matrix.team_store import Store

class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / 'team')
        self.file = self.root / 'piece.txt'
        self.file.write_text('livrable réel', encoding='utf-8')
    def mission(self, **kw):
        return self.store.create('demo-project', 'reviewer', 'Finir le lot', 'scene.tscn', **kw)['id']
    def approved(self, ident):
        self.store.transition(ident, 'WORKING')
        self.store.attach(ident, self.file, 'deliverable')
        self.store.attach(ident, self.file, 'evidence')
        self.store.transition(ident, 'REVIEW')
        return self.store.transition(ident, 'APPROVED', producer=True)
    def test_invalid_and_human_validation(self):
        i = self.mission()
        with self.assertRaises(ValueError): self.store.transition(i, 'DONE')
        self.store.transition(i, 'WORKING')
        self.store.transition(i, 'REVIEW')
        with self.assertRaises(ValueError): self.store.transition(i, 'APPROVED', producer=True)
        self.store.attach(i, self.file, 'deliverable')
        self.store.attach(i, self.file, 'evidence')
        with self.assertRaises(ValueError): self.store.transition(i, 'APPROVED')
        self.store.transition(i, 'APPROVED', producer=True)
        with self.assertRaises(ValueError): self.store.attach(i, self.file)
        self.store.transition(i, 'DONE')
    def test_hash_and_immutable_source(self):
        i = self.mission()
        self.store.transition(i, 'WORKING')
        m = self.store.attach(i, self.file, 'deliverable')
        self.store.attach(i, self.file, 'evidence')
        self.assertTrue(self.file.exists())
        Path(m['outputs'][0]['path']).write_text('altéré')
        self.store.transition(i, 'REVIEW')
        with self.assertRaises(ValueError): self.store.transition(i, 'APPROVED', producer=True)
    def test_project_lock_across_stores(self):
        a, b = self.mission(), self.mission()
        self.store.transition(a, 'WORKING')
        second = Store(self.root / 'team')
        with self.assertRaises(ValueError): second.transition(b, 'WORKING')
        self.store.transition(a, 'BLOCKED', 'Besoin du producteur')
        second.transition(b, 'WORKING')
    def test_go_and_scope_change(self):
        i = self.mission(risks=['cost'])
        with self.assertRaises(ValueError): self.store.transition(i, 'WORKING')
        self.store.authorize(i, 'GO humain budget explicite')
        self.store.attach(i, self.file)
        with self.assertRaises(ValueError): self.store.transition(i, 'WORKING')
        self.store.authorize(i, 'GO périmètre relu')
        self.store.transition(i, 'WORKING')
        self.assertEqual(self.store.attach(i, self.file)['state'], 'BLOCKED')
    def test_handoff_idempotent(self):
        i = self.mission()
        with self.assertRaises(ValueError): self.store.handoff(i, 'Mistral')
        self.approved(i)
        child = self.store.handoff(i, 'Mistral')
        again = self.store.handoff(i, 'Mistral')
        self.assertEqual(child['id'], again['id'])
        self.assertEqual(child['state'], 'READY')
        self.assertEqual(self.store.get(i)['state'], 'DONE')
        self.assertEqual(len(self.store.list()), 2)
        with self.assertRaises(ValueError): self.store.handoff(i, 'Qwen')
    def test_concurrent_lock(self):
        from concurrent.futures import ThreadPoolExecutor
        ids = [self.mission(), self.mission()]
        def run(ident):
            try:
                Store(self.root / 'team').transition(ident, 'WORKING')
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(run, ids)), 1)
    def test_chain_limit(self):
        i = self.mission()
        for index in range(16):
            self.approved(i)
            i = self.store.handoff(i, 'Agent ' + str(index))['id']
        self.approved(i)
        with self.assertRaises(ValueError): self.store.handoff(i, 'Encore')
    def test_brief_history_next(self):
        i = self.mission()
        self.store.set_next(i, 'QA')
        self.assertEqual(self.store.get(i)['next_agent'], 'QA')
        self.assertTrue(self.store.export_brief(i).is_file())
        self.assertEqual(self.store.history(i)[-1]['action'], 'prepare_handoff')

    def test_restart_persists(self):
        i = self.mission()
        self.assertEqual(Store(self.root / 'team').get(i)['id'], i)
        self.assertTrue((self.root / 'team' / 'INBOX' / (i+'.md')).is_file())

if __name__ == '__main__': unittest.main()
