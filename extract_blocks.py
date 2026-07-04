#!/usr/bin/env python3
"""Parse hand-coded page content into typed section blocks (JSON) for Sveltia CMS editing."""
import re, json, html, os

U = html.unescape

def chunks(content):
    """Split content region into top-level section/band chunks."""
    pat = re.compile(r'(<section\b.*?</section>|<div class="band[^"]*"><img[^>]*/></div>|<div class="band[^"]*".*?\n</div>)', re.S)
    return [m.group(1) for m in pat.finditer(content)]

def parse_band(c):
    img = re.search(r'<img src="([^"]+)" alt="([^"]*)"(?: style="object-position:([^"]+)")? ?/>', c)
    cap = re.search(r'<div class="q">(.*?)</div><div class="src">(.*?)</div>', c, re.S)
    return {"type": "band",
            "image": "/" + img.group(1), "alt": U(img.group(2)),
            "tall": 'band-tall' in c,
            "position": img.group(3) or "",
            "quote": U(cap.group(1)) if cap else "",
            "source": U(cap.group(2)) if cap else ""}

def paras(block):
    return [U(p) for p in re.findall(r'<p>(.*?)</p>', block, re.S)]

def parse_text_photo(c):
    fig = re.search(r'<figure class="portrait-card reveal" style="margin:0"><img src="([^"]+)" alt="([^"]*)" /></figure>', c)
    side = 'left' if c.index('<figure') < c.index('<div class="bodytext') else 'right'
    body = re.search(r'<div class="bodytext reveal">(.*?)</div>\s*(?:<figure|</div>\s*</div></section>)', c, re.S)
    bt = body.group(1)
    # offers inside bodytext (weddings)
    offers = [{"heading": U(h), "text": U(t)} for h, t in re.findall(r'<div class="o"><h4>(.*?)</h4><p>(.*?)</p></div>', bt, re.S)]
    cta = re.search(r'<div class="cta-row reveal"><a class="btn btn-gilt" href="([^"]+)">(.*?)</a></div>', bt)
    bt_clean = re.sub(r'<div class="offer".*$', '', bt, flags=re.S)
    return {"type": "text_photo",
            "paragraphs": [{"text": p} for p in paras(bt_clean)],
            "image": "/" + fig.group(1), "alt": U(fig.group(2)), "image_side": side,
            "offers": offers,
            "cta_label": U(cta.group(2)) if cta else "", "cta_link": cta.group(1) if cta else ""}

def parse_text_appointments(c):
    body = re.search(r'<div class="bodytext reveal">(.*?)</div>\s*<div class="reveal">', c, re.S)
    posts = [{"role": U(r), "place": U(p), "location": U(l)} for r, p, l in
             re.findall(r'<div class="post"><div><div class="p-role">(.*?)</div><div class="p-place">(.*?)</div></div><div class="p-loc">(.*?)</div></div>', c, re.S)]
    return {"type": "text_appointments",
            "paragraphs": [{"text": p} for p in paras(body.group(1))],
            "posts": posts}

def parse_text_studio(c):
    body = re.search(r'<div class="bodytext reveal">(.*?)</div>\s*<div class="studio reveal">', c, re.S)
    st = re.search(r'<div class="studio reveal">(.*?)</div>\s*</div>\s*</div></section>', c, re.S).group(1)
    label = U(re.search(r'<span class="lbl">(.*?)</span>', st).group(1))
    h3 = U(re.search(r'<h3>(.*?)</h3>', st).group(1))
    sp = U(re.search(r'<p>(.*?)</p>', st).group(1))
    instr = [{"icon": "/" + i, "label": U(l)} for i, l in re.findall(r'<div class="instr-card"><img src="([^"]+)" alt="[^"]*" /><span>(.*?)</span></div>', st)]
    cta = re.search(r'<a class="btn btn-gilt" href="([^"]+)">(.*?)</a>', st)
    return {"type": "text_studio",
            "paragraphs": [{"text": p} for p in paras(body.group(1))],
            "studio_label": label, "studio_heading": h3, "studio_text": sp,
            "instruments": instr,
            "cta_label": U(cta.group(2)), "cta_link": cta.group(1)}

def parse_scholarship(c):
    latin = re.search(r'<blockquote class="euch-q">(.*?)<span>(.*?)</span></blockquote>', c, re.S)
    sub = U(re.search(r'<p class="euch-sub">(.*?)</p>', c, re.S).group(1))
    label = U(re.search(r'<span class="lbl">(.*?)</span>', c).group(1))
    deg = U(re.search(r'<div class="deg">(.*?)</div>', c).group(1))
    title = U(re.search(r'<h2>(.*?)</h2>', c).group(1))
    dsub = U(re.search(r'<p class="sub">(.*?)</p>', c).group(1))
    meta = [{"role": U(k), "name": U(v)} for k, v in re.findall(r'<span>(.*?) &nbsp;<b>(.*?)</b></span>', c)]
    return {"type": "scholarship", "latin": U(latin.group(1)), "translation": U(latin.group(2)),
            "text": sub, "label": label, "degree": deg, "title": title, "subtitle": dsub, "meta": meta}

def parse_patrons(c):
    label = U(re.search(r'<div class="patron-label">(.*?)</div>', c).group(1))
    ps = [{"image": "/" + i, "alt": U(a), "name": U(n), "description": U(d), "latin": U(q), "translation": U(t)}
          for i, a, n, d, q, t in re.findall(
            r'<figure class="patron-fig"><img src="([^"]+)" alt="([^"]*)" /></figure>\s*<div class="patron-name">(.*?)</div>\s*<div class="patron-desc">(.*?)</div>\s*<blockquote class="patron-q">(.*?)<span>(.*?)</span></blockquote>', c, re.S)]
    return {"type": "patrons", "label": label, "patrons": ps}

def parse_stage_work(c):
    label = U(re.search(r'<span class="lbl">(.*?)</span>', c).group(1))
    roles = [{"role": U(r), "work": U(w), "company": U(co)} for r, w, co in
             re.findall(r'<tr><td class="role">(.*?)</td><td class="work">(.*?)</td><td class="co">(.*?)</td></tr>', c)]
    sc = re.search(r'<div class="scenes"><b>(.*?)</b>(.*?)</div>', c, re.S)
    photos = [{"image": "/" + i, "alt": U(a), "caption": U(cp)} for i, a, cp in
              re.findall(r'<figure class="figcap" style="margin:0"><img src="([^"]+)" alt="([^"]*)" /><figcaption>(.*?)</figcaption></figure>', c, re.S)]
    cols = []
    for colm in re.finditer(r'<div><h3>(.*?)</h3>(.*?)</div>\s*(?=<div><h3>|</div>\s*</div></section>)', c, re.S):
        heading, cbody = colm.group(1), colm.group(2)
        entries = []
        for e in re.finditer(r'<div class="cs-entry">(?:<span class="tag">(.*?)</span>)?<div class="t">(.*?)</div><div class="d">(.*?)</div></div>', cbody, re.S):
            entries.append({"tag": U(e.group(1)) if e.group(1) else "", "title": U(e.group(2)), "detail": U(e.group(3))})
        fig = re.search(r'<figure class="recital-fig reveal"><img src="([^"]+)" alt="([^"]*)" /></figure>', cbody)
        cols.append({"heading": U(heading), "entries": entries,
                     "photo": "/" + fig.group(1) if fig else "", "photo_alt": U(fig.group(2)) if fig else ""})
    return {"type": "stage_work", "label": label, "roles": roles,
            "scenes_heading": U(sc.group(1)), "scenes_text": U(sc.group(2)), "photos": photos, "columns": cols}

def parse_recordings(c):
    label = U(re.search(r'<span class="lbl">(.*?)</span>', c).group(1))
    intro = U(re.search(r'<p class="rec-intro reveal">(.*?)</p>', c, re.S).group(1))
    rels = []
    for r in re.finditer(r'<article class="rel-card reveal">(.*?)</article>', c, re.S):
        rc = r.group(1)
        g = lambda p: U(re.search(p, rc, re.S).group(1))
        cover = re.search(r'<img class="rel-cover" src="([^"]+)" alt="([^"]*)"', rc)
        links = [{"label": U(l), "url": u} for u, l in re.findall(r'<a class="rel-btn" href="([^"]+)"[^>]*>(.*?)</a>', rc)]
        rels.append({"cover": "/" + cover.group(1), "cover_alt": U(cover.group(2)),
                     "tag": g(r'<div class="rel-tag">(.*?)</div>'), "title": g(r'<h3 class="rel-title">(.*?)</h3>'),
                     "credit": g(r'<div class="rel-credit">(.*?)</div>'), "role": g(r'<div class="rel-role">(.*?)</div>'),
                     "note": g(r'<div class="rel-note">(.*?)</div>'), "links": links})
    return {"type": "recordings", "label": label, "intro": intro, "releases": rels}

def parse_videos(c):
    labels = re.findall(r'<span class="lbl">(.*?)</span>', c)
    feat = re.search(r'<div class="feature-film">.*?<iframe src="([^"]+)" title="([^"]*)".*?<div class="tag">(.*?)</div><h3>(.*?)</h3>\s*<p>(.*?)</p>\s*<a class="btn btn-ghost" href="([^"]+)"[^>]*>(.*?)</a>', c, re.S)
    def vitems(g):
        items = []
        for m in re.finditer(r'<div class="vcard reveal">.*?<div class="vc">.*?</div></div>', g, re.S):
            v = m.group(0)
            yt = re.search(r'data-yt="([^"]+)"', v)
            ext = re.search(r'<a class="vframe vlink" href="([^"]+)"[^>]*aria-label="([^"]*)"><span class="vlink-label">(.*?)</span>', v)
            t = U(re.search(r'<div class="vt">(.*?)</div>', v, re.S).group(1))
            cr = U(re.search(r'<div class="vc">(.*?)</div>', v, re.S).group(1))
            items.append({"youtube_id": yt.group(1) if yt else "",
                          "external_url": ext.group(1) if ext else "", "external_label": U(ext.group(3)) if ext else "",
                          "title": t, "credit": cr})
        return items
    grids = re.findall(r'<div class="vgrid">(.*?)\n  </div>', c, re.S)
    return {"type": "videos", "label": U(labels[0]),
            "feature_embed": feat.group(1), "feature_tag": U(feat.group(3)), "feature_title": U(feat.group(4)),
            "feature_text": U(feat.group(5)), "feature_button_label": U(feat.group(7)), "feature_button_url": feat.group(6),
            "videos": vitems(grids[0]),
            "label2": U(labels[1]) if len(labels) > 1 else "",
            "videos2": vitems(grids[1]) if len(grids) > 1 else []}

def parse_affiliations(c):
    label = U(re.search(r'<span class="lbl">(.*?)</span>', c).group(1))
    def logos(side_html):
        out = []
        for m in re.finditer(r'<(a|span) class="lg([^"]*)"(?: href="([^"]+)")?[^>]*><img src="([^"]+)" alt="([^"]*)" /></(?:a|span)>', side_html):
            out.append({"extra_class": m.group(2).strip(), "url": m.group(3) or "", "image": "/" + m.group(4), "alt": U(m.group(5))})
        return out
    left = re.search(r'<div class="lw-side lw-left">(.*?)</div>', c, re.S).group(1)
    right = re.search(r'<div class="lw-side lw-right">(.*?)</div>', c, re.S).group(1)
    center = re.search(r'<span class="word word-lg">(.*?)</span></span>', c, re.S).group(1)
    return {"type": "affiliations", "label": label, "left": logos(left), "center": center, "right": logos(right)}

def classify(c):
    if '"pagehead"' in c: return 'pagehead'
    if 'class="band' in c and c.startswith('<div'): return parse_band(c)
    if 'id="contact"' in c or 'class="mailing"' in c: return None
    if '<table class="program"' in c: return parse_stage_work(c)
    if 'class="studio reveal"' in c: return parse_text_studio(c)
    if 'class="p-role"' in c: return parse_text_appointments(c)
    if 'portrait-card' in c: return parse_text_photo(c)
    if 'class="diss"' in c or 'euch-q' in c: return parse_scholarship(c)
    if 'patron-sec' in c: return parse_patrons(c)
    if 'class="recordings' in c: return parse_recordings(c)
    if 'id="watch"' in c: return parse_videos(c)
    if 'logowall' in c: return parse_affiliations(c)
    raise ValueError("unclassified chunk: " + c[:120])

os.makedirs('src/_data/pages', exist_ok=True)
for page in ['about', 'performing', 'directing', 'teaching', 'weddings']:
    content = open(f'/tmp/content_{page}.html').read()
    cs = chunks(content)
    head = None
    sections = []
    for c in cs:
        r = classify(c)
        if r == 'pagehead':
            kick = U(re.search(r'<div class="kick">(.*?)</div>', c).group(1))
            title = U(re.search(r'<h1>(.*?)</h1>', c).group(1))
            intro = U(re.search(r'<p>(.*?)</p>', c, re.S).group(1))
            head = {"kick": kick, "title": title, "intro": intro}
        elif r:
            sections.append(r)
    data = {"head": head, "sections": sections}
    json.dump(data, open(f'src/_data/pages/{page}.json', 'w'), indent=2, ensure_ascii=False)
    print(f"{page}: head + {len(sections)} sections: {[s['type'] for s in sections]}")
