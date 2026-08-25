from PIL import Image, ImageDraw
from collections import deque
import os, json, statistics, shutil
HOME=os.environ['USERPROFILE']; HERE=os.path.dirname(os.path.abspath(__file__))
ART=os.path.dirname(HERE)          # art/ — what the app actually fetches
im=Image.open(os.path.join(HOME,'Downloads','DevOfficeFinal.png')).convert('RGB')
W,H=im.size; px=im.load()
out=im.copy(); op=out.load()

def floorpx(p):
    r,g,b=p
    return 55<r<145 and 95<g<165 and 85<b<150 and g>r+12 and g>b-4
def woody(p):
    r,g,b=p
    return 95<r<215 and 70<g<175 and 40<b<125 and r>g+18 and g>b+8
def purity(l,t,r,b,step=3):
    tot=hit=0
    for y in range(t,b,step):
        if y<0 or y>=H: return 0
        for x in range(l,r,step):
            if x<0 or x>=W: return 0
            tot+=1
            if floorpx(px[x,y]): hit+=1
    return hit/max(1,tot)
src=None
for t in range(340,1000,4):
    for l in range(40,1000,4):
        if purity(l,t,l+76,t+80)==1.0: src=(l,t); break
    if src: break
sl,st=src; PERX,PERY=136,16
def floorfill(l,t,r,b):
    ax=sl+((l-sl)%PERX); ay=st+((t-st)%PERY)
    if purity(ax,ay,ax+(r-l),ay+(b-t))<0.98: ax,ay=sl,st
    out.paste(im.crop((ax,ay,ax+(r-l),ay+(b-t))),(l,t))

PLATES=[(181,280)]+[(x,524) for x in (158,339,514,695,872)]+\
       [(x,714) for x in (119,280,445,604,770,925)]+\
       [(x,906) for x in (128,294,473,638,801,972)]

# ---- 1. seated devs: rebuild the desk rows, then floor below ----
for (sx,ly) in [(x,y) for x,y in PLATES[1:]]:
    sy=ly-46
    for y in range(sy-52, sy-12):
        cols=[px[x,y] for x in list(range(sx-58,sx-23))+list(range(sx+24,sx+59)) if 0<=x<W]
        if not cols: continue
        med=tuple(int(statistics.median([c[i] for c in cols])) for i in range(3))
        for x in range(sx-22, sx+23): op[x,y]=med
    floorfill(sx-38, sy-12, sx+38, sy+40)

# ---- 2. the suited manager ----
floorfill(148,130,208,208)
for y in range(208,220):
    wood=[px[x,y] for x in range(120,242) if woody(px[x,y])]
    if len(wood)<20: continue
    med=tuple(int(statistics.median([c[i] for c in wood])) for i in range(3))
    for x in range(150,206): op[x,y]=med

# ---- 3. baked-in DEV NN labels ----
for (lx,ly) in PLATES:
    floorfill(lx-45, ly-17, lx+45, ly+17)

# ---- 4. a meeting-room chair at every desk ----
chair=Image.open(os.path.join(HERE,'chair.png')).convert('RGBA')
# The manager is the one person who faces the room rather than a wall, so his chair is the one
# that has to be the other way round: backrest away from us, seat toward us. See chair.py.
chairF=Image.open(os.path.join(HERE,'chair-front.png')).convert('RGBA')
CW,CH=chair.size
seatpos=[]; chairrects=[]
MGRTOP=165          # DEV 01 sits on the FAR side: chair bottom meets his desk's top edge (y=207)
for i,(lx,ly) in enumerate(PLATES):
    ctop = MGRTOP if i==0 else ly-54
    cx = lx - CW//2
    ch = chairF if i==0 else chair
    out.paste(ch,(cx,ctop),ch)
    chairrects.append((cx,ctop,cx+CW,ctop+CH))
    # The app redraws the chair whole, in front of whoever is in it, so where they sit is
    # really the question of how much of them clears the backrest. +27 leaves the head, the
    # collar and the shoulders above it, which is what you see of someone at a desk from above;
    # at +47 the backrest reached their ears and every desk was a dark smudge on a chair.
    # The manager is the exception — he faces the room and his chair is behind him, so he keeps
    # the low seat that puts him at his own desk rather than up on it.
    seatpos.append((lx, ctop + (47 if i==0 else 27)))     # sprite is anchored at the feet
print('chairs stamped:',len(seatpos))
HANDOVER={'chairrects':chairrects,'seatpos':seatpos}

# ---- 5. DEV 01 gets a real workstation, and the meeting room gets a wall TV ----
# The monitor is lifted from a standard desk rather than drawn, so it is the same object the
# rest of the office uses. Flood-fill the floor and the desk wood away from the border inwards.
from collections import deque as _dq
def liftSprite(box, keep):
    l,t,r,b=box; w,h=r-l,b-t
    crop=im.crop(box); cp2=crop.load()
    bgm=[[False]*w for _ in range(h)]; q=_dq()
    for x in range(w):
        for y in (0,h-1):
            if not keep(cp2[x,y]) and not bgm[y][x]: bgm[y][x]=True; q.append((x,y))
    for y in range(h):
        for x in (0,w-1):
            if not keep(cp2[x,y]) and not bgm[y][x]: bgm[y][x]=True; q.append((x,y))
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<w and 0<=ny<h and not bgm[ny][nx] and not keep(cp2[nx,ny]):
                bgm[ny][nx]=True; q.append((nx,ny))
    spr=Image.new('RGBA',(w,h),(0,0,0,0)); sp=spr.load()
    for y in range(h):
        for x in range(w):
            if not bgm[y][x]:
                r0,g0,b0=cp2[x,y]; sp[x,y]=(r0,g0,b0,255)
    return spr.crop(spr.getbbox())

monitor=liftSprite((313,386,361,428), lambda c: not (floorpx(c) or woody(c)))
MW,MH=monitor.size
print('monitor sprite:',MW,'x',MH)

# clear DEV 01's desktop (printer, open book, folder) by rebuilding it from its own clean
# left-hand columns — the desk is uniform across, so one clean strip restores the whole surface
DESK=(122,205,236,262)
for y in range(DESK[1],DESK[3]):
    cols=[op[x,y] for x in range(124,133)]
    med=tuple(int(statistics.median([c[i] for c in cols])) for i in range(3))
    for x in range(133,235): op[x,y]=med

# He sits on the far side facing the room, so what you see of his monitor is its back. That is
# a supplied prop rather than the desk monitor flipped over.
OUTL=(34,30,28); BEZ=(169,171,181); DARK=(96,98,108)
d=ImageDraw.Draw(out)
pcb=Image.open(os.path.join(HOME,'Downloads','OFficeSpriteswithCharacters','sprites','props',
                            'pc-back.png')).convert('RGBA')
PW,PH=pcb.size
mx=DESK[0]+((DESK[2]-DESK[0])-PW)//2
my=DESK[3]-PH-8
out.paste(pcb,(mx,my),pcb)

# keyboard and mouse between him and the screen
kx,ky=DESK[0]+28,DESK[1]+6
d.rectangle([kx,ky,kx+43,ky+7],fill=BEZ,outline=OUTL)
for row in range(2):
    for k in range(10):
        d.point((kx+4+k*4,ky+2+row*3),fill=DARK)
d.rectangle([kx+51,ky,kx+57,ky+7],fill=BEZ,outline=OUTL)
d.line([(kx+54,ky+2),(kx+54,ky+4)],fill=DARK)

# wall TV in the meeting room, on the clear stretch between the window and the plant
TV=(700,56,772,102)
d.rectangle([TV[0]-1,TV[1]-1,TV[2]+1,TV[3]+1],fill=OUTL)
d.rectangle([TV[0],TV[1],TV[2],TV[3]],fill=DARK)
d.line([(TV[0],TV[1]),(TV[2],TV[1])],fill=BEZ)          # same silver catch-light as the monitors
d.line([(TV[0],TV[1]),(TV[0],TV[3])],fill=BEZ)
d.rectangle([TV[0]+3,TV[1]+3,TV[2]-3,TV[3]-4],fill=(34,9,24))
d.line([(TV[0]+8,TV[3]-9),(TV[2]-15,TV[1]+7)],fill=(96,74,96),width=3)
d.line([(TV[0]+18,TV[3]-9),(TV[2]-7,TV[1]+8)],fill=(74,54,74),width=2)
d.rectangle([TV[0]+30,TV[3]+2,TV[0]+42,TV[3]+5],fill=OUTL)
# clear the wall clock's baked-in hands; the app draws live ones over the face
CX,CY,CR=66,79.5,10
face=tuple(int(v) for v in im.getpixel((61,72)))
for y in range(int(CY-CR)-1,int(CY+CR)+2):
    for x in range(CX-CR-1,CX+CR+2):
        if (x-CX)**2+(y-CY)**2<=CR*CR: op[x,y]=face
print('workstation, TV and blank clock face drawn — face colour',face)

# Where each desk's screen is, so the app can light it up while its owner is sitting there.
# Found by colour rather than arithmetic: the screens are the only near-black-maroon regions
# on the floor, and this keeps working if a desk ever moves.
SCR=(34,9,24)
def screenish(c): return abs(c[0]-SCR[0])<26 and abs(c[1]-SCR[1])<26 and abs(c[2]-SCR[2])<26
np2=out.load(); seen=set(); rects=[]
for y0 in range(0,H,2):
    for x0 in range(0,W,2):
        if (x0,y0) in seen or not screenish(np2[x0,y0]): continue
        q=[(x0,y0)]; seen.add((x0,y0)); xs=[];ys=[]
        while q:
            x,y=q.pop(); xs.append(x); ys.append(y)
            for dx,dy in ((2,0),(-2,0),(0,2),(0,-2)):
                nx,ny=x+dx,y+dy
                if 0<=nx<W and 0<=ny<H and (nx,ny) not in seen and screenish(np2[nx,ny]):
                    seen.add((nx,ny)); q.append((nx,ny))
        if len(xs)<80: continue
        rects.append((min(xs),min(ys),max(xs),max(ys)))
# A desk's screen is the nearest dark region *above* it and roughly in line with it. Scoring
# by plain distance instead picked the desk behind for half the row: the desks are 160px apart
# across and only ~118px from label to monitor, so the neighbour scores about the same.
screens=[]
for (lx,ly) in PLATES:
    best=None
    for r in rects:
        cx,cy=(r[0]+r[2])/2,(r[1]+r[3])/2
        if abs(cx-lx)>45 or cy>=ly: continue
        if best is None or cy>best[0]: best=(cy,r)
    screens.append(list(best[1]) if best else None)
print('screens matched to desks:',sum(1 for s0 in screens if s0),'of',len(PLATES))
HANDOVER['screens']=screens
json.dump(HANDOVER,open(os.path.join(HERE,'chairs.json'),'w'),indent=1)

# PLATE.png is lossless on purpose: grid6.py keys walkable cells off exact floor colours,
# and webp's compression moves them enough to punch holes in the middle of the room.
out.save(os.path.join(HERE,'PLATE.png'))
out.save(os.path.join(ART,'office.webp'),'WEBP',quality=85,method=6)
print('webp KB:',os.path.getsize(os.path.join(ART,'office.webp'))//1024)

# ================= walk grid, re-derived from the finished plate =================
np=out.load(); CELL=32; GW,GH=W//CELL,H//CELL
grid=[]
for gy in range(GH):
    row=[]
    for gx in range(GW):
        hit=tot=0
        for y in range(gy*CELL+4,(gy+1)*CELL-3,4):
            for x in range(gx*CELL+4,(gx+1)*CELL-3,4):
                tot+=1
                if floorpx(np[x,y]): hit+=1
        row.append(1 if hit/tot>=0.55 else 0)
    grid.append(row)
# A chair can straddle a cell without covering enough of it to fail the colour test,
# so block by geometry too: any cell whose centre lands inside a chair is an obstacle.
chairblocked=0
for (l,t,r,b) in chairrects:
    for gy in range(max(0,t//CELL), min(GH,(b//CELL)+1)):
        for gx in range(max(0,l//CELL), min(GW,(r//CELL)+1)):
            cl,ct=gx*CELL,gy*CELL
            ov=max(0,min(r,cl+CELL)-max(l,cl))*max(0,min(b,ct+CELL)-max(t,ct))
            if ov/(CELL*CELL)>=0.35 and grid[gy][gx]:
                grid[gy][gx]=0; chairblocked+=1
print('cells blocked by chair geometry:',chairblocked)

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
main=max(size,key=size.get)
stray=0
for y in range(GH):
    for x in range(GW):
        if grid[y][x] and comp[y][x]!=main: grid[y][x]=0; stray+=1
print(f'walkable {sum(sum(r) for r in grid)} cells in one region; dropped {stray} strays')

def walk(x,y): return 0<=x<GW and 0<=y<GH and grid[y][x]==1
def approach(ax,ay,maxr=8):
    cx,cy=ax//CELL,ay//CELL; best=None
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
MEET=[(515,169),(570,169),(628,169),(685,169),(740,168),
      (466,207),(787,207),(629,260),(740,260)]
data={'w':W,'h':H,'cell':CELL,'gw':GW,'gh':GH,
      'grid':''.join(''.join(str(c) for c in r) for r in grid),
      'seats':[],'dest':{},'meetSeats':[]}
for i,(sx,sy) in enumerate(seatpos):
    ax,ay=approach(sx,sy)
    data['seats'].append({'i':i,'x':round(sx/W,5),'y':round(sy/H,5),'ax':ax,'ay':ay})
bad=[]
for k,(x,y) in DEST.items():
    ax,ay=approach(x,y)
    data['dest'][k]={'x':round(x/W,5),'y':round(y/H,5),'ax':ax,'ay':ay}
    if not walk(ax,ay): bad.append(k)
for (x,y) in MEET:
    ax,ay=approach(x,y)
    data['meetSeats'].append({'x':round(x/W,5),'y':round(y/H,5),'ax':ax,'ay':ay})
print('destinations with no walkable approach:',bad or 'none')
json.dump(data,open(os.path.join(HERE,'office-layout.json'),'w'),indent=1)
print('wrote office-layout.json')

box=(80,430,260,560); w=(box[2]-box[0])*4; h=(box[3]-box[1])*4
out.crop(box).resize((w,h),Image.NEAREST).save(os.path.join(HERE,'chair-placed.png'))
print('saved chair-placed.png')
