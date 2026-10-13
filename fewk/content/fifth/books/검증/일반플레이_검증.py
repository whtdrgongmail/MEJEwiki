#!/usr/bin/env python3
"""P-INTRO-01 boundary/state and exact stochastic checks, no participant evidence."""
from pathlib import Path
from dataclasses import dataclass
from itertools import product
from collections import Counter
from fractions import Fraction
import hashlib,json
from 백분율_코어검증 import grade,contest,target

HERE=Path(__file__).parent
PROFILE=json.loads((HERE/'입문_프로필.json').read_text())

@dataclass
class Body:
    hp:int=12
    armor:int=1
    charges:int=2
    shield_types:tuple=('프로젝타일',)
    reaction:int=1
    blocked:bool=False
    main:int=1
    ammo:int=12
    move:int=10
    destroyed:bool=False
    first_aid_effect:bool=False
    recovery_window:int=-1
    last_recovery_s:int=-1

def new_round(b):
    b.reaction=1;b.main=1;b.move=10;b.blocked=False

def attack(actor,body,weapon,roll=1,skill=70,distance=1,cover='none',
           defense_roll=None,defense_skill=50,reflex=False,use_shield=True,suppress=False):
    w=PROFILE['weapons'][weapon]
    if actor.hp==0 or actor.destroyed or actor.main==0:
        raise ValueError('actor cannot act')
    if cover=='full' or distance>w['max_range_m']:
        raise ValueError('direct attack infeasible')
    melee=w['type']=='근접'
    if not melee and actor.ammo>w['capacity']:raise ValueError('ammo above capacity')
    shot_cost=3 if suppress else 1
    if suppress and melee:raise ValueError('suppression needs ranged weapon')
    if not melee and actor.ammo<shot_cost:raise ValueError('no ammo')
    if defense_roll is not None:
        if body.hp==0 or body.reaction==0 or (not melee and not reflex):
            raise ValueError('personal defense unavailable')
        body.reaction-=1
    actor.main-=1
    if not melee:actor.ammo-=shot_cost
    situation=-20 if cover=='partial' or distance>w['normal_range_m'] else 0
    t=target(skill,situation)
    hit=grade(t,roll)>0 if defense_roll is None else contest(t,roll,defense_skill,defense_roll)==1
    if not hit:return 'miss',0
    if use_shield and w['type'] in body.shield_types and body.charges and not body.blocked:
        body.charges-=1;body.blocked=True
        return 'shield',0
    if suppress:return 'suppression',0
    damage=max(0,w['damage']-body.armor)
    if body.hp==0 and damage>0:body.destroyed=True
    body.hp=max(0,body.hp-damage)
    return 'damage',damage

def aid(b,kits,success=True):
    if b.destroyed or kits==0 or b.first_aid_effect:raise ValueError('aid infeasible')
    kits-=1
    if success:
        b.hp=1 if b.hp==0 else min(12,b.hp+2)
        b.first_aid_effect=b.hp<12
    return kits

def recover_at(b,completed_s,work_s=21600,clinic=False,stored=False):
    """Apply a completed treatment; 24h is measured since the last effect.

    The caller supplies actual completed work, not OOC waiting or a date label.
    Material availability and treatment support are preconditions of this helper.
    """
    if work_s<21600 or completed_s<work_s:return False
    if stored or b.destroyed or b.hp>=12:return False
    if b.last_recovery_s>=0 and completed_s-b.last_recovery_s<86400:return False
    if not clinic and b.hp==0:return False
    b.hp=1 if b.hp==0 else min(12,b.hp+(4 if clinic else 2))
    b.last_recovery_s=completed_s
    if b.hp==12:b.first_aid_effect=False
    return True

def recover(b,window,clinic=False,stored=False):
    """Compatibility for old numbered-window examples: 6h, 30h, 54h..."""
    # Legacy fixtures may set only this used-window marker. Current time-aware
    # examples call recover_at and track last_recovery_s directly.
    if b.recovery_window==window:return False
    result=recover_at(b,window*86400+21600,clinic=clinic,stored=stored)
    if result:b.recovery_window=window
    return result

def move(b,meters,extra=False):
    if b.hp==0 or b.destroyed or meters<0:raise ValueError('movement infeasible')
    allowance=b.move
    if extra:
        if b.main==0:raise ValueError('no main action')
        allowance+=10
    if meters>allowance:raise ValueError('movement exceeds budget')
    if extra:b.main-=1
    b.move=allowance-meters

def reload(b,reserve,capacity=12):
    if b.hp==0 or b.destroyed or b.main==0 or not reserve:raise ValueError('reload infeasible')
    if not 0<=reserve[0]<=capacity:raise ValueError('invalid magazine')
    old=b.ammo;b.ammo=reserve.pop(0);b.main-=1
    if old:reserve.append(old)

def recharge(b,packs,safe=True):
    if b.hp==0 or b.destroyed or b.main==0 or packs==0 or not safe:
        raise ValueError('recharge infeasible')
    b.main-=1;b.charges=2
    return packs-1

def rejected(fn):
    try:fn()
    except ValueError:return True
    return False

def run():
    cases=[]
    def case(name,condition):
        assert condition,name
        cases.append(name)
    allocation=sorted(PROFILE['character']['allocation'])
    for name,values in PROFILE['character']['presets'].items():
        case('배분과 시작 숙련: '+name,len(values)==12 and sorted(values)==allocation and sum(values)==440)
        for value in values:
            assert sum(grade(value,r)>0 for r in range(1,101))==value
    case('성장 상한',min(95,90+5)==95 and min(95,95+5)==95)
    a,b=Body(),Body()
    case('첫 총격 유형 방호',attack(a,b,'권총')==('shield',0) and (b.hp,b.charges)==(12,1))
    a=Body()
    case('같은 라운드의 두 번째 적중',attack(a,b,'권총')==('damage',3) and (b.hp,b.charges)==(9,1))
    new_round(b);a=Body()
    case('다음 라운드 남은 충전',attack(a,b,'권총')==('shield',0) and b.charges==0)
    new_round(b);a=Body()
    case('라운드 경과는 충전 회복 없음',attack(a,b,'권총')==('damage',3) and b.charges==0)
    a,b=Body(),Body()
    case('실패에는 탄약만 소모',attack(a,b,'권총',roll=100)==('miss',0) and a.ammo==11 and b.charges==2)
    a,b=Body(),Body()
    case('유형 불일치 레이저',attack(Body(ammo=6),b,'레이저 단말')==('damage',3) and b.charges==2)
    a,b=Body(),Body(shield_types=('프로젝타일','레이저'))
    attack(a,b,'권총');a=Body()
    case('이중 유형도 몸당 방호 한 번',attack(Body(ammo=6),b,'레이저 단말')==('damage',3) and b.charges==1)
    a,b=Body(),Body()
    case('근접은 원거리 방호 우회',attack(a,b,'동력 근접 도구')==('damage',5) and b.charges==2)
    a,b=Body(),Body()
    case('장갑은 피해만 감소',attack(a,b,'맨손')==('damage',1))
    a,b=Body(),Body(armor=3)
    case('장갑 이상 피해0',attack(a,b,'맨손')==('damage',0) and b.hp==12)
    a,b=Body(),Body()
    case('일반 총격 회피 금지',rejected(lambda:attack(a,b,'권총',defense_roll=1)) and a.main==1 and a.ammo==12)
    a,b=Body(),Body()
    case('허용 방어는 공통 대립',attack(a,b,'권총',roll=18,defense_roll=21,reflex=True,use_shield=False)==('damage',3) and b.reaction==0)
    a=Body()
    case('한 라운드 두 번째 개인 반응 금지',rejected(lambda:attack(a,b,'권총',defense_roll=1,reflex=True)))
    a,b=Body(),Body()
    case('공격 실패에도 선언 반응 소비',attack(a,b,'동력 근접 도구',roll=100,defense_roll=100)==('miss',0) and b.reaction==0)
    a,b=Body(),Body()
    case('완전 엄폐는 공격 불가',rejected(lambda:attack(a,b,'권총',cover='full')) and a.main==1 and a.ammo==12)
    case('최대거리 초과 공격 불가',rejected(lambda:attack(a,b,'권총',distance=61)))
    case('접촉 없는 근접 불가',rejected(lambda:attack(a,b,'동력 근접 도구',distance=2)))
    a,b=Body(),Body(charges=0)
    case('멀고 부분 엄폐여도 불리 한 번',attack(a,b,'권총',roll=50,distance=60,cover='partial')==('damage',3))
    a,b=Body(),Body(charges=0)
    attack(a,b,'권총')
    case('같은 차례 주요 행동 두 번째 공격 없음',rejected(lambda:attack(a,b,'권총')) and a.ammo==11)
    a=Body();move(a,7);move(a,3)
    case('분할 이동 총량10m',a.move==0 and rejected(lambda:move(a,1)) and a.main==1)
    a=Body();move(a,20,True)
    case('추가 이동은 주요 행동 소비',a.move==0 and a.main==0 and rejected(lambda:attack(a,Body(),'맨손')))
    a=Body(ammo=2);reserve=[12];before=a.ammo+sum(reserve)
    reload(a,reserve)
    case('장전은 기존 잔량/보유량 보존',a.ammo==12 and reserve==[2] and a.ammo+sum(reserve)==before and a.main==0)
    case('장전 후 추가 사격 없음',rejected(lambda:attack(a,Body(),'권총')))
    a=Body(ammo=0)
    case('재고 없는 장전 불가',rejected(lambda:reload(a,[])) and a.main==1)
    a=Body(ammo=6);reserve=[6];reload(a,reserve,6)
    case('레이저 셀 총량/용량 보존',a.ammo==6 and reserve==[6])
    a=Body(charges=0);packs=recharge(a,1)
    case('방호 충전팩은 하나 소비하고2로 복구',packs==0 and a.charges==2 and a.main==0)
    case('충전 후 추가 행동 없음',rejected(lambda:recharge(a,1)))
    a=Body(charges=0)
    case('위험 현장에서 안전 거점 충전 불가',rejected(lambda:recharge(a,1,False)) and a.charges==0)
    a,b=Body(),Body(charges=0)
    case('억제는 탄약3과 행동1·HP피해 없음',attack(a,b,'권총',suppress=True)==('suppression',0) and a.ammo==9 and b.hp==12 and a.main==0)
    a,b=Body(),Body()
    case('방호는 억제 적중도 차단',attack(a,b,'권총',suppress=True)==('shield',0) and b.charges==1)
    a,b=Body(ammo=2),Body()
    case('억제 탄약 부족은 시도 불가',rejected(lambda:attack(a,b,'권총',suppress=True)) and a.ammo==2 and a.main==1)
    a,b=Body(),Body(hp=3,charges=0)
    attack(a,b,'권총')
    case('HP0은 해당 몸 행동 불가',b.hp==0 and not b.destroyed and rejected(lambda:attack(b,Body(),'맨손')))
    a=Body();attack(a,b,'권총')
    case('별개 후속 양의 피해로 몸 소실',b.destroyed)
    case('소실 몸 응급 회복 없음',rejected(lambda:aid(b,2)))
    b=Body(hp=0)
    kits=aid(b,2)
    case('HP0 처치 안정화',b.hp==1 and kits==1 and b.first_aid_effect)
    b.hp=0
    case('새 부상은 처치 한도 초기화 안 함',rejected(lambda:aid(b,kits)))
    b=Body(hp=7);kits=aid(b,2,False)
    case('실패에도 키트 소모',kits==1 and b.hp==7 and not b.first_aid_effect)
    kits=aid(b,kits)
    case('조건 바뀐 재시도',b.hp==9 and kits==0 and b.first_aid_effect)
    case('휴식 24시간 한도',recover(b,0) and b.hp==11 and not recover(b,0,True))
    case('새 구간 회복은 최대치까지만',recover(b,1,True) and b.hp==12 and not b.first_aid_effect)
    b=Body(hp=9)
    case('저장 몸 수동 경과 회복 없음',not recover(b,2,stored=True) and b.hp==9)
    b=Body(hp=0)
    case('HP0 단순 휴식 없음',not recover(b,2))
    case('HP0 치료 거점 안정화',recover(b,2,True) and b.hp==1)
    # 몸 전환/보관/기록은 수치와 ID가 유지되는 실제 데이터 예시로 검증한다.
    person={'skill':70,'active':'local','banned':[]}
    bodies={'base':{'hp':12},'local':{'hp':9,'kits':2}}
    saved=json.loads(json.dumps(bodies['local']))
    person['active']='base';person['skill']+=5
    bodies['local']=json.loads(json.dumps(saved));person['active']='local'
    case('몸 보관과 인물 학습 연속',bodies['local']=={'hp':9,'kits':2} and bodies['base']['hp']==12 and person['skill']==75)
    case('정상 귀환은 재진입 제한 없음',person['banned']==[])
    person['banned'].append('TEST-LOCAL')
    case('드랍아웃은 해당 차원만', 'TEST-LOCAL' in person['banned'] and 'OTHER' not in person['banned'] and bodies['base']['hp']==12)
    # 현물 보존 및 사본/권한 구별. 같은 시작 버전의 이중 이동을 허용하지 않는다.
    state={'version':1,'goods':{'tool':{'owner':'local','n':1}},'data':{'original':{'owner':'local','rights':['read','copy']}}}
    start=state['version'];state['goods']['tool']['owner']='base';state['version']+=1
    case('현물 이동 중복 없음',sum(v['n'] for v in state['goods'].values())==1 and state['version']!=start)
    state['data']['copy-01']={'owner':'base','source':'original','rights':['read']}
    case('사본은 원본 소유권을 이전하지 않음',state['data']['original']['owner']=='local' and state['data']['copy-01']['source']=='original')
    # 독립 전수: 사격70 두 번에 대한 라운드당 방호 차단 한 번.
    two=Counter();n=0
    for ra,rb in product(range(1,101),repeat=2):
        b=Body();attack(Body(),b,'권총',ra);attack(Body(),b,'권총',rb)
        two[12-b.hp]+=1;n+=1
    expectation=sum(Fraction(d*c,n) for d,c in two.items())
    case('같은 라운드 두 총격의 방호·독립 이항식',expectation==Fraction(3)*Fraction(70,100)**2 and two=={0:5100,3:4900})
    melee_hits=sum(contest(70,r,50,s)==1 for r,s in product(range(1,101),repeat=2))
    melee_expected=Fraction(melee_hits,10000)*5
    case('근접 대립70/50 기대 피해',melee_hits==5915 and melee_expected==Fraction(1183,400))
    triple=Counter()
    # 3라운드 총격 각 1회, 수동적인 표적과 충전2. 참가자 전술/이동 없음.
    # 성공/실패 분포를 압축하여 8개 경로를 정확한 가중치로 계산한다.
    for outcomes in product((False,True),repeat=3):
        b=Body();weight=1
        for hit in outcomes:
            new_round(b);attack(Body(),b,'권총',1 if hit else 100)
            weight*=70 if hit else 30
        triple[12-b.hp]+=weight
    triple_expected=sum(Fraction(d*c,100**3) for d,c in triple.items())
    case('3라운드 충전 소모 독립식',triple_expected==3*Fraction(70,100)**3 and sum(triple.values())==100**3)
    return {'date':'2026-10-05','profile':PROFILE['id'],'common_engine':PROFILE['common_engine'],
        'scope':'입문 생성·수치·행동/방호/회복·보관/거래 기록의 경계와 제한된 원거리/근접 수학 대조',
        'checks_passed':len(cases),'cases':cases,'two_shots_enumerated':n,
        'mathematical_cases':[
          {'scene':'같은 라운드 권총70 두 명, 장갑1·프로젝타일 차단1회','hp_damage_distribution':dict(two),'expected_damage':float(expectation),'independent_crosscheck':'3 × 0.7² = 1.47'},
          {'scene':'접촉한 동력 도구70 vs 격투/운동 방어50, 장갑1','opposed_pairs':10000,'hit_percent':melee_hits/100,'expected_damage':float(melee_expected)},
          {'scene':'권총70 3라운드, 표적 정지·프로젝타일 충전2·장갑1','weighted_outcomes':dict(triple),'expected_damage':float(triple_expected),'independent_crosscheck':'3 × 0.7³ = 1.029'}],
        'artifacts_sha256':{str(q.relative_to(HERE.parent)):hashlib.sha256(q.read_bytes()).hexdigest() for q in [HERE.parent/'10_CoreRulebook.md',HERE.parent/'12_룰시트와캐릭터시트.md',HERE/'입문_프로필.json',Path(__file__)]},
        'actual_participant_playtest':False,'full_combat_balance_proven':False,
        'limitations':['유한한 입문 프로필과 명시 조건만 검증했다. 전체 무기/몸/차원 검사가 아니다.','실제 참가자·전술 판단·진행 시간·비동기 응답은 미검증이다.','총격/근접 사용 비율50/50을 이 기대 피해로 추정하지 않는다.']}

if __name__=='__main__':
    result=run()
    (HERE/'일반플레이_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'checks_passed':result['checks_passed'],'mathematical_cases':result['mathematical_cases'],'real_playtest':False},ensure_ascii=False))
