#!/usr/bin/env python3
"""Convierte guiones educativos en lista de planos, subtítulos y guion técnico.

No genera vídeo, voz ni rostros. No requiere red, librerías externas ni modelos.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import re

SCHEMA = "npl-educacion-storyboard/1"


def filename(value: str) -> str:
    name = re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-")
    if not name:
        raise ValueError("El ID de la pieza es inválido")
    return name[:75]


def timestamp(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, frac = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{frac:03}"


def sanitized_csv(value: object) -> str:
    s = str(value or "")
    return "'" + s if s.startswith(("=", "+", "-", "@", "\t", "\r")) else s


def validate(payload: dict) -> None:
    if payload.get("schema") != SCHEMA or not isinstance(payload.get("videos"), list):
        raise ValueError("Esquema audiovisual no reconocido")
    if not payload["videos"] or len(payload["videos"]) > 100:
        raise ValueError("La colección debe contener de 1 a 100 piezas")
    seen = set()
    for video in payload["videos"]:
        if not isinstance(video, dict) or not isinstance(video.get("scenes"), list):
            raise ValueError("Pieza o escenas inválidas")
        identifier = filename(str(video.get("id", "")))
        if identifier in seen:
            raise ValueError("Identificador de pieza repetido")
        seen.add(identifier)
        scenes = video["scenes"]
        if not scenes or len(scenes) > 120:
            raise ValueError("Número de escenas fuera de límites")
        total = 0
        for scene in scenes:
            if not isinstance(scene, dict):
                raise ValueError("Escena inválida")
            duration = scene.get("seconds")
            if type(duration) not in (int, float) or duration <= 0 or duration > 180:
                raise ValueError("Duración de escena inválida")
            total += duration
            if any(not str(scene.get(k, "")).strip() for k in ("title", "visual", "narration", "caption")):
                raise ValueError("La escena no tiene guion, visual o subtítulo")
        if abs(total - float(video.get("target_seconds", -1))) > 0.01:
            raise ValueError("La duración total no coincide con las escenas")


def convert(payload: dict, destination: Path, dry_run: bool = False) -> list[dict]:
    validate(payload)
    exports = []
    for video in payload["videos"]:
        name = filename(str(video["id"]))
        time = 0.0
        srt = []
        rows = []
        md = [f"# {video.get('title', name)}", "",
              f"Destino: {video.get('project', 'sin determinar')}", "",
              "Guion original de preproducción. NO acredita vídeo renderizado ni voz generada.", ""]
        for i, scene in enumerate(video["scenes"], start=1):
            end = time + float(scene["seconds"])
            srt.append(f"{i}\n{timestamp(time)} --> {timestamp(end)}\n{scene['caption']}\n")
            rows.append({
                "num": i, "start": timestamp(time), "end": timestamp(end),
                "title": sanitized_csv(scene["title"]),
                "visual": sanitized_csv(scene["visual"]),
                "narration": sanitized_csv(scene["narration"]),
                "caption": sanitized_csv(scene["caption"]),
            })
            md += [
                f"## Plano {i}: {scene['title']}",
                f"Intervalo: {timestamp(time)} a {timestamp(end)}",
                f"Visual: {scene['visual']}",
                f"Narración: {scene['narration']}",
                f"Subtítulo: {scene['caption']}", "",
            ]
            time = end
        files = [name + ".srt", name + ".csv", name + ".md"]
        exports.append({"id": name, "duration": time, "scenes": len(rows), "files": files})
        if dry_run:
            continue
        destination.mkdir(parents=True, exist_ok=True)
        (destination / files[0]).write_text("\n".join(srt), encoding="utf-8")
        with (destination / files[1]).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter=";")
            writer.writeheader()
            writer.writerows(rows)
        (destination / files[2]).write_text("\n".join(md), encoding="utf-8")
    return exports


def main() -> None:
    parser = argparse.ArgumentParser(description="Exportar subtítulos y lista de planos de Neuropsicolucía")
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("guiones-audiovisuales.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    for row in convert(payload, args.output, dry_run=args.dry_run):
        print(f"{row['id']}: {row['scenes']} planos, {row['duration']:.0f} s -> {', '.join(row['files'])}")


if __name__ == "__main__":
    main()
