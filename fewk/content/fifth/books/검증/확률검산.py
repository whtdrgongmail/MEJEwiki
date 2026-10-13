"""제5판 실험안의 확률 탐색. 게임 엔진이나 플레이테스트가 아니다."""
from pathlib import Path
from itertools import product
import json

def roll_grade(target,roll):
    if roll > target: return 'fail'
    return 'great' if roll <= target//2 else 'success'

def opposed(a,b,ra,rb):
    sa,sb=ra<=a,rb<=b
    if sa and not sb:return 'a'
    if sb and not sa:return 'b'
    if not sa and not sb:return 'hold'
    ma,mb=a-ra,b-rb
    return 'a' if ma>mb else 'b' if mb>ma else 'hold'

def pair_distribution(cards,bonus_difference):
    counts={'a':0,'b':0,'hold':0}
    for a,b in product(cards,repeat=2):
        if a==b:continue
        v=a[1]+bonus_difference-b[1]
        counts['a' if v>0 else 'b' if v<0 else 'hold']+=1
    total=sum(counts.values())
    return {'ordered_distinct_pairs':total,'counts':counts,'probabilities':{k:v/total for k,v in counts.items()}}


from fractions import Fraction
from math import comb

def grade_success(sides,number,target,exploding):
    # Only sums below target are stored. Their complement is exact even for
    # arbitrarily long exploding chains: any single value >= target succeeds.
    pmf={}
    if exploding:
        for value in range(1,target):
            chain,remainder=divmod(value,sides)
            if remainder:
                pmf[value]=Fraction(1,sides**(chain+1))
    else:
        pmf={value:Fraction(1,sides) for value in range(1,sides+1)}
    distribution={0:Fraction(1)}
    for _ in range(number):
        nxt={}
        for subtotal,p in distribution.items():
            for value,q in pmf.items():
                if subtotal+value < target:
                    nxt[subtotal+value]=nxt.get(subtotal+value,Fraction(0))+p*q
        distribution=nxt
    success=1-sum(distribution.values(),Fraction(0))
    return {'fraction':str(success),'probability':float(success)}

def engine_audit():
    cases=[]
    for number,sides,target in [(4,4,10),(5,8,25),(9,12,60)]:
        cases.append({'dice':f'{number}d{sides}','target':target,'modifiers':0,
          'source_claimed_success':0.5,
          'without_explosion':grade_success(sides,number,target,False),
          'with_explosion':grade_success(sides,number,target,True),
          'unexploded_mean':number*(sides+1)/2,
          'exploded_mean':number*sides*(sides+1)/(2*(sides-1))})
    fitd={}
    for number in [1,2,3]:
        fail=Fraction(1,2)**number
        no_six=Fraction(5,6)**number
        fitd[str(number)]={'1_to_3':float(fail),'4_or_5':float(no_six-fail),
                         'at_least_one_6_including_criticals':float(1-no_six)}
    costs=[0,2,5,9,15,20,26,33,45,52,60,69,85,94,104,115,135,147,160,174,200,215,231,248,266]
    dp={0:0}
    for _ in range(6):
        nxt={}
        for subtotal,cost in dp.items():
            for stat,value in enumerate(costs,1):
                if subtotal+stat<=36:
                    nxt[subtotal+stat]=min(nxt.get(subtotal+stat,10**9),cost+value)
        dp=nxt
    independent=[]
    for case in cases:
        n,s=map(int,case['dice'].split('d'));limit=case['target']-1
        below=sum((-1)**k*comb(n,k)*comb(limit-k*s,n) for k in range(n+1) if limit-k*s>=n)
        check=1-Fraction(below,s**n)
        assert str(check)==case['without_explosion']['fraction']
        independent.append({'dice':case['dice'],'method':'유계 정수 합의 포함배제식','matched':True})
    values=[a if a<4 else 4+b for a,b in product(range(1,5),repeat=2)]
    check=Fraction(sum(sum(v)>=10 for v in product(values,repeat=4)),16**4)
    assert str(check)==cases[0]['with_explosion']['fraction']
    independent.append({'dice':'4d4 Ace','method':'첫 두 번 눈의 전수 열거. 2회 최대 눈 이후는 최소 합으로 이미 TN10 이상','matched':True})
    return {'scope':'구 Grade Die 수치 설명과 공통 판정 후보의 수학적 대조',
      'independent_checks':independent,
      'grade_die':cases,
      'fitd_highest_d6':fitd,
      'budget_crosscheck_only_no_100p_rewrite':{'six_stats_mean_6_minimum_cost':dp[36],
       'all_six_stats_at_6_cost':6*costs[5],'all_six_stats_at_8_cost':6*costs[7],
       'skills_and_other_purchases_included':False},
      'limits':['확률은 외부 룰의 재미·사용성·전체 적합도 점수가 아님','FitD 분포는 6/4~5/1~3만 묶고 위치·효과·저항·스트레스는 비교하지 않음','Grade Die는 수정치 없는 표준 성공 판정이며 대립·크리티컬 해석은 미검증']}

def combat_defense_audit():
    """Finite, declared test fixtures; not a full combat or a source-game model."""
    attack, defense, hp, armor = 70, 50, 4, 1
    outcomes = [opposed(attack, defense, a, b)
                for a, b in product(range(1, 101), repeat=2)]
    hit_p = Fraction(outcomes.count('a'), 10000)
    gun, melee, reduction, charges = 2, 3, 1, 2
    static_gun_damage = max(0, gun - armor - reduction)
    naked_gun_damage = max(0, gun - armor)
    melee_damage = max(0, melee - armor)
    gun_hits = (hp + naked_gun_damage - 1) // naked_gun_damage
    melee_hits = (hp + melee_damage - 1) // melee_damage
    # Two independent attackers, one matching interception allowed per exchange.
    one_block_pair_damage = hit_p**2 * naked_gun_damage
    # Direct count: attacker successes against failed defenses, then the
    # rectangle and triangular region of successful margin comparisons.
    direct_hit_count = attack*(100-defense) + (attack-defense)*defense + sum(range(1,defense))
    assert hit_p == Fraction(direct_hit_count,10000)
    # All 4 hit/miss combinations provide a separate enumeration of the exchange.
    weighted_pair_damage = sum(
        (hit_p if a else 1-hit_p)*(hit_p if b else 1-hit_p)
        * max(0, a+b-1)*naked_gun_damage
        for a,b in product([0,1],repeat=2))
    assert weighted_pair_damage == one_block_pair_damage
    assert static_gun_damage == 0 and naked_gun_damage == 1 and melee_damage == 2
    return {
        'scope':'EASY-COMBAT-02 시험 수치와 방호 방식의 수학적 비교',
        'fixture':{'engine':'d100 prototype A opposed margin','attack_target':attack,
                   'defense_target':defense,'local_hp':hp,'armor':armor,
                   'gun_damage':gun,'melee_damage':melee,'typed_shield_charges':charges,
                   'typed_interceptions_per_exchange':1,'in_combat_recharge':False},
        'attack_win_probability':float(hit_p),'attack_win_fraction':str(hit_p),
        'constant_additive_reduction':{'reduction':reduction,'gun_hp_damage_per_hit':static_gun_damage,
                                      'hits_to_disable':None,'problem':'이 시험값에서는 사격이 계속 HP를 줄이지 못함'},
        'finite_interception':{
            'matching_gun_confirmed_hits_to_disable':charges+gun_hits,
            'nonmatching_gun_confirmed_hits_to_disable':gun_hits,
            'melee_confirmed_hits_to_disable':melee_hits,
            'one_attack_per_exchange_expected_attempts_matching_gun':float(Fraction(charges+gun_hits)/hit_p),
            'one_attack_per_exchange_expected_attempts_nonmatching_gun':float(Fraction(gun_hits)/hit_p),
            'one_attack_per_exchange_expected_attempts_melee_before_approach':float(Fraction(melee_hits)/hit_p),
            'two_independent_matching_shooters_expected_hp_damage_first_exchange':float(one_block_pair_damage),
            'two_independent_matching_shooters_both_hit_probability':float(hit_p**2),
            'two_independent_matching_shooters_any_hit_charge_consumption_probability':float(1-(1-hit_p)**2)},
        'limits':['HP 판정·차단 소모만 계산. 실제 승률·재미·반반 활용은 미검증',
                  '기대 시도 수는 고정 명중 확률·행동마다 독립·1회 공격/교환·정비 없음·적 반격/이동 없음의 비교값',
                  '근접 기대 시도 수에는 접근 행동·접근 중 피격·사선 확보·목표 수행 시간이 없음',
                  '둘 이상의 공격은 서로 다른 인물의 행동을 소비. 한 인물의 자동 추가 공격을 뜻하지 않음',
                  '부품 가격·셀 소모·원전 장치 성능으로 환산하지 않음'],
        'independent_checks':['성공/실패 사각영역과 성공 여유 삼각영역의 별도 계수로 명중 확률 확인','2인 교환의 4가지 명중 조합을 가중합해 기대 피해 확인']}


from functools import lru_cache

@lru_cache(None)
def opposed_probability(a,b):
    return Fraction(sum(opposed(a,b,x,y)=='a'
                        for x,y in product(range(1,101),repeat=2)),10000)


def encounter_model(cfg,policy):
    """Absorbing finite-state trial, not a game engine or participant playtest."""
    from functools import lru_cache
    pc_hit = opposed_probability(cfg['pc_attack'],50)
    enemy_hit = {50:opposed_probability(50,50),40:opposed_probability(40,50)}
    initial = (4,4,cfg['pc_shield'],cfg['enemy_shield'],cfg['approach'])

    def transitions(state):
        # state: player HP, enemy HP, player P-shield, enemy P-shield, steps to contact
        branches = [(Fraction(1),state)]
        for actor in ([0,1] if cfg['pc_first'] else [1,0]):
            nxt=[]
            for weight,current in branches:
                ph,eh,pq,eq,steps=current
                if ph<=0 or eh<=0:
                    nxt.append((weight,current));continue
                if actor==0 and policy=='melee' and steps:
                    nxt.append((weight,(ph,eh,pq,eq,steps-1)));continue
                close = steps==0 and policy=='melee'
                if actor==0:
                    probability=opposed_probability(70,50) if close else pc_hit
                    typ='melee' if close else policy
                else:
                    covered=(cfg['route_cover'] and not close) if policy=='melee' else cfg['pc_cover']
                    probability=enemy_hit[40 if covered else 50]
                    typ='melee' if close and cfg['enemy_melee'] else 'projectile'
                target_charge=eq if actor==0 else pq
                shield_type=cfg['enemy_shield_type'] if actor==0 else 'projectile'
                intercept = target_charge>0 and typ!='melee' and (typ==shield_type or shield_type=='both')
                damage = 0 if intercept else (2 if typ=='melee' else 1)
                hit_state = ((ph,max(0,eh-damage),pq,eq-int(intercept),steps) if actor==0
                             else (max(0,ph-damage),eh,pq-int(intercept),eq,steps))
                nxt.append((weight*probability,hit_state))
                nxt.append((weight*(1-probability),current))
            branches=nxt
        merged={}
        for weight,state in branches:merged[state]=merged.get(state,Fraction(0))+weight
        assert sum(merged.values(),Fraction(0))==1
        return merged

    @lru_cache(None)
    def solve(state):
        ph,eh,*_=state
        if ph<=0:return Fraction(0),Fraction(0),Fraction(0)
        if eh<=0:return Fraction(1),Fraction(0),Fraction(ph)
        branches=transitions(state)
        loop=branches.get(state,Fraction(0))
        win=hp_win=Fraction(0); rounds=Fraction(1)
        for other,weight in branches.items():
            if other==state or not weight:continue
            w,e,h=solve(other)
            win+=weight*w;rounds+=weight*e;hp_win+=weight*h
        divisor=1-loop
        assert divisor>0
        return win/divisor,rounds/divisor,hp_win/divisor

    win,rounds,hp_win=solve(initial)
    return {'opponent_disabled_first_probability':float(win),
            'probability_fraction':str(win),'expected_exchanges':float(rounds),
            'pc_hp_conditional_on_win':float(hp_win/win) if win else None,
            'states_solved':solve.cache_info().currsize}


def encounter_simulation(cfg,policy,number=20000,seed=2601004):
    """Independent dice-driven loop checks the finite-state probabilities."""
    import random
    rng=random.Random(seed);wins=0;round_total=0
    for _ in range(number):
        ph=eh=4;pq=cfg['pc_shield'];eq=cfg['enemy_shield'];steps=cfg['approach']
        turns=0
        while ph>0 and eh>0:
            turns+=1
            for actor in ([0,1] if cfg['pc_first'] else [1,0]):
                if ph<=0 or eh<=0:break
                if actor==0 and policy=='melee' and steps:
                    steps-=1;continue
                close=policy=='melee' and steps==0
                if actor==0:
                    target=70 if close else cfg['pc_attack']
                    typ='melee' if close else policy
                else:
                    covered=cfg['route_cover'] and not close if policy=='melee' else cfg['pc_cover']
                    target=40 if covered else 50
                    typ='melee' if close and cfg['enemy_melee'] else 'projectile'
                roll=rng.randint(1,100);defense_roll=rng.randint(1,100)
                # Independent expression for attacker-only hit; no counter-damage on failure.
                hit=(roll<=target and (defense_roll>50 or target-roll>50-defense_roll))
                if not hit:continue
                if actor==0:
                    if eq and typ!='melee' and (typ==cfg['enemy_shield_type'] or cfg['enemy_shield_type']=='both'): eq-=1
                    else:eh-=2 if typ=='melee' else 1
                else:
                    if typ=='projectile' and pq:pq-=1
                    else:ph-=2 if typ=='melee' else 1
            assert turns<1000
        wins+=eh<=0;round_total+=turns
    return {'seed':seed,'trials':number,'opponent_disabled_first_probability':wins/number,
            'mean_exchanges':round_total/number}


def encounter_audit():
    base={'pc_attack':70,'pc_first':True,'pc_shield':0,'enemy_shield':2,
          'approach':2,'pc_cover':False,'route_cover':False,'enemy_melee':False,'enemy_shield_type':'projectile'}
    scenes=[
        ('close_cover',{'approach':1,'pc_attack':60,'pc_cover':True,'route_cover':True}),
        ('open_approach',{}),
        ('long_approach',{'approach':3,'pc_attack':60}),
        ('enemy_melee_counter',{'enemy_melee':True}),
        ('protected_approach',{'pc_shield':2}),
        ('enemy_laser_shield',{'enemy_shield_type':'laser'}),
        ('enemy_both_shields',{'enemy_shield_type':'both'}),
        ('enemy_first',{'pc_first':False}),
        ('movement_favorable',{'approach':1}),
        ('movement_hindered',{'approach':3})]
    results=[]
    for index,(name,changes) in enumerate(scenes):
        cfg={**base,**changes};policies={}
        for strategy in ['projectile','laser','melee']:
            result=encounter_model(cfg,strategy)
            # Cover, counter-attack, initiative, movement, and typed shields checked
            # against a separate loop that actually generates d100 dice.
            mc=encounter_simulation(cfg,strategy,seed=2601004+index)
            assert abs(result['opponent_disabled_first_probability']-mc['opponent_disabled_first_probability'])<0.02
            assert abs(result['expected_exchanges']-mc['mean_exchanges'])<0.20
            result['independent_simulation_check']=mc
            policies[strategy]=result
        results.append({'scene':name,'conditions':cfg,'fixed_policies':policies})
    sensitivity=[]
    for steps in range(1,9):
        cfg={**base,'approach':steps}
        result=encounter_model(cfg,'melee')
        if steps in [6,8]:
            mc=encounter_simulation(cfg,'melee',seed=2601004+steps+100)
            assert abs(result['opponent_disabled_first_probability']-mc['opponent_disabled_first_probability'])<0.02
            assert abs(result['expected_exchanges']-mc['mean_exchanges'])<0.20
            result['independent_simulation_check']=mc
        sensitivity.append({'approach_actions':steps,**result})
    assert all(a['opponent_disabled_first_probability']>=b['opponent_disabled_first_probability']
               for a,b in zip(sensitivity,sensitivity[1:]))
    # Mirroring equally skilled shooting combat must reverse the initiative advantage.
    mirror={**base,'pc_attack':50,'pc_shield':2,'enemy_shield':2}
    first=encounter_model(mirror,'projectile')['opponent_disabled_first_probability']
    last=encounter_model({**mirror,'pc_first':False},'projectile')['opponent_disabled_first_probability']
    assert abs(first+last-1)<1e-12 and first>0.5>last
    return {'scope':'EASY-COMBAT-03 거리/엄폐/이동/적 행동을 포함한 유한 상태 시험',
        'model':'exact absorbing-state recursion with Fraction probabilities; independent seeded d100 simulation',
        'scenes':results,'approach_sensitivity':sensitivity,'cross_checks':{'mirrored_equal_combat_pc_first':first,'mirrored_equal_combat_pc_last':last,'sum':first+last,'more_exposed_approach_actions_never_improve_melee_result':True},
        'assumptions':['인물당 교환에 행동1회·선후행 고정·활동 불가자는 남은 행동 없음',
          '양쪽 현지 HP4/장갑1, PC 공격70/방어50, 적 공격50/방어50. 상황에 따라 사격 목표−10',
          'PC 근접 피해3/총격 피해2. 적은 총격 피해2, 근접 대응 장면만 근접 피해3',
          'PC 방호는 프로젝타일. 적의 방호 유형은 장면별 지정. 저장2·적중 시 소비·전투 중 충전 없음',
          '접근은 지정된 1~3행동으로 완료. 길이 이미 확보되어 추가 기동/등반 판정 없음',
          '위험은 적의 정상 행동으로만 처리. 이동 실패 피해나 무료 기회 공격을 추가하지 않음',
          '접촉 도달 이동에 근접 공격을 공짜로 포함하지 않음',
          '커버 보정은 사격 공격값에만 한 번 적용, 근접은 접촉 후 공격70',
          '이동/방호/공격 선택은 고정 정책. 우열은 정책·장면 조건에 종속'],
        'not_included':['실제 참가자·재미·운영 시간','다인 팀·최적 전략·중간 유형 전환·도주·자료 확보 목표',
          '실물 방호 성능·장비 가격·완전 엄폐·사선 차단·탄약 고갈·전투 중 재장전',
          '뛰어난 성공의 부가 효과·강제 제압·무장 해제·임플란트·치료',
          'R/G/Grade Die/FitD의 실제 전투·타롯·자아/본체 특수 피해'],
        'no_contact_path':'접촉 경로가 없는 표적은 근접 정책의 비교 대상에서 제외. 자동 접근 성공으로 처리하지 않음',
        'actual_playtest':False}


def generate():
    singles={}
    for target in [10,30,50,70,90]:
        counts={k:0 for k in ['fail','success','great']}
        for roll in range(1,101):counts[roll_grade(target,roll)]+=1
        singles[str(target)]={'counts':counts,'overall_success_probability':(counts['success']+counts['great'])/100}
    opposed_results=[]
    for a,b in [(30,30),(50,50),(70,50),(90,30)]:
        counts={k:0 for k in ['a','b','hold']}
        for ra,rb in product(range(1,101),repeat=2):counts[opposed(a,b,ra,rb)]+=1
        opposed_results.append({'targets':[a,b],'ordered_roll_pairs':10000,'counts':counts,'probabilities':{k:v/10000 for k,v in counts.items()}})
    decks={}
    for size,ranks in [(56,14),(52,13)]:
        cards=list(product(range(4),range(1,ranks+1)))
        decks[str(size)]={'unique_cards':len(set(cards)),'one_exchange_uniform_card_model':{str(d):pair_distribution(cards,d) for d in [0,1,2]}}
    return {'date':'2026-10-04','scope':'제안된 일반 판정·카드 단일 교환·구 Grade Die 및 FitD 분포·시험 방호·접근/엄폐/반격 모형의 검산',
            'not_verified':['실제 플레이','5장 손패 선택·순서 전략·최대 3교환의 전체 승률','타롯 미학·재미·비동기 사용성','장기거주 에고 고정 수치','개척·플라잉·모든 캠페인 IO의 완성'],
            'd100_single':singles,'d100_opposed':opposed_results,'card_decks':decks,'engine_comparison':engine_audit(),'combat_defense':combat_defense_audit(),'combat_encounters':encounter_audit(),
            'interpretation':'카드는 공통 덱의 서로 다른 두 장을 균등 추출한 단일 교환 모델. 실제 손패에서 선택한 카드 분포가 아니므로 전체 대결 승률로 사용하지 않는다. 카드 보너스 구간은 백분율 숙련 차이를 보존하지 않는다.'}

if __name__=='__main__':
    dest=Path(__file__).with_name('검증결과.json')
    dest.write_text(json.dumps(generate(),ensure_ascii=False,indent=2)+'\n')
    print('wrote',dest.name)
