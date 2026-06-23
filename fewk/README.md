# FEWKbooks

**FEWK; Far East White Kingdom** — Universe Setting Project since 2021.10.31 by Universe Designer **WhtDrgon** (Kim Dongeun).

This repository hosts the online reader sample for the **3rd edition** of FEWK — both the Core Rulebook (106 chapters, 15 parts) and the World Book (170 chapters, 12 parts). The site is a single-page vanilla HTML/CSS/JS application, designed to be served statically (GitHub Pages).

---

## 읽어보기 / Read Online

- Live site: `https://whtdrgon.github.io/FEWKbooks/` *(pending deploy)*

## 구조 / Structure

```
FEWKbooks/
├── index.html            # SPA entry (light/dark toggle, search, mailto feedback)
├── content/
│   ├── home.md           # FEWK 소개 · 마스터 연혁
│   ├── roadmap.md        # 출판 이후 로드맵
│   ├── license.md        # FWOL v1.0 전문
│   ├── corerulebook/     # Core Rulebook 3rd (122 files)
│   └── worldbook/        # World Book 3rd (228 files)
├── assets/               # CSS · JS · images
├── scripts/convert.py    # 편집본 → 독자용 샘플 변환기
├── LICENSE               # MIT (code)
└── README.md
```

## 라이선스 / License — 2층 구조

이 리포는 **이중 라이선스**를 적용합니다:

| 대상 | 라이선스 | 파일 |
|---|---|---|
| **코드** (index.html, CSS/JS, scripts/convert.py) | [MIT License](LICENSE) | `LICENSE` |
| **FEWK 세계관 콘텐츠** (`content/` 아래 모든 원고) | FWOL v2.1 (CC BY 4.0 기반) | [content/license.md](content/license.md) |

- **콘텐츠 저작권**: 김동은 Kim Dongeun (활동명 하얀용 / WhtDrgon) 개인
- **상표권**: MEJE Works Corp. ("FEWK", FEWK 로고 일체)
- **공식 관리 주체**: FEWK 거버넌스 (FEWK Governance). 2026-04-25 기준 김동은 단독 구성, 단계적 확장 예정
- **생산 기술**: MEJE Works Corp. 소유의 "세계관 관리 프로세스" 기술 활용

FWOL v2.1부터 **상업 이용이 자유롭게 허용**됩니다 (CC BY 4.0 기반, 로열티 없음). 팬·상업 2차 창작은 "FEWK 세계관 작품 / FEWK Universe Work"로 마크하며, 자세한 조건과 FEWK 브랜드 상표 라이선스 범위는 [content/license.md](content/license.md) 참조. 라이선스 개정 이력은 [[FWOL]/CHANGELOG.md]([FWOL]/CHANGELOG.md).

## 피드백 / Feedback

오탈자·규칙 모순·번역 제안 등은 사이트의 우측 하단 "편집자에게 한마디" 버튼에서 메일로 전송하거나, 직접 **FEWK@meje.kr** 로 보내주세요.

## 로컬 실행 / Run Locally

```bash
cd FEWKbooks
python3 -m http.server 8080
# 브라우저에서 http://localhost:8080/ 열기
```

## 링크 / Links

- Twitter/X: [@whtdrgon](https://x.com/whtdrgon)
- 2022 NFT 콜라보 보도: [머니투데이 기사](https://www.mt.co.kr/stock/2022/07/27/2022072715530622171)
- 2024.6 KEITI편 시범 펀딩: [tumblbug.com/fewkop](https://tumblbug.com/fewkop)

---

© 2021–2026 Kim Dongeun (WhtDrgon). "FEWK" trademark © MEJE Works Corp. Worldbuilding process technology © MEJE Works Corp. Official management: FEWK Governance (FEWK@meje.kr).
