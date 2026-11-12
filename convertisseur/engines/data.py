"""Données : JSON, JSON Lines, YAML, TOML, XML, SQLite <-> les uns vers les autres et vers CSV, XLSX, ODS, HTML…"""
from __future__ import annotations

import datetime
import json
import re
import sqlite3
from pathlib import Path
from xml.etree import ElementTree as ET

from ..util import FinalError, read_text_any

TABLE_OUT = {"csv", "tsv", "xlsx", "ods", "html", "md", "txt"}


# ---------------------------------------------------------------- lecture
def _strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _xml_to_obj(el):
    d = {f"@{k}": v for k, v in el.attrib.items()}
    for child in el:
        tag, val = _strip_ns(child.tag), _xml_to_obj(child)
        if tag in d:
            if not isinstance(d[tag], list):
                d[tag] = [d[tag]]
            d[tag].append(val)
        else:
            d[tag] = val
    text = (el.text or "").strip()
    if text:
        if not d:
            return text
        d["#text"] = text
    return d or None


def read_data(path, fmt):
    if fmt in ("sqlite", "sqlite3", "db"):
        try:
            con = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' "
                                                "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            out = {t: [dict(r) for r in con.execute(f'SELECT * FROM "{t}"')] for t in tables}
            con.close()
        except sqlite3.DatabaseError as e:
            raise FinalError(f"Base SQLite illisible : {e}")
        if not out:
            raise FinalError("La base de données ne contient aucune table.")
        return out
    text = read_text_any(path)
    try:
        if fmt == "json":
            return json.loads(text)
        if fmt in ("jsonl", "ndjson"):
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        if fmt in ("yaml", "yml"):
            import yaml
            docs = [d for d in yaml.safe_load_all(text)]
            return docs[0] if len(docs) == 1 else docs
        if fmt == "toml":
            import tomllib
            return tomllib.loads(text)
        if fmt == "xml":
            root = ET.fromstring(text.encode("utf-8"))
            return {_strip_ns(root.tag): _xml_to_obj(root)}
    except FinalError:
        raise
    except Exception as e:
        raise FinalError(f"Données illisibles ({fmt.upper()}) : {e}")
    raise FinalError(f"Format de données non géré : {fmt}")


# ---------------------------------------------------------------- tableaux
def _flat(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    if isinstance(value, bytes):
        return value.hex()
    return "" if value is None else value


def _records_table(records):
    keys = []
    for r in records:
        for k in r:
            if k not in keys:
                keys.append(k)
    return [keys] + [[_flat(r.get(k)) for k in keys] for r in records]


def to_tables(obj, name=None) -> list[tuple[str, list[list]]]:
    from ..i18n import tr
    name = name or tr("Données")
    if isinstance(obj, list):
        if obj and all(isinstance(r, dict) for r in obj):
            return [(name, _records_table(obj))]
        return [(name, [[_flat(v)] if not isinstance(v, list) else [_flat(x) for x in v] for v in obj])]
    if isinstance(obj, dict):
        lists = {k: v for k, v in obj.items() if isinstance(v, list) and v and all(isinstance(r, dict) for r in v)}
        if lists and len(lists) == len(obj):
            return [(str(k), _records_table(v)) for k, v in lists.items()]
        if len(obj) == 1:                       # racine XML ou objet enveloppe : on descend d'un niveau
            (k, v), = obj.items()
            if isinstance(v, (dict, list)):
                inner = to_tables(v, str(k))
                if inner and len(inner[0][1]) > 1:
                    return inner
        rows = [[tr("clé"), tr("valeur")]]

        def walk(prefix, val):
            if isinstance(val, dict):
                for kk, vv in val.items():
                    walk(f"{prefix}.{kk}" if prefix else str(kk), vv)
            else:
                rows.append([prefix, _flat(val)])
        walk("", obj)
        return [(name, rows)]
    return [(name, [[_flat(obj)]])]


def from_tables(sheets) -> object:
    def records(rows):
        if len(rows) > 1 and all(isinstance(h, str) and h for h in rows[0]):
            head = [str(h) for h in rows[0]]
            return [{h: (r[i] if i < len(r) else "") for i, h in enumerate(head)} for r in rows[1:]]
        return rows
    if len(sheets) == 1:
        return records(sheets[0][1])
    return {str(n): records(r) for n, r in sheets}


# ---------------------------------------------------------------- écriture
_TAG = re.compile(r"[^\w.-]")


def _tag(name) -> str:
    t = _TAG.sub("_", str(name)) or "element"
    return t if re.match(r"[A-Za-z_]", t) else f"_{t}"


def _obj_to_xml(parent, key, value):
    if isinstance(value, list):
        for v in value:
            _obj_to_xml(parent, key, v)
        return
    el = ET.SubElement(parent, _tag(key))
    if isinstance(value, dict):
        for k, v in value.items():
            if str(k).startswith("@"):
                el.set(_tag(str(k)[1:]), str(_flat(v)))
            elif k == "#text":
                el.text = str(_flat(v))
            else:
                _obj_to_xml(el, k, v)
    elif value is not None:
        el.text = str(value)


def to_xml(obj) -> str:
    if isinstance(obj, dict) and len(obj) == 1 and not isinstance(next(iter(obj.values())), list):
        (root_name, inner), = obj.items()
        root = ET.Element(_tag(root_name))
        holder = ET.Element("tmp")
        _obj_to_xml(holder, root_name, inner)
        root = holder[0]
    else:
        root = ET.Element("donnees")
        if isinstance(obj, dict):
            for k, v in obj.items():
                _obj_to_xml(root, k, v)
        else:
            _obj_to_xml(root, "element", obj if isinstance(obj, list) else [obj])
    ET.indent(root)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def _toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (datetime.date, datetime.datetime, datetime.time)):
        return v.isoformat()
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v if x is not None) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{_toml_key(k)} = {_toml_value(x)}" for k, x in v.items() if x is not None) + " }"
    return json.dumps(str(v), ensure_ascii=False)


def _toml_key(k) -> str:
    k = str(k)
    return k if re.fullmatch(r"[A-Za-z0-9_-]+", k) else json.dumps(k, ensure_ascii=False)


def to_toml(obj, prefix="") -> str:
    if not isinstance(obj, dict):
        obj = {"elements": obj}
    lines, tables = [], []
    for k, v in obj.items():
        if v is None:
            continue
        if isinstance(v, dict):
            tables.append((k, v, False))
        elif isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            tables.append((k, v, True))
        else:
            lines.append(f"{_toml_key(k)} = {_toml_value(v)}")
    out = "\n".join(lines)
    for k, v, many in tables:
        name = f"{prefix}.{_toml_key(k)}" if prefix else _toml_key(k)
        for item in (v if many else [v]):
            body = to_toml(item, name)
            out += f"\n\n[{'[' if many else ''}{name}{']' if many else ''}]\n{body}".rstrip()
    return out.strip() + "\n"


def write(obj, dst, d, opts, title) -> list[Path]:
    dst = Path(dst)
    if d == "json":
        dst.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    elif d == "yaml":
        import yaml
        dst.write_text(yaml.safe_dump(json.loads(json.dumps(obj, default=str)), allow_unicode=True, sort_keys=False),
                       encoding="utf-8")
    elif d == "xml":
        dst.write_text(to_xml(json.loads(json.dumps(obj, default=str))), encoding="utf-8")
    elif d == "toml":
        dst.write_text(to_toml(json.loads(json.dumps(obj, default=str))), encoding="utf-8")
    elif d in TABLE_OUT:
        from .office import write_tables
        return write_tables(to_tables(obj, title), dst, d, opts, title)
    else:
        raise FinalError(f"Format de sortie non géré : {d}")
    return [dst]


def convert(ctx, src, sfmt, dst, d):
    ctx.progress(None, "Lecture des données…")
    return write(read_data(src, sfmt), dst, d, ctx.opts, ctx.stem)


def from_table(ctx, src, sfmt, dst, d):
    from .office import read_tables
    ctx.progress(None, "Lecture du tableur…")
    return write(from_tables(read_tables(src, sfmt)), dst, d, ctx.opts, ctx.stem)
