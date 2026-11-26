"""R32 reader-facing choice design and qualitative comparison (advisory only)."""
from __future__ import annotations
import json,re
from .memory_continuity import arc_review
from .literary_experience import measure,choice_prompt
from .presentation_guard import presentation_preflight
CRITERIA=("continuity","causality","voice","appearance","sensory","relationships","emotion","epic","world_experience","visual_design","choice_parity")
def safe(s):
    if not isinstance(s,str) or not s.strip() or any(c in s for c in ("<",">","{","}","\n")):raise ValueError("Unsafe or empty display string")
    return s.strip()
def render_choices(packet,episode_id,*,revision=30):
    if revision not in (30,34,35):raise ValueError("Unsupported choice revision")
    if arc_review(packet)["errors"]:raise ValueError("Invalid four-route packet")
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,128}",episode_id):raise ValueError("Invalid episode ID")
    # Exact same visual hierarchy, size and button variant for all four.
    rows=['## AS CINCO PORTAS','<box gap={3}>']
    for o in packet["options"]:
        n=o["number"]
        title=safe(o["title"]);title=("ESPECIAL — "+title) if n==4 and not title.upper().startswith("ESPECIAL") else title;promise=safe(o["promise"]);reward=safe(o["reward"]);risk=safe(o["risk"])
        prompt=json.dumps(choice_prompt(episode_id,n,revision=revision),ensure_ascii=False)
        rows.extend(['  <box border radius="lg" padding={3} gap={2}>',f'    **{n} — {title}**','',f'    {promise}','',f'    **Recompensa possível:** {reward}','',f'    **Risco:** {risk}','',f'    <button block color="secondary" variant="outline" onClick={{() => GenUI.issueNewTurn({prompt})}}>Escolher opção {n}</button>','  </box>'])
    before,after=choice_prompt(episode_id,5,"__FREE_TEXT__",revision=revision).split("__FREE_TEXT__")
    free=json.dumps(before,ensure_ascii=False)+"+acaoLivre.trim()+"+json.dumps(after,ensure_ascii=False)
    rows.extend(['  <box gap={2}>','    **5 — AÇÃO LIVRE**','    <textarea value={acaoLivre} onChange={setAcaoLivre} rows={3} placeholder="Descreva suas decisões..."/>',f'    <button color="secondary" variant="outline" disabled={{!acaoLivre.trim()}} onClick={{() => GenUI.issueNewTurn({free})}}>Confirmar ação livre</button>','  </box>','</box>'])
    if revision in (34,35):
        rows[1]='<box gap={3}>'
        rows.insert(1,'<caption>Quatro caminhos · consequências distintas · sua decisão</caption>')
        rows=[line.replace("**Recompensa possível:**","**O que pode mudar:**").replace("**Risco:**","**O que está em jogo:**") for line in rows]
    return {"body_declaration":'{@body const [acaoLivre,setAcaoLivre]=DIL.useState("");}',"markup":"\n".join(rows)}
def compare_versions(a,b):
    if not a.strip() or not b.strip():raise ValueError("Complete drafts required")
    return {"criteria":list(CRITERIA),"A":{"signals":measure(a),"structure":presentation_preflight(a,min_scenes=1,min_named_turns=0)},"B":{"signals":measure(b),"structure":presentation_preflight(b,min_scenes=1,min_named_turns=0)},"human_preference":None,"literary_grade":None,"status":"BLIND_REVIEW_REQUIRED","canon_changed":False}
def review_scores(scores):
    if set(scores)!=set(CRITERIA) or any(type(v) not in (int,float) or not 1<=v<=10 for v in scores.values()):raise ValueError("Eleven reviewed scores required")
    return {"mean":sum(scores.values())/len(scores),"scores":scores,"status":"REVIEWER_RATINGS_NOT_AUTOMATED"}
