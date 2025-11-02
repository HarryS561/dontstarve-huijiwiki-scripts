import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *

def pic_to_file():
    for page in tqdm(get_pages(template="Pic")):
        text = page.text()
        wikicode = parse(text)
        changed = False
        for template in wikicode.filter_templates():
            if template.name.matches("Pic"):
                p1 = get_param(template, 1)
                p2 = get_param(template, 2)
                p3 = get_param(template, 3)
                rep = f"[[File:{p2}.png|{p1}px|link={p3}]]"
                wikicode.replace(template, rep)
                changed = True
        if changed:
            newtext = str(wikicode)
            page.save(newtext, summary='不再依赖pic')

def item_pic_to_pic():
    for page in tqdm(get_pages(template="Item/pic")):
        text = page.text()
        text = re.sub(r"{{[Ii]tem/pic", "{{Pic|32", text)
        page.save(text, summary='Item/pic改为Pic')

item_pic_to_pic()