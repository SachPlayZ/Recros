"""Download public book ratings and song listening events; no models or audio."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'ml/data/raw/domain-holdout'


def download(name, url, expected_bytes=None):
    target = RAW/name
    if not target.exists():
        temporary=target.with_suffix(target.suffix+'.partial')
        total=temporary.stat().st_size if temporary.exists() else 0
        for attempt in range(5):
            headers={'User-Agent':'Recros-academic-research'}
            if total:headers['Range']=f'bytes={total}-'
            request=urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(request,timeout=60) as response:
                if total and (response.status!=206 or not response.headers.get('Content-Range','').startswith(f'bytes {total}-')):
                    raise RuntimeError('Resume range not honored; preserve partial file: '+name)
                length=response.headers.get('Content-Length')
                required=expected_bytes or (total+int(length) if length else None)
                with temporary.open('ab' if total else 'wb') as handle:
                    next_report=total+32*1024**2
                    while True:
                        chunk=response.read(1024**2)
                        if not chunk:break
                        handle.write(chunk);total+=len(chunk)
                        if total>=next_report:
                            print(json.dumps({'file':name,'downloaded_mb':round(total/1024**2,1)}),flush=True)
                            next_report+=32*1024**2
            if required is None or total==required:break
            print(json.dumps({'file':name,'resume_after_truncated_transfer':total,'attempt':attempt+1}),flush=True)
        if required is not None and temporary.stat().st_size!=required:
            raise ValueError('Unexpected public release asset size: '+name)
        temporary.replace(target)
    if expected_bytes and target.stat().st_size!=expected_bytes:raise ValueError('Existing file size mismatch: '+name)
    with target.open('rb') as handle:digest=hashlib.file_digest(handle,'sha256').hexdigest()
    print(json.dumps({'completed':name,'bytes':target.stat().st_size,'sha256':digest}),flush=True)
    return {'name':name,'url':url,'bytes':target.stat().st_size,'sha256':digest}


def main():
    RAW.mkdir(parents=True,exist_ok=True)
    existing=RAW/'download-audit.json'
    if existing.exists():commit=json.loads(existing.read_text())['goodbooks_commit']
    else:
        request=urllib.request.Request('https://api.github.com/repos/zygmuntz/goodbooks-10k/commits/master',headers={'User-Agent':'Recros-academic-research'})
        with urllib.request.urlopen(request,timeout=30) as response:commit=json.load(response)['sha']
    prefix='https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/'+commit+'/'
    sources=[('goodbooks-'+f,prefix+f,None) for f in ['ratings.csv','books.csv','tags.csv','book_tags.csv','README.md','LICENSE']]
    prefix='https://github.com/jlieth/lastfm-dataset-1K-extended/releases/download/v2.0/'
    sources += [('lastfm-events.tsv.bz2',prefix+'userid-timestamp-artid-artname-traid-traname.tsv.bz2',430980415),
                ('lastfm-README.txt',prefix+'README.txt',2235)]
    genre_url='https://zenodo.org/api/records/2553414/files/acousticbrainz-mediaeval-lastfm-train.tsv.bz2/content'
    sources += [('acousticbrainz-lastfm-genres.tsv.bz2',genre_url,23075281)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        files=list(pool.map(lambda value:download(*value),sources))
    genre=RAW/'acousticbrainz-lastfm-genres.tsv.bz2'
    with genre.open('rb') as handle:md5=hashlib.file_digest(handle,'md5').hexdigest()
    if md5!='797a4d6dfcdbe9c405f336225a97fd9e':raise ValueError('Published genre checksum mismatch.')
    genre_audit={'source':genre_url,'bytes':genre.stat().st_size,'published_md5':md5,
                 'sha256':next(f['sha256'] for f in files if f['name']==genre.name),
                 'taxonomy_source':'https://mtg.github.io/acousticbrainz-genre-dataset/data/'}
    if not (RAW/'acousticbrainz-download-audit.json').exists():
        (RAW/'acousticbrainz-download-audit.json').write_text(json.dumps(genre_audit,indent=2)+'\n')
    report={'downloaded_utc':datetime.now(timezone.utc).isoformat(),'goodbooks_commit':commit,'files':files,
            'scope':'Public ratings/metadata and permitted academic Last.fm event mirror. No model weights, recordings or paid service.',
            'sources':['https://github.com/zygmuntz/goodbooks-10k','https://github.com/jlieth/lastfm-dataset-1K-extended']}
    if not existing.exists():existing.write_text(json.dumps(report,indent=2)+'\n')
    else:(RAW/'download-recheck.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
