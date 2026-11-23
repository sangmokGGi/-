import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import (load_file,normalize_seoul,normalize_kspon,DATA,parse_days,determine_district,
                   classify_age,level_status,rank_classes,data_quality,augment_locations)
import pandas as pd

def test_source_record_counts():
    raw=load_file(DATA/'seoul_programs.csv')
    assert len(raw)==14523
    assert raw['시설명'].nunique()>200
    assert '주소' in raw.columns

def test_cleaned_history_and_origin():
    raw=load_file(DATA/'seoul_programs.csv')
    d=normalize_seoul(raw)
    assert len(d)<=14523 and len(d)>10000
    assert d['권역'].eq('서울').all()
    assert d['기록상태'].eq('과거 공개 기록').all()
    assert d['신청링크'].map(lambda x:x=='' or x.startswith('http')).all()

def test_day_parsing():
    assert parse_days('월화수목금')==set('월화수목금')
    assert parse_days('화목')=={'화','목'}
    assert parse_days('토일')=={'토','일'}
    assert not parse_days('1개월')
    assert {'월','화','수','목','금'}.issubset(parse_days('평일'))

def test_age_conservative():
    assert classify_age('어린이',45)=='대상 불일치'
    assert classify_age('성인',45)=='범위 일치'
    assert classify_age('',45)=='대상 미확인'
    assert classify_age('성인',70)=='대상 미확인'
    assert classify_age('어르신',70)=='범위 일치'

def test_region_not_invented():
    assert determine_district('창동문화체육센터')=='도봉구'
    assert determine_district('종로문화체육센터')=='종로구'
    assert determine_district('미확인 시설')=='지역 미확인'

def test_level():
    assert level_status('수영 고급')=='경험자'
    assert level_status('탁구 기초')=='입문'
    assert level_status('배드민턴')=='수준 미확인'

def test_kspon_not_marked_available():
    d=normalize_kspon(load_file(DATA/'kspon_schedule_preview.csv'))
    assert len(d)>0
    assert d['기록상태'].eq('운영·잔여석 미확인').all()
    assert (d['권역']=='서울').any()

def test_filter_region_day_price():
    d=normalize_seoul(load_file(DATA/'seoul_programs.csv'))
    results=rank_classes(d,age=45,region='서울',district='서울 전체',goal='새로운 종목 배우기',
                         day='평일',time='오전 (06~12시)',category='라켓 운동',experience='입문',max_price=100000)
    assert len(results)>0
    assert results['종목분류'].eq('라켓 운동').all()
    assert results['연령판정'].ne('대상 불일치').all()
    assert results['가격'].le(100000).all()
    assert results['시작시각'].between(6,11).all()

def test_district_exact_only():
    d=normalize_seoul(load_file(DATA/'seoul_programs.csv'))
    results=rank_classes(d,age=45,region='서울',district='강남구',day='평일')
    assert results['자치구'].eq('강남구').all()
    assert len(results)>0

def test_location_update_exact():
    d=normalize_seoul(load_file(DATA/'seoul_programs.csv'))
    l=pd.DataFrame([{'시설명':'창동문화체육센터','자치구':'도봉구','주소':'테스트 주소'}])
    updated=augment_locations(d,l)
    sub=updated[updated['시설명']=='창동문화체육센터']
    assert sub['주소'].eq('테스트 주소').all()


def test_full_kspon_upload_correct_headers_and_counts():
    raw_schedule=load_file(DATA/'kspon_schedule.csv')
    raw_catalog=load_file(DATA/'kspon_catalog.csv')
    assert len(raw_schedule)==2137
    assert len(raw_catalog)==94
    assert {'강좌일련번호','수강요일','수강금액','수강시작일'}.issubset(raw_schedule.columns)
    assert {'스포츠센터','강좌명','강좌설명','링크주소'}.issubset(raw_catalog.columns)

def test_kspon_catalog_does_not_cross_centers():
    from engine import add_kspon_descriptions, KSPON_SOURCE
    orig=normalize_kspon(load_file(DATA/'kspon_schedule.csv'))
    catalog=load_file(DATA/'kspon_catalog.csv')
    result=add_kspon_descriptions(orig,catalog)
    assert len(result)==len(orig)
    assert result['데이터출처'].eq(KSPON_SOURCE).all()
    # Linked course pages must belong to the matching Olympics sports center, not Ilsan/Bundang.
    valid=set(catalog.loc[catalog['스포츠센터'].eq('올림픽공원스포츠센터'),'링크주소'])
    assert set(result.loc[result['신청링크'].ne(''),'신청링크']).issubset(valid)

def test_unknown_seats_not_inferred_from_capacity():
    d=normalize_kspon(load_file(DATA/'kspon_schedule.csv'))
    assert '잔여석' not in d.columns
    assert d['기록상태'].eq('운영·잔여석 미확인').all()
