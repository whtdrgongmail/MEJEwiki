"""공개된 정보만 이용하는 TAR-P-02 전략 대조.
지정 PC 손패/상대 정책에 대한 정확한 최선 대응이며, 전체 손패의 균형 전략이나 실제 참가자 검증은 아닙니다.
"""
from pathlib import Path
import hashlib
from collections import Counter,defaultdict
from functools import lru_cache
from itertools import combinations,combinations_with_replacement,permutations
from math import comb
from fractions import Fraction
import json,time

def top_three_distribution(counts):
    """공통 덱에서 상대의 비공개5장을 무복원 추출한 정확한 상위3장 분포."""
    total=comb(sum(counts.values()),5);rows={}
    for ascending in combinations_with_replacement(sorted(counts),3):
        triple=tuple(reversed(ascending));needed=Counter(triple);lowest=triple[-1]
        if any(needed[r]>counts[r] for r in needed):continue
        high_factor=1
        for r,k in needed.items():
            if r>lowest:high_factor*=comb(counts[r],k)
        high_number=sum(k for r,k in needed.items() if r>lowest)
        lower_number=sum(k for r,k in counts.items() if r<lowest)
        weight=0
        for number_lowest in range(needed[lowest],min(counts[lowest],5-high_number)+1):
            number_lower=5-high_number-number_lowest
            if 0<=number_lower<=lower_number:
                weight+=high_factor*comb(counts[lowest],number_lowest)*comb(lower_number,number_lower)
        if weight:rows[triple]=weight
    assert sum(rows.values())==total
    return rows,total

def duel_outcome(sequence,opponent,bonus_difference):
    pa=pb=0;steps=0
    for a,b in zip(sequence,opponent):
        steps+=1;pa+=a+bonus_difference>b;pb+=a+bonus_difference<b
        if pa==2 or pb==2:break
    return (pa>pb)-(pa<pb),steps

def solve_fixed_case(ranks,hand,bonus_difference,opponent_policy='top_desc'):
    counts=Counter({r:4 for r in range(1,ranks+1)})
    for rank in hand:counts[rank]-=1
    rows,total=top_three_distribution(counts)
    if opponent_policy=='top_asc':rows={tuple(reversed(triple)):weight for triple,weight in rows.items()}
    elif opponent_policy=='top_shuffle':
        ordered=defaultdict(int)
        for triple,weight in rows.items():
            unique_orders=set(permutations(triple))
            for sequence in unique_orders:ordered[sequence]+=weight*(6//len(unique_orders))
        rows=dict(ordered);total*=6
    elif opponent_policy!='top_desc':raise ValueError(opponent_policy)
    distributions={}
    for triple,weight in rows.items():
        for length in range(3):
            prefix=triple[:length]
            distributions.setdefault(prefix,defaultdict(int))[triple[length]]+=weight
    policy={}
    @lru_cache(None)
    def optimum(remaining,prefix,pa,pb):
        if pa==2 or pb==2 or len(prefix)==3:return Fraction((pa>pb)-(pa<pb))
        branches=distributions[prefix];denominator=sum(branches.values());best=None;choices=[]
        for card in sorted(set(remaining)):
            rest=list(remaining);rest.remove(card);value=Fraction(0)
            for next_card,weight in branches.items():
                score_a=pa+(card+bonus_difference>next_card);score_b=pb+(card+bonus_difference<next_card)
                value+=Fraction(weight,denominator)*optimum(tuple(rest),prefix+(next_card,),score_a,score_b)
            if best is None or value>best:best=value;choices=[card]
            elif value==best:choices.append(card)
        policy[(remaining,prefix,pa,pb)]=tuple(choices)
        return best
    adaptive=optimum(tuple(sorted(hand)),(),0,0)
    sequence_values=[]
    for sequence in sorted(set(permutations(hand,3))):
        numerator=sum(weight*duel_outcome(sequence,triple,bonus_difference)[0] for triple,weight in rows.items())
        sequence_values.append((Fraction(numerator,total),sequence))
    batch=max(value for value,sequence in sequence_values)
    best_sequences=[sequence for value,sequence in sequence_values if value==batch]
    assert adaptive>=batch
    outcomes=Counter();trace=[]
    for triple,weight in rows.items():
        remaining=tuple(sorted(hand));prefix=();pa=pb=0;own_sequence=[]
        while len(prefix)<3 and pa<2 and pb<2:
            card=min(policy[(remaining,prefix,pa,pb)]);own_sequence.append(card)
            rest=list(remaining);rest.remove(card);remaining=tuple(rest)
            next_card=triple[len(prefix)];pa+=card+bonus_difference>next_card;pb+=card+bonus_difference<next_card;prefix+=(next_card,)
        outcomes[(pa>pb)-(pa<pb)]+=weight
        if len(trace)<5:trace.append({'opponent_rank_sequence':triple,'PC_rank_sequence':own_sequence,'points':[pa,pb],'weight':weight})
    assert sum(outcomes.values())==total
    assert Fraction(outcomes[1]-outcomes[-1],total)==adaptive
    return {'ranks':ranks,'deck':ranks*4,'hand':hand,'bonus_difference':bonus_difference,'opponent_policy':opponent_policy,'possible_opponent_hands':comb(sum(counts.values()),5),'outcome_weight_denominator':total,'policy_order_factor':6 if opponent_policy=='top_shuffle' else 1,'opponent_top_three_rank_sequences':len(rows),'batch_expected_utility':str(batch),'adaptive_expected_utility':str(adaptive),'gain':str(adaptive-batch),'batch_best_orders':best_sequences,'adaptive_initial_choices':policy[(tuple(sorted(hand)),(),0,0)],'adaptive_outcome_weights':{'win':outcomes[1],'hold':outcomes[0],'loss':outcomes[-1]},'information_states_evaluated':optimum.cache_info().currsize,'example_traces':trace}


from collections import Counter,defaultdict
from functools import lru_cache
from itertools import combinations_with_replacement,permutations
from math import comb
from fractions import Fraction
import json,time

def hand_distribution(counts):
    rows=[]
    for hand in combinations_with_replacement(sorted(counts),5):
        required=Counter(hand)
        if any(number>counts[rank] for rank,number in required.items()):continue
        weight=1
        for rank,number in required.items():weight*=comb(counts[rank],number)
        if weight:rows.append((hand,weight))
    assert sum(weight for hand,weight in rows)==comb(sum(counts.values()),5)
    return rows

def npc_choice(hand,observed_prefix,pc_points,npc_points):
    remaining=list(hand)
    for used in observed_prefix:remaining.remove(used)
    if npc_points<pc_points:return max(remaining)
    if npc_points>pc_points:return min(remaining)
    return sorted(remaining)[(len(remaining)-1)//2]

def scores(own,observed,difference):
    return (sum(a+difference>b for a,b in zip(own,observed)),sum(a+difference<b for a,b in zip(own,observed)))

def fixed_trace(order,hand,difference):
    pa=pb=0;observed=[];used=[]
    for card in order:
        other=npc_choice(hand,observed,pa,pb)
        observed.append(other);used.append(card)
        pa+=card+difference>other;pb+=card+difference<other
        if pa==2 or pb==2:break
    return (pa>pb)-(pa<pb),tuple(used),tuple(observed)

def solve_reactive_case(ranks,hand,difference):
    counts=Counter({r:4 for r in range(1,ranks+1)})
    for rank in hand:counts[rank]-=1
    rows=hand_distribution(counts);total=sum(weight for hidden,weight in rows);policy={}
    @lru_cache(None)
    def optimum(remaining,own_prefix,observed_prefix,belief):
        pa,pb=scores(own_prefix,observed_prefix,difference)
        if pa==2 or pb==2 or len(own_prefix)==3:
            return ((pa>pb)-(pa<pb))*sum(rows[i][1] for i in belief)
        groups=defaultdict(list)
        for i in belief:groups[npc_choice(rows[i][0],observed_prefix,pa,pb)].append(i)
        best=None;choices=[]
        for card in sorted(set(remaining)):
            rest=list(remaining);rest.remove(card)
            value=sum(optimum(tuple(rest),own_prefix+(card,),observed_prefix+(other,),tuple(ids)) for other,ids in groups.items())
            if best is None or value>best:best=value;choices=[card]
            elif value==best:choices.append(card)
        key=(remaining,own_prefix,observed_prefix)
        if key in policy:assert policy[key]==tuple(choices), '같은 공개 이력의 선택이 숨은 실제 손패에 따라 바뀌면 안 됩니다.'
        policy[key]=tuple(choices)
        return best
    adaptive_numerator=optimum(tuple(sorted(hand)),(),(),tuple(range(len(rows))))
    values=[]
    for order in sorted(set(permutations(hand,3))):
        numerator=sum(weight*fixed_trace(order,hidden,difference)[0] for hidden,weight in rows)
        values.append((numerator,order))
    batch_numerator=max(numerator for numerator,order in values)
    assert adaptive_numerator>=batch_numerator
    outcomes=Counter();traces=[]
    for hidden,weight in rows:
        remaining=tuple(sorted(hand));own=();observed=();pa=pb=0
        while pa<2 and pb<2 and len(own)<3:
            card=min(policy[(remaining,own,observed)]);other=npc_choice(hidden,observed,pa,pb)
            rest=list(remaining);rest.remove(card);remaining=tuple(rest);own+=(card,);observed+=(other,)
            pa,pb=scores(own,observed,difference)
        outcomes[(pa>pb)-(pa<pb)]+=weight
        if len(traces)<5:traces.append({'hidden_hand':hidden,'own':own,'observed':observed,'points':[pa,pb],'weight':weight})
    assert sum(outcomes.values())==total and outcomes[1]-outcomes[-1]==adaptive_numerator
    return {'ranks':ranks,'deck':ranks*4,'hand':hand,'bonus_difference':difference,'opponent_policy':'public_score_median_chase','possible_opponent_hands':total,'hidden_rank_multisets':len(rows),'batch_expected_utility':str(Fraction(batch_numerator,total)),'adaptive_expected_utility':str(Fraction(adaptive_numerator,total)),'gain':str(Fraction(adaptive_numerator-batch_numerator,total)),'batch_best_orders':[order for numerator,order in values if numerator==batch_numerator],'adaptive_initial_choices':policy[(tuple(sorted(hand)),(),())],'information_states_evaluated':optimum.cache_info().currsize,'adaptive_outcome_hand_counts':{'win':outcomes[1],'hold':outcomes[0],'loss':outcomes[-1]},'example_traces':traces}



v=Path(__file__).resolve().parent;o=v.parent
profile=json.loads((v/'타롯_프로필.json').read_text());checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
check('same existing five-card three-exchange rules',profile['hand']==5 and profile['exchanges_max']==3 and profile['points_to_end']==2)
check('same existing temporary bonus',profile['bonus_rule']=='floor(clamp(T,1,99)/20)')
check('same main-action and five-second contract',profile['representative_main_actions_per_exchange']==1 and profile['combat_exchange_seconds']==5)
check('no new persistent resources',profile['new_persistent_person_resources']==[])
check('no participant trial inferred',profile['actual_participant_playtest'] is False)
check('NPC declared observable-score rule',profile['npc_public_score_policy']['id']=='median_chase')

# 카드ID 조합을 실제 열거하는 독립 축소 덱 대조. 플레이용 새 덱이 아닙니다.
toy_deck=[(s,r) for s in range(4) for r in range(1,6)]
own_ids={(0,r) for r in range(1,6)}
available=[card for card in toy_deck if card not in own_ids]
counts=Counter(rank for suit,rank in available)
actual_hands=Counter();actual_top=Counter()
for physical_hand in combinations(available,5):
    ranks=tuple(sorted(rank for suit,rank in physical_hand))
    actual_hands[ranks]+=1;actual_top[tuple(reversed(ranks[-3:]))]+=1
abstract_hands=dict(hand_distribution(counts));abstract_top,total=top_three_distribution(counts)
check('3003 actual physical-ID opponent hands enumerated',sum(actual_hands.values())==comb(15,5)==3003)
check('rank-multiset weighting equals independent physical-ID enumeration',actual_hands==abstract_hands)
check('top-three marginal formula equals independent physical-ID enumeration',actual_top==abstract_top and total==3003)
for prefix,pa,pb,expected in [((),0,0,3),((3,),1,0,5),((3,),0,1,1),((3,),0,0,2)]:
    check('declared median/chase NPC choice '+str((prefix,pa,pb)),npc_choice((1,2,3,4,5),prefix,pa,pb)==expected)
check('NPC requires no current hidden PC submission','current_PC' not in npc_choice.__code__.co_varnames)

cases=[]
for ranks in (14,13):
    fixtures=[(2,5,8,11,ranks),(5,5,7,9,12),(3,7,9,ranks-1,ranks),(1,2,3,4,5),(1,6,6,10,ranks)]
    for hand in fixtures:
        check('legal distinct physical IDs for benchmark hand '+str((ranks,hand)),all(number<=4 for number in Counter(hand).values()) and min(hand)>=1 and max(hand)<=ranks)
        for difference in (-1,0,1):
            for opponent in ('top_desc','top_asc','top_shuffle','median_chase'):
                if opponent=='median_chase':result=solve_reactive_case(ranks,hand,difference)
                else:result=solve_fixed_case(ranks,hand,difference,opponent)
                result['utility_definition']={'win':1,'hold':0,'loss':-1}
                result['T_A']=50 if difference<=0 else 70;result['T_B']=70 if difference<0 else 50
                assert result['T_A']//20-result['T_B']//20==difference
                assert result['possible_opponent_hands']==comb(ranks*4-5,5)
                assert Fraction(result['adaptive_expected_utility'])>=Fraction(result['batch_expected_utility'])
                assert Fraction(result['gain'])==Fraction(result['adaptive_expected_utility'])-Fraction(result['batch_expected_utility'])
                if opponent=='top_shuffle':
                    assert result['policy_order_factor']==6 and result['outcome_weight_denominator']==result['possible_opponent_hands']*6
                cases.append(result)
    print(json.dumps({'deck':ranks*4,'completed_cases':len(cases)},ensure_ascii=False),flush=True)
check('120 exact declared-policy and fixed-hand cases',len(cases)==120)
fixed_cases=[row for row in cases if row['opponent_policy']!='public_score_median_chase']
reactive_cases=[row for row in cases if row['opponent_policy']=='public_score_median_chase']
check('90 fixed-order policy cases and30 observable reactive policy cases',len(fixed_cases)==90 and len(reactive_cases)==30)
check('all examined fixed-order policies have zero adaptive utility gain',all(Fraction(row['gain'])==0 for row in fixed_cases))
positive=[row for row in cases if Fraction(row['gain'])>0]
check('reactive counterexample exists in each full deck',{row['deck'] for row in positive}=={52,56})
known56=next(row for row in reactive_cases if row['deck']==56 and row['hand']==(1,2,3,4,5) and row['bonus_difference']==-1)
known52=next(row for row in reactive_cases if row['deck']==52 and row['hand']==(1,6,6,10,13) and row['bonus_difference']==-1)
check('56-card reactive fixture exact gain',Fraction(known56['gain'])==Fraction(2117,783020))
check('52-card reactive fixture exact gain',Fraction(known52['gain'])==Fraction(2,66693))
check('conditional NPC can make smaller reserved card useful',known56['batch_best_orders']==[(4,2,5)])
check('mean utility is not a percentile success rate',Fraction(known56['adaptive_expected_utility'])<0 and known56['adaptive_outcome_hand_counts']['win']>0)
states=sum(row['information_states_evaluated'] for row in cases)
result={'id':'TAR-P-02-STRATEGY-01','date':'2026-10-06','checks_passed':len(checks),'checks':checks,'full_deck_fixed_hand_cases':len(cases),'fixed_order_policy_cases':len(fixed_cases),'reactive_policy_cases':len(reactive_cases),'independent_physical_ID_hand_enumerations':3003,'information_states_evaluated':states,'positive_adaptive_gain_cases':len(positive),'fixed_policy_zero_gain_cases':len(fixed_cases),'cases':cases,'claims':{'exact_best_response_in_declared_fixtures':True,'adaptive_sequential_strategy_tested':True,'all_possible_PC_hands_tested':False,'global_optimal_strategy_proven':False,'mutual_optimal_or_Nash_strategy_proven':False,'new_rules_or_persistent_resources_added':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False,'paradise_fleet_original_rules_compared':False,'enough_card_selection_depth_for_release':False}}
result['scope_note']='선택한 PC 손패10종·보너스 차이3종·사전 지정 상대 정책4종을 계산했다. 상대5장의 모든 실제 카드ID 조합을 확률 가중했으며, 상위 카드 무작위 순서는 추가6배 가중을 별도 기록한다. NPC와 PC의 매 교환 선택은 이전 공개 카드/점수만 참조한다. 최선 일괄/순차 대응의 기대값은 승리1/동률0/패배-1이고, 백분율 성공률이나 실제 재미/전원 최적 전략의 증거가 아니다.'
result['artifacts_sha256']={str(f.relative_to(o)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [o/'02_타롯_해킹과_지능전_초안.md',v/'타롯_프로필.json',Path(__file__)]}
(v/'타롯_전략검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['checks_passed','full_deck_fixed_hand_cases','information_states_evaluated','positive_adaptive_gain_cases','fixed_policy_zero_gain_cases']},ensure_ascii=False))
