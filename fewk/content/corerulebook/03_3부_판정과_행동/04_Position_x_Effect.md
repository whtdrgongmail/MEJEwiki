# 03-4. Position × Effect

---

TN은 "얼마나 어려운가"를 묻고, 차이값은 "얼마나 잘됐는가"를 답합니다. 여기에 두 축이 더 붙습니다. 실패했을 때 대가가 얼마나 큰가(**Position**), 성공했을 때 결실이 얼마나 큰가(**Effect**). 두 축이 결합해 3×3 매트릭스가 만들어집니다.

## 4-A. Position — 실패 대가의 크기

### 3 단계

| Position | 설명 | 실패·Partial 대가 |
|---|---|---|
| **Controlled** | PC가 상황을 통제 중 | 경미 — 재시도 가능 |
| **Risky** | 균형 잡힌 위험 | 상당 — 피해·상황 악화 |
| **Desperate** | PC가 궁지에 몰림 | 심각 — 중대 피해·파국 |

### Position별 대가 예시

**Controlled — 실패**:
- 시간 지연만
- 소량 자원 손실 (탄약 1~2)
- 재시도 가능 (+5 TN 페널티)

**Controlled — Partial**:
- 경미한 소모 (시간·자원)
- 재시도 없이 진행 가능

**Risky — 실패**:
- 피해 1d6
- 상황 악화 (Position이 Desperate로)
- 자원 손실 중급

**Risky — Partial**:
- 상당 대가 (피해 절반·Position 악화)
- 목표 달성했으나 흔적을 남김

**Desperate — 실패**:
- 중대 피해 2d6+
- 상황 파국 (동료 위험·임무 실패)
- 상태 이상 추가

**Desperate — Partial**:
- 심각 대가 (피해 + 상태 이상 + Position 최악)
- "간신히 해냈지만 무너졌다"

### Position 결정 주체

- **GM 기본 선언**: 판정 직전, 상황을 보고 Position 지정.
- **플레이어 협상**: 장르 자원(DSR) +1 소모로 1단계 완화.
- **Pack 특수**: 특정 스킬·능력이 자동 완화 (Pack 지정).

## 4-B. Effect — 성공 결실의 크기

### 4 단계 (v0.3 확장)

| Effect | 크기 | 의미 |
|---|---|---|
| **Limited** | 효과 절반 | 어려운 대상·부적합 장비·환경 방해 |
| **Standard** | 기본 효과 | 일상적 성공 |
| **Great** | 2배 효과 | 강화된 성과 |
| **Great Plus** | 3배 or 특수 | Critical 시 자동 / 비용 지출 도달 |

### Effect 결정 주체

- **GM 기본 선언**: 상황·장비·저항 기반.
- **플레이어 협상**: 장르 자원(DSR) +1당 1단계 상승.
- **자동 상승**: 차이값 20+ 또는 폭발 체인 → Effect 1단계 자동 상승.

### Effect 강화 비용 (Core 표준)

```
Limited  → Standard: DSR +1
Standard → Great:   DSR +1
Great    → Great Plus: DSR +2 (Critical 외 도달)
```

**v0.2의 "+0.5 누적식" 폐기**(Consistency Check v0.3.1). 단순 +1 단위로 통일. Pack Consistency v0.2 M-1 해결로 Pack도 Core 기준 준수.

### Effect 감소 조건

- **저항 대상**: 장갑·에고 방어·Pack 특수 저항 → Effect 1단계 감소
- **부적합 장비**: 대형 개체에 소구경 → Effect 1단계 감소 (4부 §05)
- **환경 방해**: 어둠·안개·거리 → Effect 1단계 감소

감소가 중첩되면 **Standard에서 시작해도 Limited로 떨어질 수 있습니다**. 이럴 때 Effect 강화 협상이 들어갑니다.

## 4-C. 3×3 매트릭스

Position × Effect 결합표:

|  | Limited | Standard | Great |
|---|---|---|---|
| **Controlled** | 낮은 위험 · 작은 결실 | 낮은 위험 · 보통 결실 | 낮은 위험 · 큰 결실 (이상적) |
| **Risky** | 균형 위험 · 작은 결실 (효율 낮음) | **기본 조합** | 균형 위험 · 큰 결실 |
| **Desperate** | 높은 위험 · 작은 결실 (비효율) | 높은 위험 · 보통 결실 | 높은 위험 · 큰 결실 (영웅 순간) |

- **기본 조합**은 Risky + Standard. 대부분의 판정이 이 조합입니다.
- **이상적 조합**(Controlled + Great)은 드물고, 서사적으로 쟁취됩니다.
- **영웅 순간**(Desperate + Great)은 드라마의 정점. Effect를 강화할 가치가 있는 순간입니다.
- **비효율 조합**(Desperate + Limited)은 GM이 "이 판정 굴려야 해요?"를 되물어야 할 신호입니다.

## 4-D. 협상의 문법

협상은 **굴림 전**에만 가능합니다. 굴림 이후에는 플래시백(9부 §03)으로만 우회됩니다.

### 형식

```
플레이어: "[근거]. 장르 자원 N 소모해서 [요청]하겠습니다."
GM: 판단 → 수락 or 거절
```

**수락 조건**:
- 서사적 타당성 (왜 지금 가능한가)
- PC 행동 구체성 (어떻게 위험을 낮추는가)
- 장르 자원 여유

**거절 시**:
- 자원 소모 없음
- Position·Effect 그대로

### 예시

> **플레이어**: "저 임원과는 작년 동쟁 때 같이 싸운 사이입니다. DSR 1 쓰고 Risky를 Controlled로 낮출게요."
> **GM**: "과거 인연 좋네요. 허용. DSR −1, Controlled."

> **플레이어**: "DSR 2 쓰겠습니다. Effect를 Standard에서 Great로. 만약 성공하면 임원이 뇌물 제공 정보도 같이 흘리게 해주세요."
> **GM**: "뇌물까지는 과합니다. +1로 Great까지는 좋지만, 뇌물 정보는 별도 Full 성공 시 추가 판정으로 하죠."
> **플레이어**: "그럼 +1만 쓸게요."

## 4-E. Critical 시 Effect 자동 상승

차이값 20+ 또는 폭발 체인 Critical은 **Effect 1단계 자동 상승**을 가져옵니다.

```
기본 Standard → Critical 시 Great
기본 Great    → Critical 시 Great Plus
기본 Limited  → Critical 시 Standard
```

이 자동 상승은 DSR 비용 없이 적용됩니다. Critical 자체가 이미 "드라마의 대가"로 지불된 것이기 때문입니다.

## 4-F. 연속 판정 시 Position·Effect 유지

같은 장면·같은 상대·같은 접근의 연속 판정은 Position·Effect를 **그대로 유지**합니다. 매번 GM이 다시 선언할 필요 없습니다.

Position·Effect가 바뀌는 순간:
- 다른 상대로 타깃 전환
- 장면 전환 (GM 선언)
- 위험 요소 변화 (엄폐 상실·주변 적 등장 등)
- Partial 결과로 Position 악화

> 🎯 **GM 팁** — Position과 Effect를 매번 길게 선언하지 않아도 됩니다. "Risky/Standard"가 기본값이라는 합의가 테이블에 자리 잡으면, 그와 다를 때만 "이건 Desperate" "이건 Great"로 짧게 알려주는 식으로 운영하십시오. 매 판정마다 9칸 매트릭스를 펼치는 GM이 가장 빨리 지칩니다.

## 4-G. 예시 — 침투 장면의 Position 변화

> **장면**: PC 팀이 ㈜신성 지점에 침투. 세 단계 진행:
>
> **1단계 — 외곽 접근**
> GM: "Controlled, Standard. 조용히 들어갈 수 있습니다."
> 잠입 판정 Partial → 시간 지연만. Position 유지.
>
> **2단계 — 경비 교대 시간대 통과**
> GM: "Risky, Standard. 교대 사이 10분이 좁습니다."
> 판정 Full → 통과. Position 유지.
>
> **3단계 — 서버룸 진입 중 CCTV 발견**
> GM: "이제 Desperate, Standard입니다. CCTV가 곧 당신을 잡습니다."
> 플레이어: "DSR 1, Risky로 낮춰주세요. 방금 2단계에서 확인한 교대 틈 정보를 씁니다."
> GM: "좋아요. Risky, Standard."
> 판정 Great → Effect 자동 Great로 상승. 서버룸 진입 + 추가 정보 획득.

한 장면 안에서 세 번의 판정이 세 번 다른 Position으로 진행되었습니다. 이것이 Position × Effect 운용의 전형입니다.

---

## 관련

- 이전: [03. d6 Pool — 연료 탱크](03_d6_Pool.md)
- 다음: [05. 대립·저항·협상 판정](05_대립_저항_협상.md)
- 연동: [5-4. 장르 자원 DSR](../05_5부_자원과_트랙/04_장르자원_DSR.md) · [10-3. 난이도·TN 조정](../10_10부_GM_가이드/03_난이도_TN_조정.md)
- 자동 상승: [01. Grade Die 판정 상세](01_Grade_Die_판정.md)
