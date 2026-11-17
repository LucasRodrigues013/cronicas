"""Read-only bridge to the existing private WORLDROOT 4.3 literal index."""
import sqlite3
from pathlib import Path

class LegacyLiteralIndex:
    def __init__(self,path):
        self.path=Path(path).resolve()
        if not self.path.is_file():raise FileNotFoundError(self.path)
    def query(self,phrase,limit=10):
        if not phrase or not 1<=limit<=100:raise ValueError('Phrase and bounded limit required')
        conn=sqlite3.connect(f'file:{self.path}?mode=ro&immutable=1',uri=True)
        try:
            rows=conn.execute('''SELECT l.source_id,l.line_no,l.text,l.layer
                    FROM literal_search s JOIN literal_lines l ON l.row_id=s.rowid
                    WHERE literal_search MATCH ? ORDER BY rank LIMIT ?''',(phrase,limit)).fetchall()
            return [{'source_id':r[0],'line':r[1],'literal':r[2],'layer':r[3]} for r in rows]
        finally:conn.close()
