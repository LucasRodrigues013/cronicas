"""WORLDROOT editorial production roster: one showrunner, 9 departments, 37 roles.

This is a deterministic *advisory* routing contract based on the historical
production bible, NOT 37 independently running models/agents. The author
alone controls Lucas's choices and approvals. This module never writes canon.
"""
from __future__ import annotations

from dataclasses import dataclass

CHIEF = "diretor_geral_showrunner"
ALWAYS = ("guardiao_canon", "diretor_cronologia", "diretor_conhecimento", "diretor_qa")

@dataclass(frozen=True)
class Role:
    department: str
    slug: str
    purpose: str

ROLES = (
    Role("01_ROTEIRO_LITERATURA", "diretor_historia", "Transformacao dramatica sem escolhas forcadas"),
    Role("01_ROTEIRO_LITERATURA", "diretor_aventura", "Ritmo, maravilha e iniciativa organica"),
    Role("01_ROTEIRO_LITERATURA", "diretor_interatividade", "Tres escolhas, quarta especial e quinta livre"),
    Role("01_ROTEIRO_LITERATURA", "editor_literario", "Estilo, dialogo, subtexto e exposicao"),
    Role("02_CANONE_CONTINUIDADE", "guardiao_canon", "Estado canonico e bloqueio de retcon"),
    Role("02_CANONE_CONTINUIDADE", "diretor_cronologia", "Calendario, tempo e deslocamentos"),
    Role("02_CANONE_CONTINUIDADE", "supervisor_continuidade", "Objetos, ferimentos, trajes e lugares"),
    Role("02_CANONE_CONTINUIDADE", "diretor_conhecimento", "Informacao por personagem e canal"),
    Role("03_PERSONAGENS_RELACOES", "diretor_personagens", "Agencia e objetivos pessoais"),
    Role("03_PERSONAGENS_RELACOES", "diretor_vozes", "Vozes e comportamentos distintos"),
    Role("03_PERSONAGENS_RELACOES", "diretor_vinculos", "Afetos, consentimento e laços"),
    Role("03_PERSONAGENS_RELACOES", "diretor_vidas_independentes", "Agendas e iniciativas dos NPCs"),
    Role("04_GEOGRAFIA_MEMORIA", "diretor_geografia", "Rotas, fronteiras e distancias sustentadas"),
    Role("04_GEOGRAFIA_MEMORIA", "diretor_historiografia", "Passado, evidencias e lendas"),
    Role("04_GEOGRAFIA_MEMORIA", "diretor_cidades", "Arquitetura, obras e urbanismo"),
    Role("04_GEOGRAFIA_MEMORIA", "diretor_exploracao", "Territorios e descobertas sem antecipacao"),
    Role("05_ECOLOGIA_AMBIENTE", "diretor_clima", "Clima e estacoes regionalmente"),
    Role("05_ECOLOGIA_AMBIENTE", "diretor_fauna", "Comportamento e habitat das criaturas"),
    Role("05_ECOLOGIA_AMBIENTE", "diretor_flora", "Botanica, lavouras e ecossistemas"),
    Role("05_ECOLOGIA_AMBIENTE", "diretor_fisica_natural", "Relevo, aguas e astronomia"),
    Role("06_CIVILIZACOES", "diretor_politica", "Soberania e instituicoes independentes"),
    Role("06_CIVILIZACOES", "diretor_economia", "Trabalho, recursos e comercio"),
    Role("06_CIVILIZACOES", "diretor_cultura", "Povos, idiomas, crencas e costumes"),
    Role("06_CIVILIZACOES", "diretor_genealogia", "Familias, linhagens e sucessao"),
    Role("07_MAGIA_EXTRAORDINARIO", "diretor_genese", "GÊNESE plena e pessoas livres"),
    Role("07_MAGIA_EXTRAORDINARIO", "diretor_sistemas_magia", "Escolas arcanas e limites demonstrados"),
    Role("07_MAGIA_EXTRAORDINARIO", "diretor_tecnologia", "Artefatos, prototipos e testes reais"),
    Role("07_MAGIA_EXTRAORDINARIO", "diretor_misterios", "Segredos e revelacoes sem prova inventada"),
    Role("08_CINEMA_SENSORIAL", "diretor_producao_visual", "Cenografia e arte narrativa"),
    Role("08_CINEMA_SENSORIAL", "diretor_fotografia", "Luz e atmosfera verbal"),
    Role("08_CINEMA_SENSORIAL", "diretor_figurino", "Aparencia, equipamentos e continuidade visual"),
    Role("08_CINEMA_SENSORIAL", "diretor_som_musica", "Paisagem sonora e musica diegetica"),
    Role("08_CINEMA_SENSORIAL", "diretor_coreografia", "Movimento e combate coerente"),
    Role("09_ENGENHARIA_PUBLICACAO", "diretor_causal", "Causalidade e World Pulse restrito"),
    Role("09_ENGENHARIA_PUBLICACAO", "diretor_proveniencia", "Proveniencia, SHA, status e fontes"),
    Role("09_ENGENHARIA_PUBLICACAO", "diretor_qa", "Auditoria e bloqueios P0"),
    Role("09_ENGENHARIA_PUBLICACAO", "diretor_publicacao", "Recibos, wiki e versoes verificadas"),
)

TAGS = {
    "GENESE": ("diretor_genese", "diretor_sistemas_magia"),
    "COMBATE": ("diretor_coreografia", "diretor_aventura", "diretor_sistemas_magia"),
    "ARGOS": ("diretor_tecnologia", "diretor_fisica_natural", "supervisor_continuidade"),
    "SEGREDO": ("diretor_misterios", "diretor_historiografia", "diretor_proveniencia"),
    "POV_EXTERNO": ("diretor_causal", "diretor_geografia", "diretor_vidas_independentes"),
    "POLITICA": ("diretor_politica", "diretor_cultura", "diretor_economia"),
    "CIDADE": ("diretor_cidades", "diretor_economia", "diretor_vidas_independentes"),
    "CIENCIA": ("diretor_tecnologia", "diretor_historiografia", "diretor_flora"),
    "ROMANCE": ("diretor_vinculos", "diretor_vozes", "editor_literario"),
    "PERSONAGENS": ("diretor_personagens", "diretor_vozes", "diretor_vinculos"),
    "EXPLORACAO": ("diretor_exploracao", "diretor_geografia", "diretor_clima"),
    "AMBIENTE": ("diretor_clima", "diretor_fauna", "diretor_flora"),
    "CONTINUIDADE": ("supervisor_continuidade", "diretor_proveniencia"),
    "ESCOLHAS": ("diretor_interatividade", "diretor_historia"),
    "PUBLICACAO": ("diretor_publicacao", "diretor_proveniencia"),
}

def route(scene_tags=(), max_contextual=5):
    """Select advisory roles from declared tags; no autonomous agent execution."""
    if type(max_contextual) is not int or not 0 <= max_contextual <= 5:
        raise ValueError("At most five additional editorial roles")
    if isinstance(scene_tags, str):
        raise TypeError("scene_tags must be a sequence, not a string")
    allowed = {role.slug for role in ROLES}
    tags = tuple(str(tag).upper() for tag in scene_tags)
    if any(tag not in TAGS for tag in tags):
        raise ValueError("Unknown routing tag; editorial intent must be explicit")
    selected = []
    for tag in tags:
        for slug in TAGS[tag]:
            if slug not in ALWAYS and slug not in selected:
                if slug not in allowed:
                    raise ValueError("Registered route references missing role")
                selected.append(slug)
    return {
        "director": CHIEF,
        "mandatory": list(ALWAYS),
        "contextual": selected[:max_contextual],
        "departments_available": len({x.department for x in ROLES}),
        "declared_specialties": len(ROLES),
        "operating_mode": "DECLARATIVE_ADVISORY_NOT_INDEPENDENT_AGENTS",
        "canon_changed": False,
    }


def verify_roster():
    slugs = [r.slug for r in ROLES]
    if len(slugs) != 37 or len(set(slugs)) != 37:
        raise ValueError("Production bible must have exactly 37 unique roles")
    if len({r.department for r in ROLES}) != 9:
        raise ValueError("Production bible must have nine departments")
    if any(x not in slugs for x in ALWAYS):
        raise ValueError("Missing mandatory guardian role")
    if any(x not in slugs for candidates in TAGS.values() for x in candidates):
        raise ValueError("Unknown specialist referenced by a tag")
    return True
