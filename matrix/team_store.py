# Copyright 2026 MATRIX contributors
# SPDX-License-Identifier: Apache-2.0
# Modified for the standalone public distribution, October 2026.
"""Local transactional mission registry. Never executes agents or publishes files."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from contextlib import contextmanager

STATES = ('READY', 'WORKING', 'REVIEW', 'BLOCKED', 'APPROVED', 'DONE')
FOLDERS = dict(READY='INBOX', WORKING='WORKING', REVIEW='REVIEW', BLOCKED='REVIEW', APPROVED='APPROVED', DONE='DONE')

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

class Store:
    def __init__(self, root=None):
        self.root = Path(root or os.environ.get('MATRIX_DATA_DIR', Path.home() / '.matrix-workspace')).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        for folder in (*set(FOLDERS.values()), 'REPORTS', 'ASSETS', 'FILM', 'SOCIAL', 'LEGAL'):
            (self.root / folder).mkdir(exist_ok=True)
        self.db = self.root / 'missions.sqlite3'
        with self._connect() as c:
            c.executescript('CREATE TABLE IF NOT EXISTS missions (id TEXT PRIMARY KEY, data TEXT NOT NULL); CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, mission TEXT NOT NULL, at TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL);')

    @contextmanager
    def _connect(self):
        c = sqlite3.connect(str(self.db), timeout=30)
        c.execute('PRAGMA busy_timeout=30000')
        try:
            with c:
                yield c
        finally:
            c.close()

    def _read(self, c, ident):
        row = c.execute('SELECT data FROM missions WHERE id=?', (ident,)).fetchone()
        if not row:
            raise ValueError('Mission introuvable : ' + str(ident))
        return json.loads(row[0])

    def list(self):
        with self._connect() as c:
            return [json.loads(r[0]) for r in c.execute('SELECT data FROM missions ORDER BY rowid DESC')]

    def get(self, ident):
        with self._connect() as c:
            return self._read(c, ident)

    def _save(self, c, m, action, detail=''):
        m['updated_at'] = now()
        c.execute('INSERT OR REPLACE INTO missions VALUES (?,?)', (m['id'], json.dumps(m, ensure_ascii=False)))
        c.execute('INSERT INTO events(mission,at,action,detail) VALUES (?,?,?,?)', (m['id'], m['updated_at'], action, str(detail)))

    def _new(self, project, agent, objective, deliverables, next_agent='', inputs=None, pipeline='Libre', risks=None):
        if not all(str(x).strip() for x in (project, agent, objective, deliverables)):
            raise ValueError('Projet, agent, objectif et livrables sont obligatoires.')
        t = now()
        return dict(id='MATRIX-' + dt.datetime.now().strftime('%Y%m%d') + '-' + uuid.uuid4().hex[:10], project=str(project).strip(), agent=str(agent).strip(), objective=str(objective).strip(), deliverables=str(deliverables).strip(), next_agent=str(next_agent).strip(), state='READY', created_at=t, updated_at=t, started_at=None, inputs=[], reports=[], evidence=[], outputs=[], error='', pipeline=pipeline, risks=list(risks or []), parent_id=None, depth=0, revision=1, authorization=None, child_id=None)

    def create(self, project, agent, objective, deliverables, next_agent='', inputs=None, pipeline='Libre', risks=None):
        m = self._new(project, agent, objective, deliverables, next_agent, pipeline=pipeline, risks=risks)
        # Validate requested paths before creating the mission.
        paths = [Path(x['path'] if isinstance(x, dict) else x).resolve(strict=True) for x in (inputs or [])]
        if any(not x.is_file() for x in paths):
            raise ValueError('Les entrées doivent être des fichiers.')
        with self._connect() as c:
            c.execute('BEGIN IMMEDIATE')
            self._save(c, m, 'create')
        for path in paths:
            self.attach(m['id'], path)
        self._export(m['id'])
        return self.get(m['id'])

    def authorize(self, ident, note):
        if not str(note).strip():
            raise ValueError('Le GO du producteur doit être explicite et documenté.')
        with self._connect() as c:
            c.execute('BEGIN IMMEDIATE')
            m = self._read(c, ident)
            if m['state'] not in ('READY', 'BLOCKED'):
                raise ValueError('Le GO se donne avant de commencer la mission.')
            m['authorization'] = dict(revision=m['revision'], at=now(), note=str(note))
            self._save(c, m, 'producer_go', note)
        self._export(ident)
        return m

    def _verify(self, m):
        if not m['evidence'] or not m['outputs']:
            raise ValueError('Joindre au moins une preuve et un livrable avant validation.')
        for a in m['evidence'] + m['outputs']:
            p = Path(a['path'])
            if not p.is_file() or digest(p) != a['sha256']:
                raise ValueError('Preuve ou livrable absent ou modifié : ' + a['name'])

    def transition(self, ident, state, note='', producer=False):
        allowed = dict(READY=('WORKING','BLOCKED'), WORKING=('REVIEW','BLOCKED'), REVIEW=('APPROVED','WORKING','BLOCKED'), BLOCKED=('READY',), APPROVED=('DONE',), DONE=())
        with self._connect() as c:
            c.execute('BEGIN IMMEDIATE')
            m = self._read(c, ident)
            if state not in allowed[m['state']]:
                raise ValueError('Transition interdite : ' + m['state'] + ' → ' + str(state))
            if state == 'WORKING':
                for item in m['inputs']:
                    if not Path(item['path']).is_file() or digest(item['path']) != item['sha256']:
                        raise ValueError('Entrée archivée absente ou modifiée : ' + item['name'])
                auth = m.get('authorization')
                if m['risks'] and (not auth or auth['revision'] != m['revision']):
                    raise ValueError('GO producteur requis pour cette mission à risque.')
                for (data,) in c.execute('SELECT data FROM missions WHERE id<>?', (ident,)):
                    other = json.loads(data)
                    if other['state'] == 'WORKING' and other['project'].casefold() == m['project'].casefold():
                        raise ValueError('Projet déjà occupé par ' + other['id'] + ' / ' + other['agent'])
                m['started_at'] = now()
            if state == 'APPROVED':
                if not producer:
                    raise ValueError('Seul le producteur peut valider.')
                self._verify(m)
                m['approved_at'] = now()
                m['approval_note'] = str(note)
            if state == 'DONE':
                self._verify(m)
            m['state'] = state
            m['error'] = str(note) if state == 'BLOCKED' else ''
            self._save(c, m, 'transition:' + state, note)
        self._export(ident)
        return m

    def attach(self, ident, path, kind='input'):
        keys = dict(input='inputs', report='reports', evidence='evidence', deliverable='outputs')
        if kind not in keys:
            raise ValueError('Type de pièce inconnu.')
        src = Path(path).resolve(strict=True)
        if not src.is_file():
            raise ValueError('Choisir un fichier.')
        with self._connect() as c:
            c.execute('BEGIN IMMEDIATE')
            m = self._read(c, ident)
            if m['state'] in ('APPROVED','DONE'):
                raise ValueError('Mission validée figée ; créer une nouvelle mission.')
            folder = self.root / 'ASSETS' / ident
            folder.mkdir(exist_ok=True)
            dest = folder / (uuid.uuid4().hex[:12] + '-' + src.name)
            shutil.copy2(src, dest)
            record = dict(name=src.name, path=str(dest), source=str(src), sha256=digest(dest), size=dest.stat().st_size, at=now())
            m[keys[kind]].append(record)
            # Inputs alter the scope; proofs and outputs document that same scope.
            if kind == 'input':
                m['revision'] += 1
                m['authorization'] = None
                if m['state'] == 'WORKING':
                    m['state'] = 'BLOCKED'
                    m['error'] = 'Entrées modifiées : relire la mission avant reprise.'
            self._save(c, m, 'attach:' + kind, record['name'])
        self._export(ident)
        return m

    def handoff(self, ident, next_agent):
        if not str(next_agent).strip():
            raise ValueError('Choisir un agent suivant.')
        with self._connect() as c:
            c.execute('BEGIN IMMEDIATE')
            m = self._read(c, ident)
            if m.get('child_id'):
                child = self._read(c, m['child_id'])
                if child['agent'] != next_agent:
                    raise ValueError('Cette mission a déjà un relais vers ' + child['agent'])
                return child
            if m['state'] not in ('APPROVED','DONE'):
                raise ValueError('Valider la mission avant de passer le relais.')
            self._verify(m)
            if m.get('depth', 0) >= 16:
                raise ValueError('Limite de 16 relais atteinte ; décision humaine requise.')
            child = self._new(m['project'], next_agent, m['objective'], m['deliverables'], pipeline=m['pipeline'], risks=m['risks'])
            child.update(parent_id=ident, depth=m.get('depth', 0)+1, inputs=m['inputs'] + m['outputs'] + m['reports'] + m['evidence'])
            m.update(state='DONE', next_agent=next_agent, child_id=child['id'])
            self._save(c, child, 'handoff_received', ident)
            self._save(c, m, 'handoff', child['id'])
        self._export(ident)
        self._export(child['id'])
        return child

    def set_next(self, ident, next_agent):
        with self._connect() as c:
            c.execute('BEGIN IMMEDIATE')
            m = self._read(c, ident)
            if m.get('child_id') or m['state'] == 'DONE':
                raise ValueError('Le relais est déjà enregistré.')
            m['next_agent'] = str(next_agent).strip()
            self._save(c, m, 'prepare_handoff', next_agent)
        self._export(ident)
        return m

    def history(self, ident):
        with self._connect() as c:
            self._read(c, ident)
            return [dict(seq=r[0], mission=r[1], at=r[2], action=r[3], detail=r[4]) for r in c.execute('SELECT seq,mission,at,action,detail FROM events WHERE mission=? ORDER BY seq', (ident,))]

    def export_brief(self, ident):
        self._export(ident)
        return self.root / 'REPORTS' / (ident + '-mission.md')

    def _export(self, ident):
        # Human-readable mirrors are derived. SQLite remains authoritative.
        # A fresh read under the write lock prevents stale concurrent exports.
        with self._connect() as c:
            c.execute('BEGIN IMMEDIATE')
            m = self._read(c, ident)
            folder = self.root / FOLDERS[m['state']]
            body = '# ' + m['id'] + '\n\n' + '\n'.join(f'**{k}** : {m[k]}\n' for k in ('project','agent','state','objective','deliverables','next_agent','created_at','started_at','error'))
            for key in ('inputs','reports','evidence','outputs'):
                body += '\n## ' + key + '\n\n' + '\n'.join('- ' + a['name'] + ' — ' + a['path'] + ' — SHA256 ' + a['sha256'] for a in m[key]) + '\n'
            for suffix, data in (('.json', json.dumps(m, ensure_ascii=False, indent=2)), ('.md', body)):
                target = folder / (ident + suffix)
                tmp = target.with_name(target.name + '.tmp-' + uuid.uuid4().hex)
                tmp.write_text(data, encoding='utf-8')
                os.replace(tmp, target)
            (self.root / 'REPORTS' / (ident + '-mission.md')).write_text(body, encoding='utf-8')
            # Keep earlier state snapshots as history, explicitly label them.
            for oldfolder in set(FOLDERS.values()) - {FOLDERS[m['state']]}:
                old = self.root / oldfolder / (ident + '.md')
                old_json = old.with_suffix('.json')
                if old_json.exists():
                    snapshot = json.loads(old_json.read_text(encoding='utf-8'))
                    snapshot['archived_snapshot'] = True
                    snapshot['current_state'] = m['state']
                    snapshot['canonical_registry'] = str(self.db)
                    old_json.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
                if old.exists():
                    old.write_text('# ARCHIVE — état courant : ' + m['state'] + '\n\nConsulter le registre SQLite ou ' + str(folder / (ident+'.md')) + '\n', encoding='utf-8')
            events = [dict(seq=r[0], mission=r[1], at=r[2], action=r[3], detail=r[4]) for r in c.execute('SELECT seq,mission,at,action,detail FROM events WHERE mission=? ORDER BY seq', (ident,))]
            (self.root / 'REPORTS' / (ident + '-events.json')).write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding='utf-8')
