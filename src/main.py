#!/usr/local/bin/python3
"""
Generate index.html files for directories using head.html and foot.html templates.
"""

from __future__ import annotations
import os
import json
import base64
import datetime as dt
from pathlib import Path
from typing import List, Tuple

# Paths (adjust if your repo layout differs)
TEMPLATE_DIR = Path('/src/template')
HEAD_TEMPLATE = TEMPLATE_DIR / 'head.html'
FOOT_TEMPLATE = TEMPLATE_DIR / 'foot.html'
ICONS_JSON = Path('/src/icons.json')
ICONS_DIR = Path('/src/png')

def load_icons() -> List[dict]:
    try:
        return json.loads(ICONS_JSON.read_text(encoding='utf-8'))
    except Exception:
        return []

ICONS = load_icons()

def format_size(bytes_count: int) -> str:
    if bytes_count < 1024:
        return f"{bytes_count} B"
    kb = bytes_count / 1024.0
    if kb < 1024:
        return f"{kb:.2f} KB"
    mb = kb / 1024.0
    if mb < 1024:
        return f"{mb:.2f} MB"
    gb = mb / 1024.0
    return f"{gb:.2f} GB"

def format_mtime(path: Path) -> str:
    try:
        ts = path.stat().st_mtime
        return dt.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return "-"

def get_icon_name(filename: str) -> str:
    # special tokens used by the generator
    if filename in ('o.folder', 'o.folder-home'):
        return filename + '.png'
    ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    for entry in ICONS:
        try:
            if ext and ext in entry.get('extension', []):
                return entry.get('icon') + '.png'
        except Exception:
            continue
    return 'unknown.png'

def icon_data_uri(filename: str) -> str:
    icon_file = ICONS_DIR / get_icon_name(filename)
    try:
        data = base64.b64encode(icon_file.read_bytes()).decode('ascii')
        # include a space after the comma to match your sample formatting
        return 'data:image/png;base64, ' + data
    except Exception:
        # tiny transparent PNG fallback
        return 'data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='

def read_template(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return ''

def compute_totals(root: Path) -> Tuple[int, int]:
    total_files = 0
    total_bytes = 0
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower() == 'index.html':
                continue
            p = Path(dirpath) / fn
            try:
                total_files += 1
                total_bytes += p.stat().st_size
            except Exception:
                continue
    return total_files, total_bytes

def make_index(dirpath: Path, head_tpl: str, foot_tpl: str, totals: Tuple[int, int], buildtime: str) -> None:
    index = dirpath / 'index.html'
    if index.exists():
        # keep original behavior: skip existing index.html
        return

    try:
        entries = list(dirpath.iterdir())
    except Exception:
        entries = []

    dirs = sorted([e.name for e in entries if e.is_dir()])
    files = sorted([e.name for e in entries if e.is_file() and e.name.lower() != 'index.html'])

    foldername = '/' if dirpath in (Path('.'), Path('./')) else str(dirpath)
    content = head_tpl.replace('{{foldername}}', foldername)

    # parent directory link when not root
    if dirpath not in (Path('.'), Path('./'), Path('/')):
        content += (
            '<tr class="bg-gray-800 border-b border-gray-600 hover:bg-gray-700">'
            '<th scope="row" class="py-2 px-2 lg:px-6 font-medium text-gray-300 flex align-middle">'
            f'<img style="max-width:23px;margin-right:5px" src="{icon_data_uri("o.folder-home")}">'
            '<a class="my-auto text-blue-400" href="../">../</a></th>'
            '<td>-</td><td>-</td></tr>\n'
        )

    # directories
    for d in dirs:
        content += (
            '<tr class="bg-gray-800 border-b border-gray-600 hover:bg-gray-700">'
            '<th scope="row" class="py-2 px-2 lg:px-6 font-medium text-gray-300 flex align-middle">'
            f'<img style="max-width:23px;margin-right:5px" src="{icon_data_uri(d)}">'
            f'<a class="my-auto text-blue-400" href="{d}/">{d}/</a></th>'
            '<td>-</td><td>-</td></tr>\n'
        )

    # files
    for fn in files:
        p = dirpath / fn
        try:
            size = format_size(p.stat().st_size)
        except Exception:
            size = '-'
        mtime = format_mtime(p)
        content += (
            '<tr class="bg-gray-800 border-b border-gray-600 hover:bg-gray-700">'
            '<th scope="row" class="py-2 px-2 lg:px-6 font-medium text-gray-300 flex align-middle">'
            f'<img style="max-width:23px;margin-right:5px" src="{icon_data_uri(fn)}">'
            f'<a class="my-auto text-blue-400" href="{fn}">{fn}</a></th>'
            f'<td>{size}</td><td>{mtime}</td></tr>\n'
        )

    foot = (foot_tpl
            .replace('{{total_files}}', str(totals[0]))
            .replace('{{total_size}}', format_size(totals[1]))
            .replace('{{buildtime}}', buildtime))
    content += foot

    try:
        index.write_text(content, encoding='utf-8')
    except Exception:
        # silently ignore write failures in CI environment
        pass

# --- Entry point ---
def entrypoint():
    # If a path is supplied via argv[1], use it; otherwise use current directory.
    target_arg = None
    try:
        import sys
        if len(sys.argv) > 1:
            target_arg = sys.argv[1]
    except Exception:
        target_arg = None

    root = Path(target_arg) if target_arg else Path('.')

    # compute totals for the archive (used in each generated footer)
    totals = compute_totals(root)
    buildtime = "at " + dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    head_tpl = read_template(HEAD_TEMPLATE)
    foot_tpl = read_template(FOOT_TEMPLATE)

    for dirpath, _, _ in os.walk(root):
        make_index(Path(dirpath), head_tpl, foot_tpl, totals, buildtime)

if __name__ == '__main__':
    entrypoint()
