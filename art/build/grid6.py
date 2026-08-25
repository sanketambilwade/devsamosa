"""Rebuild the walk grid from the finished plate.

The old rule marked a cell walkable when >=55% of its pixels were floor, so every cell that
straddled a desk, monitor, chair, stool, counter or sofa passed and characters walked over the
furniture. A cell is now walkable only when *every* pixel in it is floor, with the floor's
decorative motifs closed over first so they don't punch holes in the middle of the room.
"""
from PIL import Image, ImageFilter
from collections import deque
import os, json

HOME=os.environ['USERPROFILE']; HERE=os.path.dirname(os.path.abspath(__file__))
im=Image.open(os.path.join(HERE,'PLATE.png')).convert('RGB')
W,H=im.size; px=im.load()
CELL=int(os.environ.get('CELL','16')); GW,GH=W//CELL,H//CELL

def floorpx(p):
    r,g,b=p
    return 55<r<145 and 95<g<165 and 85<b<150 and g>r+12 and g>b-4

mask=Image.new('L',(W,H),0); mp=mask.load()
for y in range(H):
    for x in range(W):
        if floorpx(px[x,y]): mp[x,y]=255
# Painted-on floor and floor coverings are ground, not furniture: the MEETING ROOM plaque
# blocked the strip below the near-side chairs, and the lounge rug walled the sofa off. Applied
# before the close so the rug's speckled texture fills in — but the coffee table on it does not.
def rugpx(c):
    r,g,b=c
    return 140<r<210 and 105<g<180 and 55<b<135 and r>b+45
FLOORDECAL=[((540,288,735,326),None),((1246,536,1440,668),rugpx)]
for (l,t,r,bt),test in FLOORDECAL:
    for y in range(t,bt):
        for x in range(l,r):
            if test is None or test(px[x,y]): mp[x,y]=255
# close the floor motifs (small non-floor specks inside the room) without swallowing furniture
closed=mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
cp=closed.load()
# Painted-on floor signs are ground, not furniture. Without this the MEETING ROOM plaque blocks
# the strip below the near-side chairs, and those seats end up with no walkable cell next to them.

grid=[[0]*GW for _ in range(GH)]
for gy in range(GH):
    for gx in range(GW):
        ok=True
        for y in range(gy*CELL,(gy+1)*CELL):
            for x in range(gx*CELL,(gx+1)*CELL):
                if not cp[x,y]: ok=False; break
            if not ok: break
        grid[gy][gx]=1 if ok else 0
print('all-floor cells:',sum(map(sum,grid)))

# chairs are stamped on top of the plate by plate5.py, which hands over where they landed
CH=json.load(open(os.path.join(HERE,'chairs.json')))
chairrects=[tuple(r) for r in CH['chairrects']]; seatpos=[tuple(s) for s in CH['seatpos']]
blocked=0
for (l,t,r,b) in chairrects:
    for gy in range(max(0,t//CELL),min(GH,(b//CELL)+1)):
        for gx in range(max(0,l//CELL),min(GW,(r//CELL)+1)):
            cl,ct=gx*CELL,gy*CELL
            ov=max(0,min(r,cl+CELL)-max(l,cl))*max(0,min(b,ct+CELL)-max(t,ct))
            if ov>0 and grid[gy][gx]: grid[gy][gx]=0; blocked+=1
print('cells blocked by chair geometry:',blocked)

# keep one connected region so every destination is reachable
comp=[[-1]*GW for _ in range(GH)]; n=0; size={}
for sy in range(GH):
    for sx in range(GW):
        if grid[sy][sx] and comp[sy][sx]<0:
            q=deque([(sx,sy)]); comp[sy][sx]=n; c=0
            while q:
                x,y=q.popleft(); c+=1
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny=x+dx,y+dy
                    if 0<=nx<GW and 0<=ny<GH and grid[ny][nx] and comp[ny][nx]<0:
                        comp[ny][nx]=n; q.append((nx,ny))
            size[n]=c; n+=1
main=max(size,key=size.get); stray=0
for y in range(GH):
    for x in range(GW):
        if grid[y][x] and comp[y][x]!=main: grid[y][x]=0; stray+=1
print(f'regions {n}, sizes {sorted(size.values(),reverse=True)[:6]}; dropped {stray} strays')

def walk(x,y): return 0<=x<GW and 0<=y<GH and grid[y][x]==1
def approach(ax,ay,maxr=10):
    cx,cy=int(ax)//CELL,int(ay)//CELL; best=None      # spot centres are floats
    for r in range(0,maxr+1):
        for dy in range(-r,r+1):
            for dx in range(-r,r+1):
                if max(abs(dx),abs(dy))!=r: continue
                x,y=cx+dx,cy+dy
                if walk(x,y):
                    d=dx*dx+dy*dy
                    if best is None or d<best[0]: best=(d,x,y)
        if best: return best[1],best[2]
    return cx,cy

DEST={'pantryTable':(1310,240),'pantryCounter':(1200,180),'coffee':(1215,700),
      'vending':(1320,712),'sofa':(1345,505),'server':(1150,400),
      'entry':(1240,940),'cooler':(1085,130),'meeting':(400,208)}
# Standing spots around the meeting table, taken from the grid itself. The old list was chair
# centres, which are not walkable — one of them resolved to floor outside the room, so that
# person stood in the corridor under the MEETING ROOM sign. These hug the table, are always on
# the floor, and are spaced so nobody overlaps.
ROOM=(340,118,955,332); TCX,TCY=630,225

# A sprite is 128x192 drawn 52.1px wide with its feet at the anchor; only the middle 80x176 of
# it is opaque. This is the footprint two people must not share.
SPW,SPH=52.1,78.1
def sbox(x,y,pad=3):
    return (x-16.3-pad, y-71.7-pad, x+16.3+pad, y-0.6+pad)
def hits(a,b):
    return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]
CLAIMED=[]      # every standing spot handed out, so no two places can share one

# The 12 chairs around the table, measured off the art. y is where the feet go: at a chair on
# the far side that is the table's top edge, at a near-side chair it is down by the castors.
TABLETOP=179        # the meeting table's own top edge; the far row's legs disappear under it
MEETCHAIRS=[(515,205),(570,205),(628,205),(685,205),(740,205),          # far side, facing down
            (515,267),(570,267),(628,267),(685,267),(740,267),          # near side, facing up
            (462,229),(794,230)]     # the two ends, seen side-on: high enough that the seat
                                     # and castors show under the occupant instead of a shoe
                                     # crossing the wheelbase
# Measured off the plate, not eyeballed: the first pass had them all a few pixels left of the
# real chairs, so the redrawn backrest sat beside its occupant instead of round them.
MEETNEAR=[(497,240,534,284),(552,240,589,284),(610,240,647,284),
          (667,240,704,284),(722,240,759,284)]
def standSpots(taken,limit=12):
    cand=[]
    for gy in range(ROOM[1]//CELL,ROOM[3]//CELL+1):
        for gx in range(ROOM[0]//CELL,ROOM[2]//CELL+1):
            if not walk(gx,gy): continue
            cx,cy=gx*CELL+CELL/2,gy*CELL+CELL/2
            cand.append(((cx-TCX)**2+((cy-TCY)*1.4)**2,cx,cy))
    cand.sort(); out=[]
    for _,cx,cy in cand:
        b=sbox(cx,cy)
        if any(hits(b,t) for t in taken): continue
        taken.append(b); out.append((int(cx),int(cy)))
        if len(out)>=limit: break
    return out
taken=CLAIMED
def seatbox(i,pad=3):
    x,y=MEETCHAIRS[i]; b=list(sbox(x,y,pad))
    # the far row is drawn from behind the table and cut off at its edge, so the half of them
    # that overlaps the near row is never on screen and must not count as a collision
    if i<5: b[3]=min(b[3],TABLETOP)
    return tuple(b)
for i in range(len(MEETCHAIRS)): taken.append(seatbox(i))
for i in range(len(MEETCHAIRS)):
    for j in range(i+1,len(MEETCHAIRS)):
        assert not hits(seatbox(i,0),seatbox(j,0)), ('chairs overlap',MEETCHAIRS[i],MEETCHAIRS[j])
MEET=MEETCHAIRS+standSpots(taken)
MEETFACE=(['front']*5)+(['back']*5)+['right','left']
print('meeting places:',len(MEETCHAIRS),'chairs +',len(MEET)-len(MEETCHAIRS),'standing')
data={'w':W,'h':H,'cell':CELL,'gw':GW,'gh':GH,
      'grid':''.join(''.join(str(c) for c in r) for r in grid),
      'seats':[],'dest':{},'meetSeats':[]}
far=[]
def facing(x,y,tx,ty):
    """which way somebody standing at (x,y) is turned to look at (tx,ty)"""
    dx,dy=tx-x,ty-y
    if abs(dx)>abs(dy)*1.2: return 'right' if dx>0 else 'left'
    return 'front' if dy>0 else 'back'
def entry(x,y,key=None,face='front',sit=0,look=None):
    ax,ay=approach(x,y)
    d=max(abs(ax*CELL+CELL/2-x),abs(ay*CELL+CELL/2-y))
    if d>56 and key: far.append((key,str(round(d))+'px'))
    if look: face=facing(x,y,look[0],look[1])
    return {'x':round(x/W,5),'y':round(y/H,5),'ax':ax,'ay':ay,'f':face,'st':sit}
for i,(sx,sy) in enumerate(seatpos):
    e=entry(sx,sy,'seat%d'%i,face='front' if i==0 else 'back',sit=1)
    e['i']=i
    # trim the legs that would otherwise hang below the chair we draw in front of them
    e['clip']=round(max(0,sy+3.1-chairrects[i][3])/78.1,4)
    # and put the name plate under the chair rather than behind it. The plate is a child of the
    # sprite, so it cannot be lifted out of its stacking context to sit above the chair — it has
    # to be moved clear instead. Percent of the sprite box, which is why it goes past 100.
    if i: e['tag']=round((chairrects[i][3]+5-(sy-74.98))/78.1*100,1)
    e['fixed']=1 if i==0 else 0          # the manager desk belongs to one person, or to nobody
    data['seats'].append(e)
# Everyone heading for the coffee machine used to stand on the exact same pixel, so 5 people
# rendered as 1. Each destination now owns a few spaced-out standing spots on real floor.
def spotsNear(x,y,n=10,maxr=16):
    # spaced by the sprite's own footprint, not by a cell count: two spots three cells apart
    # vertically still overlap, because a sprite is more than four cells tall
    cx,cy=x//CELL,y//CELL; cand=[]
    for gy in range(max(0,cy-maxr),min(GH,cy+maxr+1)):
        for gx in range(max(0,cx-maxr),min(GW,cx+maxr+1)):
            if not walk(gx,gy): continue
            px,py=gx*CELL+CELL/2,gy*CELL+CELL/2
            cand.append(((px-x)**2+((py-y)*1.4)**2,px,py,gx,gy))
    cand.sort(); out=[]
    for _,px,py,gx,gy in cand:
        b=sbox(px,py,4)
        if any(hits(b,t) for t in CLAIMED): continue
        CLAIMED.append(b); out.append((px,py,gx,gy))
        if len(out)>=n: break
    return out
for k,(x,y) in DEST.items():
    e=entry(x,y,k)
    e['spots']=[dict(entry(px,py,look=(x,y)),ax=gx,ay=gy) for px,py,gx,gy in spotsNear(x,y)]
    data['dest'][k]=e
print('standing spots per destination:',{k:len(v['spots']) for k,v in data['dest'].items()})
for j,(x,y) in enumerate(MEET):
    if j<len(MEETFACE): e=entry(x,y,'meet%d'%j,face=MEETFACE[j],sit=1)
    else:               e=entry(x,y,'meet%d'%j,look=(TCX,TCY))
    # The far five are drawn from behind the table, so trim them at its edge — otherwise they
    # read as standing behind it rather than sitting at it. Same mechanism as a desk chair
    # cropping the feet; doing it with an overlay instead would bury their name plates, which
    # are children of the sprite and cannot escape its stacking context.
    if j<5:
        e['clip']=round((y+3.1-TABLETOP)/78.1,4)
        e['tag']=round((TABLETOP+3-(y-74.98))/78.1*100,1)
    if 5<=j<10:
        e['tag']=round((MEETNEAR[j-5][3]+5-(y-74.98))/78.1*100,1)
    data['meetSeats'].append(e)
# The sofa seats three, on the cushions. Same handling as a desk chair: the anchor is the
# furniture, and the walk stops at the floor beside it.
SOFA=[(1304,549),(1347,549),(1390,549)]
data['sofaSeats']=[entry(x,y,'sofa%d'%k,face='front',sit=1) for k,(x,y) in enumerate(SOFA)]
for x,y in SOFA: CLAIMED.append(sbox(x,y))

# Places to stand around and talk. Seeded in the open floor, the empty meeting room and by the
# coffee counter and pantry — never in the aisle right at someone's desk.
HUDSEEDS=[(300,556),(700,556),(1000,556),(500,748),(900,748),(300,940),(700,940),(950,940),
          (250,372),(860,372),(560,300),(430,250),(1150,660),(1300,300)]
huddles=[]
for (hx,hy) in HUDSEEDS:
    spots=spotsNear(hx,hy,3,5)
    if len(spots)<2: continue
    cx=sum(q[0] for q in spots)/len(spots); cy=sum(q[1] for q in spots)/len(spots)
    huddles.append([dict(entry(px,py,look=(cx,cy)),ax=gx,ay=gy) for px,py,gx,gy in spots])
data['huddles']=huddles
print('conversation spots:',len(huddles),'groups of',[len(h) for h in huddles])

# Chairs that have to be drawn OVER the person in them. Only where the occupant has their back
# to us: then the backrest is between them and the camera. Somebody facing the room — the
# manager at his own desk, the far side of the meeting table — sits in front of their chair, so
# those are left alone. 'clip' is how much of the top to leave behind them.
# 'clip' is how much of the chair's top to leave behind the person. Zero: the whole chair goes
# in front, backrest included, which is what you would see from above of somebody sitting with
# their back to you. Partial values were tried (.33 / .45 / .62) and read as the chair standing
# beside its occupant rather than round them.
CLIP=0.0
def cut(l,t,r,b,clip=CLIP):
    return {'x':round(l/W,5),'y':round(t/H,5),'w':round((r-l)/W,5),'h':round((b-t)/H,5),
            'clip':clip}
data['frontChairs']=[cut(*rc) for i,rc in enumerate(chairrects) if i>0]+\
                    [cut(*rc) for rc in MEETNEAR]
data['screens']=[{'x':round(r[0]/W,5),'y':round(r[1]/H,5),
                  'w':round((r[2]-r[0])/W,5),'h':round((r[3]-r[1])/H,5)} if r else None
                 for r in CH['screens']]
print('desk screens:',sum(1 for r in data['screens'] if r))
print('anchors whose nearest walkable cell is far:',far or 'none')
json.dump(data,open(os.path.join(HERE,'office-layout.json'),'w'),indent=1)
print('walkable',sum(map(sum,grid)),'of',GW*GH,'— wrote office-layout.json')
