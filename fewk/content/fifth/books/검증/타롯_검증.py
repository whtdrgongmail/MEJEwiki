"""TAR-P-02 whole-duel mathematics and declared boundary cases; no human trial claim."""
from pathlib import Path
from itertools import permutations,product
from collections import Counter
import random,json,hashlib
v=Path(__file__).parent;o=v.parent
profile=json.loads((v/'타롯_프로필.json').read_text())
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
def bonus(t):
    if not isinstance(t,int) or not 1<=t<=99:raise ValueError('final T must be 1..99')
    return t//20
def deck(n):
    return [(s,r) for s in range(4) for r in range(1,15 if n==56 else 14)]
def deal(n,rng):
    cards=rng.sample(deck(n),10);return cards[:5],cards[5:]
def validate(cards,hand,n):
    return len(cards)==3 and len(set(cards))==3 and len(hand)==5 and len(set(hand))==5 and set(cards)<=set(hand)<=set(deck(n))
def duel(a,b,ta,tb,retreat_after=None,stop_before=None):
    points=[0,0];rows=[]
    for i,(ca,cb) in enumerate(zip(a,b),1):
        if stop_before==i:return {'outcome':'interrupted','exchanges':i-1,'points':points,'rows':rows,'effect_count':0}
        va=ca[1]+bonus(ta);vb=cb[1]+bonus(tb)
        winner=0 if va>vb else 1 if vb>va else None
        if winner is not None:points[winner]+=1
        rows.append((va,vb,winner))
        if 2 in points:break
        if retreat_after==i:return {'outcome':'retreat','exchanges':i,'points':points,'rows':rows,'effect_count':0}
    outcome='A' if points[0]>points[1] else 'B' if points[1]>points[0] else 'hold'
    return {'outcome':outcome,'exchanges':len(rows),'points':points,'rows':rows,'effect_count':1 if outcome!='hold' else 0}
def policy(hand,name,rng):
    if name=='random_three':return rng.sample(hand,3)
    top=sorted(hand,key=lambda c:(c[1],c[0]),reverse=True)[:3]
    if name=='top_desc':return top
    if name=='top_asc':return list(reversed(top))
    if name=='top_shuffle':rng.shuffle(top);return top
    if name=='top_middle_first':return [top[1],top[0],top[2]]
    raise ValueError(name)

for n in (52,56):
    d=deck(n);check(f'deck {n}: unique IDs',len(d)==len(set(d))==n)
    check(f'deck {n}: four equal suits',all(sum(c[0]==s for c in d)==n//4 for s in range(4)))
    check(f'deck {n}: ranks continuous',set(c[1] for c in d)==set(range(1,n//4+1)))
    ha,hb=deal(n,random.Random(n));check(f'deck {n}: shared no replacement',len(set(ha+hb))==10)
    check(f'deck {n}: legal ordered choice',validate(ha[:3],ha,n))
    check(f'deck {n}: duplicate submission rejected',not validate([ha[0],ha[0],ha[1]],ha,n))
    check(f'deck {n}: opponent card rejected',not validate([ha[0],ha[1],hb[0]],ha,n))
    check(f'deck {n}: extra cards rejected',not validate(ha[:4],ha,n))
    check(f'deck {n}: fewer cards rejected',not validate(ha[:2],ha,n))
check('52 range rejects King14',not validate([(0,14),(0,1),(0,2)],[(0,14),(0,1),(0,2),(0,3),(0,4)],52))
for t,b in [(1,0),(19,0),(20,1),(39,1),(40,2),(59,2),(60,3),(79,3),(80,4),(99,4)]:check(f'bonus T{t}={b}',bonus(t)==b)
check('all 1..99 targets covered',all(0<=bonus(t)<=4 for t in range(1,100)))
check('each nonclamped +20 raises bonus one',all(bonus(t+20)==bonus(t)+1 for t in range(1,80)))
check('help T70+20 => T90 b4, once',bonus(min(99,70+20))==4)
check('help ceiling T90+20 => T99 b4',bonus(min(99,90+20))==4)
for t in (0,100,-1):
    try:bonus(t);ok=False
    except ValueError:ok=True
    check(f'invalid final T{t} rejected',ok)
a=[(0,9),(2,6),(1,13)];b=[(3,10),(2,13),(1,8)]
x=duel(a,b,70,50)
check('printed example scores',x['rows']==[(12,12,None),(9,15,1),(16,10,0)])
check('printed example final tie and max15 seconds',x['outcome']=='hold' and x['exchanges']*5==15 and x['effect_count']==0)
check('tie no fourth exchange',duel([(0,7)]*3,[(1,7)]*3,50,50)['exchanges']==3)
check('one-zero is win',duel([(0,8),(0,7),(0,7)],[(1,7)]*3,50,50)['outcome']=='A')
check('two-zero ends on second exchange',duel([(0,14)]*3,[(1,1)]*3,50,50)['exchanges']==2)
check('win effect once, unused third remains',duel([(0,14)]*3,[(1,1)]*3,50,50)['effect_count']==1)
check('both miss concept absent from cards: tied values hold',duel([(0,2)]*3,[(1,2)]*3,50,50)['outcome']=='hold')
check('before first exchange interrupt has no actions resolved',duel(a,b,70,50,stop_before=1)['exchanges']==0)
check('interrupt after one tie no goal effect',duel(a,b,70,50,stop_before=2)['effect_count']==0)
check('completed exchange retained on interrupt',duel(a,b,70,50,stop_before=3)['points']==[0,1])
check('retreat after first tie skips remaining orders',duel(a,b,70,50,retreat_after=1)['outcome']=='retreat')
check('retreat keeps already resolved loss',duel(a,b,70,50,retreat_after=2)['points']==[0,1])
check('win cannot be retrospectively withdrawn',duel([(0,14)]*3,[(1,1)]*3,50,50,retreat_after=2)['outcome']=='A')

# Independent full three-comparison oracle: early 2-point ending must give same victor.
oracle_cases=0
for ar,br,ta,tb in product(range(1,15),range(1,15),(1,50,99),(1,50,99)):
    a=[(0,ar),(0,5),(0,14)];b=[(1,br),(1,10),(1,1)]
    signed=sum((ca[1]+bonus(ta)>cb[1]+bonus(tb))-(ca[1]+bonus(ta)<cb[1]+bonus(tb)) for ca,cb in zip(a,b))
    expected='A' if signed>0 else 'B' if signed<0 else 'hold'
    assert duel(a,b,ta,tb)['outcome']==expected
    oracle_cases+=1
check('early-stop outcomes match independent full-comparison oracle',oracle_cases==1764)

# Exact ordering enumeration on the example's top three: values are distinct IDs.
ha=[(0,r) for r in (2,5,8,11,14)];hb=[(1,r) for r in (3,6,9,10,13)]
exact=Counter();all_orders=Counter();dominance_cases=0
for aa,bb in product(permutations(ha[-3:]),permutations(hb[-3:])):exact[duel(aa,bb,50,50)['outcome']]+=1
for aa,bb in product(permutations(ha,3),permutations(hb,3)):
    all_orders[duel(aa,bb,50,50)['outcome']]+=1
    # Increasing any chosen card to an unused higher card can't worsen that exchange
    # or the full fixed opponent outcome. A > hold > B ordered independently.
    rank={'A':2,'hold':1,'B':0};old=rank[duel(aa,bb,50,50)['outcome']]
    for pos,card in enumerate(aa):
        for higher in ha:
            if higher not in aa and higher[1]>card[1]:
                changed=list(aa);changed[pos]=higher
                assert rank[duel(changed,bb,50,50)['outcome']]>=old
                dominance_cases+=1
check('ordering can change full winner',exact['A']>0 and exact['B']>0)
check('36 sealed top-three ordering pairs',sum(exact.values())==36)
check('3600 sealed 5P3 choice pairs',sum(all_orders.values())==3600)
check('larger replacement never harms against fixed order',dominance_cases>0)

# Declared state timing examples: shared core budgets and effect boundaries.
def budgets(exchanges):return {'seconds':exchanges*5,'representative_main':exchanges,'other_actor_main_max':exchanges,'representative_extra_attacks':0}
check('two-exchange win consumes10 sec and2 mains',budgets(2)=={'seconds':10,'representative_main':2,'other_actor_main_max':2,'representative_extra_attacks':0})
check('three-exchange max15 sec, support has three turns',budgets(3)['other_actor_main_max']==3)
check('no main attack in addition to submitted exchange',budgets(3)['representative_extra_attacks']==0)
check('long residence clock at15 seconds one shared interval',15/3600==1/240)
check('no new persistent personality resources',profile['new_persistent_person_resources']==[])
check('no user test claim',profile['actual_participant_playtest'] is False)
check('not original PF reproduction',profile['paradise_fleet_rules_reproduction'] is False)

policies=[('random_three','random_three'),('top_desc','top_desc'),('top_shuffle','top_shuffle'),('top_middle_first','top_desc'),('top_asc','top_desc')]
simulations=[];sample_n=10000;seed=20261005
for n in (56,52):
    for ta,tb in ((50,50),(70,50),(90,50)):
        for pi,(pa,pb) in enumerate(policies):
            # Same deals for all policies at the same deck/skill pair; independent policy RNG.
            dr=random.Random(seed+n);pr=random.Random(seed+n+pi*100+ta)
            counts=Counter();steps=0
            for _ in range(sample_n):
                aa,bb=deal(n,dr)
                ra=policy(aa,pa,pr);rb=policy(bb,pb,pr)
                assert validate(ra,aa,n) and validate(rb,bb,n) and not set(aa)&set(bb)
                x=duel(ra,rb,ta,tb);counts[x['outcome']]+=1;steps+=x['exchanges']
            assert sum(counts.values())==sample_n
            simulations.append({'deck':n,'T_A':ta,'T_B':tb,'policies':[pa,pb],'duels':sample_n,'counts':dict(counts),'mean_exchanges':steps/sample_n})
check('30 complete fixed-policy samples, 300000 duels',len(simulations)==30)
result={'profile':profile['id'],'date':'2026-10-05','checks_passed':len(checks),'checks':checks,'independent_oracle_cases':oracle_cases,'exact_example_top_three_orders':dict(exact),'exact_example_all_three_choices':dict(all_orders),'fixed_opponent_monotonic_replacements':dominance_cases,'simulation_seed':seed,'whole_duel_simulations':simulations,'total_simulated_duels':len(simulations)*sample_n,'claims':{'actual_participant_playtest':False,'optimal_strategy_proven':False,'adaptive_sequential_strategy_tested':False,'same_win_probability_as_percentile':False,'paradise_fleet_original_rules_compared':False,'enough_card_selection_depth_for_release':False},'artifacts_sha256':{str(f.relative_to(o)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [o/'02_타롯_해킹과_지능전_초안.md',v/'타롯_프로필.json',Path(__file__)]}}
(v/'타롯_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'whole_duels':300000,'order_example':dict(exact),'actual_participant_playtest':False},ensure_ascii=False))
