# 다나와 단위가격/옵션 정보 크롤러
Python Playwright 기반의 단위 가격/옵션 정보 자동 수집 크롤러

## Overview

본 크롤러는 Playwright(Python) 기반으로 구현되었으며,
다나와 카테고리 페이지에서 상품 목록 → 개별 상품 페이지로 진입하여
아래 항목을 자동으로 수집합니다.

- 상품명 (product_title)
- 제목 내부 용량 정보(capacity)
- 옵션명(option_spec)
- 옵션 가격(price)
- 단위 가격(unit_price)
- 옵션 pcode
- 상세 페이지 URL(detail_url, 수정 예정)

수집된 데이터는 `CSV` 형식으로 저장됩니다.

## 1. 기능 개요

### 1) 카테고리 페이지 크롤링
- 지정된 카테고리 URL을 기준으로 상품 URL을 모두 수집
- 페이지네이션(`a.num`) 자동 이동

### 2) 상세 페이지 크롤링
상품 상세 페이지에서 **옵션 리스트를 정규식 기반 파싱**하여 구조화된 데이터로 저장합니다.

### 3) 용량 자동 인식
상품 제목에서 아래 패턴을 탐지합니다:

- `300g`, `800ml`
- `70매`, `1개`, `10입`, `2팩`
- `70매 x 10개` 묶음형 패턴

### 4) 단위 가격 자동 파싱
예: `"1,000원/10g"` → `{"unit_price": 1000, "unit_value": 10, "unit_type": "g"}`

---

## 주의 사항

다나와는 자동 크롤링 탐지 및 차단 정책을 운영합니다.  
본 프로젝트는 다음과 같은 보호 로직을 포함합니다:

- 페이지 이동 / 상세 페이지 진입 시 `0.8초` 지연 삽입
- DOM 안정화 대기 (`domcontentloaded`)

> **주의:**  
> 고속 크롤링 또는 대량 요청 시 IP 차단이 발생할 수 있습니다.  
> 사이트 내의 robot.txt를 참고하시길 바랍니다.

---

## 설치 및 실행 환경

### Python Version  
- Python **3.10 이상** 권장

### Installation

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install

### requirements.txt

```txt
playwright==1.48.0
pandas==2.2.3
python-dateutil==2.9.0.post0
