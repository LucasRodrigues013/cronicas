"""Unified R36 read/command facade; existing authority and projections remain owners."""
import argparse
import json
import sqlite3
from pathlib import Path
from . import git_cycle as g
from .r36_authority import ratify,continuation

def status(root):
    root=Path(root);head=g.load(root/"canon/HEAD.json")
    result={"revision":36,"head":head,"projection":g.verify_db(root,head),
            "resume":g.load(root/"ops/RESUME.json"),"production_activation":False}
    if head["sequence"]:
        c=g.load(root/"canon/episodes"/(head["episode_id"]+".json"))
        if c.get("ratification_kind")=="R36_EXPLICIT_RATIFICATION_NO_CONTINUATION":
            result["continuation"]=continuation(root,head["episode_id"])
    return result

def temporal_events(root,day,clock=None,limit=50):
    """Public events only; unknown same-day clocks excluded from timed queries."""
    if type(day) is not int or day<1 or type(limit) is not int or not 1<=limit<=200:
        raise ValueError("Invalid temporal bounds")
    if clock is not None and not g.CLOCK.fullmatch(clock):raise ValueError("Invalid clock")
    root=Path(root);g.verify_db(root,g.load(root/"canon/HEAD.json"))
    sql="SELECT event_id,episode_id,summary,event_type,day,hour,source_line FROM events WHERE visibility='PUBLICO'"
    params=[]
    if clock is None:sql+=" AND day<=?";params.append(day)
    else:sql+=" AND (day<? OR (day=? AND hour IS NOT NULL AND hour<=?))";params.extend([day,day,clock])
    sql+=" ORDER BY day DESC,hour DESC,event_id LIMIT ?";params.append(limit)
    with sqlite3.connect((root/"canon/state.sqlite").resolve().as_uri()+"?mode=ro",uri=True) as db:
        db.row_factory=sqlite3.Row
        return [dict(x) for x in db.execute(sql,params)]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("command",choices=["status","ratify","choose-status","restore","timeline"]);p.add_argument("--archive-root",type=Path,required=True);p.add_argument("--episode");p.add_argument("--approval");p.add_argument("--day",type=int);p.add_argument("--clock");a=p.parse_args()
    if a.command=="status":out=status(a.archive_root)
    elif a.command=="ratify":out=ratify(a.archive_root,a.episode,a.approval)
    elif a.command=="choose-status":out=continuation(a.archive_root,a.episode)
    elif a.command=="restore":out=g.restore(a.archive_root)
    else:out=temporal_events(a.archive_root,a.day,a.clock)
    print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
