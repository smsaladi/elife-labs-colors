'''Processes the article xml to retrieve images
'''

import os
import os.path
import glob
import re
import urllib.request
import urllib.error

from bs4 import BeautifulSoup

import pandas as pd

from tqdm import tqdm
tqdm.pandas()

# the git repo should already be cloned into this directory
all_papers = glob.glob(os.path.join('elife-article-xml', 'articles', '*.xml'))

# munge file names for article id and versions
df_meta = pd.Series(all_papers, name='full_path').to_frame()
df_meta[['dir', 'fn']] = df_meta['full_path'].str.rsplit('/', n=1, expand=True)
df_meta[['elife', 'articleid', 'ver']] = df_meta['fn'].str.split('-', expand=True)
df_meta['ver'] = df_meta['ver'].str.replace('\.xml$', '')

# keep only the most recent version of articles
df_meta.sort_values(['articleid', 'ver'], inplace=True)
df_papers = df_meta.groupby(['articleid']).apply(lambda d: d.tail(1))

# write out papers to scan just for ease of analysis later
df_papers.to_csv('papers_to_scan.csv', index=False)

def parse_xml_for_figures(xml_fn):
    with open(xml_fn, 'r') as fh:
        doc = BeautifulSoup(fh, features='lxml')

    fig_refs = doc.find_all('xref', {'ref-type': 'fig'})
    fig_refs = [[f['rid'], f.string] for f in fig_refs]
    df_figs = pd.DataFrame(fig_refs, columns=['rid', 'content'])
    df_figs['xml_fn'] = xml_fn

    return df_figs

df_meta = df_meta

df_meta_figs = df_meta['full_path'].progress_apply(parse_xml_for_figures)
df_meta_figs = pd.concat(df_meta_figs.values)
df_meta_figs.to_csv('papers_all_img_refs.csv')

# munge rid field can have multiple figure references, each separated by a space
id_vars = df_meta_figs.drop(columns=['rid']).columns
df_rids = df_meta_figs['rid'].str.split(expand=True)
df_meta_figs = pd.concat([df_meta_figs[id_vars], df_rids], axis=1)

# now, 1 rid at a time with its associated string
df_meta_figs = df_meta_figs.melt(id_vars=id_vars, var_name='col', value_name='rid')
df_meta_figs.dropna(inplace=True)
# also remove muliple occurences of a single rid
df_meta_figs = df_meta_figs[['xml_fn', 'rid']].drop_duplicates()

# add back article metadata, write data to file
df_meta_figs = df_meta_figs.merge(df_meta[['full_path', 'articleid', 'ver']],
                                  left_on='xml_fn', right_on='full_path',
                                  validate='many_to_one')
df_meta_figs.to_csv('papers_retrieve_imgs.csv')

re_supp = re.compile('fig(?P<main>\d+).*?s(?P<supp>\d+)')
def _retrieve_image(articleid, fig, ver, fpath, max_d=1500):
    img_fn = '{article}-{fig}-{ver}.default.jpg'
    img_fn = img_fn.format(article=articleid, fig=fig, ver=ver)

    # the url for figure supplements is different
    # 'fig3s1' --> 'fig3-figsupp1'
    if 's' in fig:
        m = re_supp.match(fig)
        try:
            fig = '{main}-figsupp{supp}'.format(main=m.group('main'), supp=m.group('supp'))
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

