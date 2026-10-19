#!/usr/bin/env python3
"""LUCIA LAB free-tier CPU coordinator (optional Oracle VM).
- External input: ONLY owner-authored public GitHub issue directions.
- No private files, clinical data, credentials, GitHub writes or deployment.
- Local Ollama is optional; model output is an UNVERIFIED DRAFT, never executed.
- SQLite queue survives interruption; work is rate-limited and rotates turns.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from urllib.request import Request, urlopen

HOME=Path(os.getenv("LUCIA_FACTORY_HOME","/var/lib/lucia-factory"))
PUBLIC_PROJECTS={
    "neurocity":("clucaina","NPL-CANONICAL",3),
    "psicologia-politica":("clucaina","psicologia-politica",15)
}
FOCI={"VISUAL","DATOS","CONTENIDO","INTEGRACION","SEGURIDAD","GENERAL"}
ROLES=("Revisión de fuentes","Detección de vacíos","Propuesta de mejora","Crítica metodológica")
PROBLEMS={
    "neurocity":"Ciudad 3D realista navegable con fuentes verificables y NPL/Conflictómetro integrados; no inventar alturas ni fachadas.",
    "psicologia-politica":"Fuentes fechadas, reproducibilidad, análisis político y calidad del contenido; no afirmar que V78 está desplegada."
}
def parse_focus(body):
    match=re.search(r"(?mi)^FOCO:\s*(VISUAL|DATOS|CONTENIDO|INTEGRACION|SEGURIDAD|GENERAL)\s*$",body or "")
    return match.group(1).upper() if match else "GENERAL"
def setup(db):
    db.execute("CREATE TABLE IF NOT EXISTS projects(name TEXT PRIMARY KEY, focus TEXT, issue_sha TEXT, rotations INTEGER NOT NULL DEFAULT 0, last_at TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS findings(id INTEGER PRIMARY KEY, name TEXT NOT NULL, timestamp TEXT NOT NULL, role TEXT NOT NULL, sha256 TEXT NOT NULL, status TEXT NOT NULL, content TEXT NOT NULL)")
    db.commit()
def read_direction(name, opener=urlopen):
    owner,repo,issue=PUBLIC_PROJECTS[name]
    url=f"https://api.github.com/repos/{owner}/{repo}/issues/{issue}"
    request=Request(url,headers={"User-Agent":"LuciaLab-Federated-ReadOnly/1.0","Accept":"application/vnd.github+json"})
    with opener(request,timeout=18) as resp:
        data=json.loads(resp.read(20000))
    if data.get("user",{}).get("login")!=owner:
        raise ValueError("Issue author does not match expected GitHub owner")
    return parse_focus(data.get("body","")),str(data.get("updated_at","")),str(data.get("html_url",""))
def local_model(prompt,opener=urlopen):
    model=os.getenv("LUCIA_OLLAMA_MODEL","").strip()
    if not model:return None
    url="http://127.0.0.1:11434/api/generate"
    payload=json.dumps({"model":model,"prompt":prompt,"stream":False,
        "options":{"num_predict":520,"temperature":0.25}}).encode("utf-8")
    req=Request(url,data=payload,headers={"Content-Type":"application/json"},method="POST")
    with opener(req,timeout=240) as response:
        ans=json.loads(response.read(30000))
    return str(ans.get("response",""))[:12000]
def once(home=HOME,reader=read_direction,model=local_model):
    home.mkdir(parents=True,exist_ok=True,mode=0o700)
    db=sqlite3.connect(str(home/"factory.sqlite3"),timeout=10)
    setup(db)
    report=[]
    for project in PUBLIC_PROJECTS:
        name,focus,source_link=project,"GENERAL",""
        fetch_error=None
        try:
            focus,stamp,source_link=reader(name)
        except Exception as exc:
            fetch_error=type(exc).__name__
            prev=db.execute("SELECT focus FROM projects WHERE name=?",(name,)).fetchone()
            if prev:focus=prev[0]
        db.execute("INSERT INTO projects(name,focus,issue_sha) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET focus=excluded.focus",
            (name,focus,"public GitHub issue"))
        current=db.execute("SELECT rotations FROM projects WHERE name=?",(name,)).fetchone()[0]
        role=ROLES[current%len(ROLES)]
        stamp=dt.datetime.now(dt.timezone.utc).isoformat()
        prompt=(f"Rol: {role}. Proyecto: {name}. Foco: {focus}. "
            f"Objetivo: {PROBLEMS[name]} "
            "Propón una sola mejora verificable y dos pruebas falsables. "
            "Distingue claramente hallazgos comprobados de propuestas; no inventes hechos ni tests. "
            "Nunca pidas datos privados, ni aconsejes publicar o ejecutar código sin revisión.")
        try:
            suggestion=model(prompt)
            if suggestion:
                state="PROPOSAL_UNVERIFIED_REQUIRES_REVIEW"
                content=suggestion
            else:
                state="NO_MODEL_CONFIGURED"
                content="No se ha ejecutado ninguna IA. Ciclo de supervisión y persistencia únicamente."
        except Exception as exc:
            state="MODEL_ERROR_NO_WORK_COMPLETED"
            content=type(exc).__name__
        digest=hashlib.sha256(content.encode("utf-8")).hexdigest()
        db.execute("INSERT INTO findings(name,timestamp,role,sha256,status,content) VALUES(?,?,?,?,?,?)",
            (name,stamp,role,digest,state,content))
        db.execute("UPDATE projects SET rotations=rotations+1,last_at=? WHERE name=?",(stamp,name))
        report.append({"project":name,"focus":focus,"shift":role,"state":state,
                       "read_error":fetch_error,"direction_source":source_link,
                       "report_sha256":digest,"time":stamp})
    db.commit()
    # Observe the public neural garden; preserve report locally, no GitHub writes.
    # Failure to reach evidence APIs does not interrupt the per-root queues.
    try:
        from neural_garden import assemble, save
        layout=Path("/opt/lucia-factory/garden_view.html")
        if layout.is_file():
            save(assemble(),home/"garden",layout)
    except (OSError,ImportError,ValueError) as exc:
        (home/"garden_last_error.txt").write_text(type(exc).__name__,encoding="utf-8")
    (home/"last_run.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    db.close()
    return report
def daemon():
    interval=max(1800,int(os.getenv("LUCIA_FACTORY_INTERVAL_SECONDS","7200")))
    while True:
        try:print(json.dumps(once(),ensure_ascii=False),flush=True)
        except Exception as exc:print(json.dumps({"fatal_cycle_error":type(exc).__name__}),flush=True)
        time.sleep(interval)
if __name__=="__main__":
    if os.getenv("LUCIA_FACTORY_ONCE")=="1":
        print(json.dumps(once(),ensure_ascii=False,indent=2))
    else:daemon()
