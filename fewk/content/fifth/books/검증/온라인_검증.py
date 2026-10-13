from pathlib import Path
from copy import deepcopy
from itertools import permutations
import json,hashlib,math
from 백분율_코어검증 import grade,target
from 장면운영_검증 import Scene,start_event,put,snapshot
here=Path(__file__).resolve().parent
profile=json.loads((here/'온라인_프로필.json').read_text())
example=json.loads((here/'온라인_기록예시.json').read_text())
intro=json.loads((here/'입문_프로필.json').read_text())

def integer(value,lo=0,hi=None):
    if type(value) is not int or value<lo or (hi is not None and value>hi):raise ValueError('integer range')
    return value
def ids(value):
    if not isinstance(value,list) or any(type(x) is not str or not x for x in value) or len(value)!=len(set(value)):raise ValueError('distinct nonempty IDs')
    return set(value)
def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('duplicate field')
        d[k]=v
    return d
def invalid_constant(value):raise ValueError('nonfinite JSON constant')
def load_current(text,person_id,version):
    try:
        d=json.loads(text,object_pairs_hook=unique,parse_constant=invalid_constant)
        if d['format']!='FEWK-ONLINE-SNAPSHOT-01' or d['rules']!='P-FEWK-0.2':raise ValueError('format/engine mismatch')
        integer(d['state_version']);integer(version)
        if d['state_version']!=version or d['person']['id']!=person_id:raise ValueError('different current person/version')
        if any(k in d for k in ('stats','derived','tracks')):raise ValueError('old mixed character format')
        p=d['person'];skills=p['skills']
        if set(skills)!=set(intro['character']['skills']):raise ValueError('same learned12skills')
        for value in skills.values():integer(value,1,95)
        if type(p['ego']) not in (int,float) or not math.isfinite(p['ego']) or not 0<=p['ego']<=p['ego_max']:raise ValueError('Ego range')
        integer(p['ego_max'],1);ids(p['realm_bans'])
        if not isinstance(d['bodies'],list) or not d['bodies']:raise ValueError('actual bodies')
        body_ids=ids([b['id'] for b in d['bodies']])
        if p['active_body'] not in body_ids or p['original_body'] not in body_ids:raise ValueError('actual active/original body')
        for b in d['bodies']:
            integer(b['HP_max'],1);integer(b['HP'],0,b['HP_max']);integer(b['ammo']);integer(b['shield_charge'],0,2);integer(b['armor'])
            if type(b['stored']) is not bool:raise ValueError('stored state')
            if b['id']==p['active_body'] and b['stored']:raise ValueError('stored active body')
        for interaction in d['interactions']:
            if interaction['body'] not in body_ids or interaction['skill'] not in skills:raise ValueError('interaction body/skill')
            if not interaction['origin'] or not interaction['conditions']:raise ValueError('actual origin/conditions')
        io=d['IO']
        if io['original_body']!=p['original_body'] or io['local_body'] not in body_ids:raise ValueError('IO bodies')
        scene=d['scene'];integer(scene['IC_seconds'])
        if type(scene['held']) is not bool:raise ValueError('held state')
        if ids(scene['completed_events']) & ids(scene['pending_events']):raise ValueError('pending is not confirmed')
        if ids(scene['parts']) & ids(scene['spent']):raise ValueError('part copied across inventories')
        ids(scene['contacts']);integer(scene['job']['seconds'],0,300)
        if scene['job']['seconds']>scene['IC_seconds']:raise ValueError('work exceeds actual IC time')
        if type(scene['job']['running']) is not bool:raise ValueError('actual running state')
        return deepcopy(d)
    except (KeyError,TypeError,json.JSONDecodeError) as e:raise ValueError('invalid snapshot shape') from e
def export_current(d):
    text=json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
    load_current(text,d['person']['id'],d['state_version'])
    return text
def roll_record(prepared,situation,original):
    integer(prepared,1)
    if type(situation) is not int or situation not in (-20,0,20):raise ValueError('one common situation')
    if type(original) is str:
        if original=='00':roll=100
        elif original.isascii() and original.isdigit():roll=int(original)
        else:raise ValueError('actual d100 result')
    elif type(original) is int:roll=original
    else:raise ValueError('actual d100 result')
    integer(roll,1,100);t=target(prepared,situation)
    return {'prepared':prepared,'situation':situation,'target':t,'original':original,'roll':roll,'grade':grade(t,roll)}

def run():
    checks=[]
    def check(name,got,want):
        assert got==want,(name,got,want);checks.append(name)
    def rejects(name,fn):
        try:fn()
        except ValueError:checks.append(name)
        else:raise AssertionError('accepted '+name)
    def reject_scene(name,scene,fn):
        before=snapshot(scene);rejects(name,fn);assert snapshot(scene)==before
    scene=Scene();put(scene,'S',start_event());check('start once and uses part',(scene.version,scene.state['parts'],scene.state['spent']),(21,[],['PART-01']))
    # Contact registration records facts already acquired before these edits; it is not an IC message.
    scene.submit('A',{'kind':'contact','person':'N-OWNER'});scene.submit('B',{'kind':'contact','person':'N-NEIGHBOUR'})
    check('two pending entries do not run',scene.state['contacts'],[])
    scene.commit('A',21);check('first entry next version',scene.version,22)
    reject_scene('other log cannot commit stale21',scene,lambda:scene.commit('B',21))
    check('stale entry retained for review',set(scene.pending),{'B'})
    scene.commit('B',22);check('reviewed second entry once',(scene.version,scene.state['contacts']),(23,['N-OWNER','N-NEIGHBOUR']))
    put(scene,'P',{'kind':'progress','seconds':120,'depends':['S']});check('actual partial record24',(scene.version,scene.state['job']['seconds']),(24,120))
    before=snapshot(scene);scene.hold=True;scene.ooc_wait(604800);scene.session_boundary()
    check('one week plus session end no IC/state advance',snapshot(scene),before)
    scene.submit('R',{'kind':'progress','seconds':180,'depends':['S','P']})
    reject_scene('remaining work cannot run while held',scene,lambda:scene.commit('R',24))
    check('work and resources still partial',(scene.state['job']['seconds'],scene.state['HP'],scene.state['Ego'],scene.state['ammo']),(120,5,6,4))
    scene.hold=False;scene.commit('R',24);put(scene,'C',{'kind':'complete','depends':['S','P','R']})
    check('actual180 after120 completes',(scene.version,scene.state['normal'],scene.state['job']['seconds']),(26,True,300))
    check('completion does not heal/refill',(scene.state['HP'],scene.state['Ego'],scene.state['ammo']),(5,6,4))
    reject_scene('reposted completion does not apply twice',scene,lambda:scene.commit('C',26))
    reject_scene('partial correction needs dependent scope',scene,lambda:scene.correct({'P'},26))
    scene.correct({'P','R','C'},26)
    check('explicit work correction keeps source cost/other contacts',(scene.version,scene.state['job']['seconds'],scene.state['spent'],scene.state['contacts']),(27,0,['PART-01'],['N-OWNER','N-NEIGHBOUR']))
    check('audit original events retained',[e['id'] for e in scene.events],['S','A','B','P','R','C'])
    orders=0
    for order in permutations(['A','B','D']):
        s=Scene();put(s,'S',start_event())
        for name in order:s.submit(name,{'kind':'contact','person':'KNOWN-'+name})
        for n,name in enumerate(order):
            if n:
                old=snapshot(s)
                try:s.commit(name,21)
                except ValueError:assert snapshot(s)==old
                else:raise AssertionError('stale parallel edit')
            s.commit(name,s.version)
        assert s.version==24 and set(s.state['contacts'])=={'KNOWN-A','KNOWN-B','KNOWN-D'} and s.state['job']['seconds']==0
        orders+=1
    check('three submitted edits six arrival orders',orders,6)
    text=export_current(example);check('JSON current state roundtrip',load_current(text,'P-ON-01',24),example)
    twice=export_current(load_current(text,'P-ON-01',24));check('stable copied backup hash',hashlib.sha256(twice.encode()).hexdigest(),hashlib.sha256(text.encode()).hexdigest())
    check('person learning and original/local damage stay separate',(example['person']['skills'],[(b['id'],b['HP'],b['ammo']) for b in example['bodies']],example['person']['ego'],example['person']['realm_bans']),(dict(zip(intro['character']['skills'],intro['character']['presets']['생활 중개자'])),[('B0',9,0),('B1',5,4)],6,['REMOTE-OLD']))
    rejects('other person backup',lambda:load_current(text,'OTHER',24))
    rejects('history backup cannot overwrite current25',lambda:load_current(text,'P-ON-01',25))
    rejects('duplicate top-level JSON field',lambda:load_current(text[:-1]+',"state_version":24}','P-ON-01',24))
    rejects('nonfinite JSON values',lambda:load_current(text.replace('"ego":6','"ego":NaN'),'P-ON-01',24))
    bad_cases=[]
    def malformed(name,change):
        d=deepcopy(example);change(d);bad_cases.append((name,d))
    malformed('different engine',lambda d:d.update(rules='Grade-Die'))
    malformed('different format',lambda d:d.update(format='OLD-YAML'))
    malformed('boolean state version',lambda d:d.update(state_version=True))
    malformed('missing current body',lambda d:d['person'].update(active_body='MISSING'))
    malformed('missing original body',lambda d:d['person'].update(original_body='MISSING'))
    malformed('duplicated bodyID',lambda d:d['bodies'][1].update(id='B0'))
    malformed('negative HP',lambda d:d['bodies'][1].update(HP=-1))
    malformed('HP over current body maximum',lambda d:d['bodies'][1].update(HP=13))
    malformed('boolean ammo',lambda d:d['bodies'][1].update(ammo=True))
    malformed('negative ammo',lambda d:d['bodies'][1].update(ammo=-1))
    malformed('shield charge over entry specification',lambda d:d['bodies'][1].update(shield_charge=3))
    malformed('stored active body',lambda d:d['bodies'][1].update(stored=True))
    malformed('negative Ego',lambda d:d['person'].update(ego=-1))
    malformed('Ego over maximum',lambda d:d['person'].update(ego=11))
    malformed('duplicate named realm ban',lambda d:d['person'].update(realm_bans=['REMOTE-OLD','REMOTE-OLD']))
    malformed('missing common skill',lambda d:d['person']['skills'].pop('생활'))
    malformed('old skill name',lambda d:d['person']['skills'].update(INT=9))
    malformed('boolean skill',lambda d:d['person']['skills'].update(생활=True))
    malformed('skill beyond growth limit',lambda d:d['person']['skills'].update(생활=96))
    malformed('old universal track field',lambda d:d.update(tracks={'shining':4}))
    malformed('interaction references absent body',lambda d:d['interactions'][0].update(body='MISSING'))
    malformed('interaction references old stat',lambda d:d['interactions'][0].update(skill='INT'))
    malformed('interaction loses acquisition origin',lambda d:d['interactions'][0].update(origin=''))
    malformed('IO original body differs',lambda d:d['IO'].update(original_body='B1'))
    malformed('pending event already confirmed',lambda d:d['scene'].update(pending_events=['S']))
    malformed('duplicate confirmed event',lambda d:d['scene'].update(completed_events=['S','S']))
    malformed('same part both spent and available',lambda d:d['scene'].update(parts=['PART-01']))
    malformed('duplicate registered contact',lambda d:d['scene'].update(contacts=['N-OWNER','N-OWNER']))
    malformed('work exceeds case300',lambda d:d['scene']['job'].update(seconds=301))
    malformed('work exceeds actual IC interval',lambda d:d['scene'].update(IC_seconds=119))
    for name,d in bad_cases:rejects('backup '+name,lambda d=d:load_current(json.dumps(d,ensure_ascii=False),'P-ON-01',24))
    roll_cases=0
    for base in [10,30,50,70,90,95]:
        for situation in [-20,0,20]:
            t=min(99,max(1,base+situation));results=[roll_record(base,situation,r) for r in range(1,101)]
            assert [sum(e['grade']==g for e in results) for g in [0,1,2,3]]==[100-t,t-t//2,t//2-t//5,t//5]
            assert all(e['original']==e['roll'] and e['target']==t for e in results);roll_cases+=100
    check('digital d100 bounded targets and all outcomes',roll_cases,1800)
    check('declared favourable result36',roll_record(70,20,36)['grade'],2)
    check('same original36 without advantage',roll_record(70,0,36)['grade'],1)
    check('00 means100 original preserved',(roll_record(50,0,'00')['roll'],roll_record(50,0,'00')['original'],roll_record(50,0,'00')['grade']),(100,'00',0))
    for bad in [0,101,True,'reroll','-1']:rejects('invalid original '+str(bad),lambda bad=bad:roll_record(50,0,bad))
    rejects('two stacked advantages not allowed',lambda:roll_record(50,40,20))
    check('old email sum is correct',(sum([6,4,2,7,5])+5,sum([6,4,2,7,5])+5-25),(29,4))
    files=[here.parent/'10_CoreRulebook.md',here.parent/'12_룰시트와캐릭터시트.md',here/'온라인_프로필.json',here/'온라인_기록예시.json',here/'장면운영_검증.py',here/'장면운영_프로필.json',here/'백분율_코어검증.py',here/'입문_프로필.json',Path(__file__)]
    ledger=json.loads((here/'제5판_이관검수.json').read_text());root=here.parent.parent;sources={}
    for i in profile['source_indices']:
        e=ledger['files'][i];q=root/e['source'];expected=e['observed_sha256'];assert hashlib.sha256(q.read_bytes()).hexdigest()==expected;sources[e['source']]=expected
    for e in ledger['online_operations_topic_sources']:
        assert hashlib.sha256((root/e['path']).read_bytes()).hexdigest()==e['sha256'];sources[e['path']]=e['sha256']
    return {'date':'2026-10-05','profile':profile['id'],'scope':'NEW공방같은Scene의부분작업/늦은버전/보류/정정·연락처등록6순서와예시한인물두몸JSON왕복/30잘못된기록·공통d1001800결과를한정검증. 연락처등록은새IC송신이아니며서비스인증/외부VTT/YAML·실시간동시쓰기·참가자/서사/커뮤재미검증아님.','checks_passed':len(checks),'checks':checks,'parallel_registration_orders':orders,'malformed_snapshot_cases':len(bad_cases),'digital_percentile_cases':roll_cases,'production_VTT_or_bot_verified':False,'external_YAML_or_VTT_import_verified':False,'all_online_community_concurrency_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False,'artifacts_sha256':{str(q.relative_to(here.parent)):hashlib.sha256(q.read_bytes()).hexdigest() for q in files},'source_sha256':sources}
if __name__=='__main__':
    r=run();Path(__file__).with_name('온라인_검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('profile','checks_passed','parallel_registration_orders','malformed_snapshot_cases','digital_percentile_cases','actual_participant_playtest')},ensure_ascii=False))
