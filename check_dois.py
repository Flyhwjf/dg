import urllib.request, re, sys

prefix = '10.13334/j.0258-8013.pcsee.'
nums = ['220001','220002','220003','220004','220005','220813','221005','221100','230001']
for n_str in nums:
    doi = prefix + n_str
    try:
        req = urllib.request.Request('https://doi.org/' + doi, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        resp = urllib.request.urlopen(req, timeout=5)
        content = resp.read().decode('utf-8', errors='replace')
        t = re.search(r'题名[：:]\s*([^<]+)', content)
        if t:
            auth = re.search(r'作者[：:]\s*([^<]+)', content)
            y = re.search(r'出版年[：:](\d{4})', content)
            title = t.group(1).strip()
            authors = auth.group(1).strip() if auth else 'N/A'
            year = y.group(1) if y else 'N/A'
            print(f'DOI: {doi}')
            print(f'Title: {title[:80]}')
            print(f'Authors: {authors[:80]}')
            print(f'Year: {year}')
            print()
        else:
            print(f'DOI: {doi} -> no title found')
    except Exception as e:
        print(f'DOI: {doi} -> {type(e).__name__}')
    sys.stdout.flush()
print('Done')
