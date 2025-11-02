import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *

'''
在你运行这个脚本之前，请先前往 https://steamdb.info/depot/322331/manifests/
登录后，在网页上右键另存为（Ctrl + S）至这个脚本所在目录，无需重命名
'''
with open('Depot 322331 (Don\'t Starve Together - Windows) · SteamDB.html', 'r', encoding='utf-8') as f:
    html_content = f.read()
soup = BeautifulSoup(html_content, 'html.parser')
manifests = []
for td in soup.find_all('td', class_='tabular-nums'):
    a = td.find('a')
    code = td.find('code')
    manifests.append((a.get_text(strip=True), code.get_text(
        strip=True) if code else 'public'))
for a in soup.find_all('a', href=True):
    if 'steamdb.info/patchnotes' in a['href'] and a.text.isdigit():
        public_branch_id = a.text

if os.path.exists('depots'):
    shutil.rmtree('depots')
if os.path.exists('pot'):
    shutil.rmtree('pot')

pagedata = json.loads(site.pages["Data:DST Updates.tabx"].text())
for i, field in enumerate(pagedata['schema']['fields']):
    if field['name'] == 'id':
        id_idx = i
    if field['name'] == 'ver':
        ver_idx = i
data = {line[id_idx]: line[ver_idx] for line in pagedata['data']}

with open("begin_manifest.txt", "r") as f:
    begin_manifest = f.read().strip()
begin = False

branch_to_id = {'public': public_branch_id, 'updatebeta': 0}  # 开测试服的时候不为0，需要手动修改
for manifest, branch in tqdm(manifests[::-1]):
    if manifest == begin_manifest:
        begin = True
        continue
    if not begin:
        continue
    if os.path.exists(f"pot/{manifest}"):
        continue
    cmd = f"""\
    DepotDownloader.exe \
    -username {steam_username} -password {steam_password} -remember-password \
    -use-lancache -filelist files.txt \
    -app 322330 -depot 322331 -manifest {manifest} -branch {branch}"""
    os.system(cmd)

    base_path = f'depots/322331/{branch_to_id[branch] if branch in branch_to_id else 0}/'

    while not os.path.exists(base_path + 'version.txt'):
        os.system(cmd)
    with open(base_path + 'version.txt') as f:
        ver = f.read().strip()

    if os.path.exists(base_path + 'data/databundles/scripts.zip'):
        with ZipFile(base_path + 'data/databundles/scripts.zip', 'r') as scripts:
            scripts.extract('scripts/languages/strings.pot')
        path = 'scripts/languages/strings.pot'
    elif os.path.exists(base_path + 'data/scripts/languages/strings.pot'):
        path = base_path + 'data/scripts/languages/strings.pot'
    else:
        raise FileNotFoundError(f"Not found strings.pot for ver {ver}")

    os.makedirs(f"pot/{manifest}")
    os.rename(path, f"pot/{manifest}/{ver}.pot")

    shutil.rmtree('depots')

with open("begin_manifest.txt", "w") as f:
    f.write(manifest)

if os.path.exists('scripts'):
    shutil.rmtree('scripts')

pots = []
for root, dirs, files in os.walk('pot'):
    for file in files:
        if file.endswith('.pot'):
            ver = file.replace('.pot', '')
            filepath = os.path.join(root, file)
            pots.append((ver, filepath))
pots.sort()

print(pots)

header = 'msgid ""\nmsgstr ""\n'
for ver, path in tqdm(pots):
    try:
        with open(path, 'r+', encoding='utf-8') as pot:
            line1 = pot.readline()
            line2 = pot.readline()
            if line1 + line2 != header:
                pot.seek(0)
                content = pot.read()
                pot.seek(0)
                pot.write(header + content)
        po = polib.pofile(path)
        for entry in po:
            msgctxt = entry.msgctxt.split(".")
            if msgctxt[1] == 'NAMES' and msgctxt[2].lower() not in data:
                data[msgctxt[2].lower()] = ver
    except UnicodeDecodeError as e:
        print(f"UnicodeDecodeError in file {path}")

# def find_unicode_errors(filename):
#     with open(filename, 'rb') as f:
#         for i, line in enumerate(f, 1):
#             try:
#                 line.decode('utf-8')
#             except UnicodeDecodeError as e:
#                 print(f"Error in line {i}:")
#                 print(f"Position: {e.start}-{e.end}")
#                 print(f"Offending bytes: {line[e.start:e.end]}")
#                 print(f"Full line: {line}")
# find_unicode_errors(r'pot\5065417483399777331\370368.pot')

data = sorted([[prefab, ver] for prefab, ver in data.items()])

def process_fields(indices: list):
    fields = []
    for idx in indices:
        fields.append({
            "name": idx,
            "type": "string",
            "title": {
                "en": idx,
                "zh": ""
            }
        })
    return fields


pagedata = json.dumps({
    'schema': {
        'fields': process_fields(['id', 'ver']),
    },
    'data': data,
}, indent=4, ensure_ascii=False)
site.pages[f"Data:DST Updates.tabx"].save(pagedata)
