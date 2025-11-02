import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *

path = dst_path / "data/unsafedata/DST_Prefab.json"
df = pd.read_json(path).sort_index(axis=1)
for column in tqdm(df.columns):
    pagedata = df[column].dropna()
    pagedata.loc["prefab"] = column
    pagedata = pagedata.sort_index().to_json()
    site.pages[f"Data:DST Prefab/{column}.json"].save(pagedata)
