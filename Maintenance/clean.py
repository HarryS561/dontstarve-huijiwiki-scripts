import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *

patterns = [
    re.compile(r"^模块:DST Strings [0-9a-f]{2}$"),
    re.compile(r"^模块:DS Strings [0-9a-f]{2}$"),
]

for page in tqdm(list(site.allpages(namespace=828))):  # Module namespace
    title = page.name
    if any(p.match(title) for p in patterns):
        page.delete(reason="Cleanup old md5-bucketed Strings modules", watch=False)