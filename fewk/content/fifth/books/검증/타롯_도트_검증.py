"""TAR-P-03 v0.4 arithmetic, state transitions and limited policy simulation.

Run with Python 3, no dependencies. This is an executable rules check, not
an implementation of every optional equipment skill or human playtest.
"""
import collections
import itertools
import json
import random
import statistics
from pathlib import Path

def deck(size=56):
    ranks=['2','3','4','5','6','7','8','9','10','P']+(['N'] if size==56 else [])+['Q','K','A']
    return [r+s for r in ranks for s in 'SHCD']

def rank(cards, size=56):
    if not cards or len(cards)>5 or len(set(cards))!=len(cards): return None
    order={c[:-1]:i+2 for i,c in enumerate(deck(size)[::4])}
    if any(c not in deck(size) for c in cards): return None
    values=sorted((order[c[:-1]] for c in cards),reverse=True)
    counts=collections.Counter(values)
    groups=sorted(((n,v) for v,n in counts.items()),reverse=True)
    n=len(cards)
    if n==1:return (0,values[0])
    if n==2 and len(counts)==1:return (1,values[0])
    if n==3 and len(counts)==1:return (3,values[0])
    if n==4:
        if len(counts)==1:return (7,values[0])
        if [g[0] for g in groups]==[2,2]:return (2,groups[0][1],groups[1][1])
    if n==5:
        flush=len({c[-1] for c in cards})==1
        straight=0
        if len(counts)==5:
            if values[0]-values[-1]==4:straight=values[0]
            elif values==[order['A'],5,4,3,2]:straight=5
        if straight and flush:return (8,straight)
        if [g[0] for g in groups]==[3,2]:return (6,groups[0][1],groups[1][1])
        if flush:return (5,*values)
        if straight:return (4,straight)
    return None

def spend(level,dots,count):
    if not 1<=level<=5 or not 0<=count<=5:raise ValueError('level/count')
    cost=max(0,count-level)
    if dots-cost<1:raise ValueError('must retain one dot')
    return cost

def damage(a,b):
    if a==b:return None,0
    winner=0 if (b is None or a is not None and a>b) else 1
    high,low=(a,b) if winner==0 else (b,a)
    gap=high[0]-(low[0] if low else 0)
    return winner,1 if gap<=1 else 2 if gap<=3 else 3

def select(pool,held,played,discarded,level,dots,size=56):
    if len(set(pool))!=len(pool) or not set(held)<=set(pool):raise ValueError('pool')
    out=list(played)+list(discarded)
    if len(set(out))!=len(out) or not set(out)<=set(pool):raise ValueError('selected cards')
    if set(held)&set(discarded):raise ValueError('held ordinary discard')
    hand=rank(played,size)
    if played and hand is None:raise ValueError('not an exact made hand')
    cost=spend(level,dots,len(played))
    return dict(pool=[c for c in pool if c not in out],held=[c for c in held if c not in played],rank=hand,cost=cost,discard=out)

def replenish(pools,modes,stock,discard,rng,first):
    # Called after resolution, only if the duel has not ended.
    targets=[len(p) if mode==10 else mode for p,mode in zip(pools,modes)]
    while any(len(p)<n for p,n in zip(pools,targets)):
        for i in (first,1-first):
            if len(pools[i])>=targets[i]:continue
            if not stock:
                stock.extend(discard);discard.clear();rng.shuffle(stock)
            if not stock:raise ValueError('empty shared deck')
            pools[i].append(stock.pop())

def hold(pool,held,card):
    if card not in pool or card in held:raise ValueError('hold target')
    return held+[card]

def available_swap(mode,held,card):return mode!=10 and card not in held

def reserve_end(pools,modes,dots):
    if 0 in dots:return 'dot_end'
    exhausted=[i for i in (0,1) if modes[i]==10 and not pools[i]]
    return 'draw' if len(exhausted)==2 else 'withdraw_'+str(exhausted[0]) if exhausted else None

def choices(pool,level,dots,size,boost):
    result=[]
    limit=min(5,level+dots-1 if boost else level)
    for n in range(1,min(len(pool),limit)+1):
        for cs in itertools.combinations(sorted(pool),n):
            value=rank(cs,size)
            if value is not None:result.append((value,-spend(level,dots,n),cs))
    return max(result)[2]

def checks():
    passed=[]
    def check(name,ok):
        assert ok,name
        passed.append(name)
    def rejected(fn):
        try:fn()
        except ValueError:return True
        return False
    check('KK9 is not a made hand',rank(['KS','KH','9C']) is None)
    check('three-card flush is invalid',rank(['2S','4S','6S']) is None)
    check('two-pair below triple',rank(['KS','KH','9S','9H'])<rank(['2S','2H','2C']))
    check('four-card quads are valid',rank(['9S','9H','9C','9D'])[0]==7)
    check('quads cannot carry a kicker',rank(['9S','9H','9C','9D','KS']) is None)
    check('one-card high card',rank(['9S'])==(0,9))
    check('suits do not break ties',damage(rank(['KS','KH']),rank(['KC','KD']))==(None,0))
    for size in (52,56):
        check(f'{size}: ace low',rank(['AS','2H','3C','4D','5S'],size)==(4,5))
        top=['PS','NH','QC','KD','AS'] if size==56 else ['10S','PH','QC','KD','AS']
        check(f'{size}: ace high straight',rank(top,size)==(4,15 if size==56 else 14))
        check(f'{size}: no wraparound',rank(['KS','AH','2C','3D','4S'],size) is None)
    check('single play requires no extra dot at level 5',spend(5,1,1)==0)
    check('level2 triple costs1',spend(2,5,3)==1)
    check('level2 full house costs3',spend(2,5,5)==3)
    check('cannot spend last dot',rejected(lambda:spend(2,1,3)))
    check('cannot exceed 5 cards',rejected(lambda:spend(5,5,6)))
    pool=['KS','KH','9S','7C','2D']
    check('held card cannot ordinary-discard',rejected(lambda:select(pool,['9S'],['KS','KH'],['9S'],2,5)))
    stay=select(pool,['9S'],['KS','KH'],['7C','2D'],2,5)
    check('hold occupies remaining pool slot',stay['pool']==['9S'] and stay['held']==['9S'])
    release=select(pool,['9S'],['9S'],['KS','KH','7C','2D'],2,5)
    check('single held card clears even on losing play',release['pool']==[] and release['held']==[] and damage(release['rank'],rank(['KS','KH','QS','QH']))==(1,2))
    allout=select(pool,[],['KS','KH'],['9S','7C','2D'],2,5)
    check('all five cycle but only pair costs count',not allout['pool'] and allout['cost']==0)
    check('full ordinary discard allowed',not select(pool,[],[],pool,1,5)['pool'])
    check('empty play loses as high-card category',damage(None,rank(['KS','KH','QS','QH']))==(1,2))
    check('both empty tie',damage(None,None)==(None,0))
    check('damage success1 good2 excellent3',[damage((n,9),(0,2))[1] for n in (0,1,2,3,4,8)]==[1,1,2,2,3,3])
    check('boost paid before additional loss',5-spend(2,5,3)-damage((3,9),(6,13,8))[1]==2)
    check('boost not refunded on tie',5-spend(2,5,3)==4 and damage((3,9),(3,9))==(None,0))
    pools=[['9S'],[]];stock=[c for c in deck() if c!='9S'];discard=[]
    replenish(pools,[5,6],stock,discard,random.Random(1),0)
    check('refill includes hold and supports6',list(map(len,pools))==[5,6] and '9S' in pools[0])
    check('shared cards conserved',len(set(pools[0]+pools[1]+stock))==56)
    check('hold after refill remains total5',len(pools[0])==5 and len(hold(pools[0],[],pools[0][0]))==1)
    check('cannot hold same card twice',rejected(lambda:hold(pools[0],[pools[0][0]],pools[0][0])))
    pools=[[],[]];stock=[];discard=deck()
    replenish(pools,[5,5],stock,discard,random.Random(2),1)
    check('discard-only reshuffle conserves56',len(set(pools[0]+pools[1]+stock+discard))==56 and not discard)
    pools=[deck()[:4],[]];stock=deck()[4:];discard=[]
    replenish(pools,[10,5],stock,discard,random.Random(3),0)
    check('10 reserve never refills below5',list(map(len,pools))==[4,5])
    check('10 reserve cannot situation-swap',not available_swap(10,[],'KS'))
    check('held cannot situation-swap',not available_swap(5,['KS'],'KS'))
    check('empty reserve withdraws',reserve_end([[],['KS']],[10,5],[1,1])=='withdraw_0')
    check('both empty reserves draw',reserve_end([[],[]],[10,10],[1,1])=='draw')
    check('dot end precedes reserve exhaustion',reserve_end([[],[]],[10,10],[1,0])=='dot_end')
    # Concrete sequential example, including continuity and card uniqueness.
    pools=[['9S','9H','9C','7D','2C'],['KS','KH','6S','4D','3C']]
    rounds=[
        ([['9S','9H','9C'],['KS','KH']],[['7D','2C'],['4D','3C']],[['QS','QH','QC','8D','6H'],['PS','PH','7S','7H']],[4,3]),
        ([['8D'],['PS','PH']],[['6H'],['6S']],[['6D','6C'],['7C','5S','5H']],[3,3]),
        ([['QS','QH','QC'],['7S','7H','7C']],[[],[]],[['AS','10H','4C'],['KD','8C','2H']],[2,1]),
        ([['6D','6C'],['5S','5H']],[[],[]],[[],[]],[2,0])]
    dots=[5,5];seen=set(pools[0]+pools[1]);trace=[]
    for ix,(plays,discards,draws,expected) in enumerate(rounds,1):
        moves=[select(pools[i],[],plays[i],discards[i],2,dots[i]) for i in (0,1)]
        dots=[dots[i]-moves[i]['cost'] for i in (0,1)]
        winner,harm=damage(moves[0]['rank'],moves[1]['rank'])
        if winner is not None:dots[1-winner]=max(0,dots[1-winner]-harm)
        check(f'example round{ix} dots',dots==expected)
        for i in (0,1):
            assert not set(draws[i])&seen
            seen.update(draws[i]);pools[i]=moves[i]['pool']+draws[i]
        check(f'example round{ix} continuity',len(set(pools[0]+pools[1]))==sum(map(len,pools)) and (0 in dots or list(map(len,pools))==[5,5]))
        trace.append(dict(round=ix,dots=list(dots),pools=[list(p) for p in pools]))
    return passed,trace

def simulate(size,levels,boost,seed,count=200):
    rng=random.Random(seed);wins=[0,0];censored=0;lengths=[];costs=[]
    for _ in range(count):
        stock=deck(size);rng.shuffle(stock);discard=[];pools=[[],[]];dots=[5,5];spent=[0,0]
        replenish(pools,[5,5],stock,discard,rng,0)
        for r in range(1,81):
            plays=[choices(pools[i],levels[i],dots[i],size,boost) for i in (0,1)]
            moves=[select(pools[i],[],plays[i],[c for c in pools[i] if c not in plays[i]],levels[i],dots[i],size) for i in (0,1)]
            dots=[dots[i]-moves[i]['cost'] for i in (0,1)]
            spent=[spent[i]+moves[i]['cost'] for i in (0,1)]
            winner,harm=damage(moves[0]['rank'],moves[1]['rank'])
            if winner is not None:dots[1-winner]=max(0,dots[1-winner]-harm)
            for i in (0,1):discard.extend(moves[i]['discard']);pools[i]=moves[i]['pool']
            assert len(set(stock+discard+pools[0]+pools[1]))==size
            if 0 in dots:
                wins[1-dots.index(0)]+=1;lengths.append(r);costs.append(spent);break
            replenish(pools,[5,5],stock,discard,rng,(r+1)%2)
        else:censored+=1
    return dict(deck=size,levels=levels,policy='strongest_affordable' if boost else 'no_boost_strongest',seed=seed,duels=count,wins=wins,censored_at80=censored,mean_rounds=round(statistics.mean(lengths),3) if lengths else None,median_rounds=statistics.median(lengths) if lengths else None,mean_dot_spend=[round(statistics.mean(c[i] for c in costs),3) for i in (0,1)] if costs else None)

if __name__=='__main__':
    here=Path(__file__).resolve().parent
    passed,trace=checks()
    simulations=[simulate(size,levels,boost,261013+ix) for ix,(size,levels,boost) in enumerate(itertools.product((52,56),((1,1),(4,4),(4,5)),(False,True)))]
    result=dict(profile='TAR-P-03',version='0.4',date='2026-10-13',passed=len(passed),checks=passed,worked_example=trace,simulations=simulations,limits=['Policies use only own cards, choose highest rank and discard all unused cards. They do not optimize future hands or remaining dots.','Simulation covers ordinary five-card duels only; optional states have deterministic checks, not balance simulations.','These small fixed-policy samples are not balanced win-rate claims. 4 vs 5 human growth experience remains untested.','80-round cap only censors simulations; it is not a duel rule.'],human_playtest=dict(selection_seconds=None,other_participant_wait_seconds=None,level4_to5_experience=None))
    (here/'타롯_도트_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=len(passed),simulated_duels=sum(s['duels'] for s in simulations),censored=sum(s['censored_at80'] for s in simulations),results=simulations),ensure_ascii=False))
