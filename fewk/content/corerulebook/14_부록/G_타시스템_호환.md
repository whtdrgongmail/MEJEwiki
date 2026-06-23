# 부록 G. 타 시스템 호환 가이드

> FEWK 세계관을 D&D 5e·Pathfinder·PbtA 계열·Lasers & Feelings·Mörk Borg·Mothership에서 운영하는 변환 가이드. 본 부록은 D&D 5e부터 시작하며, 다른 시스템 변환은 분기별 확장 예정.

---

FEWK 세계관은 룰과 분리해서 가져갈 수 있습니다. FWOL v2.1 (CC BY 4.0) 라이선스에 따라 다른 시스템에서의 활용을 환영하며, 본 부록은 그 변환을 GM에게 가이드합니다.

세계관과 룰의 결합도가 가장 강한 항목 — 흑공·신기·차원 이동·BP%·인과율 — 은 어떤 시스템으로 옮기든 그 시스템의 자연스러운 어휘로 다시 짜야 합니다. 본 가이드는 *수치 변환표*를 제공하지만, 톤은 GM이 다시 지어야 합니다.

> **원칙**: 수치는 옮길 수 있어도, 톤은 다시 짓는다.

## G-1. D&D 5e 변환

D&D 5e는 가장 보편적인 시스템이고 변환 수요가 가장 큽니다. FEWK Core Rulebook을 쓰지 않아도 D&D 5e 룰로 FEWK 세계관을 굴릴 수 있도록 핵심 메커니즘 매핑.

### G-1.1 판정 변환 — Grade Die ↔ d20

FEWK Grade Die의 핵심은 *Tier별 다이스 수*입니다. D&D는 d20 + 모디파이어. 두 체계의 변환:

| FEWK 스탯 (1~20+) | FEWK Grade | D&D 5e 모디파이어 | D&D 5e 능력치 |
|:---:|:---:|:---:|:---:|
| 1~4 | 1~4d4 | -1 | 8 |
| 5~8 | 3~6d6 | +0~+1 | 10~12 |
| 9~12 | 5~8d8 | +2~+3 | 14~16 |
| 13~16 | 7~10d10 | +4~+5 | 18~20 |
| 17~20 | 9~12d12 | +5~+6 | 20~22 |
| 21+ | 8d20+ | +6~+7 | 22+ |

FEWK 6 Prime Stats (BOD·REF·INT·SEN·PRE·LCK)는 D&D 6 능력치와 다음으로 매핑:

- **BOD** ↔ Constitution (체력·내구의 단일 능력치). Strength는 PC 빌드 시 자유 선택 (전사형은 BOD와 동일치, 다른 빌드는 별도 배분)
- **REF** ↔ Dexterity
- **INT** ↔ Intelligence
- **SEN** ↔ Wisdom (감지·통찰)
- **PRE** ↔ Charisma
- **LCK** ↔ D&D 5e엔 없음. *영감(Inspiration) 토큰*으로 대체 (LCK Tier당 영감 1)

### G-1.2 판정 결과 — Margin ↔ DC 차이

FEWK는 *차이값*으로 결과를 4단 분류 (실패·근소실패·Partial·Full·Great·Critical). D&D는 *DC 도달 여부*로 단순 분류. 호환:

- 굴림 = DC : Partial 성공 (성공이지만 대가)
- 굴림 = DC + 5 : Full 성공
- 굴림 = DC + 10 : Great
- 굴림 = DC + 20 : Critical
- 굴림 = DC - 5 : 근소 실패 (대가 동반)
- 굴림 ≤ DC - 10 : 대실패

FEWK의 **Position × Effect 매트릭스**는 D&D 5e의 **DC + Advantage/Disadvantage** 조합으로 표현 가능. Risky Position = Disadvantage. Desperate = Disadvantage + 실패 시 추가 대가. Controlled = Advantage.

### G-1.3 흑공·신기 — 마법 학파로

D&D 5e의 마법 학파 8종에 두 학파를 추가하거나 기존 학파를 재배치:

- **흑공 마법 (Black-Smoke)** — 새 학파. 환영(Illusion) + 변환(Transmutation)의 결합. 사용자의 의지를 형상화. 10단계 농도 룰은 *주문 슬롯 단계*로 표현 (1단계 슬롯 = 농도 1).
- **신기 마법 (White-Light)** — 새 학파. 신성(Divinity) + 보호(Abjuration). 신단(Shrine) 30m 반경 내에서만 시전. 신단은 *Sacred Site* 마법 위치로 처리.

또는 **흑공 = Wild Magic Sorcerer 변종, 신기 = Cleric 변종**으로 단순화 가능.

### G-1.4 차원 이동·코핀 — 새 메커니즘

D&D의 Plane Shift 주문을 *FEWK 코핀 시스템*으로 재구성:

- **혼백만 이동** — Plane Shift의 변종. 육체는 본 차원에 남고, 의식만 목적 차원의 *new body*로 이동.
- **차원별 비용** — Plane Shift 시 *바이트 비용*을 GP·시간·물질 component로 환산
- **광전** — 마법 화폐. 1 광전 = 100 GP 가치 + 1회용 Plane Shift 매개체
- **드랍아웃** — 차원 이동 실패 시 PC 영구 비활성화 (D&D 5e의 *True Death* 처리)

### G-1.5 BP% (생체순도) — 새 능력치

D&D 5e에 *BP%* 변종 룰 추가:

- 신규 PC는 BP% 100으로 시작
- 사이버 임플란트 1개 장착마다 BP% -5
- BP% 50 미만 시 신단 신기 이용 불가
- BP% 25 미만 시 4대 신수 인지 불가
- BP% 0 시 *변형인간*으로 분류 (D&D 5e의 *Construct* 종족 변종)

### G-1.6 트라우마·자원 — Inspiration·Hit Point 변종

- **트라우마 트랙** — D&D의 Exhaustion 6단계와 호환. FEWK 트라우마 4종은 정신·신체·관계·신앙으로 분리하면 더 정밀
- **운 토큰** — Inspiration 다회 사용 가능 변종 (LCK Tier당 1)
- **에고** — Sanity 변종 (Volo·Curse of Strahd의 Sanity 룰 응용)
- **DSR (장르 자원)** — Hero Point 변종 (Pathfinder 2e의 Hero Point와 더 가까움)

### G-1.7 D&D 5e 변환 시 잃는 것·얻는 것

**잃는 것**:
- FEWK Grade Die의 폭발 주사위 드라마성
- Position × Effect의 정밀 위치 운영
- 트랙 4종의 누적 압력감
- 인과율·먹개비의 메타 회계 시스템

**얻는 것**:
- 광범위한 D&D 5e 캠페인 도구·서드파티 자료
- D&D 5e 익숙한 플레이어의 즉시 합류
- Roll20·Foundry의 풍부한 D&D 5e 자동화

> 🎯 **GM 팁** — D&D 5e로 FEWK를 굴릴 때 *모든 것을 옮기지 마십시오*. 핵심 5가지 (흑공·신기·코핀·BP%·러너 직업)만 옮기고 나머지(트라우마·DSR·시간도보 등)는 첫 캠페인에서 생략하셔도 됩니다. 익숙해진 후 한두 개씩 추가.

## G-2. PbtA 계열 변환 (Apocalypse World·Heart·Blades 호환)

PbtA(Powered by the Apocalypse) 계열은 *6+/7-9/10+* 의 3단 결과가 표준. FEWK Position × Effect와 자연스럽게 맵핑.

### G-2.1 판정

- 2d6 + 모디파이어
- 6 이하: Miss (실패 + 대가)
- 7-9: Mixed (성공 + 대가)
- 10+: Strong (성공)

이는 FEWK의 Partial / Full / Critical과 사실상 동일 구조.

### G-2.2 Move 형식으로 흑공·신기

PbtA의 Move 형식에 FEWK 핵심을 표현:

```
**흑공에 노출되어 의지를 발현하다**

흑공이 가까이에 분출하면, +SEN 또는 +PRE 굴려.
- 10+: 의지를 통제. 흑공이 *원하는 형상*으로 발현. Effect 1
- 7-9: 의지가 새어나감. 흑공이 *PC가 두려워하는 것*으로 발현
- 6-: 흑공이 *예측 못 한 것*으로 발현. GM이 결정
```

```
**신단 신기를 이용하다**

신단 30m 안에서, +PRE 또는 +SEN 굴려.
- 10+: 신기 한 효과 정확히 발현
- 7-9: 신기 발현되지만 신단이 *흠결*을 입음
- 6-: 신기 폭주. GM이 결과 결정
```

### G-2.3 추천 PbtA 베이스

- **Apocalypse World** — 거친 미래 사회 톤. FEWK 노마드·서민구 톤에 잘 맞음
- **Blades in the Dark** — Position × Effect가 사실상 FEWK와 동일. 러너 캠페인에 가장 자연스러움. **추천 1순위**
- **Heart: The City Beneath** — 차원 하강 + 시적 운명 톤. FEWK의 차원 이동·드랍아웃에 잘 맞음
- **The Sprawl** — 사이버펑크 PbtA. 가장 직접 호환

### G-2.4 Blades in the Dark 변환 (가장 자연스러운 호환)

FEWK는 Blades와 매우 유사한 메커니즘. 거의 직접 호환:

| FEWK | Blades |
|---|---|
| Grade Die + 스킬 | Action rating dice |
| Position × Effect | Position × Effect (동일) |
| DSR (장르 자원) | Stress |
| 트라우마 트랙 | Trauma (4 = 은퇴) |
| 러너 길드 | Crew |
| 차원 이동 | Heist target locations |
| 흑공 노출 | Devil's Bargain 변종 |

**Blades in the Dark 룰북 그대로 사용 + FEWK 세계관**. 가장 가벼운 변환. 러너 캠페인 운영에 추천.

## G-3. Lasers & Feelings 변환 (1페이지 미니멀)

세상에서 가장 짧은 TRPG 시스템 중 하나. FEWK를 한 페이지로 압축한 미니멀 변종:

```
=== FEWK Lasers & Feelings ===

캐릭터: 이름 / 직업 / 한 줄 동기
스탯: Lasers (논리·기술·차원) ↔ Feelings (의지·신기·인간)
2~5 사이의 숫자 1개. 낮으면 Lasers 유리, 높으면 Feelings 유리.

판정: d6 굴림. Lasers 행동이면 숫자 *미만* 성공. Feelings 행동이면 숫자 *초과* 성공.
정확히 같으면: Laser Feeling — 추가 정보 + 결정권.

여분 d6: 성공 시 추가 효과. 실패 시 추가 대가.

흑공: 모든 PC가 흑공에 노출되면, GM이 한 PC의 두려움을 묻고 그것이 발현.
신기: 신단 30m 안에서, Feelings 굴림 자동 +1 (낮은 숫자에 유리하게).
드랍아웃: 한 세션 결정적 실패 시 PC 사망. 다음 세션 새 PC.

=== 끝 ===
```

한 페이지 안에 FEWK가 들어옵니다. 첫 세션 운영용·시범용으로 적합.

## G-4. Mörk Borg / Mothership 호환 (OSR·호러)

### Mörk Borg

종말론·죽음·다크 판타지 톤. FEWK의 *흑공의 종말론적 무게*와 잘 맞음:

- Mörk Borg의 *Misery* 메커니즘 = FEWK 패러독스 누적
- Mörk Borg의 *Death* 통계 = FEWK의 드랍아웃·진사
- 색채·디자인 톤 — FEWK 1판의 검은 표지와 친화

### Mothership

우주 호러·고립된 환경 게임. FEWK의 *차원 이동의 고립감*과 호환:

- Mothership *Stress·Panic* 시스템 = FEWK 트라우마 + 에고 통합
- Mothership *Death Save* = FEWK 드랍아웃 회피 굴림
- 차원 균열 = Mothership의 우주 비행 환경 호러

## G-5. 시스템 호환의 일반 원칙

### 옮길 때 고려할 다섯 가지

1. **수치보다 톤**: 수치는 어떤 시스템이든 환산 가능하지만, 톤은 시스템마다 다르게 짜야 함
2. **모든 것을 옮기지 마라**: 핵심 3~5개만 옮기고 나머지는 첫 캠페인에서 생략
3. **시스템의 강점 활용**: D&D는 풍부한 보충 자료, PbtA는 서사 유연성, OSR은 죽음의 무게 — 그 시스템이 잘하는 것을 FEWK에 더하기
4. **캐논은 변하지 않는다**: 세계관 캐논(흑공·신기·4대 신수·인과율)은 어떤 시스템에서도 그대로. 게임 메커니즘만 시스템에 맞게 변환
5. **잃는 것을 인정**: 변환은 항상 무언가를 잃습니다. 잃는 것을 GM이 의식적으로 받아들이고 캠페인 톤에 보상

### 라이선스

본 가이드를 따라 다른 시스템에서 FEWK 세계관을 운영한 결과물은 **FEWK 세계관 작품**(FEWK Universe Work)으로 마크하시면 됩니다. CC BY 4.0 + FEWK 거버넌스 가이드라인. 자세한 내용은 [라이선스 페이지](#license).

타 시스템 자체의 SRD/라이선스(D&D 5e SRD CC BY 4.0, PbtA license, OGL 등)는 별도 준수.

## G-6. Pathfinder 2e 변환

PF2e의 4단계 성공(Critical Success / Success / Failure / Critical Failure)은 FEWK Position × Effect와 자연스럽게 호환됩니다. PF2e의 정밀한 액션 경제도 FEWK 전투에 깊이를 더할 수 있습니다.

### G-6.1 판정

PF2e: d20 + 모디파이어 vs DC. 4단계 결과:

- DC + 10 이상: Critical Success
- DC ~ DC+9: Success
- DC - 9 ~ DC - 1: Failure
- DC - 10 이하: Critical Failure

FEWK Margin과 직접 매핑:
- Critical Success ↔ Critical (차이값 +20)
- Success ↔ Full (차이값 +5~9)
- Failure ↔ 근소 실패
- Critical Failure ↔ 대실패 (펌블 포함)

### G-6.2 Position × Effect 호환

PF2e의 *MAP (Multiple Attack Penalty)* 와 *Conditions* 시스템이 FEWK Position을 정밀하게 표현. Risky = -2 상황 모디파이어, Desperate = -5 + Critical Failure 시 추가 대가.

### G-6.3 종족·클래스 → FEWK 직업

- 수호사 ↔ Champion (Paladin 변종)
- 신사 ↔ Cleric (Domain: Fate·Truth·Light)
- 흑사 ↔ Sorcerer (Bloodline: Aberrant)
- 현물제조사 ↔ Alchemist (Bomber + Mutagenist)
- 러너 ↔ Rogue (Racket: Mastermind·Scoundrel)

### G-6.4 추천: PF2e Free Archetype 룰 활용

FEWK는 PC가 *여러 직업을 거치는* 톤이 강합니다. PF2e의 Free Archetype 옵션 룰로 PC가 두 번째 직업(예: 수호사 + 야전교수)을 가질 수 있게 하면 FEWK 톤이 더 살아납니다.

## G-7. Cypher System 변환 (Numenera·The Strange)

Monte Cook의 Cypher System은 *추상화된 차원 이동·이상 사물*을 다루는 데 강합니다. FEWK의 차원·코핀과 메커니즘적으로 잘 어울립니다.

### G-7.1 판정

Cypher: d20 vs Difficulty (1~10). PC가 Effort·Asset·Skill로 Difficulty를 낮춤. FEWK의 *수정치 합산* 구조와 직결.

- Difficulty 1 (DC 3) ↔ FEWK TN 5
- Difficulty 4 (DC 12) ↔ FEWK TN 25
- Difficulty 7 (DC 21) ↔ FEWK TN 60
- Difficulty 10 (DC 30) ↔ FEWK TN 100

### G-7.2 Pool 시스템 — FEWK 자원과 호환

Cypher PC는 Might·Speed·Intellect 3 Pool. FEWK 자원으로:
- Might Pool ↔ HP + d6 Pool
- Speed Pool ↔ DSR (장르 자원)
- Intellect Pool ↔ 에고

### G-7.3 Cyphers (일회용 이상 사물) ↔ FEWK 광전·돌칩·신단칩

Cypher 시스템의 핵심 — 일회용 마법 도구(Cypher) — 가 FEWK의 광전·돌칩·신단칩과 완벽 호환:
- Cypher = 광전 (한 번 쓰고 사라지는 차원 이동 매개)
- Cypher = 돌칩 (한 번의 신기 효과)
- Cypher = 신단칩 (저장된 신기)

PC는 *언제 어느 Cypher를 쓸지*를 결정 — FEWK 자원 운영 톤과 정확히 일치.

### G-7.4 차원 — The Strange가 FEWK에 가장 가까움

Cypher System의 자매 게임 *The Strange*는 다중 차원 횡단을 다룹니다. FEWK의 차원 이동 톤에 가장 직접 호환.

## G-8. Genesys 변환 (Fantasy Flight)

Genesys는 Star Wars: Edge of the Empire의 시스템을 일반화한 *narrative dice* 시스템. 결과가 *성공/실패 + 부수 효과* 다층으로 나오는 점이 FEWK의 Position × Effect와 잘 맞습니다.

### G-8.1 Narrative Dice

Genesys: 6 종류 다이스(Boost·Setback·Ability·Difficulty·Proficiency·Challenge). 결과는 Success/Failure × Advantage/Threat × Triumph/Despair의 3축.

FEWK의 결과 해석에 매핑:
- Success + Advantage ↔ Full + 좋은 부수 효과
- Success + Threat ↔ Partial (성공 + 대가)
- Failure + Advantage ↔ 실패하지만 부수 이득
- Failure + Threat ↔ 대실패
- Triumph ↔ Critical (Ace 폭발)
- Despair ↔ Fumble

### G-8.2 흑공 ↔ Setback Dice

흑공 노출의 효과를 Genesys의 Setback dice로 표현. 농도 1단계마다 Setback 1개 추가. PC가 농도 6단계 환경에서 판정하면 6개 Setback dice 추가.

### G-8.3 추천: Shadow of the Beanstalk Setting Pack

Genesys의 사이버펑크 세팅 팩 *Shadow of the Beanstalk*가 FEWK 톤과 가장 가까움. 그 룰을 그대로 사용하고 세계관만 FEWK로 교체.

## G-9. Call of Cthulhu 7e 변환

CoC 7e의 *Sanity 시스템*과 *Pulp 옵션 룰*이 FEWK의 흑공 호러·트라우마와 호환됩니다.

### G-9.1 판정 — d100 직접 호환

CoC: d100 vs Skill. FEWK의 d100 판정과 직접 호환.
- Skill 50 = TN 50
- Hard Success (Skill / 2) ↔ Full
- Extreme Success (Skill / 5) ↔ Critical

### G-9.2 Sanity ↔ FEWK 에고 + 트라우마

CoC Sanity는 FEWK 에고 + 트라우마 트랙의 직접 변환:
- Starting Sanity (POW × 5) ↔ FEWK 에고 (PRE × 2)
- Sanity Loss → 에고 감소 + 해당 트라우마 +1
- Indefinite Insanity ↔ FEWK 트라우마 임계 도달
- Permanent Insanity ↔ 진사 (Permanent Removal)

### G-9.3 흑공 ↔ Mythos Encounter

CoC의 *Mythos Encounter* 시스템이 흑공 분출에 직접 매핑. 흑공 농도별 Sanity Loss 표 (**예시 변환값** — FEWK 본 룰북엔 다른 메커니즘. CoC 호환용 가이드라인이며, GM 자유 조정):

| 흑공 농도 | Sanity Loss (예시) |
|:---:|:---:|
| 1~3 (저) | 0/1d3 |
| 4~6 (중) | 1/1d6 |
| 7~9 (고) | 1d4/2d6 |
| 10 (극한) | 1d6/2d10 |
| 신단출 (역사 사건) | 1d10/3d10 |

### G-9.4 추천: Pulp Cthulhu 옵션 룰

CoC 7e의 *Pulp Cthulhu* 옵션이 FEWK 톤과 더 가깝습니다. PC가 *액션 영웅*에 더 가까워 — FEWK 러너의 톤과 직결.

## G-10. 향후 확장

본 v2부터 D&D 5e + PbtA + L&F + Mörk Borg/Mothership + Pathfinder 2e + Cypher + Genesys + CoC 7e의 8 시스템 변환 가이드 제공. 향후 추가 후보:

- **Free League 시스템** — Forbidden Lands·Mutant Year Zero·Vaesen
- **OSR 일반** — Knave·Old-School Essentials
- **Forged in the Dark** — Blades 외 Scum & Villainy 등
- **Powered by the Apocalypse 다른 변종** — Monsterhearts·Masks·Avatar Legends

마스터 또는 거버넌스가 시스템별 전문가 협업을 통해 분기별 추가.

---

## 관련 항목

- 다음 부록: [H. BGM·플레이리스트 가이드](H_BGM_플레이리스트.md)
- 라이선스: [FWOL v2.1](#license) — CC BY 4.0 + FEWK 거버넌스
- World Book 참조: [부록 E](E_WorldBook_참조가이드.md)
- FEWK Core Rulebook 핵심 공식: [부록 B 치트 시트](B_치트시트.md)
