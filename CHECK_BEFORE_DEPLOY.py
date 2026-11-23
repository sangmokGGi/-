from pathlib import Path
import csv, sys
p=Path(__file__).resolve().parent
specs=[('data/seoul_programs.csv',{'시설명','프로그램명'},14523),('data/kspon_schedule.csv',{'강좌명','수강요일','수강시작일'},2137),('data/kspon_catalog.csv',{'스포츠센터','강좌명','강좌설명'},94)]
failed=False
for fn, fields, n in specs:
    f=p/fn
    if not f.exists():
        print('누락:',fn);failed=True;continue
    try:
        b=f.read_bytes();t=None
        for enc in ['utf-8-sig','cp949','euc-kr']:
            try:t=b.decode(enc);break
            except UnicodeDecodeError:pass
        if t is None:raise ValueError('인코딩')
        rows=csv.DictReader(t.splitlines());hdr=set(rows.fieldnames or []);count=sum(1 for _ in rows)
        ok=fields.issubset(hdr) and count==n
        print(('OK' if ok else '검토 필요'),fn,'행:',count)
        if not ok:failed=True
    except Exception as e:
        print('오류:',fn,e);failed=True
for name in ['app.py','engine.py','copytext.py','requirements.txt']:
    if not (p/name).exists():print('누락:',name);failed=True
if failed:sys.exit(1)
print('배포 데이터 점검 통과. 단, 현재 운영·잔여석은 확인되지 않았습니다.')
