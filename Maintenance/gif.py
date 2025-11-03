import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *

threshold = 12500000

res = []
for img in tqdm(list(site.allimages())):
    if not img.name.lower().endswith('.gif'):
        continue
    imageinfo = img.imageinfo
    for metadata in imageinfo['metadata']:
        if metadata['name'] == 'frameCount':
            size = imageinfo['width'] * imageinfo['height'] * metadata['value']
            if size > threshold:
                res.append(img.name)
with open("Maintenance/gif.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=4)