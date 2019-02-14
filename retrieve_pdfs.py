'''Processes the article xml to retrieve pdfs
'''

import os
import os.path

import urllib.request
import urllib.error

import pandas as pd

from tqdm import tqdm
tqdm.pandas()

df_meta_figs = pd.read_csv("papers_to_scan.csv")

def _retrieve(articleid, ver, fpath):
    fn = 'elife-{article:05d}-{ver}.pdf'.format(article=articleid, ver=ver)
    url = 'https://cdn.elifesciences.org/articles/{article:05d}/elife-{article:05d}-{ver}.pdf'
    url = url.format(article=articleid, ver=ver)

    try:
        urllib.request.urlretrieve(url, os.path.join(fpath, fn))
    except urllib.error.HTTPError:
        with open("errors_pdf.txt", 'a') as fh:
            print("Malformed URL:", url, fn, file=fh)
    return

def retrieve(row, **kwargs):
    return _retrieve(row['articleid'], row['ver'], **kwargs)

out_path = 'elife-article-pdf'
os.makedirs(out_path, exist_ok=True)

# now we are ready to retrieve images
df_meta_figs.progress_apply(retrieve, axis=1, fpath=out_path)

