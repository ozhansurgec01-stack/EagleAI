"""Strict local SI calculations; unsupported wording falls through."""
import math
import re


def bilim_hesapla(mesaj):
    s = str(mesaj or '').lower().replace('\u0307', '').translate(str.maketrans('çğıöşü', 'cgiosu'))
    s = re.sub(r'\s+', ' ', s).strip().rstrip('?.!')
    n = r'([+-]?\d{1,9}(?:[.,]\d{1,9})?)'
    u = r'(mm|cm|m|km)'
    s = re.sub(r'\b(milimetre|santimetre|kilometre|metre)(?:dir|dur)?\b', lambda m: {'milimetre':'mm','santimetre':'cm','kilometre':'km','metre':'m'}[m[1]], s)
    scales = {'mm': .001, 'cm': .01, 'm': 1, 'km': 1000}
    def fmt(v):
        return format(v, '.12g').replace('.', ',')
    def val(x):
        return float(x.replace(',', '.'))
    m = re.fullmatch(rf'{n}\s*{u} kac {u}(?:dir|dur)?', s)
    if m:
        x, a, b = m.groups()
        return f'{fmt(val(x))} {a} = {fmt(val(x)*scales[a]/scales[b])} {b}.'
    for shape, pattern, formula, fn, power in (
        ('Daire', rf'yaricapi {n}\s*{u} olan dairenin (alani|cevresi)(?: kac(?:tir)?)?', '', None, 0),
        ('Kare', rf'kenari {n}\s*{u} olan karenin (alani|cevresi)(?: kac(?:tir)?)?', '', None, 0),
        ('Küp', rf'kenari {n}\s*{u} olan kupun (hacmi)(?: kac(?:tir)?)?', '', None, 0),
    ):
        m = re.fullmatch(pattern, s)
        if not m:
            continue
        x, unit, goal = m.groups(); x = val(x)
        if x <= 0:
            return 'Uzunluk sıfırdan büyük olmalıdır.'
        if shape == 'Daire':
            formula, result, power = ('π × r²', math.pi*x*x, 2) if goal == 'alani' else ('2 × π × r', 2*math.pi*x, 1)
        elif shape == 'Kare':
            formula, result, power = ('a²', x*x, 2) if goal == 'alani' else ('4 × a', 4*x, 1)
        else:
            formula, result, power = 'a³', x**3, 3
        return f'{shape}: {formula} = {fmt(result)} {unit}{ {1:"",2:"²",3:"³"}[power] }.'
    m = re.fullmatch(rf'kenarlari {n}\s*{u}?\s+ve {n}\s*{u} olan dikdortgenin (alani|cevresi)(?: kac(?:tir)?)?', s)
    if m:
        a, ua, b, ub, goal = m.groups(); a, b = val(a)*scales[ua or ub], val(b)*scales[ub]
        if min(a,b) <= 0:
            return 'Uzunluklar sıfırdan büyük olmalıdır.'
        return f'Alan = a × b = {fmt(a*b)} m².' if goal == 'alani' else f'Çevre = 2 × (a + b) = {fmt(2*(a+b))} m.'
    m = re.fullmatch(rf'kutlesi {n}\s*kg (?:ve )?ivmesi {n}\s*m/s(?:²|\^2|2) olan cismin (?:net )?kuvveti(?: kac(?:tir)?)?', s)
    if m:
        mass, acc = map(val, m.groups())
        if mass <= 0:
            return 'Kütle sıfırdan büyük olmalıdır.'
        return f'Newton yasası: F = m × a = {fmt(mass)} × {fmt(acc)} = {fmt(mass*acc)} N (seçilen eksende).'
    return None
