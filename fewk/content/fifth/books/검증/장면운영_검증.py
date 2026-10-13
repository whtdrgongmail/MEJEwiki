from pathlib import Path
from copy import deepcopy
from itertools import product
import json, hashlib

here=Path(__file__).resolve().parent
p=json.loads((here/'장면운영_프로필.json').read_text())

class Scene:
    """작성 시트의 제한된 사건/정정 모형. 서비스나 자동 서사 생성기가 아니다."""
    def __init__(self):
        self.version=p['work_example']['start_version']
        self.pending={}; self.hold=False; self.events=[]; self.void=set()
        self.initial={'parts':['PART-01'], 'spent':[], 'job':None, 'normal':False,
          'HP':5, 'Ego':6, 'ammo':4, 'contacts':[], 'knowledge':{}, 'suspected':True,
          'realm_bans':[], 'body':'B1'}
        self.state=deepcopy(self.initial)
    def submit(self,event_id,event):
        if event_id in self.pending or any(e['id']==event_id for e in self.events):
            raise ValueError('duplicate submission')
        self.pending[event_id]=deepcopy(event)
    def cancel(self,event_id):
        if event_id not in self.pending:raise ValueError('no pending submission')
        del self.pending[event_id]
    def apply(self,state,event):
        kind=event['kind']
        if kind=='start':
            if state['job'] is not None or state['normal']:raise ValueError('job already exists')
            if not all(event.get(k,False) for k in ('consent','access','tools','compatible')):
                raise ValueError('actual start conditions absent')
            part=event['part']
            if part not in state['parts']:raise ValueError('actual part absent')
            state['parts'].remove(part);state['spent'].append(part)
            state['job']={'seconds':0,'running':True}
        elif kind=='progress':
            if not state['job'] or not state['job']['running']:raise ValueError('job not running')
            seconds=event['seconds']
            if type(seconds) is not int or seconds<0:raise ValueError('actual nonnegative seconds')
            state['job']['seconds']=min(300,state['job']['seconds']+seconds)
        elif kind=='complete':
            if not state['job'] or not state['job']['running'] or state['job']['seconds']<300:
                raise ValueError('unfinished work')
            # This worksheet example is approved safe functional repair, not HP healing.
            state['normal']=True;state['job']['running']=False
        elif kind=='contact':state['contacts'].append(event['person'])
        elif kind=='observe':
            source=event['source'];who=event['who']
            state['knowledge'].setdefault(who,{})[source]=set(event['facts'])
        elif kind=='transmit':
            known=state['knowledge'].get(event['from'],{}).get(event['source'],set())
            facts=set(event['facts'])
            if not facts or not facts<=known:raise ValueError('facts need actual known source')
            state['knowledge'].setdefault(event['to'],{}).setdefault(event['source'],set()).update(facts)
        elif kind=='confirm_permission':
            receipt=state['knowledge'].get('guard',{}).get('RECEIPT-01',set())
            if not {'issuer','export_permission'}<=receipt:raise ValueError('receipt not received')
            state['suspected']=False
        elif kind=='dropout':
            if event['realm'] not in state['realm_bans']:state['realm_bans'].append(event['realm'])
        elif kind=='switch_body':state['body']=event['body']
        else:raise ValueError('unsupported example event')
    def commit(self,event_id,base_version):
        if self.hold:raise ValueError('held scene')
        if base_version!=self.version:raise ValueError('stale state')
        if any(e['id']==event_id for e in self.events):raise ValueError('already committed')
        if event_id not in self.pending:raise ValueError('no pending event')
        event=deepcopy(self.pending[event_id]);event['id']=event_id
        active={e['id'] for e in self.events if e['id'] not in self.void}
        if not set(event.get('depends',[]))<=active:raise ValueError('missing active dependency')
        candidate=deepcopy(self.state)
        self.apply(candidate,event)  # failure has no partial state/cost/version effect
        self.state=candidate;self.events.append(event);del self.pending[event_id];self.version+=1
    def correct(self,scope,base_version):
        if base_version!=self.version:raise ValueError('stale correction')
        scope=set(scope);active=[e for e in self.events if e['id'] not in self.void]
        if not scope or not scope<={e['id'] for e in active}:raise ValueError('explicit active scope required')
        for e in active:
            if set(e.get('depends',[])) & scope and e['id'] not in scope:
                raise ValueError('dependent events must also be corrected')
        candidate=deepcopy(self.initial);new_void=self.void|scope
        for event in self.events:
            if event['id'] not in new_void:self.apply(candidate,event)
        self.state=candidate;self.void=new_void;self.version+=1
    def ooc_wait(self,seconds):
        if seconds<0:raise ValueError('negative OOC wait')
    def session_boundary(self):pass

def start_event(**kw):
    e={'kind':'start','part':'PART-01','consent':True,'access':True,'tools':True,'compatible':True}
    e.update(kw);return e

def put(scene,name,event):
    scene.submit(name,event);scene.commit(name,scene.version)

def snapshot(scene):return deepcopy((scene.state,scene.version,scene.events,scene.void))

def run():
    checks=[]
    def check(name,got,want):
        assert got==want,(name,got,want);checks.append(name)
    def rejected(name,scene,action):
        old=snapshot(scene)
        try:action()
        except ValueError:pass
        else:raise AssertionError(name+' accepted')
        check(name+' preserves committed state',snapshot(scene),old)
    check('same common engine',p['engine'],'P-FEWK-0.2')
    check('no universal new stats',p['new_universal_stats'],[])
    check('feelings remain owner authored',p['feelings_are_owner_authored'],True)
    scene=Scene();old=snapshot(scene);scene.submit('S',start_event())
    check('pending is not start or cost',snapshot(scene),old)
    scene.cancel('S');check('cancel before start no cost',snapshot(scene),old)
    put(scene,'S',start_event())
    check('start uses one actual part',(scene.state['parts'],scene.state['spent']),([],['PART-01']))
    check('start advances version once',scene.version,21)
    rejected('duplicate applied start',scene,lambda:scene.commit('S',scene.version))
    scene.submit('OTHER',start_event());rejected('no duplicate part repair',scene,lambda:scene.commit('OTHER',scene.version))
    put(scene,'P1',{'kind':'progress','seconds':120,'depends':['S']})
    check('partial work not complete',(scene.state['job']['seconds'],scene.state['normal']),(120,False))
    old=snapshot(scene);scene.hold=True;scene.ooc_wait(86400)
    check('hold and real-world wait do not spend time or resources',snapshot(scene),old)
    scene.submit('P2',{'kind':'progress','seconds':180,'depends':['P1']})
    rejected('held completion progress',scene,lambda:scene.commit('P2',scene.version))
    scene.hold=False
    rejected('stale version',scene,lambda:scene.commit('P2',21))
    scene.commit('P2',scene.version);put(scene,'DONE',{'kind':'complete','depends':['P2']})
    check('resume finishes same work and part',(scene.state['job']['seconds'],scene.state['normal'],scene.state['spent']),(300,True,['PART-01']))
    check('function repair not HP Ego or ammo',tuple(scene.state[k] for k in ('HP','Ego','ammo')),(5,6,4))
    old=snapshot(scene);scene.session_boundary();scene.ooc_wait(3600)
    check('session ending no resource reset',snapshot(scene),old)
    put(scene,'CALL',{'kind':'contact','person':'NPC-WORKSHOP'})
    old_version=scene.version
    rejected('correction lacking dependent completion',scene,lambda:scene.correct(['P1'],scene.version))
    rejected('correction lacking second progress',scene,lambda:scene.correct(['P1','DONE'],scene.version))
    scene.correct(['P1','P2','DONE'],scene.version)
    check('correction creates monotonic version',scene.version,old_version+1)
    check('correction keeps started cost',(scene.state['parts'],scene.state['spent']),([],['PART-01']))
    check('correction keeps unrelated latest contact',scene.state['contacts'],['NPC-WORKSHOP'])
    check('dependent results jointly removed',(scene.state['job'],scene.state['normal']),({'seconds':0,'running':True},False))
    check('prior events remain audit-visible',len(scene.events),5)
    rejected('corrected event cannot be replayed under old ID',scene,lambda:scene.submit('P1',{'kind':'progress','seconds':120}))
    put(scene,'NEW-PROGRESS',{'kind':'progress','seconds':300,'depends':['S']})
    put(scene,'NEW-DONE',{'kind':'complete','depends':['NEW-PROGRESS']})
    check('new continuation no extra part',scene.state['spent'],['PART-01'])
    scene=Scene();put(scene,'S',start_event())
    scene.submit('EARLY',{'kind':'complete','depends':['S']})
    rejected('premature completion atomic',scene,lambda:scene.commit('EARLY',scene.version))
    scene.submit('NEG',{'kind':'progress','seconds':-1,'depends':['S']})
    rejected('negative IC work rejected',scene,lambda:scene.commit('NEG',scene.version))
    scene.submit('MISSING',{'kind':'progress','seconds':120,'depends':['NONEXISTENT']})
    rejected('missing dependency',scene,lambda:scene.commit('MISSING',scene.version))
    start_cases=0
    for conditions in product((False,True),repeat=4):
        scene=Scene();e=start_event(**dict(zip(('consent','access','tools','compatible'),conditions)))
        scene.submit('S',e)
        if all(conditions):scene.commit('S',20);assert scene.state['spent']==['PART-01']
        else:
            old=snapshot(scene)
            try:scene.commit('S',20)
            except ValueError:pass
            else:raise AssertionError('missing start condition')
            assert snapshot(scene)==old
        start_cases+=1
    check('finite actual-start combinations',start_cases,16)
    time_cases=0
    for a,b in product((0,5,120,299),(0,1,5,180,300)):
        scene=Scene();put(scene,'S',start_event())
        put(scene,'A',{'kind':'progress','seconds':a,'depends':['S']})
        put(scene,'B',{'kind':'progress','seconds':b,'depends':['A']})
        assert scene.state['job']['seconds']==min(a+b,300) and scene.state['spent']==['PART-01']
        if a+b>=300:put(scene,'DONE',{'kind':'complete','depends':['B']});assert scene.state['normal']
        else:
            scene.submit('DONE',{'kind':'complete','depends':['B']});old=snapshot(scene)
            try:scene.commit('DONE',scene.version)
            except ValueError:pass
            else:raise AssertionError('premature completion')
            assert snapshot(scene)==old
        time_cases+=1
    check('finite split-work boundaries',time_cases,20)
    scene=Scene()
    put(scene,'CAM',{'kind':'observe','who':'guard','source':'CAM-01','facts':['local_appearance','box_id']})
    put(scene,'RECEIPT',{'kind':'observe','who':'workshop','source':'RECEIPT-01','facts':['issuer','export_permission']})
    check('video not physical identity', 'physical_identity' in scene.state['knowledge']['guard']['CAM-01'],False)
    scene.submit('CONFIRM-EARLY',{'kind':'confirm_permission'})
    rejected('confirm requires actual receipt transmission',scene,lambda:scene.commit('CONFIRM-EARLY',scene.version))
    scene.submit('FORGED',{'kind':'transmit','from':'workshop','to':'guard','source':'RECEIPT-01','facts':['physical_identity']})
    rejected('transmission cannot invent unknown facts',scene,lambda:scene.commit('FORGED',scene.version))
    put(scene,'SEND',{'kind':'transmit','from':'workshop','to':'guard','source':'RECEIPT-01','facts':['issuer','export_permission'],'depends':['RECEIPT']})
    put(scene,'CONFIRM',{'kind':'confirm_permission','depends':['SEND']})
    check('valid receipt corrects suspicion',scene.state['suspected'],False)
    check('video evidence not erased',scene.state['knowledge']['guard']['CAM-01'],{'local_appearance','box_id'})
    check('no automatic other faction propagation','other_faction' in scene.state['knowledge'],False)
    known=deepcopy(scene.state['knowledge'])
    put(scene,'DROP',{'kind':'dropout','realm':'C1'});put(scene,'BODY',{'kind':'switch_body','body':'B2'})
    check('dropout and new body preserve knowledge',scene.state['knowledge'],known)
    check('dropout has named realm ban only',scene.state['realm_bans'],['C1'])
    check('no global emotional fields',all(k not in scene.state for k in ('love','sanity','luck','DSR','trauma')),True)
    check('actual human evidence remains absent',(p['actual_participant_playtest'],p['actual_async_community_test']),(False,False))
    files=[here.parent/'10_CoreRulebook.md',here.parent/'12_룰시트와캐릭터시트.md',here/'장면운영_프로필.json',Path(__file__)]
    return {'date':'2026-10-05','profile':p['id'],'scope':'작성된 운영 예의 제한된 사건 모형: 실제 시작/부분 작업·중복/오래된 상태/명시적 의존 사건 정정·자원 유지·증거 전달. 서비스의 동시성/보안·모든 이야기 상황·세계 시간도보·실제 참가자 이해/재미 검증 아님.','checks_passed':len(checks),'checks':checks,'start_condition_cases':start_cases,'split_work_cases':time_cases,'correction_is_world_time_travel':False,'production_VTT_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False,'artifacts_sha256':{str(f.relative_to(here.parent)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}

if __name__=='__main__':
    r=run();Path(__file__).with_name('장면운영_검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('profile','checks_passed','start_condition_cases','split_work_cases','actual_participant_playtest')},ensure_ascii=False))
