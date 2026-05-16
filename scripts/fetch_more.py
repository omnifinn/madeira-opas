#!/usr/bin/env python3
"""Hae kuvat Aguagelle ja Cabo Girãolle (puuttuvat tai uudet)."""
import json, urllib.request, urllib.parse, ssl, os, sys

OUT = os.path.join(os.path.dirname(__file__), '..', 'images')
OUT = os.path.abspath(OUT)
ctx = ssl.create_default_context()

# Tarkemmat hakusanat
PLACES = [
    ('aguage',     ['Cascata Aguage', 'Aguage Faial Santana', 'Aguage waterfall Santana Madeira',
                    'Vereda Lamaceiros', 'Faial Madeira waterfall']),
    ('cabo-girao', ['Cabo Girão', 'Cabo Girao skywalk', 'Cabo Girao Madeira', 'Cabo Girão Câmara de Lobos']),
]

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={'User-Agent': 'MadeiraGuide/1.0 (niko@konsensus.network)'})
    return urllib.request.urlopen(req, timeout=timeout, context=ctx).read()

def wp_summary(title):
    for lang in ('en', 'pt', 'fi'):
        try:
            url = f'https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title.replace(" ", "_"))}'
            data = json.loads(fetch(url, 8))
            if 'originalimage' in data: return data['originalimage']['source']
            if 'thumbnail' in data: return data['thumbnail']['source']
        except Exception:
            continue
    return None

def commons_search(query, limit=12):
    try:
        api = ('https://commons.wikimedia.org/w/api.php?'
               'action=query&format=json&generator=search&gsrnamespace=6'
               f'&gsrsearch={urllib.parse.quote(query)}&gsrlimit={limit}'
               '&prop=imageinfo&iiprop=url|mime|extmetadata&iiurlwidth=1200')
        data = json.loads(fetch(api, 12))
        pages = data.get('query', {}).get('pages', {}).values()
        for p in pages:
            for info in p.get('imageinfo', []):
                mime = info.get('mime', '')
                url = info.get('thumburl') or info.get('url')
                title = p.get('title', '').lower()
                if not url: continue
                if 'svg' in mime: continue
                if any(skip in title for skip in ['.svg','logo','flag','coa','crest','icon','symbol','map']): continue
                print(f'    found: {title}', file=sys.stderr)
                return url
    except Exception as e:
        print(f'  commons err: {e}', file=sys.stderr)
    return None

for pid, queries in PLACES:
    found_url = None
    found_q = None
    for q in queries:
        url = wp_summary(q)
        if url:
            found_url, found_q = url, q
            print(f'  wp hit on "{q}"', file=sys.stderr)
            break
    if not found_url:
        for q in queries:
            url = commons_search(q)
            if url:
                found_url, found_q = url, q
                print(f'  commons hit on "{q}"', file=sys.stderr)
                break
    if not found_url:
        print(f'MISS  {pid}')
        continue
    ext = 'jpg'
    if '.png' in found_url.lower(): ext = 'png'
    out = f'{OUT}/{pid}.{ext}'
    try:
        data = fetch(found_url, 25)
        with open(out, 'wb') as f:
            f.write(data)
        kb = len(data) // 1024
        print(f'OK    {pid:14s}  {kb:>4}KB  ({found_q})')
    except Exception as e:
        print(f'ERR   {pid}: {e}')
