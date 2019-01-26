"""Detects colormap from images
"""

import glob

import pandas as pd
from tqdm import tqdm
tqdm.pandas()

from joblib import Parallel, delayed

from jetfighter.detect_cmap import parse_img, \
        detect_rainbow_from_colors, convert_to_jab, find_cm_dists

def main():
    images = glob.glob("elife-article-img/*.jpg")
    raw = Parallel(n_jobs=40)(delayed(_detect_rainbow)(f) for f in tqdm(images))

    df_parsed = pd.concat(raw)
    df_parsed.reset_index(inplace=True)

    for c in ['articleid', 'rid', 'ver']:
        df_parsed[c] = None

    df_parsed[['articleid', 'rid', 'ver']] = (df_parsed['fn']
            .str.split('/', n=1).str[1]
            .str.split('.', n=1).str[0]
            .str.split('-', expand=True)
            )
    df_parsed['articleid'] = pd.to_numeric(df_parsed['articleid'])

    df_parsed.to_csv("images_screened.csv", index=False)
    return

def _detect_rainbow(fn, *args, **kwargs):
    try:
        return detect_rainbow(fn, *args, **kwargs)
    except:
        with open("errors_detect.txt", "a") as fh:
            print("Some error:", fn, file=fh)
            return pd.DataFrame()

def detect_rainbow(fn, debug=False):
    """Full paper processing code (from file to detection)
    """
    # Read image, find convert to jab, find distance to colormaps
    df = parse_img(fn)
    df = convert_to_jab(df)
    df_cmap = find_cm_dists(df)
    _, df_detect = detect_rainbow_from_colors(df_cmap)

    df_detect = df_detect.copy()
    df_detect['fn'] = fn
    return df_detect


if __name__ == '__main__':
    main()

