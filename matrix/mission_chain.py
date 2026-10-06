# Copyright 2026 MATRIX contributors
# SPDX-License-Identifier: Apache-2.0
# Modified for the standalone public distribution, October 2026.
"""Persistent shared brief and assignments for a sequential, bounded agent chain."""
import json
import re
from pathlib import Path
from datetime import datetime, timezone

DIRECTORY = Path.home() / '.matrix-workspace' / 'chains'

def order_agents(aliases):
    agents=list(dict.fromkeys(aliases))
    for lead in ('aws-mistral-large-3','aws-extra-qwen-qwen3-next-80b-a3b'):
        if lead in agents:
            agents.remove(lead);agents.insert(0,lead);break
    return agents

class MissionChain:
    def __init__(self, identifier, brief, aliases, folder, directory=DIRECTORY):
        if not re.fullmatch(r'[A-Za-z0-9_-]+',identifier):raise ValueError('Identifiant invalide')
        self.path=Path(directory)/identifier
        self.path.mkdir(parents=True,exist_ok=False)
        self.data={'id':identifier,'project':str(folder),'brief':brief,'status':'en cours',
                   'tasks':{a:{'assignment':'Lire la mission commune et prendre un lot ciblé selon sa spécialité, en tenant compte des résultats précédents.','state':'en attente'} for a in aliases},'passes':[]}
        (self.path/'MISSION_COMMUNE.md').write_text(brief,encoding='utf-8')
        self.save()

    def save(self):
        self.data['updated']=datetime.now(timezone.utc).isoformat()
        temp=self.path/'etat.tmp'
        temp.write_text(json.dumps(self.data,ensure_ascii=False,indent=2),encoding='utf-8')
        temp.replace(self.path/'etat.json')
        lines=['# Répartition de mission',self.data['id'],f"Source commune : {self.data['project']}",f"État : {self.data['status']}",
               'Les réponses ne certifient ni écritures ni tests. Consulter les bilans outils MATRIX.']
        for alias,task in self.data['tasks'].items():lines.extend(['',f"## {alias} — {task['state']}",task['assignment']])
        (self.path/'REPARTITION.md').write_text('\n'.join(lines),encoding='utf-8')

    def start(self, alias):
        self.data['tasks'][alias]['state']='en cours';self.save()
        return ('\nMISSION COMMUNE ET RÉPARTITION\n'+self.data['brief']+
                '\nTON LOT : '+self.data['tasks'][alias]['assignment']+
                '\nTABLEAU ACTUEL : '+json.dumps(self.data['tasks'],ensure_ascii=False)+
                '\nAu premier passage, répartis les lots entre les candidats encore disponibles avec des lignes '
                'TACHE_AGENT: <alias exact> | <objectif, fichiers, dépendances et preuve attendue>. '
                'Tu peux préciser les lots en attente aux passages suivants. Exécute ensuite ton propre lot. '
                'Ne refais pas les lots déjà passés. Le relais exécute une seule passe par agent, successivement pour éviter les écrasements. '
                'Termine par RESULTAT_LOT: <faits et références outils>, RESTE_A_FAIRE: <reste concret>. '
                'Do not claim execution or passing tests without evidence. This coordinator does not execute tools or models.\n')

    def finish(self, alias, answer='', error='', execution=None):
        self.data['tasks'][alias]['state']=execution['status'] if execution else 'erreur' if error else 'réponse reçue — à vérifier'
        self.data['passes'].append({'agent':alias,'answer':answer,'error':error})
        if not error:
            for line in answer.splitlines():
                line=line.strip().lstrip('- ').replace('**','').replace('`','')
                match=re.fullmatch(r'TACHE_AGENT:\s*([^|\s]+)\s*\|\s*(.{1,3000})',line)
                if match and match[1] in self.data['tasks'] and self.data['tasks'][match[1]]['state']=='en attente':
                    self.data['tasks'][match[1]]['assignment']=match[2]
        self.save()

    def close(self, cancelled=False):
        self.data['status']='arrêt demandé' if cancelled else 'passes terminées — livraison à vérifier'
        self.save()
