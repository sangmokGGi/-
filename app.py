"""모두핏 V3: 서울 중심 운동 탐색 + 공공데이터 품질 진단. 실행: py -m streamlit run app.py"""
from __future__ import annotations
from datetime import date
from pathlib import Path
from html import escape
import pandas as pd
import plotly.express as px
import streamlit as st
from engine import (DATA,SEOUL_SOURCE,KSPON_SOURCE,SEOUL_URL,KSPON_SCHEDULE_URL,
 KSPON_CATALOG_URL,FACILITIES_URL,PROGRAMS_URL,DISTRICTS,SPORT_CATEGORY,GOAL_CATEGORY,
 load_csv_bytes,load_file,normalize_seoul,normalize_kspon,add_kspon_descriptions,
 augment_locations,normalize_facility_source,rank_classes,friendly_evidence,data_quality,search_map_link,clean)
import copytext as T

st.set_page_config(page_title=f'{T.APP_NAME} | 운동 찾기',page_icon='🟢',layout='wide',initial_sidebar_state='collapsed')

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
:root{color-scheme:light}
html, body,[class*="css"],p,div,button,input,textarea,label{font-family:'DM Sans','Noto Sans KR',sans-serif!important}
.stApp{background:#f6f8f5;color:#152b24}
.block-container{max-width:1160px;padding-top:1.7rem;padding-bottom:5rem}
[data-testid="stSidebar"]{background:#f0f5ee}
[data-testid="stSidebar"] .stButton button{border-radius:12px}
h1,h2,h3{letter-spacing:-.04em;color:#152b24}
[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:26px;border-bottom:1px solid #e0e8df}
[data-testid="stTabs"] button{font-weight:700;font-size:15px}
[data-testid="stForm"]{border:1px solid #dfe9df;background:#fff;padding:24px;border-radius:22px;box-shadow:0 10px 40px rgba(18,45,32,.035)}
div.stButton > button[kind="primary"],div.stFormSubmitButton > button[kind="primary"]{background:#214b37;color:#fff;border:0;border-radius:14px;min-height:49px;font-weight:800}
div.stButton > button[kind="primary"]:hover,div.stFormSubmitButton > button[kind="primary"]:hover{background:#143325;color:#fff}
[data-testid="stMetric"]{background:white;padding:17px 19px;border-radius:17px;border:1px solid #e2e9e0}
[data-testid="stMetricLabel"]{font-size:13px;color:#61766a}
[data-testid="stMetricValue"]{font-size:25px;color:#1b4230}
.stTextInput input,.stNumberInput input{border-radius:12px}
section[data-testid="stSidebar"]{border-right:1px solid #dce6d8}
.hero{border-radius:28px;background:radial-gradient(ellipse at 90% 10%,#4d8e63 0,transparent 39%),linear-gradient(122deg,#173a2a,#24573d 70%,#3c7b4c);padding:45px 48px;color:white;margin-bottom:24px;overflow:hidden;position:relative}
.hero::after{content:'◯';position:absolute;right:45px;top:-120px;font-size:340px;color:rgba(255,255,255,.06);font-weight:400}
.hero .eyebrow{display:inline-block;font-size:12px;font-weight:800;letter-spacing:.13em;color:#d5f8a8;margin-bottom:16px}
.hero h1{color:white!important;font-size:clamp(31px,4vw,50px);margin:0 0 13px;font-weight:800;line-height:1.23;letter-spacing:-.055em}
.hero p{color:#daebe0!important;font-size:15px;line-height:1.85;margin:0;max-width:670px}
.hero .mini{display:inline-block;background:rgba(255,255,255,.11);border:1px solid rgba(255,255,255,.18);border-radius:99px;padding:8px 14px;margin:25px 10px 0 0;font-size:12px;color:#f4fff2}
.section-head{font-size:25px;font-weight:800;color:#1c3829;margin:16px 0 6px;letter-spacing:-.04em}
.small-muted{color:#708277;font-size:13px;line-height:1.65}
.notice{background:#f0f4e6;border:1px solid #e0e7c5;color:#44583c;border-radius:14px;padding:13px 17px;margin:12px 0 18px;font-size:13px;line-height:1.7}
.pill{display:inline-block;border:1px solid #dae8da;background:#edf7eb;color:#346448;border-radius:999px;padding:5px 10px;font-size:11px;font-weight:700;margin:3px 6px 4px 0}
.pill.warn{border-color:#f4e2ad;background:#fff6de;color:#83632d}
.pill.gray{border-color:#e7e7e7;background:#f7f8f7;color:#64746a}
.rank{font-weight:900;color:#214b37;background:#e7f4e0;border-radius:9px;padding:5px 9px;display:inline-block;font-size:12px;margin-bottom:9px}
.sport-label{font-size:11px;font-weight:800;color:#3a7652;letter-spacing:.08em}
.sub-head{font-size:13px;color:#738478;margin:0 0 10px}
.meta{font-size:14px;line-height:1.9;color:#324b3c}
.smallbox{background:white;border:1px solid #e4ebe2;border-radius:18px;padding:18px}
.source-card{padding:12px 16px;border-radius:13px;background:#fff;border:1px solid #e5ebe6;margin:7px 0}
@media(max-width:650px){.hero{padding:30px 25px}.hero::after{display:none}.block-container{padding-left:1rem;padding-right:1rem}}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def initial_data():
    seoul=normalize_seoul(load_file(DATA/'seoul_programs.csv'))
    schedule_path=DATA/'kspon_schedule.csv'
    catalog_path=DATA/'kspon_catalog.csv'
    real_schedule=schedule_path.exists()
    schedule_raw=load_file(schedule_path if real_schedule else DATA/'kspon_schedule_preview.csv')
    raw_schedule_count=len(schedule_raw)
    kspon_schedule=normalize_kspon(schedule_raw)
    catalog=load_file(catalog_path if catalog_path.exists() else DATA/'kspon_catalog_preview.csv')
    kspon_schedule=add_kspon_descriptions(kspon_schedule,catalog)
    return seoul,kspon_schedule,catalog,real_schedule,raw_schedule_count

try:
    seoul,kspon,catalog,full_kspon,raw_schedule_count=initial_data()
except Exception as err:
    st.error(f'내장 데이터를 열지 못했습니다. 파일 위치를 확인해 주세요. 상세: {err}')
    st.stop()

with st.sidebar:
    st.markdown('### 모두핏 설정')
    st.caption('일반 이용자는 설정하지 않아도 검색할 수 있어요.')
    with st.expander('데이터 관리자 · CSV 업로드',expanded=False):
        st.caption('업로드는 현재 접속한 세션에만 적용됩니다. 친구와 공유할 버전은 ZIP의 data 폴더에 파일을 넣어 배포하세요.')
        f1=st.file_uploader('한국체육산업개발 강좌 일정 CSV',type='csv',key='schedule_upload')
        f2=st.file_uploader('한국체육산업개발 강좌 설명 CSV',type='csv',key='catalog_upload')
        f3=st.file_uploader('시설 위치 정리표 CSV (시설명·자치구·주소)',type='csv',key='locations_upload')
        f4=st.file_uploader('서울시 공공체육시설 정보 원본 CSV (선택)',type='csv',key='facilities_latest_upload')
        st.caption('서울시 역사 데이터는 기본 포함되어 있습니다. 새 서울시 프로그램 데이터는 별도로 확인해야 합니다.')

try:
    if f1 is not None:
        schedule_uploaded=load_csv_bytes(f1.getvalue())
        raw_schedule_count=len(schedule_uploaded)
        kspon=normalize_kspon(schedule_uploaded)
        full_kspon=True
    if f2 is not None:catalog=load_csv_bytes(f2.getvalue())
    kspon=add_kspon_descriptions(kspon,catalog)
    data=pd.concat([seoul,kspon],ignore_index=True)
    latest_facility_path=DATA/'seoul_facilities_latest.csv'
    latest_facilities=load_file(latest_facility_path) if latest_facility_path.exists() else None
    if f4 is not None:latest_facilities=load_csv_bytes(f4.getvalue())
    location_audit={'loaded': False,'rows':0,'names':0,'matches':0}
    if latest_facilities is not None:
        location_audit['loaded']=True
        location_audit['rows']=len(latest_facilities)
        locations_norm=normalize_facility_source(latest_facilities)
        location_audit['names']=len(locations_norm)
        location_audit['matches']=data[data['권역'].eq('서울') & data['시설명'].isin(set(locations_norm['시설명']))]['시설명'].nunique()
        data=augment_locations(data,locations_norm)
    default_locations=DATA/'facility_locations.csv'
    if default_locations.exists():data=augment_locations(data,load_file(default_locations))
    if f3 is not None:data=augment_locations(data,load_csv_bytes(f3.getvalue()))
except Exception as err:
    st.error(f'추가 CSV를 처리할 수 없습니다. 열 이름과 파일 형식을 확인하세요. 상세: {err}')
    st.stop()

st.markdown('<div class="hero"><span class="eyebrow">MODUFIT · YOUR LOCAL SPORTS FINDER</span><h1>내 동네에서,<br>새로운 운동을 발견하세요.</h1><p>나이와 생활 패턴에 맞춰 공공 체육강좌 기록을 찾고,<br>운동 목표에 맞는 종목도 함께 살펴보세요.</p><span class="mini">서울 25개 자치구 선택</span><span class="mini">공공데이터 기반</span><span class="mini">추천 이유 공개</span></div>',unsafe_allow_html=True)

st.markdown('<div class="notice">'+escape(T.HISTORY_NOTICE)+'<br>실시간 예약 서비스가 아닙니다. 강좌 기록의 정원은 잔여 좌석 수를 뜻하지 않습니다.</div>',unsafe_allow_html=True)

tab_find,tab_insight,tab_coverage,tab_sources=st.tabs(['🔎 운동 찾기','📊 지역·데이터 인사이트','🗂️ 데이터 수록 현황','📖 추천 근거·데이터 출처'])

with tab_find:
    st.markdown('<div class="section-head">어떤 운동을 찾고 계세요?</div>',unsafe_allow_html=True)
    st.markdown('<p class="small-muted">실제 나이와 생활권을 선택해 보세요. 주소나 GPS를 입력할 필요는 없습니다.</p>',unsafe_allow_html=True)
    with st.form('finder'):
        a,b,c=st.columns([1,1,1])
        with a:
            region=st.selectbox('활동 지역',['서울','경기 (성남·고양 중심)'])
            region_code='서울' if region=='서울' else '경기'
            district=st.selectbox('사는 곳 또는 운동할 자치구',['서울 전체']+DISTRICTS,disabled=region_code!='서울')
        with b:
            age=st.number_input('만 나이',min_value=7,max_value=99,value=45,step=1)
            goal=st.selectbox('운동 목적',list(GOAL_CATEGORY.keys()))
        with c:
            experience=st.selectbox('운동 경험',['입문','경험 있음','상관없음'])
            category=st.selectbox('관심 운동', ['전체 종목']+list(SPORT_CATEGORY.keys()))
        d,e,f=st.columns(3)
        with d:day=st.selectbox('가능한 요일',['평일','주말','요일 상관없음'])
        with e:clock=st.selectbox('선호 시간대',['시간 상관없음','오전 (06~12시)','오후 (12~18시)','저녁 (18~24시)'])
        with f:
            budget_option=st.selectbox('한 달 예산(기록상 금액)',['상관없음','5만원 이하','8만원 이하','10만원 이하','15만원 이하'])
        budget={'상관없음':None,'5만원 이하':50000,'8만원 이하':80000,'10만원 이하':100000,'15만원 이하':150000}[budget_option]
        all_sports=sorted({clean(s) for s in data['종목'] if clean(s)})
        excluded=st.multiselect('이미 해 본 운동 (선택 · 추천에서 제외)',all_sports,placeholder='해 본 종목을 골라주세요')
        submitted=st.form_submit_button(T.SEARCH_BUTTON,type='primary',use_container_width=True)
    if submitted:
        st.session_state['search']={'age':age,'region':region_code,'district':district,'goal':goal,'day':day,
                                    'time':clock,'category':category,'experience':experience,
                                    'max_price':budget,'excluded':excluded}
        st.session_state['show_more']=False
    if 'search' not in st.session_state:
        st.markdown('### 모두핏은 이렇게 이용해요')
        c1,c2,c3=st.columns(3)
        for col,ttl,desc in [(c1,'01 · 내 조건 입력','사는 구·나이·요일·종목을 선택해요.'),
                             (c2,'02 · 강좌 비교','적합 조건과 확인할 내용을 함께 살펴봐요.'),
                             (c3,'03 · 공식 채널 확인','운영 여부와 잔여석을 직접 확인해요.')]:
            with col:st.markdown(f'<div class="smallbox"><b>{escape(ttl)}</b><p class="small-muted">{escape(desc)}</p></div>',unsafe_allow_html=True)
    else:
        params=st.session_state['search']
        ranked=rank_classes(data,**params,count=450)
        st.markdown('<div class="section-head">'+escape(T.RESULT_TITLE)+'</div>',unsafe_allow_html=True)
        st.markdown('<div class="small-muted">'+escape(f"만 {params['age']}세 · {params['district'] if params['region']=='서울' else '경기'} · {params['day']} · {params['goal']}")+'</div>',unsafe_allow_html=True)
        a,b,c=st.columns(3)
        a.metric('조건에 맞는 탐색 기록',f'{len(ranked):,}건'+(' 이상' if len(ranked)==450 else ''))
        b.metric('검색 기록 내 시설',f"{ranked['시설명'].nunique() if not ranked.empty else 0:,}곳")
        c.metric('모집 상태','모두 확인 필요')
        if ranked.empty:
            st.info(T.EMPTY_NOTICE)
        else:
            nshow=24 if st.session_state.get('show_more') else 9
            st.caption('적합도는 검색 조건의 일치 정도를 비교하는 자체 지표입니다. 강좌의 안전성·건강 효과·현재 등록 가능 여부를 뜻하지 않습니다.')
            for i,(_,r) in enumerate(ranked.head(nshow).iterrows(),1):
                with st.container(border=True):
                    l,m=st.columns([4.5,1])
                    with l:
                        st.markdown(f'<span class="rank">#{i:02d} · 강좌 탐색</span> <span class="sport-label">{escape(str(r["종목분류"]))}</span>',unsafe_allow_html=True)
                        st.markdown(f'### {escape(clean(r["프로그램"]) or clean(r["종목"]) or "프로그램명 미기재")}')
                        st.markdown(f'<p class="sub-head">{escape(str(r["시설명"]))} · {escape(str(r["자치구"]))}</p>',unsafe_allow_html=True)
                    with m:st.metric('조건 일치',f"{r['조건일치점수']}점")
                    source_is_old=(r['데이터출처']==SEOUL_SOURCE)
                    tags=[('과거 공개 기록' if source_is_old else '현재 운영 확인 필요','warn'),
                          (r['수준분류'],'gray'),('잔여석 미확인','warn')]
                    st.markdown(' '.join(f'<span class="pill {typ}">{escape(clean(title))}</span>' for title,typ in tags),unsafe_allow_html=True)
                    price=(f"{int(r['가격']):,}원" if pd.notna(r['가격']) else '가격 확인 필요')
                    st.markdown('<div class="meta">'+escape(f"요일  {clean(r['요일']) or '미기재'}  ·  시간  {clean(r['시간']) or '미기재'}")+'<br>'+escape(f"기록상 수강료  {price}  ·  수강대상  {clean(r['대상']) or '미기재'}")+'</div>',unsafe_allow_html=True)
                    proof=friendly_evidence(r,params['age'],params['goal'])
                    st.caption('추천 근거: '+' · '.join(proof))
                    if pd.notna(r['정원']):
                        st.caption(f"기록상 정원 {int(r['정원']):,}명 · 현재 남은 자리가 아닙니다.")
                    if clean(r['소개']):
                        with st.expander('프로그램 설명 보기'):
                            st.write(clean(r['소개'])[:550])
                    with st.expander('신청 전에 무엇을 확인해야 하나요?'):
                        st.write('① 이 강좌가 현재 실제로 운영되는지 ② 신규 접수를 받는지 ③ 빈자리가 있는지 ④ 나이·실력 조건이 맞는지')
                        if clean(r['접수방법']):st.caption('과거 자료에 기재된 접수방법: '+clean(r['접수방법'])[:180])
                        if clean(r['접수기간']):st.caption('과거 자료에 기재된 접수기간: '+clean(r['접수기간'])[:180])
                    linkcol1,linkcol2=st.columns(2)
                    with linkcol1:
                        if clean(r['신청링크']):st.link_button('종목 소개 또는 기록상 링크 · 신청 여부는 별도 확인',r['신청링크'],use_container_width=True)
                        else:st.link_button('시설명 지도 검색 · 실제 운영 확인',search_map_link(r['시설명']),use_container_width=True)
                    with linkcol2:
                        st.link_button('공공데이터 원문 보기',r['원문링크'],use_container_width=True)
            if not st.session_state.get('show_more') and len(ranked)>9:
                if st.button('검색 결과 더 보기',use_container_width=True):st.session_state['show_more']=True;st.rerun()
            st.markdown('<div class="notice">시설 검색 링크는 외부 지도 검색으로 연결됩니다. 모집 가능 여부는 확인되지 않았습니다. 같은 운동의 다른 시간·센터를 찾으려면 위 검색 조건을 변경해 주세요.</div>',unsafe_allow_html=True)

with tab_insight:
    st.markdown('<div class="section-head">데이터 인사이트</div>',unsafe_allow_html=True)
    st.caption('이 화면은 공개된 기록의 구성과 정보 품질을 분석합니다. 실제 강좌 공급량이나 수강 수요를 보여주지는 않습니다.')
    hist=data[data['데이터출처'].eq(SEOUL_SOURCE)]
    current=data[data['데이터출처'].eq(KSPON_SOURCE)]
    c1,c2,c3=st.columns(3)
    c1.metric('서울시 원본',f'{len(seoul):,}행')
    c2.metric('중복 정리 후 서울시 기록',f'{len(hist):,}건')
    c3.metric('기관 강좌 기록',f'{len(current):,}건')
    st.markdown('<div class="notice">서울시 제공 파일의 명시적인 강좌 기간은 주로 2011년입니다. 이 기록을 2026년 운영 현황으로 해석하면 안 됩니다. '+('기관 강좌 CSV 전체가 연결되어 있습니다.' if full_kspon else '한국체육산업개발 강좌는 현재 기본 예시 일부만 포함되어 있습니다. 전체 CSV를 연결해 주세요.')+'</div>',unsafe_allow_html=True)
    col1,col2=st.columns([1.2,1])
    with col1:
        freq=hist['종목분류'].value_counts().reset_index()
        freq.columns=['종목군','기록 수']
        fig=px.bar(freq,x='종목군',y='기록 수',text_auto=True,
          title='서울시 과거 기록: 운동 분야별 분포',template='plotly_white',color_discrete_sequence=['#2f6848'])
        fig.update_layout(height=380,margin=dict(t=48,b=20,l=10,r=10),xaxis_title='',yaxis_title='기록 수')
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        mapped=(hist['자치구']!='지역 미확인').sum()
        st.metric('구 분류 가능한 과거 기록',f'{mapped:,}건')
        st.metric('구 분류 미확인',f"{(hist['자치구']=='지역 미확인').sum():,}건")
        st.caption('구 정보는 시설명에 나타난 지명과 일부 이름 매핑을 이용한 예비 분류입니다. 주소 원본이 없어 위치가 확정된 것은 아닙니다.')
    st.markdown('#### 데이터 필드 기재율')
    st.dataframe(data_quality(hist),hide_index=True,use_container_width=True)
    st.caption('기재율은 빈칸/NULL 계열 문자열 기준으로 산출합니다. 레벨이 미기재된 강좌도 프로그램명·반명에 초급 등이 표시될 수 있습니다.')
    by_district=hist[hist['자치구'].isin(DISTRICTS)].groupby('자치구').size().sort_values(ascending=False).reset_index(name='기록 수')
    st.markdown('#### 자치구별 기록 수 (시설명 기반 예비 분류)')
    fig2=px.bar(by_district,x='자치구',y='기록 수',template='plotly_white',color_discrete_sequence=['#6b936d'])
    fig2.update_layout(height=370,margin=dict(t=12,b=25,l=10,r=10),xaxis_title='',yaxis_title='기록 수')
    st.plotly_chart(fig2,use_container_width=True)
    st.markdown('**데이터 개선 요청 제안** — 최근 갱신일, 현재 운영 여부, 신청 가능 인원, 참가 대상 연령 하한·상한, 입문 수준, 시설 주소와 자치구를 표준 항목으로 제공할 필요가 있습니다.')

with tab_coverage:
    st.markdown('<div class="section-head">데이터 수록 현황과 미연결 영역</div>',unsafe_allow_html=True)
    st.caption('아래 숫자는 현재 배포된 파일 또는 이번 접속에서 읽은 데이터 기준입니다. 서울시 모든 현재 운영 시설의 숫자가 아닙니다.')
    seoul_raw_rows=len(load_file(DATA/'seoul_programs.csv'))
    a,b,c=st.columns(3)
    a.metric('서울시 과거 프로그램 원본',f'{seoul_raw_rows:,}행')
    b.metric('한국체육산업개발 일정 원본',f'{raw_schedule_count:,}행'+(' · 전체 CSV' if full_kspon else ' · 일부 예시'))
    c.metric('한국체육산업개발 강좌 소개',f'{len(catalog):,}행')
    st.caption(f'일정 원본 {raw_schedule_count:,}행 중 강좌명·요일·시간 등 조합이 중복된 기록을 묶으면 {len(kspon):,}건입니다. 이는 현재 개설된 강좌 수가 아닙니다. 일정 CSV에는 개별 센터명 필드가 없어서 올림픽공원스포츠센터로 예비 분류했습니다. 실제 센터는 공식 안내에서 확인해야 합니다.')
    if location_audit['loaded']:
        x,y,z=st.columns(3)
        x.metric('최신 시설 원본 행',f"{location_audit['rows']:,}건")
        y.metric('시설명·자치구 유효 행',f"{location_audit['names']:,}개")
        z.metric('기존 기록과 시설명 일치',f"{location_audit['matches']:,}개")
        st.caption('일치 수는 정확한 문자열로 연결된 시설 이름만 센 것이며 신규 시설 전체 포함률은 아닙니다. 이름 변경/중복 시설은 추가 대조가 필요합니다.')
    else:
        st.warning('최신 서울시 시설 위치 원본이 아직 없습니다. 자치구는 상당 부분 시설명에서 추정한 값입니다.')
    st.markdown('#### 필요한 공식 데이터')
    requirements=[
      ('한국체육산업개발 강좌 일정 (전체 CSV)',KSPON_SCHEDULE_URL,'연결됨' if full_kspon else '미리보기만 연결'),
      ('한국체육산업개발 강좌 소개 (전체 CSV)',KSPON_CATALOG_URL,'연결됨' if (DATA/'kspon_catalog.csv').exists() or f2 is not None else '미리보기만 연결'),
      ('서울시 생활체육포털 우리동네 프로그램',PROGRAMS_URL,'미연결 · 최신 강좌 확보 필요'),
      ('서울시 공공체육시설 정보',FACILITIES_URL,'파일 연결됨' if location_audit['loaded'] else '미연결 · 정확한 자치구/주소 필요'),
      ('서울시 체육시설 공공서비스예약 정보','https://data.seoul.go.kr/dataList/OA-2266/S/1/datasetView.do','미연결 · 일부 예약정보 및 공식 상세링크'),
      ('서울시 공공체육시설 통계','https://stat.eseoul.go.kr/statHtml/statHtml.do?orgId=201&tblId=DT_201004_O130034_03','미연결 · 시설 모수와 범위 대조'),
    ]
    for label,url,status in requirements:
        st.markdown(f'- **{label}** · {status} · [공식 원본]({url})')
    st.info('필요한 CSV를 추가한 뒤 data 폴더에 저장해 재배포하면, 친구도 별도 업로드 없이 동일한 데이터를 볼 수 있습니다. 단, 서울시 최신 프로그램·예약 원본은 아직 자동 결합하지 않습니다.')

with tab_sources:
    st.markdown('<div class="section-head">운동 추천 근거와 데이터 출처</div>',unsafe_allow_html=True)
    st.markdown('**중요:** 아래 자료는 일반적인 신체활동 권고를 설명합니다. 특정 나이의 사람에게 검도·수영·댄스 중 무엇이 의학적으로 더 적합한지 자동 판정하는 근거가 아닙니다.')
    st.markdown('#### 연령별 권고 가이드')
    st.markdown('''| 연령 | 공식 기준과 서비스 적용 |
|---|---|
| 만 7~17세 | WHO는 5~17세의 규칙적인 중·고강도 신체활동을 권고합니다. 본 서비스는 종목 탐색용이며 미성년자 수강 조건을 별도로 확인합니다. |
| 만 18~64세 | WHO·질병관리청: 주당 중강도 유산소 신체활동 약 150~300분 및 근력운동 주 2일 이상 권고. |
| 만 65세 이상 | 유산소·근력운동에 더해 기능적 균형 능력 강화를 위한 복합 신체활동을 주 3일 이상 권고. |
''')
    st.caption('국민체력100은 성인기 만 19~64세, 어르신 만 65세 이상 등의 체력 측정·평가 체계를 운영합니다. 모두핏은 개인 측정값을 입력받지 않으며 체력 수준을 임의로 추정하지 않습니다.')
    st.markdown('**모두핏 자체 규칙** — 운동 목표와 종목군의 관련성은 사이트 설계상의 분류이며 임상 검증을 거친 개인 처방이 아닙니다. 대상 표시·요일·시간·입문 문구·가격의 일치도만 점수로 계산합니다.')
    refs=[
      ('WHO 신체활동 권고','https://www.who.int/europe/news-room/fact-sheets/item/physical-activity'),
      ('질병관리청 국가건강정보포털 신체활동 안내','https://health.kdca.go.kr/healthinfo/biz/health/gnrlzHealthInfo/gnrlzHealthInfo/gnrlzHealthInfoView.do?cntnts_sn=6251'),
      ('국민체력100 연령별 체력인증 기준','https://nfa.kspo.or.kr/reserve/0/selectMeasureGradeItemListByAgeSe.kspo'),
      ('한국체육산업개발 강좌 일정',KSPON_SCHEDULE_URL),
      ('한국체육산업개발 강좌 소개',KSPON_CATALOG_URL),
      ('서울시 과거 체육시설 프로그램',SEOUL_URL),
      ('서울시 생활체육포털 우리동네 프로그램 (갱신 중)',PROGRAMS_URL),
      ('서울시 공공체육시설 정보 (갱신 중)',FACILITIES_URL),
    ]
    for label,url in refs:
        st.markdown(f'- [{label}]({url})')
    st.markdown('#### 현재 확보한 데이터의 한계')
    st.write('① 서울시 업로드 원본은 14,523행이지만 현재 개설 여부 검증에 적합하지 않습니다. ② 원본 주소·홈페이지·전화번호가 공란이라 지역을 확정하거나 이동 시간을 계산할 수 없습니다. ③ 강좌 정원만으로 잔여석을 구할 수 없습니다. ④ 경기도·인천은 현재 충분한 프로그램 데이터가 없어 서울처럼 전역 탐색을 지원하지 않습니다.')
    st.write('⑤ 한국체육산업개발 데이터는 경진대회 요건을 충족하는 필수 출처입니다. 서울시 데이터는 추가 비교용이며 기관 원본을 실제로 활용한 분석·결과를 기획서에 명확히 제시해야 합니다.')

st.divider()
st.caption(T.FOOTER)
st.caption('MODUFIT V3.2 · Python + Streamlit · 최신 모집 정보가 아닌 공개 기록 기반 탐색 · 데이터 파일 출처 및 기준일은 각 데이터 제공처에서 확인')
