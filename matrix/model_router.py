# Copyright 2026 MATRIX contributors
# SPDX-License-Identifier: Apache-2.0
# Modified for the standalone public distribution, October 2026.
"""Local role matching; no network call and no extra model recruitment."""
import re
import unicodedata

RULES=[
 ('aws-extra-deepseek-v3-2',('performance','performances','lent','lenteur','lenteurs','fps','optimiser','optimisation','saccades'),'Performance et diagnostic'),
 ('aws-extra-amazon-nova-2-lite-v1-0',('pdf','document','documents'),'Analyse des documents'),
 ('aws-minimax',('interface','visuel','visuelle','couleur','couleurs','design','matrix'),'Interface et direction visuelle'),
 ('aws-extra-zai-glm-4-7',('gameplay','pnj','collision','collisions','joueur'),'Gameplay et logique'),
 ('aws-extra-nvidia-nemotron-super-3-120b',('test','tests','regression','regressions'),'Tests et cas limites'),
 ('aws-qwen-coder',('code','script','scripts','bug','bugs','corrige','corriger'),'Correction de code'),
 ('aws-kimi-k3',('godot','scene','scenes'),'Analyse technique Godot'),
 ('aws-extra-anthropic-claude-haiku-4-5-20251001-v1-0',('documentation','resume','resumer','consignes'),'Documentation et synthèse'),
 ('aws-extra-anthropic-claude-sonnet-4-6',('architecture','architecte','refonte'),'Architecture logicielle'),
]

def recommend(prompt,available):
    normalized=''.join(c for c in unicodedata.normalize('NFD',prompt.lower()) if unicodedata.category(c)!='Mn')
    words=set(re.findall(r'\w+',normalized))
    ranked=[(len(words.intersection(keys)),alias,reason) for alias,keys,reason in RULES if alias in available]
    best=max(ranked,key=lambda row:row[0],default=(0,None,''))
    if best[0]:return best[1],best[2]
    if not available: raise ValueError('No available agents')
    alias='aws-mistral-large-3' if 'aws-mistral-large-3' in available else next(iter(available))
    return alias,'Coordination de la demande'
