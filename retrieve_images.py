'''Processes the article xml to retrieve images
'''

import os
import os.path

import re
import urllib.request
import urllib.error

import pandas as pd

from tqdm import tqdm
tqdm.pandas()

df_meta_figs = pd.read_csv("papers_retrieve_imgs.csv")

re_supp = re.compile('fig(?P<main>\d+).*?s(?P<supp>\d+)')
def _retrieve_image(articleid, fig, ver, fpath, max_d=1000):
    img_fn = '{article}-{fig}-{ver}.default.jpg'
    img_fn = img_fn.format(article=articleid, fig=fig, ver=ver)

    # don't redownload files
    if os.path.isfile(img_fn):
        return

    # the url for figure supplements is different
    # 'fig3s1' --> 'fig3-figsupp1'
    if 's' in fig:
        m = re_supp.match(fig)
        try:
            fig = 'fig{}-figsupp{}'.format(m.group('main'), m.group('supp'))
        except:
            with open("errors.txt", 'a') as fh:
                print("Parsing issue:", '', img_fn, file=fh)
            return

    url = 'https://iiif.elifesciences.org/lax:{article}/elife-{article}-{fig}-{ver}.tif/full/!{x},{y}/0/default.jpg'
    url = url.format(article=articleid, fig=fig, ver=ver, x=max_d, y=max_d)

    try:
        urllib.request.urlretrieve(url, os.path.join(fpath, img_fn))
    except urllib.error.HTTPError:
        with open("errors.txt", 'a') as fh:
            print("Malformed URL:", url, img_fn, file=fh)
    return

def retrieve_image(row, **kwargs):
    return _retrieve_image(row['articleid'], row['rid'], row['ver'], **kwargs)

img_path = 'elife-article-img'
os.makedirs(img_path, exist_ok=True)

# now we are ready to retrieve images
df_meta_figs.progress_apply(retrieve_image, axis=1, fpath=img_path)

