#!/usr/bin/env python3
"""Build a fully offline, single-file HTML slide deck from a JSON manifest."""

import argparse
import base64
import html
import json
import mimetypes
import re
from pathlib import Path


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def image_markup(item: dict, base: Path) -> str:
    src = data_uri((base / item["image"]).resolve())
    alt = html.escape(item.get("alt", "论文图表"))
    caption = item.get("caption", "")
    return f'<figure><img src="{src}" alt="{alt}"><figcaption>{caption}</figcaption></figure>'


def render_slide(slide: dict, base: Path, index: int) -> str:
    kind = slide.get("type", "content")
    kicker = f'<div class="kicker">{slide.get("kicker", "")}</div>' if slide.get("kicker") else ""
    title = slide.get("title", "")
    subtitle = slide.get("subtitle", "")
    body = slide.get("body", "")
    source = slide.get("source", "")
    image = image_markup(slide, base) if slide.get("image") else ""
    metrics = "".join(
        f'<div class="metric"><b>{m.get("value", "")}</b><span>{m.get("label", "")}</span></div>'
        for m in slide.get("metrics", [])
    )
    plain_length = len(re.sub(r"<[^>]+>", "", f"{title}{subtitle}{body}{slide.get('right', '')}"))
    density = "dense" if plain_length > 340 else "sparse" if plain_length < 120 else "balanced"
    if kind == "title":
        content = f'<div class="title-block">{kicker}<h1>{title}</h1><p>{subtitle}</p></div>{image}'
    elif kind == "figure":
        content = f'<header>{kicker}<h2>{title}</h2></header><div class="figure-layout"><div class="copy">{body}</div>{image}</div>'
    elif kind == "split":
        content = f'<header>{kicker}<h2>{title}</h2></header><div class="split"><div>{body}</div><div>{slide.get("right", "")}</div></div>'
    elif kind == "metrics":
        content = f'<header>{kicker}<h2>{title}</h2></header><div class="metrics">{metrics}</div><div class="wide-copy">{body}</div>'
    elif kind == "section":
        content = f'<div class="section-block">{kicker}<h2>{title}</h2><p>{subtitle}</p></div>'
    else:
        content = f'<header>{kicker}<h2>{title}</h2></header><div class="wide-copy">{body}</div>{image}'
    footer = f'<div class="source">{source}</div>' if source else ""
    return f'<section class="slide {kind} {density}" data-index="{index}"><div class="inner">{content}{footer}</div></section>'


CSS = r"""
:root{--ink:#17324d;--muted:#5c6d7e;--accent:#0b8f87;--pale:#eef7f6;--line:#d9e2e8;--paper:#fff;--shadow:0 20px 60px rgba(23,50,77,.15)}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#e8edf1;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",Arial,sans-serif}
#stage{position:fixed;inset:0;display:grid;place-items:center}.deck{position:relative;width:min(100vw,calc(100vh * 16 / 9));height:min(100vh,calc(100vw * 9 / 16));background:white;box-shadow:var(--shadow);overflow:hidden}
.slide{position:absolute;inset:0;display:none!important;background:var(--paper)}.slide.active{display:block!important}.inner{position:absolute;inset:0;padding:5.6% 6.4% 5.2%;display:flex;flex-direction:column}
header{flex:0 0 auto;margin-bottom:2.6%}.kicker{font-size:clamp(14px,1.45vw,23px);font-weight:700;letter-spacing:.08em;color:var(--accent);text-transform:uppercase;margin-bottom:.55em}
h1{font-size:clamp(32px,3.75vw,60px);line-height:1.13;letter-spacing:-.032em;margin:.1em 0 .35em}h2{font-size:clamp(27px,2.75vw,44px);line-height:1.17;letter-spacing:-.022em;margin:0;border-left:.15em solid var(--accent);padding-left:.42em}
p,li{font-size:clamp(18px,1.62vw,26px);line-height:1.48}ul{margin:.35em 0;padding-left:1.25em}li{margin:.38em 0}.sparse p,.sparse li{font-size:clamp(19px,1.78vw,28px)}.dense p,.dense li{font-size:clamp(16px,1.48vw,23px);line-height:1.42}.dense li{margin:.3em 0}strong{color:#0b6f69}.muted{color:var(--muted)}.tag{display:inline-block;padding:.18em .55em;border-radius:999px;background:var(--pale);color:#08776f;font-weight:700}
.title .inner{display:grid;grid-template-columns:1.2fr .8fr;gap:5%;align-items:center;background:linear-gradient(135deg,#fff 0 72%,#eff8f7 72%)}.title-block p,.section-block p{font-size:clamp(18px,1.85vw,30px);color:var(--muted)}.title figure{margin:0}.title figure img{max-height:58vh}
.section .inner{justify-content:center;background:linear-gradient(120deg,#fff 0 65%,#eef7f6 65%)}.section-block{max-width:70%}.section-block h2{font-size:clamp(38px,4.8vw,76px);border:0;padding:0}
.figure-layout{min-height:0;flex:1;display:grid;grid-template-columns:.78fr 1.52fr;gap:4%;align-items:center}.figure-layout .copy{align-self:start}.figure-layout figure{height:100%}
figure{min-width:0;min-height:0;margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center}figure img{max-width:100%;max-height:calc(100% - 2.4em);object-fit:contain;border-radius:7px;cursor:zoom-in;transition:transform .18s ease,box-shadow .18s ease}figure img:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(23,50,77,.16)}figcaption{font-size:clamp(11px,1.02vw,16px);line-height:1.3;color:var(--muted);margin-top:.6em;align-self:flex-start}
.split{display:grid;grid-template-columns:1fr 1fr;gap:3.2%;min-height:0;flex:1}.split>div{background:#f7fafb;border:1px solid var(--line);border-radius:16px;padding:4% 5%}.split h3{font-size:clamp(20px,2vw,32px);margin:.1em 0 .6em;color:var(--accent)}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(0,1fr));gap:2.2%;margin:2% 0 3%}.metric{background:var(--pale);border-top:5px solid var(--accent);border-radius:12px;padding:8% 6%;text-align:center}.metric b{display:block;font-size:clamp(30px,3.4vw,54px);line-height:1.05;color:#086e68}.metric span{display:block;margin-top:.6em;font-size:clamp(13px,1.25vw,20px);line-height:1.3;color:var(--muted)}
.wide-copy{min-height:0;flex:1}.wide-copy.columns{columns:2;column-gap:5%}.source{position:absolute;left:6.4%;right:10%;bottom:2.3%;font-size:clamp(10px,.9vw,14px);color:#71808e;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#progress{position:fixed;left:0;bottom:0;height:4px;background:var(--accent);transition:width .25s}.controls{position:fixed;right:14px;bottom:14px;display:flex;gap:8px}.controls button{width:38px;height:38px;border:1px solid #ccd7de;background:rgba(255,255,255,.9);border-radius:50%;color:var(--ink);font-size:18px;cursor:pointer}.counter{position:absolute;right:2.4%;bottom:2%;font-size:clamp(11px,.95vw,15px);color:#7d8a95}
.lightbox{position:fixed;inset:0;z-index:50;display:none;align-items:center;justify-content:center;padding:3vh 3vw;background:rgba(8,20,32,.9);backdrop-filter:blur(5px)}.lightbox.open{display:flex}.lightbox img{display:block;max-width:94vw;max-height:88vh;object-fit:contain;border-radius:8px;box-shadow:0 24px 90px rgba(0,0,0,.45)}.lightbox .zoom-caption{position:absolute;left:5vw;right:5vw;bottom:2vh;text-align:center;color:#eaf1f4;font-size:14px}.lightbox button{position:absolute;right:2vw;top:2vh;width:44px;height:44px;border:1px solid rgba(255,255,255,.5);border-radius:50%;background:rgba(0,0,0,.25);color:white;font-size:26px;cursor:pointer}
@media(max-aspect-ratio:4/3){.deck{box-shadow:none}.inner{padding:5%}.figure-layout{grid-template-columns:.9fr 1.1fr}.controls{opacity:.55}}
@media print{html,body{overflow:visible;background:white}.deck{width:100%;height:auto;box-shadow:none}.slide{position:relative;display:block!important;width:100vw;height:56.25vw;page-break-after:always}.controls,#progress,.lightbox{display:none!important}}
"""

JS = r"""
(()=>{const slides=[...document.querySelectorAll('.slide')],bar=document.querySelector('#progress'),box=document.querySelector('#lightbox'),zoom=document.querySelector('#zoomed'),zoomCaption=document.querySelector('#zoom-caption');let i=0;function show(n){i=(n+slides.length)%slides.length;slides.forEach((s,j)=>s.classList.toggle('active',j===i));document.querySelector('.counter').textContent=`${i+1} / ${slides.length}`;bar.style.width=`${(i+1)/slides.length*100}%`;location.hash=`s${i+1}`}function next(){show(i+1)}function prev(){show(i-1)}function closeZoom(){box.classList.remove('open');box.setAttribute('aria-hidden','true');zoom.removeAttribute('src')}document.addEventListener('click',e=>{const image=e.target.closest?.('figure img');if(image){zoom.src=image.src;zoom.alt=image.alt;zoomCaption.textContent=image.closest('figure')?.querySelector('figcaption')?.textContent||image.alt;box.classList.add('open');box.setAttribute('aria-hidden','false')}else if(e.target===box||e.target.closest?.('#close-zoom'))closeZoom()});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&box.classList.contains('open')){closeZoom();return}if(box.classList.contains('open'))return;if(['ArrowRight','ArrowDown',' ','PageDown'].includes(e.key)){e.preventDefault();next()}if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();prev()}if(e.key==='Home')show(0);if(e.key==='End')show(slides.length-1);if(e.key.toLowerCase()==='f')document.documentElement.requestFullscreen?.()});document.querySelector('#next').onclick=next;document.querySelector('#prev').onclick=prev;document.querySelector('#full').onclick=()=>document.documentElement.requestFullscreen?.();const h=location.hash.match(/s(\d+)/);show(h?Number(h[1])-1:0)})();
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.manifest.read_text(encoding="utf-8"))
    base = args.manifest.parent
    slides = "".join(render_slide(s, base, i) for i, s in enumerate(spec["slides"]))
    title = html.escape(spec.get("title", "组会文献汇报"))
    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><div id="stage"><main class="deck">{slides}<div class="counter"></div></main></div><div id="progress"></div><div class="controls"><button id="prev" aria-label="上一页">‹</button><button id="next" aria-label="下一页">›</button><button id="full" aria-label="全屏">⛶</button></div><div id="lightbox" class="lightbox" role="dialog" aria-modal="true" aria-hidden="true" aria-label="图片放大查看"><button id="close-zoom" aria-label="关闭图片">×</button><img id="zoomed" alt=""><div id="zoom-caption" class="zoom-caption"></div></div><script>{JS}</script></body></html>'''
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding="utf-8")
    print(f"Wrote {args.output} ({len(spec['slides'])} slides)")


if __name__ == "__main__":
    main()
