"""모두핏 V3 — 공공데이터를 과장 없이 탐색하는 검증 가능한 규칙 엔진."""
from __future__ import annotations
import io
import re
from pathlib import Path
from datetime import date
from urllib.parse import quote
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data'
SEOUL_SOURCE = '서울시 공공 체육시설별 운영프로그램 정보 (과거 기록)'
KSPON_SOURCE = '한국체육산업개발 스포츠센터 강좌정보'
SEOUL_URL = 'https://data.seoul.go.kr/dataList/OA-1221/S/1/datasetView.do'
KSPON_SCHEDULE_URL = 'https://www.data.go.kr/data/15110953/fileData.do'
KSPON_CATALOG_URL = 'https://www.data.go.kr/data/15147992/fileData.do'
FACILITIES_URL = 'https://data.seoul.go.kr/dataList/OA-21779/S/1/datasetView.do'
PROGRAMS_URL = 'https://data.seoul.go.kr/dataList/OA-21780/A/1/datasetView.do'
DAYS = ['월','화','수','목','금','토','일']
DISTRICTS = ['강남구','강동구','강북구','강서구','관악구','광진구','구로구','금천구','노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구','성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구']
DISTRICT_STEMS = {d[:-1]:d for d in DISTRICTS if d!='중구'}
DISTRICT_STEMS['중구']='중구'

# 지명이 포함되지 않은 시설 중 위치를 비교적 명확히 확인할 수 있는 이름만 보강.
# 추정이 불가능한 시설명은 절대 임의 구로 채우지 않고 '지역 미확인'으로 남긴다.
KNOWN_NAME_TO_DISTRICT = {
 '창동문화체육센터':'도봉구','망우청소년수련관':'중랑구','충무아트홀스포츠센터':'중구',
 '신림체육센터':'관악구','목동청소년수련관':'양천구','목동문화체육센터':'양천구',
 '회현체육센터':'중구','수서청소년수련관':'강남구','흑석체육센터':'동작구',
 '문래청소년수련관':'영등포구','서울곰두리체육센터':'송파구',
 '금호초등학교(열린금호교육문화관)':'성동구','남산타운문화체육센터':'중구',
 '온조대왕문화체육관':'강동구','돈암초등학교':'성북구',
 '신월문화체육센터':'양천구','사당문화회관':'동작구',
 '올림픽공원스포츠센터':'송파구','올림픽수영장':'송파구',
 '삼청테니스장':'종로구','마곡레포츠센터':'강서구','역삼청소년수련관':'강남구',
 '마곡실내배드민턴장':'강서구','목동실내빙상장':'양천구',
 '면목2동체육관':'중랑구','이문체육문화센터':'동대문구',
 '강남주민편익시설':'강남구','마장국민체육센터':'성동구',
 '화곡청소년수련관':'강서구','이태원2동헬스장':'용산구',
 '목동종합사회복지관':'양천구','오금공원테니스장':'송파구',
 '오금공원인라인경기장':'송파구','잠실종합사회복지관':'송파구',
 '서초카페거리사계절스케이트장':'서초구',
 '창동종합사회복지관':'도봉구','장충문화체육센터':'중구',
 '광장종합사회복지관':'광진구','마곡유수지테니스장':'강서구',
 '잠원스포츠파크':'서초구','양재근린공원축구장':'서초구',
 '양재시민의숲테니스장':'서초구','양재천수영장':'서초구',
 '신길종합사회복지관':'영등포구','등촌1종합사회복지관':'강서구',
 '등촌4종합사회복지관':'강서구','등촌7종합사회복지관':'강서구',
 '등촌9종합사회복지관':'강서구','이촌2동 헬스장':'용산구',
 '한남1동헬스장':'용산구','한남동헬스장':'용산구',
 '서빙고동헬스장':'용산구','청파1동 헬스장':'용산구',
 '용문동헬스장':'용산구','금호공원체육관':'성동구',
 '성내종합사회복지관':'강동구','마천종합사회복지관':'송파구',
 '가락종합사회복지관':'송파구','신당종합사회복지관':'중구',
 '포이테니스장':'강남구','봉은테니스장':'강남구',
 '청담종합사회복지관':'강남구','대청종합사회복지관':'강남구',
 '수서명화종합사회복지관':'강남구',
}
NULL_VALUES = {'', 'null', 'none', 'nan', 'n/a', '#name?', '-', '정보없음', '미기재'}
LEVEL_BEGINNER = re.compile(r'초보|입문|초급|기초|처음|신규|스타터|비기너')
LEVEL_ADVANCED = re.compile(r'고급|상급|중급|선수|선수반|전문반|마스터|숙련|연수반')
CHILD = re.compile(r'어린이|유아|유치|초등|초등생|아동|키즈|주니어|영아|아기')
YOUTH = re.compile(r'중학생|고등학생|청소년|중등|고등|학생')
ADULT = re.compile(r'성인|직장인|일반인|중장년|중년|장년|주부|대학생|남녀성인')
SENIOR = re.compile(r'어르신|시니어|노인|고령')
SPORT_CATEGORY = {
 '라켓 운동':['탁구','테니스','배드민턴','스쿼시','정구','라켓'],
 '수중 운동':['수영','아쿠아','수중','스쿠버','다이빙'],
 '근력·체력':['헬스','근력','웨이트','트레이닝','trx','피트니스','크로스핏','순환운동','체력'],
 '댄스·리듬':['댄스','발레','줌바','에어로빅','라인댄스','재즈','방송댄스','무용'],
 '유연성·균형':['요가','필라테스','스트레칭','체조','태극권','기공'],
 '골프':['골프','파크골프'],
 '빙상·레저':['스케이트','빙상','인라인','클라이밍','자전거'],
 '무도':['검도','태권도','합기도','유도','복싱','권투','무술','가라테'],
 '구기 운동':['농구','축구','풋살','배구','야구','핸드볼','족구'],
 '그 밖의 운동':[]
}
GOAL_CATEGORY = {
 '새로운 종목 배우기':[],
 '심폐지구력 기르기':['수중 운동','라켓 운동','댄스·리듬','구기 운동'],
 '근력 기르기':['근력·체력','유연성·균형'],
 '유연성·균형 관리':['유연성·균형','수중 운동'],
 '즐겁게 꾸준히 운동하기':['댄스·리듬','라켓 운동','수중 운동']
}


def clean(v):
    if v is None: return ''
    try:
        if pd.isna(v): return ''
    except (ValueError, TypeError): pass
    s = str(v).strip()
    return '' if s.lower() in NULL_VALUES else s


def load_csv_bytes(b: bytes) -> pd.DataFrame:
    last = None
    for encoding in ['utf-8-sig','cp949','euc-kr']:
        try:
            return pd.read_csv(io.BytesIO(b), dtype=str, keep_default_na=False, encoding=encoding, low_memory=False)
        except UnicodeDecodeError as e:
            last = e
    raise ValueError('CSV 파일의 문자 인코딩을 확인해 주세요.') from last


def load_file(path:Path):
    return load_csv_bytes(path.read_bytes())


def determine_category(sport, name=''):
    s = (clean(sport) + ' ' + clean(name)).lower()
    for category, keys in SPORT_CATEGORY.items():
        if any(k in s for k in keys): return category
    return '그 밖의 운동'


def determine_district(facility: str):
    s=clean(facility)
    if not s:return '지역 미확인'
    if s in KNOWN_NAME_TO_DISTRICT:return KNOWN_NAME_TO_DISTRICT[s]
    # 구명 전체 문자열이 있는 경우 또는 명확한 구 이름 어간으로 시작하는 경우.
    for district in DISTRICTS:
        if district in s:return district
    for stem, district in DISTRICT_STEMS.items():
        if stem=='중구':continue
        if s.startswith(stem) and len(stem)>=2:return district
    return '지역 미확인'


def parse_days(s):
    s=clean(s).replace(' ', '')
    if not s:return set()
    s=s.replace('개월','').replace('요일','')
    found=set()
    if '평일' in s:found.update(DAYS[:5])
    if '주말' in s:found.update(DAYS[5:])
    if re.search(r'월[~～\-–]금',s):found.update(DAYS[:5])
    if re.search(r'월[~～\-–]일',s):found.update(DAYS)
    if re.search(r'토[~～\-–]일',s):found.update(DAYS[5:])
    found.update(re.findall(r'[월화수목금토일](?=[,，/()\s]|$)',s))
    # '월화수목금' 같은 연속 나열을 허용하되 '1개월'은 사전 제거함.
    for token in re.findall(r'[월화수목금토일]{2,}',s):found.update(token)
    return found


def start_hour(s):
    s=clean(s)
    match=re.search(r'(?<!\d)(\d{1,2}):([0-5]\d)',s)
    if match:
        hour=int(match.group(1))
        return hour if 0<=hour<=23 else None
    return None


def duration_weekly(s):
    # 시간 정보만으로 실제 주간 운동량을 계산하지 않음; 1회 시간이 명확한 경우에만 추정.
    match = re.search(r'(\d{1,2}):([0-5]\d)\s*[-~∼]\s*(\d{1,2}):([0-5]\d)',clean(s))
    if not match:return None
    a,b,c,d=map(int,match.groups())
    minutes=(c*60+d)-(a*60+b)
    return minutes if 0<minutes<=180 else None


def level_status(name, raw=''):
    text=f'{clean(name)} {clean(raw)}'
    if LEVEL_ADVANCED.search(text):return '경험자'
    if LEVEL_BEGINNER.search(text):return '입문'
    return '수준 미확인'


def classify_age(target, age):
    """참여 가능하다는 의학적 판정이 아니라 텍스트상의 대상 불일치 여부만 판정."""
    s=clean(target)
    if not s:return '대상 미확인'
    has_child=bool(CHILD.search(s));has_youth=bool(YOUTH.search(s))
    has_adult=bool(ADULT.search(s));has_senior=bool(SENIOR.search(s))
    if '누구나' in s or '전연령' in s or '전체'==s:return '범위 일치'
    # 기재된 연령범위. 단, 표기 예외가 있으므로 보수적으로 처리.
    mm=re.search(r'(\d{1,2})\s*[~～-]\s*(\d{1,2})\s*세',s)
    if mm:return '범위 일치' if int(mm.group(1))<=age<=int(mm.group(2)) else '대상 불일치'
    if age<13:
        if (has_child or has_youth) and not has_adult:return '범위 일치'
        return '대상 불일치' if has_adult and not has_child and not has_youth else '대상 미확인'
    if age<19:
        if has_youth:return '범위 일치'
        if has_adult and not (has_child or has_youth):return '대상 불일치'
        return '대상 미확인'
    if age>=65:
        if has_child or has_youth:
            if not (has_adult or has_senior):return '대상 불일치'
        if has_senior:return '범위 일치'
        if has_adult:return '대상 미확인' # 일반 성인 강좌가 고령자에게 적합하다고 판정하지 않음
        return '대상 미확인'
    if has_child or has_youth:
        if not has_adult:return '대상 불일치'
    # 연령대 특정 표기는 함부로 성인 전체로 판정하지 않음.
    decades=re.findall(r'([2-8])0대',s)
    if decades and str(age//10) not in decades and not has_adult:return '대상 불일치'
    if has_adult or (decades and str(age//10) in decades):return '범위 일치'
    return '대상 미확인'


def valid_link(url):
    s=clean(url)
    return s if re.match(r'^https?://[^\s]+$',s) else ''


def normalize_seoul(df):
    # 이 파일의 명시적 강좌 기간은 주로 2011년. 행별 현재 운영 여부와 무관하게 역사 데이터임.
    d=df.fillna('').copy()
    def get(col):return d[col].map(clean) if col in d.columns else pd.Series(['']*len(d),index=d.index)
    out=pd.DataFrame({
       '시설명':get('시설명'), '프로그램':get('프로그램명'), '종목':get('종목명'),
       '반명':get('반명'), '레벨':get('레벨'), '대상':get('대상'),
       '요일':get('요일'), '시간':get('진행시간(1회)'), '가격원문':get('수강료(원)'),
       '정원원문':get('전체정원수'), '소개':get('프로그램소개'),
       '접수방법':get('접수방법'), '접수기간':get('접수기간'),
       '링크':get('온라인예약링크'), '원문_종료일':get('강좌종료일'),
       '무료확인':get('가격무료확인'),
    })
    out['권역']='서울';out['자치구']=out['시설명'].map(determine_district)
    out['주소']='';out['데이터출처']=SEOUL_SOURCE;out['기록상태']='과거 공개 기록'
    out['원문링크']=SEOUL_URL
    return finish(out)


def normalize_kspon(df):
    d=df.fillna('').copy()
    def get(col):return d[col].map(clean) if col in d.columns else pd.Series(['']*len(d),index=d.index)
    sport=get('종목');name=get('강좌명'); center=get('스포츠센터')
    # 센터명은 일정 CSV에 없으며, 데이터셋의 '올림픽스포츠센터' 맥락에서만 예비 지정.
    if (center=='').all():center=pd.Series(['올림픽공원스포츠센터']*len(d),index=d.index)
    region=[];district=[]
    for f in center:
        if '분당' in f:region.append('경기');district.append('성남시 분당구')
        elif '일산' in f:region.append('경기');district.append('고양시 (세부 지역 미확인)')
        else:region.append('서울');district.append('송파구' if ('올림픽' in f) else '지역 미확인')
    out=pd.DataFrame({
        '시설명':center, '프로그램':name, '종목':sport,'반명':pd.Series(['']*len(d),index=d.index),
        '레벨':pd.Series(['']*len(d),index=d.index),'대상':get('수강대상'), '요일':get('수강요일'),
        '시간':get('수강시간'),'가격원문':get('수강금액'), '정원원문':get('정원'),
        '소개':pd.Series(['']*len(d),index=d.index), '접수방법':pd.Series(['']*len(d),index=d.index),
        '접수기간':pd.Series(['']*len(d),index=d.index), '링크':pd.Series(['']*len(d),index=d.index),
        '원문_종료일':get('수강종료일'), '무료확인':pd.Series(['']*len(d),index=d.index),
    })
    out['권역']=region;out['자치구']=district;out['주소']='';out['데이터출처']=KSPON_SOURCE
    out['기록상태']='운영·잔여석 미확인';out['원문링크']=KSPON_SCHEDULE_URL
    return finish(out)


def finish(d):
    d=d.copy()
    d['종목분류']=[determine_category(sp,name) for sp,name in zip(d['종목'],d['프로그램'])]
    d['수준분류']=[level_status(f'{a} {b}',c) for a,b,c in zip(d['프로그램'],d['반명'],d['레벨'])]
    d['요일집합']=[parse_days(s) for s in d['요일']]
    d['시작시각']=d['시간'].map(start_hour)
    d['가격']=pd.to_numeric(d['가격원문'].str.replace(',','',regex=False),errors='coerce')
    # 0이 무료를 뜻하는지 알 수 없는 경우: 0=가격 미확인 처리
    free=d['무료확인'].eq('Y')
    d.loc[(d['가격']==0) & (~free),'가격']=float('nan')
    d['정원']=pd.to_numeric(d['정원원문'],errors='coerce')
    d.loc[d['정원']<=0,'정원']=float('nan')
    d['신청링크']=d['링크'].map(valid_link)
    d['키']=d['시설명']+'|'+d['프로그램']+'|'+d['반명']+'|'+d['요일']+'|'+d['시간']+'|'+d['대상']+'|'+d['가격원문']
    d=d.drop_duplicates(subset=['데이터출처','키'],keep='first').drop(columns=['키'])
    return d.reset_index(drop=True)


def augment_locations(df, locations):
    """선택 업로드한 시설별 지역/주소 정보가 있는 경우 정확히 일치하는 시설명만 갱신."""
    if locations is None or locations.empty:return df
    if not {'시설명','자치구'}.issubset(locations.columns):
        raise ValueError('시설 위치 CSV에는 시설명, 자치구 열이 필요합니다. 주소 열은 선택사항입니다.')
    lc=locations.copy().fillna('');lc['시설명']=lc['시설명'].map(clean)
    lc['자치구']=lc['자치구'].map(clean)
    lc=lc[lc['자치구'].isin(DISTRICTS)].drop_duplicates('시설명')
    addr=lc.set_index('시설명')['주소'].map(clean).to_dict() if '주소' in lc.columns else {}
    mapping=lc.set_index('시설명')['자치구'].to_dict()
    out=df.copy()
    mask=out['권역'].eq('서울') & out['시설명'].isin(mapping)
    out.loc[mask,'자치구']=out.loc[mask,'시설명'].map(mapping)
    out.loc[mask,'주소']=out.loc[mask,'시설명'].map(lambda x:addr.get(x,''))
    return out


def add_kspon_descriptions(schedule, catalog):
    """정확히 일치하는 센터·종목 소개만 결합. 다른 센터의 설명은 붙이지 않음.

    일정 CSV에는 센터명이 없다. 공식 데이터셋 맥락상 올림픽공원스포츠센터
    출처로 분류한 기록만 해당 센터의 종목 소개와 결합한다.
    설명 파일의 다른 네 센터 기록은 독립적인 카탈로그로 유지한다.
    """
    if catalog is None or catalog.empty:
        return schedule
    out = schedule.copy()
    required = {'스포츠센터', '강좌명', '강좌설명', '링크주소'}
    if not required.issubset(catalog.columns):
        return out
    ct = catalog.fillna('').copy()
    def canon_center(v):
        return clean(v).replace(' ', '').replace('올림픽공원스포츠센터', '올림픽공원스포츠센터')
    def canon_sport(v):
        return clean(v).replace(' ', '').lower()
    ct['_center'] = ct['스포츠센터'].map(canon_center)
    ct['_sport'] = ct['강좌명'].map(canon_sport)
    ct = ct[ct['_center'].ne('') & ct['_sport'].ne('')]
    # Duplicate center/sport identities should not lead to arbitrary first-row selection.
    uniques = ct.drop_duplicates(['_center', '_sport'], keep=False)
    lookup = { (r['_center'], r['_sport']): r for _, r in uniques.iterrows() }
    for idx, rec in out.iterrows():
        if rec['데이터출처'] != KSPON_SOURCE:
            continue
        key = (canon_center(rec['시설명']), canon_sport(rec['종목']))
        matched = lookup.get(key)
        if matched is None:
            continue
        if not clean(rec['소개']):
            out.at[idx, '소개'] = clean(matched['강좌설명'])
        if not clean(rec['신청링크']) and valid_link(matched['링크주소']):
            # 종목 소개 페이지이며 실제 수강신청·잔여석 페이지는 아님.
            out.at[idx, '신청링크'] = valid_link(matched['링크주소'])
    return out


def data_quality(d):
    n=max(1,len(d))
    cols=['대상','요일','시간','레벨','주소','신청링크']
    return pd.DataFrame({'정보 항목':cols,'기재 건수':[int(d[c].map(clean).ne('').sum()) for c in cols],
       '기재율(%)':[round(100*d[c].map(clean).ne('').sum()/n,1) for c in cols]})


def rank_classes(df, *, age=45, region='서울', district='서울 전체', goal='새로운 종목 배우기',
                 day='평일', time='시간 상관없음', category='전체 종목', experience='입문',
                 max_price=None, excluded=(), count=50):
    """텍스트 기반 탐색 적합도. 연령과 종목별 의학적 적합성이나 잔여석을 판정하지 않음."""
    if df.empty:return df.copy()
    out=df[df['권역'].eq(region)].copy()
    if region=='서울' and district!='서울 전체':out=out[out['자치구'].eq(district)]
    if category!='전체 종목':out=out[out['종목분류'].eq(category)]
    if excluded:out=out[~out['종목'].isin(excluded)]
    if day!='요일 상관없음':
        days=set(DAYS[:5] if day=='평일' else DAYS[5:])
        out=out[out['요일집합'].map(lambda x:bool(x&days))]
    if time!='시간 상관없음':
        lim={'오전 (06~12시)':(6,12),'오후 (12~18시)':(12,18),'저녁 (18~24시)':(18,24)}[time]
        out=out[out['시작시각'].map(lambda x:pd.notna(x) and lim[0]<=x<lim[1])]
    if max_price is not None:
        out=out[out['가격'].map(lambda x:pd.notna(x) and x<=max_price)]
    if out.empty:return out
    out['연령판정']=out['대상'].map(lambda t:classify_age(t,age))
    out=out[out['연령판정']!='대상 불일치']
    if experience=='입문':out=out[out['수준분류']!='경험자']
    if out.empty:return out
    current=date.today()
    def has_ended(s):
        s=clean(s)
        if s.startswith('9999'):return False
        if re.fullmatch(r'\d{8}',s):
            try:return date(int(s[:4]),int(s[4:6]),int(s[6:8]))<current
            except ValueError:return False
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',s):
            try:return date.fromisoformat(s)<current
            except ValueError:return False
        return False
    # KSPON 강좌 중 종료일이 명시된 과거 기록은 탐색에서 제외.
    ended=out['원문_종료일'].map(has_ended)
    out=out[~(ended & out['데이터출처'].eq(KSPON_SOURCE))]
    if out.empty:return out
    chosen=GOAL_CATEGORY.get(goal,[])
    def score(r):
        points=20 # 선택한 권역·구 안에서 발견된 기록
        points+=20 if r['연령판정']=='범위 일치' else 6
        points+=15 if r['요일집합'] else 0
        points+=10 if pd.notna(r['시작시각']) else 0
        points+=15 if (not chosen or r['종목분류'] in chosen) else 3
        points+=12 if r['수준분류']=='입문' else (8 if experience!='입문' else 2)
        points+=8 if pd.notna(r['가격']) else 0
        return min(100,points)
    out['조건일치점수']=out.apply(score,axis=1)
    # 입문 표기를 앞세우고 고령자 참가 요건 미확인은 무조건 표시
    out=out.sort_values(['조건일치점수','시설명','프로그램'],ascending=[False,True,True],kind='stable')
    return out.head(count).reset_index(drop=True)


def friendly_evidence(r,age,goal):
    results=[]
    if r['연령판정']=='범위 일치':results.append('대상 표기 일치')
    else:results.append('대상 연령 확인 필요')
    if r['수준분류']=='입문':results.append('입문·기초 표기 확인')
    else:results.append('초보자 수강 가능 여부 확인 필요')
    if r['요일집합']:results.append('운영 요일 기록 있음')
    if GOAL_CATEGORY.get(goal) and r['종목분류'] in GOAL_CATEGORY[goal]:
        results.append('선택한 운동 목표와 종목 유형이 관련됨(서비스 분류)')
    return results


def search_map_link(name):
    return 'https://map.naver.com/p/search/'+quote(clean(name))


def normalize_facility_source(raw):
    """서울시 공공체육시설 정보 원본의 한국어 필드에서 시설명/자치구/주소를 읽습니다.
    시설명과 자치구가 둘 다 확인되는 행만 사용하며 임의 주소를 생성하지 않습니다.
    """
    d=raw.fillna('').copy()
    d.columns=[str(k).replace('\ufeff','').strip() for k in d.columns]
    def choose(*keys):
        for key in keys:
            if key in d.columns:
                return d[key].map(clean)
        return pd.Series(['']*len(d),index=d.index)
    result=pd.DataFrame({
      '시설명':choose('시설명','체육시설명','장소명','시설명칭'),
      '자치구':choose('자치구','자치구명','지역구','구명'),
      '주소':choose('시설주소','주소','도로명주소','소재지도로명주소'),
    })
    result['자치구']=result['자치구'].str.replace('서울특별시','',regex=False).str.replace('서울시','',regex=False).str.strip()
    return result[(result['시설명']!='') & result['자치구'].isin(DISTRICTS)].drop_duplicates('시설명')
