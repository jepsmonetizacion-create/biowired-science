import random, subprocess
import os
OUT=os.path.dirname(os.path.abspath(__file__))
BG1,BG2="#0E3A44","#061A20"
G="#3DFFA0"

MARK=f'''
<g fill="none" stroke="{G}" stroke-width="20" stroke-linecap="round" stroke-linejoin="round">
  <path d="M170,400 H285 L322,325 L362,505 L402,245 L442,475 L468,400 H525"/>
  <path d="M525,400 L575,345 H628"/>
  <path d="M525,400 H640"/>
  <path d="M525,400 L575,455 H618"/>
</g>
<g fill="{BG2}" stroke="{G}" stroke-width="12">
  <circle cx="152" cy="400" r="18"/>
  <circle cx="646" cy="345" r="18"/>
  <circle cx="658" cy="400" r="18"/>
  <circle cx="636" cy="455" r="18"/>
</g>'''

DEFS=f'''
<defs>
  <radialGradient id="bg" cx="50%" cy="45%" r="75%">
    <stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/>
  </radialGradient>
  <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="14" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>'''

logo=f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
{DEFS}
<rect width="800" height="800" fill="url(#bg)"/>
<circle cx="400" cy="400" r="318" fill="none" stroke="{G}" stroke-opacity="0.18" stroke-width="4"/>
<g filter="url(#glow)" transform="translate(-5,0)">{MARK}</g>
</svg>'''
open(f"{OUT}/logo.svg","w").write(logo)

# banner
random.seed(7)
W,H=2560,1440
traces=[]
def trace(x,y):
    pts=[(x,y)]
    d=random.choice([1,-1])
    for _ in range(random.randint(2,4)):
        L=random.randint(90,260)
        kind=random.choice(["h","d","h"])
        if kind=="h": x+=d*L
        else:
            s=random.choice([1,-1]); x+=d*L*0.6; y+=s*L*0.6
        pts.append((x,y))
    p="M"+" L".join(f"{a:.0f},{b:.0f}" for a,b in pts)
    ex,ey=pts[-1]
    return f'<path d="{p}"/><circle cx="{ex:.0f}" cy="{ey:.0f}" r="9" fill="{G}" stroke="none"/><circle cx="{pts[0][0]:.0f}" cy="{pts[0][1]:.0f}" r="6" fill="{G}" stroke="none"/>'
n=0
while n<46:
    x=random.randint(60,W-60); y=random.randint(60,H-60)
    t=trace(x,y)
    import re
    pts=[(float(a),float(b)) for a,b in re.findall(r'(-?\d+),(-?\d+)',t.split('"/>')[0])]
    if any(330<a<2230 and 430<b<1010 for a,b in pts): continue   # keep safe area clean
    traces.append(t); n+=1
deco=f'<g fill="none" stroke="{G}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity="0.16">{"".join(traces)}</g>'

s=0.62; cx,cy=745,722
banner=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
{DEFS}
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{deco}
<g filter="url(#glow)" transform="translate({cx-400*s:.0f},{cy-400*s:.0f}) scale({s})">{MARK}</g>
<text x="985" y="712" font-family="Inter Display" font-weight="800" font-size="150" fill="#FFFFFF" letter-spacing="2">BIOWIRED</text>
<text x="991" y="800" font-family="Inter Display" font-weight="500" font-size="72" fill="{G}" letter-spacing="34">SCIENCE</text>
<text x="991" y="884" font-family="Inter" font-weight="400" font-size="42" fill="#B9D4D8">The science and tech behind your everyday health</text>
</svg>'''
open(f"{OUT}/banner.svg","w").write(banner)
for n in ("logo","banner"):
    subprocess.run(["rsvg-convert",f"{OUT}/{n}.svg","-o",f"{OUT}/biowired-{n}.png"],check=True)
