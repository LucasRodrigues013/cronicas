"""Read-only complementary recovery. Candidates never enter canon automatically."""
import hashlib
import re
import unicodedata

DOMAINS = frozenset(("character","world","technology","journey","archaeology","event"))
HEADING = re.compile(r"^\d{2}h\d{2}\s*\|")
def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def normalize(name):
    return " ".join(unicodedata.normalize("NFKC", name).casefold().split())

def scenes(text, book, source):
    if book not in range(1,7):
        raise ValueError("invalid book")
    lines = text.split("\n")
    starts = sorted(set([0]+[i for i,line in enumerate(lines) if HEADING.match(line)]))
    return [{"book":book,"source":source,"start":a+1,"end":z,
             "sha256":digest("\n".join(lines[a:z])),
             "status":"UNREVIEWED_SCENE"} for a,z in zip(starts,starts[1:]+[len(lines)])]

def candidates(text, book, source, observations, registry_names):
    """Validate reviewer-supplied discoveries; no inference of identity or canon."""
    lines=text.split("\n")
    known={normalize(n) for n in registry_names}
    result={}
    for item in observations:
        name=item["name"]
        domain=item["domain"]
        line=item["line"]
        if book not in range(1,7) or domain not in DOMAINS or not normalize(name):
            raise ValueError("invalid candidate")
        if not isinstance(line,int) or not 1<=line<=len(lines) or lines[line-1]!=item["anchor"] or not item["anchor"].strip():
            raise ValueError("invalid literal evidence")
        if item["scope"] not in ("PUBLIC","RESTRICTED","UNKNOWN") or item["role"] not in ("NARRATED","TESTIMONY","HYPOTHESIS","PREVIEW"):
            raise ValueError("invalid scope or role")
        day=item.get("day")
        if day is not None and (not isinstance(day,int) or day<1):
            raise ValueError("invalid day")
        key=(normalize(name),domain,line)
        row={**item,"book":book,"source":source,"anchor_sha256":digest(item["anchor"]),
             "registry_match":normalize(name) in known,"status":"AUTHOR_GATE_PENDING"}
        if key in result and result[key]!=row:
            raise ValueError("conflicting duplicate")
        result[key]=row
    return list(result.values())
