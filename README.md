# 모두핏 V3.2 — 실제 공공데이터 3종 통합, 친구 공유용

이 파일은 **이미 두 개의 한국체육산업개발 전체 CSV를 포함**합니다. 별도로 강좌 CSV를 찾아 이름을 바꿀 필요가 없습니다.

## 데이터가 포함됐나요?

| 파일 | 내용 | 규모 | 현재성 |
|---|---|---:|---|
| `data/seoul_programs.csv` | 서울시 공공 체육시설별 운영프로그램 | 14,523행 | 과거 강좌 기록, 현재 모집 여부 미확인 |
| `data/kspon_schedule.csv` | 한국체육산업개발 올림픽스포츠센터 일정 | 2,137행 | 종료일 9999 표시 포함, 현재 개설·잔여석 미확인 |
| `data/kspon_catalog.csv` | 한국체육산업개발 5개 센터 종목 소개 | 94행 | 소개 자료, 실시간 일정·잔여석 아님 |

**중요:** 일정 CSV의 센터명 열이 없어 화면에서 '올림픽공원스포츠센터'로 표시한 것은 데이터셋 맥락에 기초한 예비 분류입니다. 강좌별 실제 장소는 기관 공식 채널에서 확인해야 합니다. 소개 CSV 94행을 일정 강좌 2,137행에 무조건 연결하지 않으며, 센터·종목명이 고유하게 일치할 때만 설명을 붙입니다.

### 내가 실행하는 방법 (Windows)

1. 압축파일에서 `모두 추출`을 눌러 압축을 풉니다.
2. `app.py` 파일과 `START_MODUFIT.bat`가 보이는 폴더를 엽니다.
3. `START_MODUFIT.bat`를 더블클릭하거나 폴더 주소창에 `cmd`를 적고 Enter, 이어서 `py -m streamlit run app.py`를 실행합니다.
4. 브라우저에서 `http://localhost:8501`에 접속합니다. 검은 창을 닫으면 종료됩니다.

처음 실행 시 라이브러리 설치가 필요하면 `py -m pip install -r requirements.txt`를 먼저 실행합니다.

### 친구에게 Python 설치 없이 공유하는 방법

1. https://github.com/new 에서 `modufit-seoul`이라는 **Public** 저장소를 만듭니다.
2. GitHub 저장소에서 `Add file` → `Upload files`를 선택합니다.
3. 압축을 푼 폴더 안의 **파일과 하위 폴더**를 업로드합니다. `app.py`가 저장소 첫 화면(최상위)에 있어야 합니다. `.env`, API키, 비밀번호를 업로드하면 안 됩니다. 이 배포본은 공공데이터 CSV를 이미 포함합니다.
4. `Commit changes`를 누릅니다.
5. https://share.streamlit.io 에 접속해 GitHub 계정으로 로그인하고 `Create app`을 선택합니다.
6. 저장소 `modufit-seoul`, branch `main`, Main file path `app.py`를 선택하고 `Deploy`를 누릅니다.
7. `*.streamlit.app` 링크가 열리는지 테스트한 뒤 카카오톡으로 친구에게 보냅니다. 친구에게 Python은 필요 없습니다.

**이 압축파일을 만든 것과 실제 인터넷 배포는 다릅니다.** GitHub/Streamlit Cloud에 게시해야 공개 주소가 생깁니다. 무료 서비스는 사용량·휴면에 따른 제약이 있을 수 있습니다.

### 사이트 한글 문구 수정

`EDIT_TEXT.bat`를 더블클릭 → `copytext.py`의 따옴표 안 텍스트 수정 → `Ctrl+S`. 내 PC 화면은 새로고침, 이미 배포했다면 GitHub에서 파일 수정 후 Commit합니다.

### 데이터 추가와 한계

- 최신 서울시 생활체육 프로그램: https://data.seoul.go.kr/dataList/OA-21780/A/1/datasetView.do (아직 미연결)
- 서울시 공공체육시설 위치: https://data.seoul.go.kr/dataList/OA-21779/S/1/datasetView.do (아직 미연결)
- 서울시 공공서비스예약 정보: https://data.seoul.go.kr/dataList/OA-2266/S/1/datasetView.do (아직 미연결)
- 한국체육산업개발 강좌 일정: https://www.data.go.kr/data/15110953/fileData.do
- 한국체육산업개발 종목 소개: https://www.data.go.kr/data/15147992/fileData.do

서울시 14,523행은 현재 운영 시설·강좌 수를 의미하지 않습니다. 한국체육산업개발 2,137행에는 과거 종료 강좌와 기한 미정 기록이 포함됩니다. 가격·정원은 잔여석 정보를 의미하지 않습니다. 실제 현재 모집·운영은 공식 채널에서 재확인해야 합니다. 서울시 구별 주소는 최신 시설원본이 없어서 일부 시설명으로만 추정한 값입니다.

### 자동 검사

```
py CHECK_BEFORE_DEPLOY.py
py -m pip install pytest
py -m pytest tests
```

최신 데이터 적용 및 상세 확인 기준은 `DATA_COVERAGE.md`와 `KSPON_SOURCE_AUDIT.md`를 참고하세요.
