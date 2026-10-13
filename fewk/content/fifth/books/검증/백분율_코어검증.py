#!/usr/bin/env python3
"""FEWK P-FEWK v0.2 판정 검산. 참가자 플레이테스트/전투 엔진 아님."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import hashlib,json

VERSION="P-FEWK-0.2"

def target(prepared,situation=0):
    if situation not in (-20,0,20):
        raise ValueError("상황 보정은 -20/0/20")
    return min(99,max(1,prepared+situation))

def grade(t,r):
    if not 1<=t<=99 or not 1<=r<=100:
        raise ValueError("판정 목표1~99, 굴림1~100")
    if r<=t//5:return 3
    if r<=t//2:return 2
    if r<=t:return 1
    return 0

def contest(ta,ra,tb,rb):
    a,b=grade(ta,ra),grade(tb,rb)
    if a==b==0:return 0
    if a!=b:return 1 if a>b else -1
    if ta!=tb:return 1 if ta>tb else -1
    if ra!=rb:return 1 if ra<rb else -1
    return 0

def defended_hit(ta,ra,td,rd):
    return contest(ta,ra,td,rd)==1

def distribution(t):
    e=t//5;h=t//2
    return {0:100-t,1:t-h,2:h-e,3:e}

def exact_case(a,b):
    general=Counter();hits=0
    for ra in range(1,101):
        for rb in range(1,101):
            result=contest(a,ra,b,rb)
            assert result==-contest(b,rb,a,ra)
            general[result]+=1
            hits+=defended_hit(a,ra,b,rb)
    # 독립 성공 수준 분포의 곱
    da,db=distribution(a),distribution(b)
    class_hits=sum(da[k]*sum(db[j] for j in range(k)) for k in (1,2,3))
    if a>b:class_hits+=sum(da[k]*db[k] for k in (1,2,3))
    if a==b:class_hits+=sum(da[k]*(da[k]-1)//2 for k in (1,2,3))
    assert hits==class_hits==general[1]
    both_fail=(100-a)*(100-b)
    expected_hold=both_fail+(a if a==b else 0)
    assert general[0]==expected_hold
    assert sum(general.values())==10000
    if a==b:assert general[1]==general[-1]
    return {"targets":[a,b],"ordinary_single_success_percent":a,
            "contest_win_percent":general[1]/100,"contest_loss_percent":general[-1]/100,
            "contest_hold_percent":general[0]/100,
            "defended_attack_hit_percent":hits/100,
            "crosscheck":"10,000쌍 전수 열거와 성공 수준 분포 곱의 독립 대조"}

def run():
    scalar=0
    for t in range(1,100):
        actual=Counter(grade(t,r) for r in range(1,101))
        expected=distribution(t)
        assert dict(actual)=={k:v for k,v in expected.items() if v}
        assert sum(v for k,v in actual.items() if k)>0
        assert sum(v for k,v in actual.items() if k)==t
        assert grade(t,t)>0
        assert grade(t,t+1)==0
        assert grade(t,100)==0
        for r in range(1,101):
            if t<99:assert grade(t+1,r)>=grade(t,r)
        scalar+=100
    assert (target(50,20),target(50,-20),target(50,0))==(70,30,50)
    assert target(-30)==1 and target(130)==99
    # 동률 방어·양측 실패·일반 사격·몸 저항 참조 예시
    assert grade(70,18)==grade(50,21)==2
    assert defended_hit(70,18,50,21)
    assert defended_hit(50,18,50,21)
    assert not defended_hit(50,21,50,18)
    assert not defended_hit(50,18,50,18)
    assert grade(70,18)>0
    assert not defended_hit(30,70,50,90)
    assert grade(50,34)==1
    assert grade(60,55)==1 and grade(40,55)==0
    assert contest(50,18,50,20)==1
    assert contest(70,18,50,21)==1
    assert contest(50,99,30,80)==0
    cases=[exact_case(a,b) for a,b in [(1,1),(30,30),(50,50),(70,50),(90,30),(50,70),(99,99),(1,99)]]
    budget_checks=[]
    for name,levels,old in [
        ("표준 러너",[4,3,4,3,2,1],17),
        ("전담 해커",[6,4,4,3,1,2],20),
        ("사회 공작원",[5,5,4,3,3,2],22),
        ("전담 신사",[6,5,4,3,2,2],22)]:
        iterative=sum(sum(range(1,n+1)) for n in levels)
        triangular=sum(n*(n+1)//2 for n in levels)
        assert iterative==triangular
        assert sum(levels)==old
        budget_checks.append({"name":name,"levels":levels,"old_claim_p":old,"cumulative_skill_p":iterative,"same_as_level_sum_error":True})
    here=Path(__file__).parent
    core=here.parent/"10_CoreRulebook.md"
    return {"date":"2026-10-05","version":VERSION,"scope":"Core v0.10의 P-FEWK v0.2 단일 대립 판정 정의·작성 예시와 구판 숙련 비용 검산",
        "core_sha256":hashlib.sha256(core.read_bytes()).hexdigest(),
        "scalar_rolls_checked":scalar,"opposed_pairs_checked":len(cases)*10000,
        "cases":cases,"legacy_skill_cost_checks":budget_checks,
        "old_A_results_used_as_P_results":False,"actual_participant_playtest":False,
        "complete_physical_combat_balance_tested":False,
        "notes":["각 독립 d100 결과를 균등하게 가정한 수학 검산이다.","일반 경쟁과 방어 대립의 성공/동률 비교가 같은 절차다. 방어 성공이 자동 반격을 주지는 않는다.","목표가 확률로 읽힌다는 것은 일반 단일 성공 기준이다. 대립 승률이나 실제 캠페인 성공률을 의미하지 않는다.","상황±20과 성공 수준·대립 규약은 신규 FEWK 구현이다.","무료 재굴림·추가 반응·별도의 무기/거리/피해 척도는 이 파일에서 시험하지 않았다."]}

if __name__=="__main__":
    out=run()
    destination=Path(__file__).with_name("백분율_코어검증결과.json")
    destination.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"scalar_rolls_checked":out["scalar_rolls_checked"],"opposed_pairs_checked":out["opposed_pairs_checked"],"cases":out["cases"],"legacy_skill_cost_checks":out["legacy_skill_cost_checks"]},ensure_ascii=False))
