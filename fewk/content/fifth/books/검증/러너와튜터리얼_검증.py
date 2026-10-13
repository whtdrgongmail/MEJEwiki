"""레디메이드의 실제 시트/구매와 튜터리얼의 시간·물품·기존 전투/운전 경계 검산."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import contextlib,io,json,hashlib,re,math

HERE=Path(__file__).resolve().parent;O=HERE.parent
with contextlib.redirect_stdout(io.StringIO()):
    from 일반플레이_검증 import Body,move,new_round,attack
    from 운송_검증 import Rider,vehicle,round_start,drive,dismount
    from 백분율_코어검증 import grade,target,contest
    from 스페셜_검증 import cost

def run():
    runners=json.loads((HERE/'레디메이드_러너프로필.json').read_text())
    p=json.loads((HERE/'표준튜터리얼_프로필.json').read_text())
    roster=(O/'14_레디메이드_러너.md').read_text();book=(O/'15_표준튜터리얼_시나리오.md').read_text()
    checks=[]
    def check(name,actual,expected):
        assert actual==expected,(name,actual,expected)
        checks.append(name)
    def reject(name,obj,fn):
        old=deepcopy(obj)
        try:fn()
        except ValueError:pass
        else:raise AssertionError(name+' accepted')
        check(name+' state preserved',obj,old)
    check('one engine',runners['engine'],p['engine'])
    check('base engine',p['engine'],'P-FEWK-0.2')
    by_id={r['id']:r for r in runners['runners']}
    check('unique complete PCs',len(by_id),12)
    check('main/reserve parity',Counter(r['main'] for r in by_id.values()),Counter({True:6,False:6}))
    all_bodies=[]
    thresholds=0
    for r in by_id.values():
        rid=r['id'];values=list(r['skills'].values())
        check(rid+' creation distribution',Counter(values),Counter({70:2,50:3,30:4,10:3}))
        check(rid+' total',sum(values),440)
        check(rid+' twelve skills',len(values),12)
        fragment=roster.split(f'<a id="fewk-runner-{rid.lower()}"></a>',1)[1].split('<a id=',1)[0]
        row=next(l for l in fragment.splitlines() if re.match(r'^\| \d+ \|',l))
        check(rid+' reader numeric row',[int(x.strip()) for x in row.strip('|').split('|')],values)
        price=sum(runners['catalog'][n]*q for n,q in r['kit'])
        check(rid+' actual purchase and remaining',(price,r['starting_cash']-price),(6,0))
        check(rid+' story substance',all(len(r[k])>=18 for k in ['back','want','flaw','joy','secret','hook']),True)
        check(rid+' two contacts and two chosen relations',(len(r['contacts']),len(r['relations'])),(2,2))
        check(rid+' specialty and learned interactions',(len(r['special']),len(r['actions'])>=3),(2,True))
        for layer,state in r['body_state'].items():
            all_bodies.append(r['body_ids'][layer])
            check(rid+layer+' complete physical state',(state['HP'],state['max_HP'],state['resistance'],state['move_m']),(12,12,50,10))
        check(rid+' single active body',[k for k,s in r['body_state'].items() if s['active']],['B1'])
        for t in values:
            check(rid+str(thresholds)+' success threshold',sum(grade(t,x)>0 for x in range(1,101)),t)
            check(rid+str(thresholds)+' good threshold',sum(grade(t,x)>=2 for x in range(1,101)),t//2)
            thresholds+=1
    check('person/body distinct IDs',len(set(all_bodies)),24)
    check('one body installed communication',[(r['id'],r['body_state']['B1']['installed']) for r in by_id.values() if r['body_state']['B1']['installed']],[('R10',['IM-COMM'])])
    check('module purchase covers installation',sum(runners['catalog'][n]*q for n,q in by_id['R10']['kit']),6)
    check('two physical bodies different installed BP',(by_id['R10']['body_state']['B0']['BP'],by_id['R10']['body_state']['B1']['BP']),(90,89))
    effects=json.loads((HERE/'고유효과_프로필.json').read_text())
    check('R11 allowed sensing body only',(by_id['R11']['body_state']['B0']['sensing_support'],by_id['R11']['body_state']['B1']['sensing_support']),(None,effects['sensing']['id']))
    check('R11 awakening no new runtime resource',by_id['R11']['formation']['runtime_resource_added'],False)
    check('sensing has no universal future range','최대300초 앞' in roster,False)
    check('R08 existing connector work specification',(effects['repair']['work_seconds'],effects['repair']['part_cost_at_start']),(300,1))

    # Core의 실제 장비 모형: P방호를 쓰는 같은 몸에서 L만 빠져나가지는 않는다.
    h=Body(shield_types=('프로젝타일','레이저'))
    check('R12 first L hit blocked',attack(Body(ammo=6),h,'레이저 단말',distance=10,roll=10),('shield',0))
    check('R12 next same-round P hit reaches armor',attack(Body(),h,'권총',distance=10,roll=10),('damage',3))
    check('R12 shared state after two types',(h.hp,h.charges),(9,1))
    p_only=Body(shield_types=('프로젝타일',))
    check('T06 laser bypasses P shield',attack(Body(ammo=6),p_only,'레이저 단말',distance=10,roll=10),('damage',3))
    check('wrong type does not consume shield',p_only.charges,2)
    check('melee higher local damage',attack(Body(),Body(),'동력 근접 도구',distance=1,roll=10),('damage',5))

    def walk(distance,extra=False):
        b=Body();done=0;rounds=0
        while done<distance:
            if rounds:new_round(b)
            first=min(10,distance-done);move(b,first);done+=first
            if extra and done<distance:
                second=min(10,distance-done);move(b,second,extra=True);done+=second
            rounds+=1
        return rounds*5,b

    check('six distinct mission objects',len({m['object'] for m in p['missions']}),6)
    used=set()
    for m in p['missions']:
        mid=m['id'];used.update(m['main']);used.update(m['alternatives'])
        check(mid+' actually findable',f'<a id="fewk-tutorial-{mid.lower()}"></a>' in book,True)
        check(mid+' three distinct main PCs',len(set(m['main'])),3)
        check(mid+' three distinct alternative PCs',len(set(m['alternatives'])),3)
        check(mid+' ready referenced PCs',all(r in by_id for r in m['main']+m['alternatives']),True)
        check(mid+' guards bounded',m['guards'],2)
        check(mid+' payment',3*(m['advance']+m['completion']),m['income_example'])
        check(mid+' settlement',m['income_example']-sum(m['expenses_example']),m['net_example'])
        edges={frozenset((a,b)):d for a,b,d in m['edges']}
        for name,nodes in m['routes'].items():
            length=sum(edges[frozenset((a,b))] for a,b in zip(nodes,nodes[1:]))
            check(mid+name+' real path positive',length>0,True)
    check('every main/reserve gets an assigned mission',used,set(by_id))
    missions={x['id']:x for x in p['missions']}
    # T01:20m 접근+5초 잠금+5초 수거+20m귀환+5초 인계. 각자 주요의 중복이 없다.
    approach,_=walk(20);ret,_=walk(20)
    check('T01 basic service delivery timeline',approach+5+5+ret+5,35)
    check('T01 before seizure',35<=missions['T01']['deadline_s'],True)
    # T02:사본/반납을 순차로 해도 대피하는 사람은 그동안 각자 움직인다.
    check('T02 two independent authorized copy sizes',missions['T02']['personal_copy_chars']<=10000,True)
    check('T02 aid and actual move change',(missions['T02']['miso_start_HP']+2,missions['T02']['miso_first_aid_HP'],missions['T02']['miso_after_aid_move']),(7,7,10))
    check('T02 person choosing to go',missions['T02']['consent_required'],True)

    # T03:실제 운전 모형의 주요/기본 이동·셀·충돌·좌석을 사용한다.
    riders=[Rider(id=rid,life=70 if i==0 else 30,armor=1 if i<3 else 0) for i,rid in enumerate(['R06-B1','R01-B1','R03-B1','T03-H'])]
    van=vehicle('ROAD-VAN-01',id='VAN-T03',riders=riders,cargo={'COLD-01':20000})
    for i in range(8):
        if i:round_start(van)
        moved,success=drive(van,riders[0],30,stop=i==7)
        check('T03 safe movement '+str(i),(moved,success,riders[0].main,riders[0].move),(30,True,0,0))
    check('T03 actual safe route/fuel',(van.position,van.power),(240,920))
    check('T03 all four moved once',[x.position for x in riders],[240]*4)
    reject('T03 no same round second driver movement',van,lambda:drive(van,riders[1],30))
    m=missions['T03'];finish=8*5+m['checkpoint_s']+m['arrival_actions']*5
    check('T03 safe exact deadline',finish,m['deadline_s'])
    check('T03 late pickup equality',[finish+d<=90 for d in [0,5]],[True,False])
    check('T03 paid pack route completes before expiry',m['pack_s']+finish<90+m['pack_extension_s'],True)
    check('T03 pack time/remaining margin',(m['pack_s']+finish,90+m['pack_extension_s']-m['pack_s']-finish),(95,55))
    round_start(van);passenger=riders[1];dismount(van,passenger);check('T03 actual dismount action',passenger.main,0)
    # 위험 경로에서는 정규 불리와 충돌 처리를 한 번 사용한다.
    rs=[Rider(id='TEST-'+str(i),life=70,armor=1 if i<3 else 0) for i in range(4)]
    bad=vehicle('ROAD-VAN-01',riders=rs,cargo={'COLD-01':20000})
    drive(bad,rs[0],30,stop=True);round_start(bad)
    moved,success=drive(bad,rs[0],30,risk=True,roll=51,situation=-20,collision=True,stop=True)
    check('T03 risk threshold',target(70,-20),50)
    check('T03 failed risk not free travel',(moved,success,bad.position,bad.power,bad.hp),(0,False,30,980,19))
    check('T03 collision each actual body',[x.hp for x in rs],[10,10,10,9])
    check('T03 collision shields untouched',[x.charges for x in rs],[2]*4)
    over=vehicle('ROAD-VAN-01',riders=[Rider(id=str(i)) for i in range(5)])
    reject('T03 fifth passenger cannot silently fit',over,lambda:drive(over,over.riders[0],30))
    over=vehicle('ROAD-VAN-01',riders=[Rider()],cargo={'COLD-01':200001})
    reject('T03 overweight actual cargo rejected',over,lambda:drive(over,over.riders[0],30))
    # T04:접근을 주요에 쓰면 같은 주요로 작업할 수 없다. 중단해도 재료는 되돌아오지 않는다.
    elapsed,body=walk(30,extra=True)
    check('T04 fastest service approach',(elapsed,body.main),(10,1))
    body.main-=1
    for i in range(2):new_round(body);body.main-=1
    check('T04 basic arrival permits first work main',(elapsed+10,elapsed+10<60),(20,True))
    check('T04 safety circuits preserved',missions['T04']['hazardous_life_system_affected'],False)
    # T05:구매금과 개인 보수를 나눠 할인 잔액은 의뢰인에게 반환한다.
    m=missions['T05']
    check('T05 escrow at both prices',[m['escrow']-x for x in (m['asking_price'],m['discount_price'])],[0,1])
    check('T05 returning disputed goods gives no completion',m['voluntary_return_completion'],0)
    check('T05 device is not precharged',m['device_charges'],0)
    check('T05 identify then actual message/response',m['record_lookup_s']+5+m['response_after_message_s'],30)
    check('T05 reply before arrival',30<m['deadline_s'],True)
    # T06:곡의 유효60초는 정전/협상으로 늘지 않는다. 별개 인물의 작업은 병행할 수 있다.
    m=missions['T06'];song_interruption=15
    check('T06 interruption preserves required active song',m['song_actual_s']+song_interruption,75)
    check('T06 cancelled show payment',3*(m['advance']+m['partial']),6)
    check('T06 evacuation is an actual end condition',m['end_requires_evacuation'],True)
    # S2:추가 이동을 쓴 최단 경로도 무료 안전 우회로는 마감에 늦는다.
    s2=json.loads((HERE/'시나리오_확장프로필.json').read_text())['one_shots']['S2']
    basic,_=walk(s2['detour_distance_m']);fast,_=walk(s2['detour_distance_m'],extra=True)
    check('S2 safe detour walking and sprinting',(basic+5,fast+5),(80,45))
    check('S2 no dominant free safe in-time path',s2['elapsed_at_open_seconds']+fast+5>s2['booking_deadline_seconds'],True)
    check('S2 actual late rebooking cost/time',(s2['late_rebooking_cost_team_oyat'],s2['late_rebooking_delay_seconds']),(1,1200))
    check('S2 additional real residence loss',cost(Fraction(1,3),'lower3','runner'),Fraction(5,18))
    check('S2 exact boundary ego',cost(Fraction(21605,3600),'lower3','runner'),Fraction(5)+Fraction(1,864))
    check('no added universal resource',p['new_universal_stats'],[])
    check('human evidence not simulated',(p['human_tests_performed'],runners['actual_participant_playtest']),(False,False))
    # 배포 시트의 수치·식별자와 공개/진행자 자료를 대조한다.
    before=json.loads((HERE/'이전/시나리오북편성전_20261008.json').read_text())
    before_files={x['path']:x for x in before['files']}
    check('preserved previous complete package',len(before_files),9)
    for row in before_files.values():
        check('snapshot integrity '+row['path'],hashlib.sha256(row['text'].encode()).hexdigest(),row['sha256'])
    check('character book edition',runners['editorial_version'],'1.1')
    check('scenario book edition',p['editorial_version'],'1.1')
    for r in by_id.values():
        rid=r['id'];frag=roster.split(f'<a id="fewk-runner-{rid.lower()}"></a>',1)[1].split('<a id=',1)[0]
        for heading in runners['character_book_sections']:
            check(rid+' section '+heading,'#### '+heading in frag,True)
        for field in ['back','want','flaw','joy','secret','hook','training']:
            check(rid+' retained '+field,r[field] in frag,True)
        for n,t in r['skills'].items():
            actual=[int(x) for x in re.search(r'^\| '+n+r' \| (\d+) \| (\d+) \| (\d+) \|$',frag,re.M).groups()]
            check(rid+' prepared boundaries '+n,actual,[t,t//2,t//5])
            check(rid+' percentile threshold '+n,r['prepared_thresholds'][n],actual)
        check(rid+' persistent slot',r['storage_slot'] in frag,True)
        for index,(item,q) in enumerate(r['kit'],1):
            expected=(f'{rid}-SVC01 | 설치 작업 영수증 | 지출 증빙' if item=='설치 작업' else f'{rid}-O{index:02d} | {item}×{q} | 소유')
            check(rid+' owned item or service identity '+str(index),expected in frag,True)
        for index in (1,2,3):check(rid+' personal loan identity '+str(index),f'{rid}-L{index:02d}' in frag,True)
        for field in ['play_guide','community_opening','mission_guide']:
            check(rid+' playable guide '+field,r[field] in frag,True)
    check('pool has exactly two pistols',len(re.findall(r'^\| TEAM-GUN-0[12] \|',roster,re.M)),2)
    handouts=book.split('<a id="fewk-tutorial-handouts"></a>',1)[1].split('<a id="fewk-tutorial-tracker"></a>',1)[0]
    check('six separately copyable public handouts',len(re.findall(r'<a id="fewk-handout-t\d{2}"></a>',handouts)),6)
    for m in p['missions']:
        mid=m['id'];frag=book.split(f'<a id="fewk-tutorial-{mid.lower()}"></a>',1)[1].split('<a id=',1)[0]
        d=m['book_materials']
        for title in ['도입 낭독','진행자용 운영표','장소 키와 최초 위치','사건 시간표','튜터리얼 진행 순서','종료와 다음 장면']:
            check(mid+' usable section '+title,title in frag,True)
        for field in ['kr_opening','clue','gm','stalls','handoff','partial','aftermath']:
            check(mid+' field '+field,d[field] in frag,True)
        check(mid+' handout content',d['handout'] in handouts,True)
        check(mid+' GM paragraph not distributed',d['gm'] in handouts,False)
        nodes={x for edge in m['edges'] for x in edge[:2]}
        check(mid+' map locations keyed',nodes <= {x[0] for x in d['locations']},True)
        check(mid+' tutorial beats complete',len(d['lessons']),4)
    check('T02 previously permitted copy not renegotiated','반납 전에5초간 메모 사본 작성 허용' in book,False)
    check('T06 civilian route uses actual movement',walk(35)[0],20)
    check('T04 actual combined movement and work',walk(30,extra=True)[0]+10+5,25)
    # 2nd round reaches C by basic movement and keeps main for first work: finish20, inspection25.
    check('T04 arrival round major remains',walk(30,extra=True)[1].main,1)
    check('scenario appendix ready forms',all(x in book for x in ['현재 경과=','물건ID=','누적/필요=','별도'] ),True)
    core=(O/'10_CoreRulebook.md').read_text();world=(O/'11_WorldLorebook.md').read_text();sheets=(O/'12_룰시트와캐릭터시트.md').read_text()
    for r in by_id.values():
        link='14_레디메이드_러너.md#fewk-runner-'+r['id'].lower()
        check(r['id']+' in Core and World',link in core and link in world,True)
    filled=sheets.split('<a id="fewk-sheet-readymade"></a>',1)[1].split('<a id="fewk-sheet-07"></a>',1)[0]
    check('filled R03 row matches actual profile',list(map(int,re.search(r'^\| 준비값 \| (.+) \|$',filled,re.M).group(1).split(' | '))),list(by_id['R03']['skills'].values()))
    check('filled R03 saved body identity',all(x in filled for x in ['R03-B0','R03-B1','SLOT-R03','R03-O03','10000자','남은8000자']),True)
    names=['14_레디메이드_러너.md','15_표준튜터리얼_시나리오.md','10_CoreRulebook.md','11_WorldLorebook.md','12_룰시트와캐릭터시트.md','13_입문시나리오.md']
    names+=['검증/'+n for n in ['레디메이드_러너프로필.json','표준튜터리얼_프로필.json','러너와튜터리얼_검증.py','시나리오_확장프로필.json','일반플레이_검증.py','운송_검증.py','운송_프로필.json','백분율_코어검증.py','스페셜_검증.py','고유효과_프로필.json']]
    hashes={n:hashlib.sha256((O/n).read_bytes()).hexdigest() for n in names}
    return {'date':'2026-10-08','id':'FEWK-RUNNER-TUTORIAL-CHECK','checks_passed':len(checks),'checks':checks,'runners':12,'principal_runners':6,'reserve_runners':6,'complete_bodies':24,'skill_rows':144,'tutorial_scenarios':6,'artifacts_sha256':hashes,'actual_participant_playtest':False,'full_encounter_balance_verified':False,'scope':'완성 시트의 배분/구매/몸/고유 기능 조건·실제 전투/운전 모형과 공개된 경로/시간/마감/정산 경계. 재미·참가자 독해·전술 균형의 실측은 포함하지 않음.'}

if __name__=='__main__':
    d=run();(HERE/'러너와튜터리얼_검증결과.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:d[k] for k in ['id','checks_passed','runners','complete_bodies','skill_rows','tutorial_scenarios','actual_participant_playtest']},ensure_ascii=False))
