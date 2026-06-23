# 13-9. 매크로 사양·YAML 캐릭터시트

---

디지털 플레이를 위한 **표준 매크로 세트**와 **YAML 기반 캐릭터시트**를 제공합니다. 플랫폼 독립적 포맷이므로 Roll20·Foundry·Discord 봇 모두에서 사용 가능합니다.

## 9-A. 표준 매크로 세트

### Grade Die 판정

```
/roll ${stat_grade} + ${skill} + ${modifier} vs TN ${tn}

예:
/roll 5d6! + 3 vs TN 15
(5d6 폭발 + 스킬 3 + TN 15)
```

### d100 저항

```
/roll 1d100 <= ${target}

예:
/roll 1d100 <= 40
(40 이하면 성공)
```

### d6 Pool 소모

```
/roll ${N}d6>4

예:
/roll 10d6>4
(10개 d6, 5+ 개수 = Hit 수)
```

### Initiative

```
/roll ${REF_grade} + ${SEN_grade}

예:
/roll 5d6 + 3d6
```

### 운 토큰 사용

```
/luck ${amount} ${purpose}

예:
/luck 1 reroll
/luck 2 critical
/luck 5 dropout_avoid
```

### 특수 매크로

```
/ace ${n}d${d}  → Ace 폭발 주사위
/fumble ${n}d${d}  → Fumble 체크 (모두 1인지)
/opposed ${att1} vs ${att2}  → 대립 판정
```

## 9-B. YAML 캐릭터시트 포맷

### 기본 구조

```yaml
character:
  name: 민
  player: 지우
  preset: G-4 네트워크
  created: 2026-04-01
  
stats:
  BOD: 5
  REF: 7
  INT: 9
  SEN: 6
  PRE: 4
  LCK: 5
  
derived:
  HP: 25
  HP_max: 25
  ego: 8
  ego_max: 8
  ego_resist: 2
  DSR: 4
  DSR_max: 12
  luck_tokens: 7
  luck_max: 10
  d6_pool: 5
  d6_pool_max: 12
  initiative_grade: "5d8 + 4d6"
  
skills:
  hacking: 5
  stealth: 3
  investigation: 3
  social: 1
  perception: 2
  
tags:
  body: "감각 예리"
  personality: "호기심"
  background: "서민구 출신"
  runner: ["해커 전담", "C급 러너"]
  
interactions:
  power:
    name: "영감 번뜩임"
    level: 1
  skill:
    name: "해킹 심화"
    level: 2
  function:
    name: "뇌네 인터페이스"
    level: 3
    bp_cost: -15
    
bp: 70
  
tracks:
  shining: 0
  matting: 2
  paradox: 1
  ego_track: 0
  corporeal: "locked"
  
heat:
  corp_sinseong: 4
  corp_pekkeures: 1
  peacemaker: 0
  
bonds:
  - target: "하얀 (여동생)"
    category: "family"
    value: 5
    note: "아픈 여동생"
  - target: "페이 (브로커)"
    category: "ally"
    value: 3
    note: "첫 의뢰 인"
  - target: "빅터 (갱단 두목)"
    category: "rival"
    value: -4
    note: "3년 전 동료 살해"
    
equipment:
  weapons:
    - "여우 S건 (1d8+2)"
    - "은닉형 권총"
  armor: "경장 갑옷 (+1)"
  implants:
    - "뇌네 인터페이스 Lv 3 (-15% BP)"
  tools:
    - "뉴로덱 (고급)"
    - "흑공앰플 × 1"
  vehicles:
    - "리브 스트레이트"
    
wealth:
  cash: 25 oyt
  credit: 5000 cr
  debt: 0
  
trauma:
  - "사회 트라우마 (페이 관련)"
  
notes: |
  민은 서민구 출신 해커.
  여동생 하얀의 의료비를 위해 러닝 중.
  페이의 남편 실종 사건이 계속 마음에 걸림.
```

## 9-C. 매크로 ↔ 시트 연동

### 동적 참조

YAML 시트에 저장된 값을 매크로가 참조:

```
Roll20 예시:
/roll @{민|REF_grade} + @{민|skill_shooting} vs TN 15

Foundry 예시:
/roll @character.stats.REF_grade + @character.skills.shooting
```

### 자동 갱신

- 운 토큰 사용 시 시트 자동 차감
- HP 변화 자동 반영
- 트랙 증가 자동 기록

## 9-D. YAML의 장점

- **플랫폼 독립**: 어느 툴에서든 읽기 쉬움
- **사람이 읽을 수 있음**: 디버깅·수동 편집 용이
- **버전 관리**: Git 등으로 관리 가능
- **AI 친화**: AI가 파싱·생성 쉬움

## 9-E. YAML 편집 도구

- **VS Code + YAML 플러그인**: 문법 검사
- **Notion·Obsidian**: YAML front matter
- **전용 시트 제너레이터** (계획 중)

## 9-F. 시트 업데이트 프로세스

```
세션 전: 시트 최신 상태 확인
세션 중: 매크로가 자동 갱신
세션 후: GM이 트랙·트라우마 수동 갱신
매달: 전체 시트 백업
```

---

## 관련

- 이전: [08. Roll20·Foundry 세팅](08_Roll20_Foundry.md)
- 다음: [10. AI 병행 플레이](10_AI_병행.md)
- 연동: [부록 A. 캐릭터 시트](../14_부록/A_캐릭터시트.md)
