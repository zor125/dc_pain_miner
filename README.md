# 🚀 DC Pain Miner

디시인사이드 게시글을 크롤링하여
**고통 신호(창업 아이디어, 문제, 불편함)**를 자동으로 추출하는 데이터 분석 프로젝트

---

## 🔥 프로젝트 목적

사람들은 이미 문제를 말하고 있다.
단지 **그걸 구조적으로 수집하고 해석하지 않을 뿐이다.**

이 프로젝트는
👉 디시 커뮤니티의 “불만 / 고통 / 문제”를 수집하고
👉 데이터 기반으로 정리하여
👉 **사업 아이디어로 변환**하는 것을 목표로 한다.

---

## ⚙️ 주요 기능

### 1️⃣ 크롤링

* 디시인사이드 특정 갤러리 글 수집
* 최신 글 기준 자동 수집

### 2️⃣ 고통 신호 분석

* 키워드 기반 점수화 (`e_score`)
* 문제/불만 글 필터링

### 3️⃣ 클러스터링

* 유사한 문제끼리 그룹화
* 반복되는 패턴 탐지

### 4️⃣ 대시보드 (Streamlit)

* 설정값 기반 실시간 분석
* 신호 / 클러스터 / 대표 글 시각화

---

## 🧠 시스템 구조

```text
[DCInside]
    ↓ (crawl_dc.py)
[Raw Data]
    ↓ (e_score.py)
[Scored Data]
    ↓ (db.py)
[SQLite DB]
    ↓ (aggregate.py)
[Signal / Cluster]
    ↓ (dashboard.py)
[Streamlit UI]
```

---

## 📂 프로젝트 구조

```text
dc_pain_miner/
│
├── src/
│   ├── dashboard.py      # Streamlit UI
│   ├── aggregate.py      # 신호/클러스터 생성
│   ├── pipeline.py       # 전체 실행 흐름
│   ├── crawl_dc.py       # 디시 크롤링
│   ├── db.py             # DB 저장/조회
│   ├── e_score.py        # 고통 점수 계산
│   ├── report.py         # 리포트 생성
│   └── rules_v1.py       # 키워드 룰셋
│
├── data/                 # SQLite DB 및 결과 저장
├── scripts/              # 자동 실행 스크립트
├── .gitignore
└── README.md
```

---

## 🚀 실행 방법

### 1️⃣ 환경 준비

```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
pip install -r requirements.txt
```

---

### 2️⃣ 데이터 수집 (필수)

```bash
python -m src.pipeline
```

👉 디시 글 크롤링 + 점수 계산 + DB 저장

---

### 3️⃣ 대시보드 실행

```bash
streamlit run src/dashboard.py
```

👉 브라우저에서 분석 결과 확인

---

## ⚠️ 주의사항

* DB가 없으면 대시보드에 데이터가 표시되지 않음
* 반드시 먼저 `pipeline.py` 실행 필요
* `.gitignore`에 DB 파일 포함 (GitHub 업로드 금지)

---

## 💡 향후 발전 방향

* 실시간 크롤링 (버튼 기반 실행)
* 자동 트렌드 추출
* AI 기반 요약 / 인사이트 생성
* SaaS 형태 서비스화

---

## 🧠 핵심 아이디어

> “사람들이 불편을 말하는 곳 = 돈이 만들어지는 곳”

이 프로젝트는
단순한 크롤러가 아니라
👉 **문제 → 데이터 → 기회로 변환하는 엔진**이다.

---

## 📌 Author

* GitHub: https://github.com/zor125
* Project: DC Pain Miner

---
