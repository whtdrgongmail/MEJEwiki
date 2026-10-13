#!/usr/bin/env python3
"""세 시험 인터랙션의 판정·시간·저장 보존 검산. 전체 게임 엔진/참가자 시험 아님."""
from pathlib import Path
from itertools import product
from collections import Counter
import json,hashlib
from 백분율_코어검증 import grade,target

here=Path(__file__).parent
profile=json.loads((here/'고유효과_프로필.json').read_text())

def charge(body,supply,elapsed,compatible=True):
    # 시험 장치의 완료 때 원자적 이전. 중단/미지원/포화 시 이전하지 않음.
    if compatible and elapsed>=30 and body<2 and supply>=1:
        return body+1,supply-1
    return body,supply

def output(body,lamp,compatible=True):
    if compatible and body>=1 and 0<=lamp<=1800:
        return body-1,lamp+1800
    return body,lamp

def marking_live(body_id,marked_body,now,expires,active=True,compatible=True,hp=1):
    return body_id==marked_body and active and compatible and hp>0 and now<expires

def marking_activation_valid(now,expires,charge=1,main=1,actor_hp=1,compatible=True):
    return charge>0 and main>0 and actor_hp>0 and compatible and now+5<expires

def mark_travel(state,route_open=True,permission=True,arrival=True,ban=False):
    # 같은 몸을 한 위치에서 다른 위치로 옮긴다. 복제 기능은 이 도안에 없다.
    from copy import deepcopy
    out=deepcopy(state)
    allowed=marking_activation_valid(state['now'],state['expires'],state['charge'],state['main'],state['hp'])
    if not (allowed and state['realm']=='MARK-A' and state['body']==state['marked_body'] and route_open and permission and arrival and not ban):return out
    out.update(realm='MARK-B',now=state['now']+5,charge=state['charge']-1,main=state['main']-1)
    return out

def mark_call(state,accepted=True,sight=True,empty=True,distance=20,same_realm=True):
    from copy import deepcopy
    out=deepcopy(state)
    a,t=state['actor'],state['target']
    allowed=marking_activation_valid(state['now'],state['expires'],state['charge'],a['main'],a['hp'])
    if not (allowed and accepted and sight and empty and 0<=distance<=20 and same_realm and t['body']==state['registered_body'] and t['reaction']>0 and t['hp']>0):return out
    out['now']+=5;out['charge']-=1;out['actor']['main']-=1;out['target']['reaction']-=1
    out['target']['position']=state['arrival_position']
    return out

def mark_seal(state,ra,rd=None,in_contact=True,target_supported=True):
    from copy import deepcopy
    from 백분율_코어검증 import contest
    out=deepcopy(state)
    allowed=marking_activation_valid(state['now'],state['expires'],state['charge'],state['main'],state['hp'])
    if not (allowed and in_contact and target_supported and state['target_body']==state['registered_body'] and state['target_hp']>0 and not state['sealed']):return out
    out['now']+=5;out['charge']-=1;out['main']-=1
    if state['target_reaction']>0:
        assert rd is not None
        out['target_reaction']-=1
        hit=contest(50,ra,50,rd)==1
    else:hit=grade(50,ra)>0
    if hit:out.update(sealed=True,seal_end=min(out['now']+60,state['expires']))
    return out

def mark_work(state,seconds,allowed=True,success=True):
    from copy import deepcopy
    out=deepcopy(state)
    if not allowed or seconds<=0 or state['completed']:return out
    if not state['started']:
        if state['kits']<1:return out
        out['kits']-=1;out['spent']+=1;out['started']=True
    used=min(seconds,300-state['progress'])
    out['progress']+=used;out['clock']+=used
    if out['progress']==300:
        out['completed']=True
        if success:out.update(outputs=1,expires=out['clock']+600)
    return out

def marking_checks():
    from copy import deepcopy
    from 백분율_코어검증 import contest,exact_case
    notes=[];boundaries=0
    def verify(name,actual,expected):
        assert actual==expected,(name,actual,expected);notes.append(name)
    m=profile['marking']
    verify('same engine and no added stats',(profile['engine'],m['additional_person_stats'],m['formation_tracks_added']),('P-FEWK-0.2',[],False))
    verify('four named functions',[m[k]['id'] for k in ('boost','travel','summon','seal')],['MARK-BOOST-01','MARK-IO-01','MARK-CALL-01','MARK-SEAL-01'])
    verify('preparation/time/action units',(m['preparation']['seconds'],m['preparation']['lifetime_seconds_after_completion'],m['activation']['seconds']),(300,600,5))
    # 분할 작업은 같은 재료/작업ID를 이어 사용하고 완료 도안을 중복 지급하지 않는다.
    initial={'job':'JOB-M1','clock':0,'progress':0,'started':False,'completed':False,'kits':2,'spent':0,'outputs':0}
    for a in range(301):
        partial=mark_work(initial,a)
        if a<300:assert partial['outputs']==0
        finished=mark_work(partial,300-a)
        assert finished['job']=='JOB-M1' and finished['progress']==300
        assert finished['clock']==300 and finished['outputs']==1 and finished['expires']==900
        assert finished['kits']==1 and finished['spent']==1
        assert mark_work(finished,300)==finished;boundaries+=1
    paused=mark_work(initial,100);paused['clock']+=60
    resumed=mark_work(paused,200)
    verify('pause time and one kit preserved',(resumed['clock'],resumed['expires'],resumed['spent']),(360,960,1))
    verify('failed production has no output',mark_work(initial,300,success=False)['outputs'],0)
    verify('invalid work does not consume',mark_work(initial,300,allowed=False),initial)
    verify('body/use origins',m['boost']['follows_body_id'] and not m['boost']['copy_to_another_body'],True)
    for body,active,compatible,hp,now in product(('B-M2','B-M3'),(False,True),(False,True),(0,1,12),(0,599,600,601)):
        live=marking_live(body,'B-M2',now,600,active,compatible,hp)
        assert live==(body=='B-M2' and active and compatible and hp>0 and now<600)
        # 다른 몸은 같은 인물의 숙련을 읽지만 도안의 보정을 복사하지 않는다.
        points=20 if live else 0
        t=target(50,points)
        assert t in (50,70);boundaries+=1
    verify('bonus once with preparation',target(50,20),70)
    verify('adverse cancels positive',target(50,0),50)
    verify('last valid cast start',marking_activation_valid(594,600),True)
    verify('known expiry at finish',marking_activation_valid(595,600),False)
    verify('no actor action',marking_activation_valid(0,600,main=0),False)
    travel={'body':'B-M2','marked_body':'B-M2','realm':'MARK-A','now':0,'expires':600,'charge':1,'main':1,'hp':7,'ego':6,'inventory':{'ammo':3,'shield':0,'mark':'M1'},'growth':55,'aid_used':True}
    moved=mark_travel(travel)
    verify('travel same body/hp/items',[(moved[k],travel[k]) for k in ('body','hp','ego','inventory','growth','aid_used')],[(travel[k],travel[k]) for k in ('body','hp','ego','inventory','growth','aid_used')])
    verify('travel new location and spent budgets',(moved['realm'],moved['charge'],moved['main'],moved['now']),('MARK-B',0,0,5))
    verify('no return/recast from copy',mark_travel(moved),moved)
    wrong_origin=deepcopy(travel);wrong_origin['realm']='MARK-X'
    verify('registered origin is required',mark_travel(wrong_origin),wrong_origin)
    wrong_body=deepcopy(travel);wrong_body['body']='B-M3'
    verify('skin route does not follow another body',mark_travel(wrong_body),wrong_body)
    for route,permission,arrival,ban in product((False,True),repeat=4):
        out=mark_travel(travel,route,permission,arrival,ban)
        allowed=route and permission and arrival and not ban
        assert (out['realm']=='MARK-B')==allowed
        if not allowed:assert out==travel
        assert out['inventory']==travel['inventory'] and out['hp']==7 and out['ego']==6;boundaries+=1
    call={'now':0,'expires':600,'charge':1,'registered_body':'B-S1','arrival_position':1,'actor':{'id':'P-M1','body':'B-M1','main':1,'reaction':1,'hp':12,'position':0},'target':{'id':'S-M1','body':'B-S1','main':0,'reaction':1,'hp':7,'position':20,'items':3}}
    wrong_called_body=deepcopy(call);wrong_called_body['target']['body']='B-S2'
    verify('registered summon target required',mark_call(wrong_called_body),wrong_called_body)
    summoned=mark_call(call)
    verify('target does not regain action',(summoned['target']['main'],summoned['target']['reaction'],summoned['target']['position']),(0,0,1))
    verify('target same body/items/hp',[(summoned['target'][k],call['target'][k]) for k in ('id','body','hp','items')],[(call['target'][k],call['target'][k]) for k in ('id','body','hp','items')])
    for accept,sight,empty,same,react,distance in product((False,True),(False,True),(False,True),(False,True),(0,1),(-1,19,20,21)):
        s=deepcopy(call);s['target']['reaction']=react;out=mark_call(s,accept,sight,empty,distance,same)
        allowed=accept and sight and empty and same and react>0 and 0<=distance<=20
        assert (out['charge']==0)==allowed
        if not allowed:assert out==s
        assert out['target']['main']==0 and out['target']['hp']==7;boundaries+=1
    seal={'now':0,'expires':600,'charge':1,'target_body':'B-S1','registered_body':'B-S1','main':1,'hp':12,'target_hp':7,'target_reaction':1,'sealed':False,'ego':6}
    wrong_sealed_body=deepcopy(seal);wrong_sealed_body['target_body']='B-S2'
    verify('seal target is a body not shared person',mark_seal(wrong_sealed_body,17,38),wrong_sealed_body)
    counts=Counter()
    for ra,rd in product(range(1,101),repeat=2):
        out=mark_seal(seal,ra,rd);counts[out['sealed']]+=1
        assert out['charge']==0 and out['main']==0 and out['target_reaction']==0
        assert out['target_hp']==7 and out['hp']==12 and out['ego']==6
        if out['sealed']:assert out['seal_end']==65
        boundaries+=1
    # 성공 수준 분포를 곱한 독립 대조: T50의 성공 군은10/15/25이다.
    successes=[10,15,25]
    hits=sum(successes[i]*(50+sum(successes[:i])) for i in range(3))+sum(n*(n-1)//2 for n in successes)
    verify('seal 10000 pairs against independent groups',counts[True],hits)
    verify('seal matched ordinary defended hit',counts[True]/100,exact_case(50,50)['defended_attack_hit_percent'])
    verify('seal both fail and exact tie',(mark_seal(seal,99,99)['sealed'],mark_seal(seal,17,17)['sealed']),(False,False))
    for reaction,ra in product((0,1),range(1,101)):
        s=deepcopy(seal);s['target_reaction']=reaction;out=mark_seal(s,ra,100 if reaction else None)
        assert out['sealed']==(ra<=50) and out['target_reaction']==0;boundaries+=1
    s=deepcopy(seal);s['now']=594;last=mark_seal(s,17,38)
    verify('one second remaining after last cast',(last['now'],last['seal_end'],last['seal_end']-last['now']),(599,600,1))
    s['now']=595;verify('invalid before cast no cost',mark_seal(s,17,38),s)
    s=mark_seal(seal,17,38);s['charge']=1;s['main']=1
    verify('second seal does not refresh',mark_seal(s,17,38),s)
    escape_counts=Counter(contest(50,ra,50,rd)==1 for ra,rd in product(range(1,101),repeat=2))
    verify('escape same ordinary comparison',escape_counts[True],hits)
    verify('escape consumes its main only',(m['seal']['escape_main_actions'],m['seal']['escape_comparison_consumes_caster_reaction']),(1,False))
    verify('paper zero armor can be broken',max(0,4-m['seal']['glyph_armor'])>=m['seal']['glyph_HP'],True)
    verify('not absolute cover/damage/person injury',(m['seal']['blocks_projectile_lines'],m['seal']['damage_on_success'],m['seal']['body_change_affects_person_or_other_body']),(False,0,False))
    return notes,boundaries


def interaction_available(scene,function):
    # Eligibility for three declared functions, derived from actual actor/body/
    # medium records. A compatible travel IO is not a remote power source.
    body=scene['bodies'].get(scene['active_body'])
    if body is None or body['person_id']!=scene['person_id'] or body['hp']<=0:return False
    if function not in scene['person']['learned'] or function not in body['supported']:return False
    realm=scene['realms'].get(body['realm'])
    if realm is None or function not in realm['supported']:return False
    if function==profile['sensing']['id']:return scene['person']['awakened_sensing_allowed']
    if function==profile['repair']['id']:
        return any(tool['held_by']==scene['active_body'] and tool['realm']==body['realm'] and tool['accessible'] and tool['connection_tools'] and tool['parts']>=1 for tool in scene['tools'].values())
    if function==profile['storage']['id']:return body['storage_capacity']==profile['storage']['capacity']
    return False

def local_storage_output(scene):
    from copy import deepcopy
    result=deepcopy(scene)
    if not interaction_available(scene,profile['storage']['id']):return result
    body=scene['bodies'][scene['active_body']];lamp=scene['output_target']
    if scene['person']['main']<1 or lamp['realm']!=body['realm'] or lamp['contact_body']!=scene['active_body'] or not lamp['compatible'] or lamp['capacity_seconds']!=profile['storage']['lamp_capacity_seconds']:return result
    amount,seconds=output(body['stored_energy'],lamp['seconds'])
    if amount==body['stored_energy']:return result
    result['bodies'][scene['active_body']]['stored_energy']=amount
    result['person']['main']-=1
    result['output_target']['seconds']=seconds;result['now']+=profile['storage']['output_seconds']
    return result

def compatibility_checks():
    from copy import deepcopy
    notes=[]
    def verify(name,actual,expected):
        assert actual==expected,(name,actual,expected);notes.append(name)
    case=profile['body_compatibility_case'];functions=[profile[k]['id'] for k in ('sensing','repair','storage')]
    verify('one character twelve skills total440',(len(case['person']['skills']),sum(case['person']['skills'].values())),(12,440))
    verify('one learned list no three mandatory slots',(case['person']['skills']['관찰'],case['person']['skills']['공학'],profile['mandatory_power_skill_function_slots']),(70,70,False))
    verify('approved first body supports three declared uses',[interaction_available(case,x) for x in functions],[True,True,True])
    other=deepcopy(case);other['active_body']='B-U2';other['output_target']['realm']='TEST-COF-B'
    verify('same IO second body does not inherit senses tools or reservoir',[interaction_available(other,x) for x in functions],[False,False,False])
    verify('unavailable output preserves both bodies person lamp and action',local_storage_output(other),other)
    other['tools']['KIT-U2']={'held_by':'B-U2','realm':'TEST-COF-B','connection_tools':True,'parts':1,'accessible':True}
    verify('actually supplied local kit makes learned repair feasible',interaction_available(other,profile['repair']['id']),True)
    verify('supplying tools does not grant sensing or storage',[interaction_available(other,functions[i]) for i in (0,2)],[False,False])
    verify('same skilled person record survives other body',other['person'],case['person'])
    invalid=deepcopy(case);invalid['person']['learned'].remove(functions[1])
    verify('engineering70 alone does not teach declared connection technique',interaction_available(invalid,functions[1]),False)
    invalid=deepcopy(case);invalid['person']['awakened_sensing_allowed']=False
    verify('observation70 alone does not grant special sensing',interaction_available(invalid,functions[0]),False)
    completed=local_storage_output(case)
    verify('actual independent output consumes existing one unit one action five seconds',(completed['bodies']['B-U1']['stored_energy'],completed['person']['main'],completed['output_target']['seconds'],completed['now']),(0,0,1800,5))
    verify('other body injury equipment and stored state preserved',completed['bodies']['B-U2'],case['bodies']['B-U2'])
    verify('output does not heal active body or clear treatment',(completed['bodies']['B-U1']['hp'],completed['bodies']['B-U1']['ammo'],completed['bodies']['B-U1']['shield'],completed['bodies']['B-U1']['treated_since_full_recovery']),(5,3,0,True))
    verify('same action and stored unit cannot be reused',local_storage_output(completed),completed)
    # Alternative case: the replacement body was separately prepared with a
    # reservoir BEFORE this action. Switching does not create another budget.
    variant=deepcopy(case);variant['bodies']['B-U2'].update(supported=functions.copy(),storage_capacity=2,stored_energy=1)
    spent=local_storage_output(variant);spent['active_body']='B-U2'
    spent['output_target']={'id':'LAMP-U2','realm':'TEST-COF-B','seconds':0,'capacity_seconds':3600,'compatible':True,'contact_body':'B-U2'}
    verify('supported body switch cannot replenish same person main action',local_storage_output(spent),spent)
    # Only the separately declared next action window supplies another action.
    spent['person']['main']=1;next_output=local_storage_output(spent)
    verify('next declared person action spends only second body reservoir',(next_output['person']['main'],next_output['bodies']['B-U1']['stored_energy'],next_output['bodies']['B-U2']['stored_energy'],next_output['output_target']['seconds']),(0,0,0,1800))
    offline=deepcopy(case);offline['return_route_online']=False
    offline_result=local_storage_output(offline)
    verify('broken return route does not disable independently stored local power',(offline_result['output_target']['seconds'],offline_result['return_route_online']),(1800,False))
    for field,value in [('person_id','OTHER-PERSON'),('hp',0)]:
        invalid=deepcopy(case);invalid['bodies']['B-U1'][field]=value
        verify('wrong controller or incapable body preserves use '+field,local_storage_output(invalid),invalid)
    invalid=deepcopy(case);invalid['output_target']['realm']='TEST-COF-B'
    verify('output cannot act on other realm lamp without declared route',local_storage_output(invalid),invalid)
    invalid=deepcopy(case);invalid['tools']['KIT-U1']['held_by']='B-U2'
    verify('kit on inactive other body is not present tool',interaction_available(invalid,functions[1]),False)
    invalid=deepcopy(case);invalid['bodies']['B-U1']['storage_capacity']=0
    verify('body declared unsupported has no reservoir use',local_storage_output(invalid),invalid)
    for field,value in [('contact_body','B-U2'),('compatible',False),('capacity_seconds',7200)]:
        invalid=deepcopy(case);invalid['output_target'][field]=value
        verify('actual target contact/compatibility/capacity required '+field,local_storage_output(invalid),invalid)
    cases=0
    for learned,capable,support,realm_support,main,energy,lamp in product((False,True),(False,True),(False,True),(False,True),(False,True),range(3),(0,1,1799,1800,1801,3599,3600)):
        state=deepcopy(case);b=state['bodies']['B-U1']
        if not learned:state['person']['learned'].remove(functions[2])
        if not support:b['supported'].remove(functions[2])
        if not realm_support:state['realms']['TEST-COF']['supported'].remove(functions[2])
        b.update(hp=5 if capable else 0,stored_energy=energy);state['person']['main']=int(main);state['output_target']['seconds']=lamp
        before=deepcopy(state);out=local_storage_output(state)
        expected=learned and capable and support and realm_support and main and energy>=1 and lamp<=1800
        assert (out!=before)==expected and state==before
        if expected:
            assert out['bodies']['B-U1']['stored_energy']==energy-1 and out['person']['main']==0
            assert out['output_target']['seconds']==lamp+1800 and out['now']==5
            assert energy*1800+lamp==out['bodies']['B-U1']['stored_energy']*1800+out['output_target']['seconds']
            assert {k:value for k,value in out['person'].items() if k!='main'}=={k:value for k,value in before['person'].items() if k!='main'} and out['bodies']['B-U2']==before['bodies']['B-U2']
            assert {k:out['bodies']['B-U1'][k] for k in ('hp','ammo','shield','treated_since_full_recovery')}=={k:before['bodies']['B-U1'][k] for k in ('hp','ammo','shield','treated_since_full_recovery')}
        else:assert out==before
        cases+=1
    verify('672 actual person/body/realm/action/energy/lamp conditions',cases,672)
    return notes,cases

def run():
    checks=[]
    def check(name,actual,expected):
        assert actual==expected,(name,actual,expected)
        checks.append(name)
    s,r,e=profile['sensing'],profile['repair'],profile['storage']
    check('공통 엔진',profile['engine'],'P-FEWK-0.2')
    check('숙련/T',[(x['skill'],x['target']) for x in (s,r)],[('관찰',70),('공학',70)])
    check('same common grade distribution',dict(Counter(grade(70,x) for x in range(1,101))),{3:14,2:21,1:35,0:30})
    check('situations',tuple(target(70,x) for x in (-20,0,20)),(50,70,90))
    check('same thresholds',(grade(70,14),grade(70,35),grade(70,70),grade(70,71)),(3,2,1,0))
    check('warning/repair rounds',(s['warning_seconds']//5,r['work_seconds']//5),(60,60))
    check('charging continuous main actions',e['transfer_seconds']//5,6)
    check('charging no round shortcut',e['transfer_seconds']%5,0)
    check('energy/output and reservoir units',(e['capacity'],e['output_amount'],e['lamp_seconds_per_output'],e['lamp_capacity_seconds']),(2,1,1800,3600))
    # 감지/연락 후에도 같은5분 안에 수리를 완료했다는 오류를 시간선으로 검산한다.
    for preliminary in [5,10,30,60,120]:
        remaining=s['warning_seconds']-preliminary
        check(f'work cannot finish after prep {preliminary}',remaining>=r['work_seconds'],False)
    check('already-completed part can matter',300-10>=280,True)
    check('source requires separate awakened sensor',(s['requires_awakened_person'],s['requires_supporting_body']),(True,True))
    check('direction is not coordinates/safety',(s['gives_exact_coordinates'],s['failure_confirms_safe']),(False,False))
    check('NPC professional default',profile['rhythm_filler_default_role'].startswith('NPC'),True)
    check('creation labels, not action tracks',profile['matting_shining_use'],'character_creation_origin_not_runtime_skill_or_track')
    check('unified action term',profile['unified_action_term'],'인터랙션')
    check('no mandatory3 or new stats',(profile['mandatory_power_skill_function_slots'],profile['new_universal_stats']),(False,[]))
    # 불변 조건: 공급원과 몸의 총량을 보존하며 중단·미지원은 소모하지 않는다.
    charge_cases=0
    for body,supply,elapsed,compatible in product(range(3),range(3),(0,5,29,30),(False,True)):
        nb,ns=charge(body,supply,elapsed,compatible)
        assert nb+ns==body+supply and 0<=nb<=2 and 0<=ns<=2
        expected_completed=compatible and elapsed==30 and body<2 and supply>0
        assert (nb-body,ns-supply)==((1,-1) if expected_completed else (0,0))
        charge_cases+=1
    check('charge finite cases',charge_cases,72)
    output_cases=0
    for body,lamp,compatible in product(range(3),(0,1,1799,1800,1801,3599,3600),(False,True)):
        nb,nl=output(body,lamp,compatible)
        # 독립 단위 환산으로 총량을 대조한다. 초과/부분 출력은 허용하지 않는다.
        assert body*1800+lamp==nb*1800+nl and 0<=nl<=3600 and nb>=0
        if not compatible or not body or lamp>1800:assert (nb,nl)==(body,lamp)
        else:assert (nb,nl)==(body-1,lamp+1800)
        output_cases+=1
    check('output finite cases',output_cases,42)
    # 정상 사용·몸 교체·보관·시간 경과의 독립 정산 예.
    body,supply,lamp=1,2,0
    body,supply=charge(body,supply,30)
    check('charge completed',(body,supply),(2,1))
    body,lamp=output(body,lamp)
    check('output once',(body,supply,lamp),(1,1,1800))
    oldbody=body;unsupported_body=0
    unsupported_body,lamp_after=output(unsupported_body,lamp,False)
    check('body switch never copies',(oldbody,unsupported_body,lamp_after),(1,0,1800))
    lamp=max(0,lamp-1020)
    check('17min elapsed',lamp,780)
    body,lamp=output(oldbody,lamp)
    check('output after partial expiry',(body,lamp),(0,2580))
    check('expired completely',max(0,lamp-3000),0)
    check('full has no accepted output',output(1,3600),(1,3600))
    check('exact headroom accepts whole unit',output(1,1800),(0,3600))
    check('insufficient headroom rejects whole unit',output(1,1801),(1,1801))
    check('mid-charge interrupted consumes nothing',charge(1,2,29),(1,2))
    check('unsupported/fill does not consume',(charge(1,2,30,False),charge(2,2,30)),((1,2),(2,2)))
    check('repair functions are conditional',(r['new_stone_carving_allowed'],r['supply_is_separate']),(False,True))
    check('storage does not heal or share',(e['follows'],e['heals_hp_or_ego']),('body',False))
    check('known legacy arithmetic',(9*6.5,9*6.5+7,100-(20+10+5)),(58.5,65.5,65))
    mark_notes,mark_boundaries=marking_checks()
    checks.extend('marking: '+name for name in mark_notes)
    compatibility_notes,compatibility_cases=compatibility_checks()
    checks.extend('body compatibility: '+name for name in compatibility_notes)
    files=[here.parent/'10_CoreRulebook.md',here.parent/'12_룰시트와캐릭터시트.md',here/'고유효과_프로필.json',here/'백분율_코어검증.py',Path(__file__)]
    return {'date':'2026-10-07','profile':profile['id'],'scope':'세 NEW 시험 규격의 공통 판정·저장량·작업 시간만 검산한다.','checks_passed':len(checks),'marking_checks_passed':len(mark_notes),'body_compatibility_checks_passed':len(compatibility_notes),'body_compatibility_condition_cases':compatibility_cases,'marking_boundary_cases':mark_boundaries,'checks':checks,'charge_boundary_cases':charge_cases,'output_boundary_cases':output_cases,'artifacts_sha256':{str(f.relative_to(here.parent)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'all_ability_and_exposure_specs_complete':False,'actual_participant_playtest':False}

if __name__=='__main__':
    result=run()
    result['scope']='기존 세 기능/네 도안과 두 승인 몸의 제한된 사용 조건·독립 저장 출력: 공통 판정·저장량/행동·작업/충전 시간. 진입·몸 구성·감지/현물 물리·전체 능력/치료·실제 참가자 검증 아님.'
    result['checks']=[s.replace('共通','공통').replace('熟練','숙련') for s in result['checks']]
    Path(__file__).with_name('고유효과_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['profile','checks_passed','charge_boundary_cases','output_boundary_cases','actual_participant_playtest']},ensure_ascii=False))
