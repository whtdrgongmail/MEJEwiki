from pathlib import Path
from copy import deepcopy
from collections import Counter
from itertools import product
import json,hashlib,re
from 백분율_코어검증 import grade,target
from 일반플레이_검증 import Body,attack,new_round
from 팀지원_검증 import Sender,prepared_for_attempt
here=Path(__file__).resolve().parent
profile=json.loads((here/'NPC_프로필.json').read_text())
intro=json.loads((here/'입문_프로필.json').read_text())

def body_from(card):
    b=card['body']
    return Body(hp=b['hp_max'],armor=b['armor'],charges=b['shield_charge'],shield_types=tuple(b['shield_types']),reaction=b['reaction_per_round'],main=b['main_per_round'],ammo=b['ammo'],move=b['move_m'])

def named_sample(sample_id,body_id,registry):
    """Initialize a selected NEW example once; the returned body is the live state."""
    sample=next((s for s in profile['named_samples'] if s['id']==sample_id),None)
    if sample is None or not isinstance(body_id,str) or not body_id.strip():raise ValueError('unknown sample or absent body ID')
    if sample_id in registry or any(c['active_body']==body_id for c in registry.values()):raise ValueError('person/body already registered')
    base=next(c for c in profile['templates'] if c['id']==sample['base_template'])
    card=deepcopy(base)
    card.update(id=sample_id,person_id=sample_id,active_body=body_id,name=sample['name'],status=sample['status'],base_template=base['id'],known_facts=set(sample['known_facts']),contact=sample['approved_contact'],interactions=deepcopy(sample['interactions']))
    card['body_state']=body_from(card)
    registry[sample_id]=card
    return card

def run():
    checks=[]
    def check(name,got,want):
        assert got==want,(name,got,want)
        checks.append({'name':name,'passed':True})
    def rejects(name,obj,fn):
        before=deepcopy(obj)
        try:fn()
        except ValueError:check(name,obj,before)
        else:raise AssertionError('accepted '+name)
    cards=profile['templates'];check('six NEW cards',len(cards),6)
    keys=set(intro['character']['skills'])
    single=0
    for c in cards:
        check(c['id']+' common12skills',set(c['skills']),keys)
        check(c['id']+' same440allocation',sum(c['skills'].values()),440)
        check(c['id']+' sameallocationcounts',Counter(c['skills'].values()),Counter({70:2,50:3,30:4,10:3}))
        b=body_from(c)
        check(c['id']+' active budget',(b.hp,b.main,b.reaction,b.move),(12,1,1,10))
        highest=max(c['skills'].values());check(c['id']+' independent full die success count',sum(grade(target(highest),r)>0 for r in range(1,101)),highest);single+=100
    recorder=cards[0];guard=cards[3]
    check('only specified guard has ranged shield',[(c['id'],c['body']['armor'],c['body']['shield_charge'],c['body']['weapon']) for c in cards],[(f'N{i:02d}',1 if i==4 else 0,2 if i==4 else 0,'권총' if i==4 else None) for i in range(1,7)])
    g=body_from(guard);r=body_from(recorder)
    check('guard actual gun attack on unarmored recorder',attack(g,r,'권총',roll=20,skill=guard['skills']['사격'],distance=20),('damage',4))
    check('actual injury and guard ammunition',(r.hp,g.main,g.ammo),(8,0,11))
    rejects('same guard main cannot shoot again',g,lambda:attack(g,r,'권총',roll=20,skill=70,distance=20))
    g=body_from(guard)
    check('guard first shield hit',attack(Body(),g,'권총',roll=20,skill=70,distance=20),('shield',0))
    check('guard same round second hit',attack(Body(),g,'권총',roll=20,skill=70,distance=20),('damage',3))
    check('shield and body budget preserved',(g.hp,g.charges,g.blocked),(9,1,True))
    new_round(g);check('new round permits remaining charge',attack(Body(),g,'권총',roll=20,skill=70,distance=20),('shield',0))
    check('next round does not refill shield',(g.hp,g.charges),(9,0))
    g=body_from(guard);check('contact damage uses common melee and armor',attack(Body(),g,'동력 근접 도구',roll=20,skill=70,distance=1),('damage',5))
    check('melee does not spend ranged shield',(g.hp,g.charges),(7,2))
    send_cases=0
    for c in cards:
        source='FACT-'+c['id']
        for live,main,network,account,contact,knows in product((False,True),repeat=6):
            b=body_from(c);b.hp=b.hp if live else 0;b.main=1 if main else 0
            sender=Sender(body=b,active='BODY-'+c['id'],installed='BODY-'+c['id'],network=network,account=account,contact=contact,facts={source} if knows else set())
            before=deepcopy(sender)
            eligible=all((live,main,network,account,contact,knows))
            try:got=sender.send('EVENT-'+c['id'],source)
            except ValueError:
                assert not eligible and sender==before
            else:
                assert eligible and got=={'source':source,'seconds':5} and sender.body.main==0
            send_cases+=1
    check('actual sender boundaries',send_cases,384)
    g=body_from(guard);sender=Sender(body=g,active='GUARD',installed='GUARD',facts={'CAM-01'})
    sender.send('REPORT','CAM-01');rejects('report cannot also shoot same main',g,lambda:attack(g,body_from(recorder),'권총',roll=20,skill=70,distance=20))
    sender=Sender(body=body_from(recorder),active='CURRENT',installed='INACTIVE',facts={'RECEIPT-01'})
    rejects('inactive body cannot transmit known record',sender,lambda:sender.send('REMOTE','RECEIPT-01'))
    sender=Sender(body=body_from(recorder),active='CURRENT',installed='CURRENT',facts={'RECEIPT-01'})
    sender.send('ONCE','RECEIPT-01');new_round(sender.body)
    rejects('new round does not repeat already sent event',sender,lambda:sender.send('ONCE','RECEIPT-01'))
    prerequisites=0
    for c in cards:
        for terminal,access in product((False,True),repeat=2):
            try:got=prepared_for_attempt(c['skills']['지식'],terminal,access,False)
            except ValueError:assert not (terminal and access)
            else:assert terminal and access and got==c['skills']['지식']
            prerequisites+=1
    check('known specialty never supplies absent access',prerequisites,24)
    ledger=json.loads((here/'제5판_이관검수.json').read_text());root=here.parent.parent
    rows=[]
    for idx,lo,hi in [(91,10,20),(93,40,55),(94,60,85)]:
        source=(root/ledger['files'][idx]['source']).read_text();bad=[];parsed=0
        for part in source.split('### ')[1:]:
            match=re.search(r'^HP: (\d+)',part,re.M)
            if not match:continue
            name=part.splitlines()[0];hp=int(match[1]);parsed+=1
            if not lo<=hp<=hi:bad.append({'name':name,'HP':hp})
        rows.append({'index':idx,'overview_range':[lo,hi],'sample_rows_read':parsed,'outside_overview':bad})
    check('D overview inconsistent actual rows',(rows[0]['sample_rows_read'],len(rows[0]['outside_overview'])),(10,4))
    check('B overview inconsistent actual rows',(rows[1]['sample_rows_read'],len(rows[1]['outside_overview'])),(5,3))
    check('A overview inconsistent actual rows',(rows[2]['sample_rows_read'],len(rows[2]['outside_overview'])),(6,3))
    # These part sums are correct but do not prove equipment anatomy or combat balance.
    check('old Qinghu stated part sum',200+100+50*2,400)
    check('old truck stated part sum',150+25*4+50,300)
    check('entry engine and supplied dice',(profile['engine'],intro['common_engine']),('P-FEWK-0.2','P-FEWK-0.2'))
    before_named=len(checks)
    registry={};templates_before=deepcopy(profile['templates'])
    samples=profile['named_samples']
    check('three named NEW samples',[(s['id'],s['base_template']) for s in samples],[('NP-HAN-01','N01'),('NP-WHITE-01','N04'),('NP-BIPA-01','N05')])
    named_rolls=0
    for sample in samples:
        card=named_sample(sample['id'],'B-'+sample['id'],registry)
        base=next(c for c in profile['templates'] if c['id']==sample['base_template'])
        check(sample['id']+' uses actual existing numeric card',(card['skills'],card['body']),(base['skills'],base['body']))
        check(sample['id']+' same skills only',set(card['skills']),keys)
        check(sample['id']+' interactions reference existing skills',all(x['skill'] is None or x['skill'] in keys for x in card['interactions']),True)
        check(sample['id']+' facts are declared only',card['known_facts'],set(sample['known_facts']))
        check(sample['id']+' original ranks grant no access',(sample['automatic_PC_relationship'],sample['automatic_access_to_other_sources']),(False,False))
        for item in card['interactions']:
            if item['skill'] is None:continue
            skill=card['skills'][item['skill']]
            assert sum(grade(target(skill),roll)>0 for roll in range(1,101))==skill
            named_rolls+=100
    check('named skills use same d100 enumeration',named_rolls,700)
    check('three distinct person and body states',(len(registry),len({c['active_body'] for c in registry.values()})),(3,3))
    check('initialization does not mutate baseline templates',profile['templates'],templates_before)
    named_guard=registry['NP-WHITE-01'];named_han=registry['NP-HAN-01'];named_bipa=registry['NP-BIPA-01']
    guard_body=named_guard['body_state'];guard_body.hp=9;guard_body.ammo=7;guard_body.main=0
    rejects('same named person cannot reinitialize resources',registry,lambda:named_sample('NP-WHITE-01','B-NEW',registry))
    other={};named_sample('NP-HAN-01','B-SHARED',other)
    rejects('different named person cannot borrow already registered body',other,lambda:named_sample('NP-BIPA-01','B-SHARED',other))
    rejects('missing body identity rejects before registration',other,lambda:named_sample('NP-BIPA-01','',other))
    rejects('unknown named sample rejects before registration',other,lambda:named_sample('UNKNOWN','B-N',other))
    check('alias rejection keeps wounded used state',(guard_body.hp,guard_body.ammo,guard_body.main),(9,7,0))
    check('other named person resources stay independent',(named_han['body_state'].hp,named_han['body_state'].main,named_bipa['body_state'].hp,named_bipa['body_state'].main),(12,1,12,1))
    new_round(guard_body)
    sender=Sender(body=guard_body,active=named_guard['active_body'],installed=named_guard['active_body'],facts=named_guard['known_facts'])
    sender.send('WHITE-REPORT','DOOR-WHITE-01')
    check('named guard report spends actual action',(guard_body.main,guard_body.ammo,guard_body.hp),(0,7,9))
    rejects('named guard report cannot also shoot same action',guard_body,lambda:attack(guard_body,named_han['body_state'],'권총',roll=20,skill=70,distance=20))
    sender=Sender(body=named_han['body_state'],active=named_han['active_body'],installed=named_han['active_body'],facts=named_han['known_facts'])
    rejects('receipt holder does not know guard private access record',named_han['body_state'],lambda:sender.send('ABSENT-FACT','ACCESS-WHITE-01'))
    sender=Sender(body=named_bipa['body_state'],active=named_bipa['active_body'],installed='OTHER-BODY',facts=named_bipa['known_facts'])
    rejects('named runner inactive installation cannot report route',named_bipa['body_state'],lambda:sender.send('INACTIVE-ROUTE','ROUTE-BIPA-01'))
    named_sender_cases=0
    for sample in samples:
        card=registry[sample['id']]
        for live,main,network,account,contact,known in product((False,True),repeat=6):
            b=body_from(card);b.hp=b.hp if live else 0;b.main=1 if main else 0
            fact=sample['known_facts'][0]
            s=Sender(body=b,active=card['active_body'],installed=card['active_body'],network=network,account=account,contact=contact,facts={fact} if known else set())
            before=deepcopy(b)
            try:s.send('NAMED-REPORT',fact)
            except ValueError:assert not all((live,main,network,account,contact,known)) and b==before
            else:assert all((live,main,network,account,contact,known)) and b.main==0 and b.hp==before.hp and b.ammo==before.ammo
            named_sender_cases+=1
    check('three named senders actual prerequisites',named_sender_cases,192)
    named_sample_checks=len(checks)-before_named
    files=[here.parent/'10_CoreRulebook.md',here.parent/'11_WorldLorebook.md',here.parent/'12_룰시트와캐릭터시트.md',here/'NPC_프로필.json',here/'입문_프로필.json',here/'백분율_코어검증.py',here/'일반플레이_검증.py',here/'팀지원_검증.py',here/'임플란트_검증.py',here/'임플란트_프로필.json',Path(__file__)]
    sources={str(q.relative_to(root)):hashlib.sha256(q.read_bytes()).hexdigest() for q in [root/ledger['files'][i]['source'] for i in (91,92,93,94,96,97)]}
    for family in ledger['NPC_life_topic_sources']:sources[family['path']]=family['sha256'];assert hashlib.sha256((root/family['path']).read_bytes()).hexdigest()==family['sha256']
    return {'date':'2026-10-06','profile':profile['id'],'scope':'NEW입문NPC6과그값을쓰는NEW명명예3의12숙련/몸·구판등급불승계·인물/몸중복초기화거부·상태보존·송신192조건/백분율700경우를기존함수로대조하며,기존입문6의송신384조건/접근24조건을유지하고구판D/B/A정의와21표본HP범위·부위합계를독립추출/검산. 전NPC/고유능력·세계프로필·지식/감정판단·거대전투·참가자/균형검증아님.','checks_passed':len(checks),'checks':checks,'named_sample_checks':named_sample_checks,'named_sample_sender_cases':named_sender_cases,'named_sample_percentile_rolls':named_rolls,'all_17_legacy_NPC_numeric_profiles_complete':False,'single_percentile_rolls':single,'sender_condition_cases':send_cases,'access_prerequisite_cases':prerequisites,'old_HP_overview_rows':rows,'all_NPC_and_large_entity_profiles_complete':False,'full_encounter_balance_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False,'artifacts_sha256':{str(q.relative_to(here.parent)):hashlib.sha256(q.read_bytes()).hexdigest() for q in files},'source_sha256':sources}
if __name__=='__main__':
    r=run();Path(__file__).with_name('NPC_검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('profile','checks_passed','single_percentile_rolls','sender_condition_cases','access_prerequisite_cases','old_HP_overview_rows','actual_participant_playtest')},ensure_ascii=False))
