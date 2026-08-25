from PIL import Image
from collections import deque
import os
HOME=os.environ['USERPROFILE']; HERE=os.path.dirname(os.path.abspath(__file__))
im=Image.open(os.path.join(HOME,'Downloads','DevOfficeFinal.png')).convert('RGB')
px=im.load()

# generous box around the middle bottom-row meeting chair; y starts below the table edge
L,T,R,B=608,241,654,288
w,h=R-L,B-T
crop=im.crop((L,T,R,B)); cp=crop.load()

def bg(p):
    """floor green (incl. the chair's shadow) and the table's wood edge.
    Maroon body, dark outline and grey castors all fail both tests, so the chair survives."""
    r,g,b=p
    green = 40<r<150 and 80<g<175 and 70<b<160 and g>r+8 and g>b-8
    wood  = r>75 and r>g+25 and g>b+15 and b<115
    return green or wood

# flood fill background inward from the border so the chair blob is whatever is left
mask=[[False]*w for _ in range(h)]   # True = background
q=deque()
for x in range(w):
    for y in (0,h-1):
        if bg(cp[x,y]) and not mask[y][x]: mask[y][x]=True; q.append((x,y))
for y in range(h):
    for x in (0,w-1):
        if bg(cp[x,y]) and not mask[y][x]: mask[y][x]=True; q.append((x,y))
while q:
    x,y=q.popleft()
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx,ny=x+dx,y+dy
        if 0<=nx<w and 0<=ny<h and not mask[ny][nx] and bg(cp[nx,ny]):
            mask[ny][nx]=True; q.append((nx,ny))

out=Image.new('RGBA',(w,h),(0,0,0,0)); op=out.load()
for y in range(h):
    for x in range(w):
        if not mask[y][x]:
            r,g,b=cp[x,y]; op[x,y]=(r,g,b,255)
# The table's dark edge line survives the colour key and is contiguous with the chair,
# so a run-fill won't separate it. The chair body is a rectangle, so measure its width
# on a row well clear of the table and clamp the top rows to that.
ref=22
xs=[x for x in range(w) if op[x,ref][3]]
bl,br=min(xs),max(xs)
for y in range(0,14):
    for x in range(w):
        if x<bl or x>br: op[x,y]=(0,0,0,0)
print(f'body columns {bl}..{br} (measured at row {ref})')

bb=out.getbbox()
out=out.crop(bb)
print('chair bbox in crop:',bb,'-> size',out.size)
out.save(os.path.join(HERE,'chair.png'))

# preview on a checkerboard so alpha is visible
cw,ch=out.size; sc=9
chk=Image.new('RGB',(cw*sc,ch*sc))
for y in range(ch*sc):
    for x in range(cw*sc):
        chk.putpixel((x,y),(70,70,70) if ((x//18)+(y//18))%2 else (110,110,110))
chk.paste(out.resize((cw*sc,ch*sc),Image.NEAREST),(0,0),out.resize((cw*sc,ch*sc),Image.NEAREST))
chk.save(os.path.join(HERE,'chair-preview.png'))
print('saved chair.png and chair-preview.png')

# ---------------------------------------------------------------------------------------------
# The same chair the other way round, for the one desk whose occupant faces the room.
#
# There is no second chair sprite in the artwork to cut out — the meeting room's far row is this
# same chair, and everything below its backrest is hidden behind the table. What differs from
# above is only the vertical structure: seen from behind you get the backrest filling the block
# with the castors under it, seen from in front you get the backrest as a band at the top and
# then the seat. So take that structure row by row — the median of the far chair's own interior
# columns, the trick the desks are rebuilt with in plate5.py — and lay it over this sprite's
# body. Silhouette, outline and castors stay exactly as they are.
import statistics
FAR=(499,146,534,178)          # one far-side meeting chair, measured off the artwork
front=out.copy(); fp=front.load()
w2,h2=front.size
BODY=slice(2,w2-2)             # interior, so the dark outline columns are left alone
for i in range(FAR[3]-FAR[1]):
    row=[px[x,FAR[1]+i] for x in range(FAR[0]+3,FAR[2]-3)]
    med=tuple(int(statistics.median([c[k] for c in row])) for k in range(3))
    for x in range(BODY.start,BODY.stop):
        if fp[x,i][3]>128: fp[x,i]=med+(255,)
front.save(os.path.join(HERE,'chair-front.png'))
print('saved chair-front.png (rows 0..%d rebuilt from the far meeting chair)'%(FAR[3]-FAR[1]-1))
