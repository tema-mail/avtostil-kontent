#!/usr/bin/env python3
"""Проверка текстов Автостиля. Запуск: python3 lint.py [файл ...] (без аргументов – все dzen/*.md и vk/*.md).
Формат: шапка «ключ: значение» до строки ---, дальше текст. Дзен: {img1} и {img2} отдельными абзацами."""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
PLAN = {r["id"]: r for r in csv.DictReader(open(ROOT / "docs/plan.csv"), delimiter=";")}
SITE = "https://avtostil76.ru"
VKME = "vk.me/avtostil_yaroslavl"
BAN = [r"—", r"₽|\bруб\.?\b|\bрубл", r"\bот \d", r"WhatsApp|ватсап", r"идеальн|лучш(ий|ая|ее|ие)\b|уникальн|№ ?1\b",
       r"по нашим данным|в базе|на сайте указано", r"гарантируем|100 ?%", r"\bшок\b|сенсаци", r"[A-ZА-ЯЁ]{7,}",
       r"угнать невозможно|не угонят", r"к нам (приехал|обратил)", r"наш клиент"]
PHOTOS = {p.name for p in (ROOT / "foto/src").glob("*.jpg")}


def parse(f):
    head, _, body = Path(f).read_text(encoding="utf8").partition("\n---\n")
    m = {}
    for l in head.splitlines():
        if ": " in l:
            k, v = l.split(": ", 1)
            m[k.strip()] = v.strip()
    return m, [b.strip() for b in re.split(r"\n\s*\n", body.strip()) if b.strip()]


def words(t):
    return len(re.findall(r"[0-9A-Za-zА-Яа-яЁё%+-]+", re.sub(r"\]\([^)]+\)", "]", t)))


def ban(text):
    e = []
    for rx in BAN:
        for x in re.finditer(rx, text):
            e.append(f"запрет {rx}: …{text[max(0, x.start() - 25):x.end() + 25]}…".replace("\n", " "))
    return e


def lint_dzen(f):
    m, blocks = parse(f)
    e = []
    p = PLAN.get(m.get("id", ""))
    if not p: return [f"нет id из плана: {m.get('id')}"], 0
    title = m.get("title", "")
    text = "\n".join(blocks)
    n = words(text)
    if not 1200 <= n <= 1800: e.append(f"объём {n} слов (нужно 1200–1800)")
    if not 15 <= len(title) <= 110: e.append(f"заголовок {len(title)} знаков (15–110)")
    low = (title + "\n" + text).lower().replace("ё", "е")
    def has(key):
        ws = [w for w in re.findall(r"[a-zа-я0-9]+", key.lower().replace("ё", "е")) if len(w) > 2 and not w.isdigit()]
        return all(w[:max(4, len(w) - 3)] in low for w in ws)
    keys = lambda f: [re.sub(r"\s+\d+$", "", x.strip()) for x in p.get(f, "").split(";") if x.strip()]
    g = keys("glavnyy")
    if g and not all(w[:max(4, len(w) - 3)] in title.lower().replace("ё", "е") for w in re.findall(r"[а-яa-z]+", g[0].lower()) if len(w) > 3):
        e.append(f"главный ключ не в заголовке: {g[0]}")
    if g and not has(g[0]): e.append(f"нет главного ключа в тексте: {g[0]}")
    miss = [k for k in keys("hvosty") if not has(k)]
    if miss: e.append("нет хвостов: " + ", ".join(miss))
    if "Звук на Волге" not in text: e.append("нет названия «Звук на Волге»")
    if text.count("Автостиль") != 1: e.append(f"«Автостиль» должен быть ровно 1 раз в конце, сейчас {text.count('Автостиль')}")
    elif text.index("Автостиль") < len(text) * 0.8: e.append("«Автостиль» не в конце")
    if sum(b.startswith("## ") for b in blocks) < 5: e.append("меньше 5 подзаголовков ##")
    if "!" in title or title.count("?") > 1: e.append("знаки в заголовке")
    need = f"{SITE}/{p['stranica']}/?utm_source=dzen&utm_medium=article&utm_campaign={p['slug']}"
    if need not in text: e.append(f"нет ссылки {need}")
    if "Октября" not in text: e.append("нет адреса студии")
    if [b for b in blocks if b.startswith("{img")] != ["{img1}", "{img2}"]: e.append("нужно ровно {img1} и {img2} отдельными абзацами")
    if blocks and blocks[0].startswith("#"): e.append("первый абзац – не подзаголовок, а сцена")
    for b in blocks:
        if not b.startswith(("##", "{img")) and len(b) > 600: e.append(f"абзац {len(b)} знаков: {b[:40]}…")
    e += ban(title + "\n" + text)
    return e, n


def lint_vk(f):
    m, blocks = parse(f)
    e = []
    p = PLAN.get(m.get("id", ""))
    if not p: return [f"нет id из плана: {m.get('id')}"], 0
    text = "\n".join(blocks)
    n = words(text)
    if not 60 <= n <= 260: e.append(f"пост {n} слов (60–260)")
    if VKME not in text: e.append(f"нет шага {VKME}")
    if not blocks or len(blocks[0]) > 160: e.append("первая строка длиннее 160 знаков или нет")
    if "?" not in blocks[-1] and "?" not in (blocks[-2] if len(blocks) > 1 else ""): e.append("нет вопроса для обсуждения в конце")
    e += ban(text)
    j = Path(f).with_suffix(".json")
    if m.get("kartinka"):
        if not (ROOT / "gen/vk" / m["kartinka"]).exists(): e.append(f"нет картинки gen/vk/{m['kartinka']}")
        if "Звук на Волге" not in text: e.append("нет названия «Звук на Волге»")
    elif not j.exists(): e.append("нет .json карусели")
    else:
        cfg = json.loads(j.read_text(encoding="utf8"))
        ks = cfg.get("kartochki", [])
        if not 5 <= len(ks) <= 8: e.append(f"карточек {len(ks)} (обычно 6)")
        for i, k in enumerate(ks, 1):
            if k.get("foto") and k["foto"] not in PHOTOS: e.append(f"карточка {i}: нет фото {k['foto']}")
            e += [f"карточка {i}: {x}" for x in ban(k.get("tekst", "") + "\n" + k.get("melko", ""))]
            if len(k.get("tekst", "")) > 70: e.append(f"карточка {i}: заголовок длиннее 70 знаков")
            if len(k.get("melko", "")) > 220: e.append(f"карточка {i}: мелкий текст длиннее 220 знаков")
    return e, n


def main(files):
    files = files or sorted(map(str, list((ROOT / "dzen").glob("*.md")) + list((ROOT / "vk").glob("*.md"))))
    bad = 0
    for f in files:
        e, n = (lint_vk if Path(f).resolve().parent.name == "vk" else lint_dzen)(f)
        print(("OK  " if not e else "ОШИБ") + f" {Path(f).name}: {n} слов")
        for x in e: print("     -", x)
        bad += bool(e)
    print(f"итого {len(files)}, с ошибками {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
