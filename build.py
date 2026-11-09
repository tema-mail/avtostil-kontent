#!/usr/bin/env python3
"""Сборка site/: главная со всеми материалами, страница на каждую статью Дзена и каждый пост ВК.
Картинки Дзена режутся из foto/src (обложка 4:3, в тексте 16:9), карусели ВК – ~/Sites/redakciya/scripts/karusel.py."""
import csv, html, json, re, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).parent
SITE = ROOT / "site"
BASE = "https://tema-mail.github.io/avtostil-kontent/"
KARUSEL = Path.home() / "Sites/redakciya/scripts/karusel.py"
sys.path.insert(0, str(ROOT))
from lint import parse, lint_dzen, lint_vk, words  # noqa: E402

PLAN = list(csv.DictReader(open(ROOT / "docs/plan.csv"), delimiter=";"))
UNAME = {"shumoizolyaciya": "Шумоизоляция", "avtozvuk": "Автозвук", "android-magnitoy": "Android-магнитолы",
         "ohrannie-komplekci": "Охранные системы", "dopolnitelnoe-oborudovanie": "Доп. оборудование", "magazin": "Магазин"}
CSS = """:root{--bg:#fff;--fg:#111;--mut:#666;--card:#f3f4f6;--line:#ddd;--acc:#1d6fe0}
@media (prefers-color-scheme:dark){:root{--bg:#121417;--fg:#eee;--mut:#9aa;--card:#1d2126;--line:#333;--acc:#5ab4ff}}
*{box-sizing:border-box}body{font:17px/1.55 -apple-system,Segoe UI,Arial,sans-serif;max-width:860px;margin:0 auto;padding:16px;background:var(--bg);color:var(--fg)}
img{max-width:100%;border-radius:8px;display:block}a{color:var(--acc)}h1{font-size:26px;line-height:1.25}h2{margin-top:1.4em}
.kit{background:var(--card);padding:16px;border-radius:12px;font-size:15px}.meta{color:var(--mut);margin-bottom:10px}
.step{display:flex;align-items:center;gap:10px;margin:8px 0;flex-wrap:wrap}.step span{width:26px;height:26px;border-radius:50%;background:var(--fg);color:var(--bg);display:grid;place-items:center;font-size:14px;flex:none}
button,.btn{padding:10px 14px;border:1px solid var(--line);background:var(--bg);color:var(--fg);border-radius:8px;cursor:pointer;font:15px -apple-system,Arial,sans-serif;text-decoration:none;display:inline-block}
button.main{background:var(--acc);color:#fff;border-color:var(--acc)}
table{border-collapse:collapse;width:100%;font-size:15px}td,th{border-bottom:1px solid var(--line);padding:7px 6px;text-align:left;vertical-align:top}
.wrap{overflow-x:auto}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}.post{white-space:pre-wrap;background:var(--card);padding:14px;border-radius:10px}
.note{background:var(--card);border-left:4px solid var(--acc);padding:10px 14px;border-radius:6px}.bad{border-left-color:#d33}"""
JS = """<script>const done=(b,t)=>{const o=b.textContent;b.textContent=t;setTimeout(()=>b.textContent=o,1800)};
function copyText(id,b){navigator.clipboard.writeText(document.getElementById(id).innerText);done(b,'Скопировано')}
async function copyBody(b){const d=document.getElementById('b').cloneNode(true);d.querySelectorAll('img').forEach(i=>{i.setAttribute('src',i.src);i.removeAttribute('alt')});
await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([d.innerHTML],{type:'text/html'}),'text/plain':new Blob([d.innerText],{type:'text/plain'})})]);done(b,'Скопировано: вставляйте в редактор Дзена')}</script>"""


def head(title):
    return f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style></head><body>'


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda x: f'<a href="{x.group(2)}">{x.group(1)}</a>', s)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def crop(src, dst, ratio, w=1200):
    im = ImageOps.exif_transpose(Image.open(ROOT / "foto/src" / src)).convert("RGB")
    im = ImageOps.fit(im, (w, round(w / ratio)), centering=(0.5, 0.5))
    im.save(dst, quality=84, optimize=True)


def dzen_page(f, row):
    m, blocks = parse(f)
    e, n = lint_dzen(str(f))
    slug, ph = m["slug"], row["foto"].split()
    (SITE / "img").mkdir(parents=True, exist_ok=True)
    cov = ROOT / "gen/covers" / f"{row['id']}.png"
    if cov.exists():
        im = ImageOps.fit(Image.open(cov).convert("RGB"), (1200, 900)); im.save(SITE / f"img/dzen-{slug}-0.jpg", quality=86, optimize=True)
    else:
        e.append("нет сгенерированной обложки")
    for i, p in enumerate(ph[:2], 1):
        crop(p + ".jpg", SITE / f"img/dzen-{slug}-{i}.jpg", 16 / 9)
    parts, kit = [], []
    for b in blocks:
        if b.startswith("{img"):
            i = b[4]; u = f"{BASE}img/dzen-{slug}-{i}.jpg"
            parts.append(f'<p><img src="img/dzen-{slug}-{i}.jpg" alt=""></p>')
            kit.append(f'<li><a href="{u}" download>Картинка {i}</a></li>')
        elif b.startswith("## "):
            parts.append(f"<h2>{inline(b[3:])}</h2>")
        else:
            parts.append(f"<p>{inline(' '.join(b.split()))}</p>")
    warn = "" if not e else '<p class="note bad">Проверка: ' + "; ".join(map(html.escape, e)) + "</p>"
    page = head(m["title"] + " – Дзен") + f"""<p><a href="index.html">← Все материалы</a></p>{warn}
<div class="kit"><div class="meta">{row['id']} · выход {m['date']} · {UNAME[row['stranica']]} · {n} слов · главный ключ: {html.escape(row['glavnyy'])}<br>хвосты: {html.escape(row['hvosty'])}</div>
<div class="step"><span>1</span><button onclick="copyText('t',this)">Скопировать заголовок</button></div>
<div class="step"><span>2</span><a class="btn" href="img/dzen-{slug}-0.jpg" download>Скачать обложку</a></div>
<div class="step"><span>3</span><button class="main" onclick="copyBody(this)">Скопировать весь текст с картинками</button></div>
<details><summary>Если картинки не вставились</summary><ol>{''.join(kit)}</ol></details></div>
<h1 id="t">{html.escape(m['title'])}</h1><p><img src="img/dzen-{slug}-0.jpg" alt="обложка"></p><div id="b">{''.join(parts)}</div>{JS}</body></html>"""
    (SITE / f"dzen-{slug}.html").write_text(page, encoding="utf8")
    return m, n, e


def vk_page(f, row):
    m, blocks = parse(f)
    e, n = lint_vk(str(f))
    out = SITE / "vk" / row["id"]
    if out.exists(): shutil.rmtree(out)
    if m.get("kartinka"):
        out.mkdir(parents=True, exist_ok=True)
        src = ROOT / "gen/vk" / m["kartinka"]
        if src.exists(): ImageOps.fit(Image.open(src).convert("RGB"), (1080, 1350)).save(out / "01.jpg", quality=86, optimize=True)
    else:
        r = subprocess.run([sys.executable, str(KARUSEL), str(Path(f).with_suffix(".json")), str(ROOT / "foto/src"), str(out)], capture_output=True, text=True)
        if r.returncode: e.append("карусель не собралась: " + (r.stderr or r.stdout)[-200:])
    cards = sorted(out.glob("*.png")) + sorted(out.glob("*.jpg"))
    imgs = "".join(f'<a href="vk/{row["id"]}/{c.name}" download><img src="vk/{row["id"]}/{c.name}" alt="карточка {i}"></a>' for i, c in enumerate(cards, 1))
    post = "\n\n".join(blocks)
    alt = "".join(f"<li>{html.escape(m[k])}</li>" for k in ("zapas1", "zapas2") if m.get(k))
    warn = "" if not e else '<p class="note bad">Проверка: ' + "; ".join(map(html.escape, e)) + "</p>"
    page = head(f"{row['id']} ВК – {blocks[0][:50] if blocks else ''}") + f"""<p><a href="index.html">← Все материалы</a></p>{warn}
<div class="kit"><div class="meta">{row['id']} · выход {m['date']} · подача: {html.escape(m.get('podacha', ''))} · {n} слов · ключ: {html.escape(row['glavnyy'])}</div>
<div class="step"><span>1</span><button class="main" onclick="copyText('p',this)">Скопировать текст поста</button></div>
<div class="step"><span>2</span>{"Картинка: нажмите, чтобы скачать, и загрузите в пост." if m.get("kartinka") else "Карточки: нажмите на каждую, чтобы скачать, и загрузите в пост по порядку (вид «карусель»)."}</div>
<details><summary>Запасные первые строки</summary><ul>{alt}</ul></details></div>
<h2>Текст поста</h2><div class="post" id="p">{html.escape(post)}</div><h2>{"Картинка" if m.get("kartinka") else f"Карусель: {len(cards)} карточек"}</h2><div class="cards">{imgs}</div>{JS}</body></html>"""
    (SITE / f"vk-{row['id']}.html").write_text(page, encoding="utf8")
    return m, n, e, len(cards)


def main():
    SITE.mkdir(exist_ok=True)
    rows_d, rows_v, bad = [], [], 0
    for row in PLAN:
        d = "dzen" if row["ploshchadka"] == "dzen" else "vk"
        fs = sorted((ROOT / d).glob(f"{row['id']}-*.md"))
        if not fs:
            (rows_d if d == "dzen" else rows_v).append((row, None)); continue
        if d == "dzen":
            m, n, e = dzen_page(fs[0], row); rows_d.append((row, (m["title"], n, e, f"dzen-{m['slug']}.html")))
        else:
            m, n, e, k = vk_page(fs[0], row); rows_v.append((row, (parse(fs[0])[1][0], n, e, f"vk-{row['id']}.html", k)))
        bad += bool(e)

    def tr(row, x):
        if not x: return f"<tr><td>{row['id']}</td><td>{row['data']}</td><td>{html.escape(row['tema'])}</td><td>не написано</td></tr>"
        st = "готово к проверке" if not x[2] else "ошибки проверки"
        return f"<tr><td>{row['id']}</td><td>{row['data']}</td><td><a href=\"{x[3]}\">{html.escape(x[0])}</a><br><small>{html.escape(row['glavnyy'])}</small></td><td>{st}</td></tr>"

    th = "<tr><th>№</th><th>Выход</th><th>Материал и запрос</th><th>Статус</th></tr>"
    done_d = sum(1 for _, x in rows_d if x); done_v = sum(1 for _, x in rows_v if x)
    idx = head("Звук на Волге: Дзен и ВК") + f"""<h1>«Звук на Волге» (бывш. «Автостиль»), Ярославль: 30 статей Дзена и 20 постов ВК</h1>
<p class="meta">Студия автозвука «Звук на Волге» (раньше «Автостиль»), проспект Октября, 82б. Сборка {__import__('datetime').date.today().strftime('%d.%m.%Y')}. Черновики: публикуем только после «да» владельца.</p>
<audio controls src="itog.mp3" preload="none" style="width:100%"></audio>
<p>Дзен: {done_d} из 30 · ВК: {done_v} из 20 · с ошибками проверки: {bad}</p>
<p><a href="#dzen">Дзен</a> · <a href="#vk">ВК</a> · <a href="kak.html">Как сделано и что проверить</a></p>
<h2 id="dzen">Дзен – по одной статье в день с 12.11</h2><div class="wrap"><table>{th}{''.join(tr(r, x) for r, x in rows_d)}</table></div>
<h2 id="vk">ВК – V01–V15 карусели (без изменений, кроме названия), V16–V20 про сигнализации и отопители с одной картинкой</h2><div class="wrap"><table>{th}{''.join(tr(r, x) for r, x in rows_v)}</table></div></body></html>"""
    (SITE / "index.html").write_text(idx, encoding="utf8")
    kak = ROOT / "docs/kak.html"
    if kak.exists(): shutil.copy(kak, SITE / "kak.html")
    (SITE / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    print(f"Дзен {done_d}/30, ВК {done_v}/20, с ошибками {bad}")


if __name__ == "__main__":
    main()
