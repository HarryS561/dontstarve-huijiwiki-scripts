# 先运行 Skins/update_skins.py，再运行此脚本

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *
from convert import convert

BUILDS_ZIP_PATH = dst_path / "data/databundles/anim_dynamic.zip"
TEX_PATH = dst_path / "data/anim/dynamic"
ANIM_PATH = dst_path / "data/anim/accountitem_frame.zip"

skin_names = []
for address in ['Item', 'Player', 'Other']:
    pagedata = json.loads(site.pages[f"Data:DST Skins {address}.tabx"].text())
    fields = pagedata['schema']['fields']
    for i, field in enumerate(fields):
        if field['name'] == 'huijiwiki_icon':
            icon_idx = i
        elif field['name'] == 'blacklist':
            blacklist_idx = i
    icons = [line[icon_idx]
             for line in pagedata['data'] if line[blacklist_idx] == 'n/a']
    for icon in tqdm(icons):
        if not site.pages[icon].exists:
            skin_names.append(icon.replace(
                'File:', '').replace('_icon.png', ''))

print(skin_names)

with ZipFile(BUILDS_ZIP_PATH, 'r') as builds_zip:
    builds_zip.extractall('builds')

for skin_name in tqdm(skin_names):
    with ZipFile('temp.zip', 'w') as temp_zip:
        with ZipFile(ANIM_PATH, 'r') as anim_zip:
            temp_zip.writestr('anim.bin', anim_zip.read('anim.bin'))

        build_path = f'builds/anim/dynamic/{skin_name}.zip'
        if not os.path.exists(build_path):
            build_path = f'builds/anim/{skin_name}.zip'
        with ZipFile(build_path, 'r') as build_zip:
            temp_zip.writestr('build.bin', build_zip.read('build.bin'))

        tex_dyn_path = f'{TEX_PATH}/{skin_name}.dyn'
        tex_zip_path = f'{TEX_PATH}/{skin_name}.zip'
        if not os.path.exists(tex_dyn_path):
            tex_zip_path = f'/data/anim/{skin_name}.zip'
        else:
            convert(tex_dyn_path)
        with ZipFile(tex_zip_path, 'r') as tex_zip:
            for tex_file in tex_zip.namelist():
                if 'atlas' in tex_file:
                    temp_zip.writestr(tex_file, tex_zip.read(tex_file))
    convert('temp.zip')
    os.remove('temp.zip')
    os.remove(f'{TEX_PATH}/{skin_name}.zip')
    site.upload(f'{skin_name}/swap_icon/swap_icon-0.png',
                f"{skin_name}_icon.png", '[[分类:皮肤]]', True)
    shutil.rmtree(skin_name)

shutil.rmtree('builds')
