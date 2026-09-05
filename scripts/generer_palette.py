#!/usr/bin/env python3
"""Genere la palette (OKLCH -> hex) optimisee pour fond sombre.

Luminosite/chroma cales dans la bande sombre validee (L 0.48-0.67, C>=0.1),
teintes regroupees par famille, clarte en zigzag pour separer les voisins.
Valide avec le script dataviz validate_palette.js (--mode dark).
Colle les hex produits dans config/categories.json.
"""
import math,json
def oklch_to_hex(L,C,H):
    h=math.radians(H); a=C*math.cos(h); b=C*math.sin(h)
    l_=L+0.3963377774*a+0.2158037573*b; m_=L-0.1055613458*a-0.0638541728*b; s_=L-0.0894841775*a-1.2914855480*b
    l=l_**3; m=m_**3; s=s_**3
    r=4.0767416621*l-3.3077115913*m+0.2309699292*s; g=-1.2684380046*l+2.6097574011*m-0.3413193965*s; bb=-0.0041960863*l-0.7034186147*m+1.7076147010*s
    def enc(c):
        c=max(0.0,min(1.0,c)); c=12.92*c if c<=0.0031308 else 1.055*c**(1/2.4)-0.055; return round(max(0,min(1,c))*255)
    return "#%02x%02x%02x"%(enc(r),enc(g),enc(bb))
C=0.135
# (id, hue, L) — L en zigzag (0.66 / 0.54) pour separer les voisins en clarte
rows=[
 ("religieux",305,0.66),("cotier",212,0.54),("riverain",250,0.66),("germanique_heim",150,0.60),
 ("germanique_ange",120,0.66),("germanique_dorf",88,0.54),("franc_court",268,0.60),("villa_ville",330,0.54),
 ("galloromain_gnac",28,0.54),("galloromain_ac",50,0.66),("occitan_argues",350,0.60),("galloromain_ieu",72,0.62),
 ("galloromain_y",40,0.60),("galloromain_an",8,0.66),("savoyard_alpin",285,0.66),("norrois_eur",178,0.54),
 ("suffixe_uit",318,0.66),("suffixe_ou",100,0.60),("bourg",62,0.66),("mont",50,0.54),
 ("val",190,0.66),("mesnil",135,0.54),("complement_les",96,0.66),("complement_en",342,0.66),
]
out={i:oklch_to_hex(L,C,h) for i,h,L in rows}
print(",".join(out[i] for i,_,_ in rows))
print(json.dumps(out))
