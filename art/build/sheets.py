"""Pack each character's thirteen sprites into the one sheet the app draws them from.

Thirteen files each is 221 requests; as one 4x6 sheet per character it is 17, and they compress
better sharing a palette. The grid, left to right and top to bottom:

    row 0  walk front (4 frames)      row 3  walk right (4)
    row 1  walk back  (4)             row 4  idle: front, back, left, right
    row 2  walk left  (4)             row 5  sit:  front, back, left, right

which is what `.ofc-spr` in index.html indexes with --cx and --cy.

The order comes from the source manifest and must not be sorted or otherwise tidied: a board
stores which character somebody uses as a number into these sheets, so reordering them silently
gives eighteen people someone else's face. It is also the reason the sheets ship numbered and
their source does not ship at all — the source is one file per developer, named after them, and
this repository is public.
"""
import os, json
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__)); ART=os.path.dirname(HERE)
SRC=os.path.join(ART,'CharacterSprites')
FULL=os.path.join(SRC,'full')
if not os.path.isdir(FULL):
    raise SystemExit('character source not found at '+FULL+
                     ' — it is gitignored, see the README')

W,H,COLS,ROWS=128,192,4,6
WALK=['-walk4','-back-walk4','-walk4-left','-walk4-right']
IDLE=['','-back','-left','-right']
SIT =['-sit-front','-sit-back','-sit-left','-sit-right']

names=list(json.load(open(os.path.join(SRC,'_chars.json'),encoding='utf-8')))
def grab(n,suf,want):
    p=os.path.join(FULL,n+suf+'.png')
    if not os.path.exists(p): raise SystemExit('missing '+os.path.basename(p))
    im=Image.open(p).convert('RGBA')
    assert im.size==want,(os.path.basename(p),im.size,'expected',want)
    return im

tot=0
for i,n in enumerate(names):
    sheet=Image.new('RGBA',(W*COLS,H*ROWS),(0,0,0,0))
    for r,suf in enumerate(WALK): sheet.paste(grab(n,suf,(W*4,H)),(0,r*H))
    for c,suf in enumerate(IDLE): sheet.paste(grab(n,suf,(W,H)),(c*W,4*H))
    for c,suf in enumerate(SIT):  sheet.paste(grab(n,suf,(W,H)),(c*W,5*H))
    f=os.path.join(ART,'c%02d.png'%i)
    sheet.save(f,optimize=True); tot+=os.path.getsize(f)
print(f'{len(names)} sheets of {W*COLS}x{H*ROWS}, {round(tot/1024)} KB in total')
