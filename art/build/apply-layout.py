"""Put the freshly built office-layout.json into index.html's `const L=` line.

Kept as its own step so the grid can be rebuilt and re-checked without touching the app, and
so the swap is a single asserted edit rather than a hand-pasted 19 KB line.
"""
import json, os
HERE=os.path.dirname(os.path.abspath(__file__))
APP=os.path.join(os.path.dirname(os.path.dirname(HERE)),'index.html')
d=json.load(open(os.path.join(HERE,'office-layout.json'),encoding='utf-8'))
mini=json.dumps(d,separators=(',',':'))
open(os.path.join(HERE,'office-layout.min.json'),'w',encoding='utf-8').write(mini)
s=open(APP,encoding='utf-8').read()
i=s.index('const L={"w":'); j=s.index('\n',i)
before=s[i:j]
s=s[:i]+'const L='+mini+';'+s[j:]
open(APP,'w',encoding='utf-8').write(s)
print('layout swapped:',len(before),'->',len(mini)+9,'chars;  app',round(len(s)/1024),'KB')
