"""The two plates the app draws the floor with, from the supplied artwork.

The art arrives 1535px wide; the grid wants 1536, which is 96 whole 16px cells. One duplicated
column at the right edge is the cheapest way there — resampling a crisp illustration to gain a
single pixel softens every line in it, and nothing downstream cares about that column: it is
the outer frame. Everything else is measured off the padded plate, so there is no old
coordinate for it to disagree with.

PLATE.png is lossless and is what measure.py and grid6.py read: both key on exact colours, and
webp moves them enough to punch holes in the middle of the room.
"""
import os
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__)); ART=os.path.dirname(HERE)
W,H=1536,1024

def pad(name):
    im=Image.open(os.path.join(ART,name)).convert('RGB')
    if im.size==(W,H): return im
    assert im.size==(W-1,H),('unexpected art size',im.size)
    out=Image.new('RGB',(W,H)); out.paste(im,(0,0))
    out.paste(im.crop((W-2,0,W-1,H)),(W-1,0))
    return out

lit=pad('OfficeLightOn.png'); dark=pad('OfficeLightOff.png')
lit.save(os.path.join(HERE,'PLATE.png'))
# The lights-off plate is kept losslessly too, because it is what the walk grid is keyed off.
# Under daylight the desks and the floor are the same warm tan — near enough identical to the
# pixel — and no colour rule can tell a desk from the ground it stands on. With the lights out
# the floor goes dark and the wood stays lit, and they separate cleanly.
dark.save(os.path.join(HERE,'DARK.png'))
lit.save(os.path.join(ART,'office.webp'),'WEBP',quality=88,method=6)
dark.save(os.path.join(ART,'office-dark.webp'),'WEBP',quality=88,method=6)
for f in ('office.webp','office-dark.webp'):
    print(f'{f:18}',os.path.getsize(os.path.join(ART,f))//1024,'KB')
