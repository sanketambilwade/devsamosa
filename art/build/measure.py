"""Find the furniture in the supplied artwork, so the app can put people on it.

plate5.py used to *build* the empty floor: strip the drawn-in people, rebuild each desk from its
own clean columns, stamp a chair at every desk. The artwork now arrives with the chairs already
on it and nobody sitting in them, so all of that is gone and this measures instead.

Measured, never eyeballed. The one time chair rectangles were typed in by eye they were ten
pixels off, and every backrest ended up drawn beside its occupant instead of round them.

Writes chairs.json for grid6.py: the chairs, where the feet of whoever sits in one go, and the
screens the typing animation is drawn into.
"""
import os, json, collections
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__))
im=Image.open(os.path.join(HERE,'PLATE.png')).convert('RGB')
W,H=im.size; px=im.load()

def lum(p): return (p[0]*299+p[1]*587+p[2]*114)//1000
def pink(p):
    r,g,b=p
    return r>195 and 115<g<225 and 115<b<225 and r>g+30 and abs(g-b)<34
def screenpx(p):
    r,g,b=p
    # A monitor is the one cool-toned thing standing on a warm desk. Not simply "near black":
    # the manager's is drawn switched on, a lit blue-grey, and keying on darkness alone left his
    # the only desk in the room whose screen never came up.
    return b>r+8 and lum(p)<168
INK=118                                    # the art outlines everything in near-black

def blobs(test,minarea):
    seen=set(); out=[]
    for y in range(H):
        for x in range(W):
            if (x,y) in seen or not test(px[x,y]): continue
            q=collections.deque([(x,y)]); seen.add((x,y)); cells=[]
            while q:
                cx,cy=q.popleft(); cells.append((cx,cy))
                for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny=cx+dx,cy+dy
                    if 0<=nx<W and 0<=ny<H and (nx,ny) not in seen and test(px[nx,ny]):
                        seen.add((nx,ny)); q.append((nx,ny))
            if len(cells)>=minarea:
                xs=[c[0] for c in cells]; ys=[c[1] for c in cells]
                out.append([min(xs),min(ys),max(xs)+1,max(ys)+1])
    return out

def grow(rc,side=6,down=22,up=4):
    """A cushion is only the middle of a chair: push the edges out to the outline round the seat
       and the castors under it. The sideways test stays inside the cushion's own rows and the
       downward test inside its own columns, or the desk's dark front edge — which runs the full
       width of the desk, well above the seat — swallows the chair whole. It did."""
    l,t,r,b=rc; t0,b0,l0,r0=t,b,l,r
    for _ in range(side):
        if l>0 and any(lum(px[l-1,y])<INK for y in range(t0,b0)): l-=1
        else: break
    for _ in range(side):
        if r<W and any(lum(px[r,y])<INK for y in range(t0,b0)): r+=1
        else: break
    for _ in range(up):
        if t>0 and any(lum(px[x,t-1])<INK for x in range(l0,r0)): t-=1
        else: break
    for _ in range(down):
        if b<H and any(lum(px[x,b])<INK for x in range(l0,r0)): b+=1
        else: break
    return [l,t,r,b]

cush=blobs(pink,350)
MEET=(430,120,840,320)
inmeet=lambda c:MEET[0]<=(c[0]+c[2])/2<=MEET[2] and MEET[1]<=(c[1]+c[3])/2<=MEET[3]
deskc=sorted([c for c in cush if not inmeet(c)],key=lambda c:(round(c[1]/60),c[0]))
meetc=sorted([c for c in cush if inmeet(c)],key=lambda c:(round(c[1]/45),c[0]))
print(f'cushions: {len(cush)} — {len(deskc)} at desks, {len(meetc)} in the meeting room')

# The manager's desk has a visitor chair on the far side as well as his own. Only the one with
# castors under it is a seat; the pair is told apart by which sits lower.
head=[c for c in deskc if c[1]<340]
if len(head)==2:
    visitor=min(head,key=lambda c:c[1]); deskc.remove(visitor)
    print('  visitor chair at the manager desk left as furniture:',tuple(visitor))

chairrects=[grow(c) for c in deskc]
# Feet go 21px below the top of the cushion: the offset that leaves a head, a collar and the
# shoulders clear of the backrest. Judged on a strip of four — at 27, which is what the old
# artwork wanted, these taller chairs reached the collar and every desk was a dark block on a
# bright desk; at 9 they float above the seat.
seatpos=[[(c[0]+c[2])//2, c[1]+21] for c in deskc]

# A monitor is the dark rectangle standing on the desk above its chair.
scr=[b for b in blobs(screenpx,420) if b[2]-b[0]>18 and b[3]-b[1]>14]
screens=[]
for (sx,sy) in seatpos:
    near=[b for b in scr if abs((b[0]+b[2])/2-sx)<70 and 40<sy-(b[1]+b[3])/2<135]
    near.sort(key=lambda b:abs((b[0]+b[2])/2-sx))
    screens.append(near[0] if near else None)
print('screens matched to a desk:',sum(1 for s in screens if s),'of',len(seatpos))

# ---- the meeting table ----
# Three kinds of chair round it and a different rule for each, so they are grouped by where they
# sit rather than by anything in the art: the far row is behind the table, the near row in front
# of it, and the two on the ends are drawn side on.
def wood(p):
    r,g,b=p
    return r>200 and r>g+35 and g>b+45 and b<150
tx=[];ty=[]
for y in range(150,300):
    for x in range(430,860):
        if wood(px[x,y]): tx.append(x); ty.append(y)
table=[min(tx),min(ty),max(tx)+1,max(ty)+1]
mid=(table[1]+table[3])/2
far =[c for c in meetc if (c[1]+c[3])/2<table[1]+6]
near=[c for c in meetc if (c[1]+c[3])/2>table[3]-6]
ends=[c for c in meetc if c not in far and c not in near]
far.sort(key=lambda c:c[0]); near.sort(key=lambda c:c[0]); ends.sort(key=lambda c:c[0])
print('table',tuple(table),' far',len(far),'near',len(near),'ends',len(ends))
meeting={'table':table,
         'far':[grow(c) for c in far], 'near':[grow(c) for c in near],
         'ends':[grow(c) for c in ends]}

json.dump({'chairrects':chairrects,'seatpos':seatpos,'screens':screens,
           'meeting':meeting,'visitor':head[0] if len(head)==2 else None},
          open(os.path.join(HERE,'chairs.json'),'w'),indent=1)
for i,(rc,sp,sc) in enumerate(zip(chairrects,seatpos,screens)):
    print(f'  {i:2} chair {tuple(rc)} w{rc[2]-rc[0]} h{rc[3]-rc[1]}  seat {tuple(sp)}  screen {tuple(sc) if sc else "-"}')
for k in ('far','near','ends'):
    print(k,':',[tuple(c) for c in meeting[k]])
