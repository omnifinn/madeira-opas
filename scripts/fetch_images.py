#!/usr/bin/env python3
"""Lataa kuvat Wikimediasta/Wikipediasta jokaiselle Madeira-paikalle."""
import json, urllib.request, urllib.parse, ssl, os, sys

OUT = os.path.join(os.path.dirname(__file__), '..', 'images')
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)
ctx = ssl.create_default_context()

# (id, hakusana(t) priorisoidussa järjestyksessä)
PLACES = [
    ('funchal-old',    ['Funchal', 'Zona Velha Funchal', 'Funchal Cathedral']),
    ('monte-palace',   ['Monte Palace Tropical Garden', 'Monte Madeira']),
    ('pico-arieiro',   ['Pico do Arieiro', 'Pico Areeiro Madeira']),
    ('pico-ruivo',     ['Pico Ruivo', 'Pico Ruivo Madeira']),
    ('porto-moniz',    ['Porto Moniz', 'Porto Moniz natural pools']),
    ('seixal',         ['Seixal Madeira', 'Praia da Laje Seixal']),
    ('veu-da-noiva',   ['Véu da Noiva Madeira', 'Bridal Veil Madeira waterfall']),
    ('fanal',          ['Fanal Madeira', 'Fanal forest Madeira', 'Laurissilva Madeira']),
    ('25-fontes',      ['Levada das 25 Fontes', '25 Fontes Madeira Rabacal']),
    ('santana',        ['Santana Madeira', 'Casas de Santana']),
    ('rocha-navio',    ['Rocha do Navio', 'Teleférico Rocha do Navio']),
    ('aguage',         ['Cascata Aguage Madeira', 'Aguage waterfall Faial']),
    ('sao-vicente',    ['São Vicente Madeira', 'Grutas São Vicente']),
    ('boaventura',     ['Boaventura Madeira', 'Boaventura São Vicente']),
    ('ponta-do-sol',   ['Ponta do Sol Madeira', 'Ponta do Sol']),
    ('cascata-anjos',  ['Cascata dos Anjos Madeira', 'Anjos Madeira waterfall']),
    ('lombinho',       ['Ribeira da Janela Madeira', 'Porto Moniz coast', 'Cascata Lombinho']),
    ('risco',          ['Cascata do Risco', 'Risco waterfall Madeira', 'Rabacal Madeira']),
    ('dolphins',       ['Atlantic spotted dolphin Madeira', 'Whale watching Madeira', 'Funchal harbour']),
    ('doca-cavacas',   ['Doca do Cavacas', 'Madeira natural pool']),
    ('praia-formosa',  ['Praia Formosa Funchal', 'Praia Formosa Madeira']),
]

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={'User-Agent': 'MadeiraGuide/1.0 (niko@konsensus.network)'})
    return urllib.request.urlopen(req, timeout=timeout, context=ctx).read()

def wp_summary(title):
    """Wikipedia REST API summary -> originalimage."""
    for lang in ('en', 'pt', 'fi'):
        try:
            url = f'https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title.replace(" ", "_"))}'
            data = json.loads(fetch(url, 8))
            if 'originalimage' in data:
                return data['originalimage']['source']
            if 'thumbnail' in data:
                return data['thumbnail']['source']
        except Exception:
            continue
    return None

def commons_search(query):
    """Wikimedia Commons search for first photo file."""
    try:
        api = ('https://commons.wikimedia.org/w/api.php?'
               'action=query&format=json&generator=search&gsrnamespace=6'
               f'&gsrsearch={urllib.parse.quote(query)}&gsrlimit=8'
               '&prop=imageinfo&iiprop=url|mime&iiurlwidth=1200')
        data = json.loads(fetch(api, 12))
        pages = data.get('query', {}).get('pages', {}).values()
        for p in pages:
            for info in p.get('imageinfo', []):
                mime = info.get('mime', '')
                url = info.get('thumburl') or info.get('url')
                title = p.get('title', '').lower()
                if not url: continue
                if 'svg' in mime: continue
                if any(skip in title for skip in ['.svg', 'logo', 'flag', 'coa', 'crest', 'icon', 'symbol']): continue
                return url
    except Exception as e:
        print(f'  commons err: {e}', file=sys.stderr)
    return None

def get_image(queries):
    for q in queries:
        url = wp_summary(q)
        if url: return ('wp', q, url)
    for q in queries:
        url = commons_search(q)
        if url: return ('commons', q, url)
    return (None, None, None)

results = {}
for pid, queries in PLACES:
    try:
        src, q, url = get_image(queries)
        if not url:
            print(f'MISS  {pid}', flush=True)
            results[pid] = None
            continue
        ext = 'jpg'
        ul = url.lower()
        if ul.endswith('.png') or '.png' in ul: ext = 'png'
        elif ul.endswith('.jpeg') or '.jpeg' in ul: ext = 'jpg'
        out = f'{OUT}/{pid}.{ext}'
        data = fetch(url, 25)
        with open(out, 'wb') as f:
            f.write(data)
        kb = len(data) // 1024
        print(f'OK    {pid:18s}  {src:8s}  {kb:>4}KB  ({q})', flush=True)
        results[pid] = ext
    except Exception as e:
        print(f'ERR   {pid}: {e}', flush=True)
        results[pid] = None

with open(f'{OUT}/_index.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f'\nDone: {sum(1 for v in results.values() if v)}/{len(PLACES)}')
