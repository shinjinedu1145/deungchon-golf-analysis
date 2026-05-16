---
title: 등촌골프연습장 사업성 분석
emoji: ⛳
colorFrom: indigo
colorTo: blue
sdk: streamlit
sdk_version: 1.55.0
app_file: app.py
pinned: false
license: mit
---

# 등촌골프연습장 사업성 분석 대시보드

88타석 실외 골프연습장(서울 강서구 등촌동)의 10개년 재무모델링 및 투자의사결정 지원 대시보드입니다.

## 주요 기능
- 5개년/10개년 NPV, IRR, Payback 산출
- 매출 시뮬레이션 (회원수 회복 곡선, 시즌 가중치, 상품 단가 조정)
- 한국회계기준(K-GAAP) 추정손익계산서
- Exit 시나리오 (3,000억 @ 2030 / 3,500억 @ 2035)
- 경영진 보고용 PPT/PDF 출력

## 기술 스택
Streamlit · Plotly · pandas · numpy-financial · reportlab · python-pptx
