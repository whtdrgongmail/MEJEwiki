from pathlib import Path
from copy import deepcopy
from itertools import product
from dataclasses import dataclass,field
import json,hashlib
from 백분율_코어검증 import grade
from 일반플레이_검증 import Body,new_round,aid,recover
from 임플란트_검증 import can_submit
here=Path(__file__).resolve().parent;o=here.parent;p=o.parent
profile=json.loads((here/'몸노출_계산프로필.json').read_text())
E,I,R,C=(profile[k] for k in ('exposure','injury','paradox','computation'))

class Person:
    def __init__(self):
        self.bodies={'B-F0':Body(hp=9),'B-F1':Body()};self.grips={'B-F0':True,'B-F1':True}
        self.stored=set();self.active='B-F1';self.ego=6;self.bans=[];self.skills={'공학':50,'해킹':50,'사격':70}
        self.seconds=0;self.events=set()
    def __eq__(self,other):return isinstance(other,Person) and self.__dict__==other.__dict__
    def contact(self,event_id,source,roll,access=True,device_supported=True):
        b=self.bodies[self.active];e=profile['exposure']
        if not event_id or event_id in self.events or source not in ('REC-F1','COPY-F1') or not access or not device_supported or self.active in self.stored or b.hp<=0 or b.destroyed or b.main<1 or type(roll) is not int or not 1<=roll<=100:
            raise ValueError('actual new eligible direct contact required')
        b.main-=1;self.seconds+=e['seconds'];self.events.add(event_id)
        success=grade(e['body_resistance'],roll)>0
        if not success:
            b.hp=max(0,b.hp-max(0,e['raw_damage_on_failed_contact']-b.armor));self.grips[self.active]=False
        return success
    def function_available(self,body,required):
        b=self.bodies[body]
        if body in self.stored or b.hp<=0 or b.destroyed:return False
        if required in ('left','both'):return self.grips[body]
        if required=='right':return True
        raise ValueError('declared grasp requirements only')
    def select_supported_IO_result(self,body):
        # 다른 절차에서 해결한 지원 IO의 몸 선택 결과만 참조한다. IO 전체의 구현은 아니다.
        if body not in self.bodies:raise ValueError('unknown body')
        self.active=body
    def ooc_wait(self,seconds):
        if seconds<0:raise ValueError('negative OOC')

@dataclass
class Clinic:
    person:Person=field(default_factory=Person)
    supply:int=1
    job:dict|None=None
    started:set=field(default_factory=set)
    held:bool=False
    def start(self,event_id,body='B-F1',provider=True,access=True,compatible=True,support=True):
        b=self.person.bodies[body]
        if self.held or not event_id or event_id in self.started or (self.job is not None and self.job['running']) or not all((provider,access,compatible,support)) or body in self.person.stored or b.destroyed or self.supply<1:
            raise ValueError('actual supported treatment required')
        self.supply-=1;self.started.add(event_id);self.job={'id':event_id,'body':body,'seconds':0,'running':True}
    def progress(self,seconds):
        if self.held or not self.job or not self.job['running'] or type(seconds) is not int or seconds<0:
            raise ValueError('actual ongoing treatment seconds required')
        if self.job['body'] in self.person.stored or self.person.bodies[self.job['body']].destroyed:raise ValueError('body unavailable')
        self.job['seconds']=min(I['clinic_hours']*3600,self.job['seconds']+seconds)
    def finish(self,window,success=True):
        if self.held or not self.job or not self.job['running'] or self.job['seconds']<I['clinic_hours']*3600:raise ValueError('actual completed treatment required')
        body=self.job['body'];b=self.person.bodies[body]
        if body in self.person.stored or b.destroyed:raise ValueError('body unavailable')
        self.job['running']=False
        if success:
            self.person.grips[body]=True
            return recover(b,window,clinic=True)
        return False
    def ooc_wait(self,seconds):self.person.ooc_wait(seconds)

@dataclass
class Relay:
    body:Body=field(default_factory=Body)
    buffer:int=R['starting_actual_buffer']
    suspended:bool=False
    seconds:int=0
    events:set=field(default_factory=set)
    job:dict|None=None
    held:bool=False
    def force(self,event_id,mismatched=True,actual_access=True):
        if self.held or not event_id or event_id in self.events or self.suspended or not mismatched or not actual_access or self.body.hp<=0 or self.body.destroyed or self.body.main<1:
            raise ValueError('one declared mismatched actual output required')
        self.body.main-=1;self.seconds+=5;self.events.add(event_id);self.suspended=True
    def start(self,event_id,learned=True,compatible=True,access=True,support=True):
        if self.held or not event_id or event_id in self.events or not self.suspended or (self.job is not None and self.job['running']) or not all((learned,compatible,access,support)) or self.buffer<R['correction_cost_on_start'] or self.body.hp<=0 or self.body.destroyed or self.body.main<1:
            raise ValueError('actual correction resources and conditions required')
        self.body.main-=1;self.buffer-=R['correction_cost_on_start'];self.events.add(event_id);self.job={'id':event_id,'seconds':0,'running':True}
    def progress(self,seconds):
        if self.held or not self.job or not self.job['running'] or type(seconds) is not int or seconds<0 or self.body.hp<=0 or self.body.destroyed:
            raise ValueError('actual available correction work required')
        delta=min(seconds,R['correction_seconds']-self.job['seconds']);self.job['seconds']+=delta;self.seconds+=delta
    def finish(self,roll=None):
        if self.held or not self.job or not self.job['running'] or self.job['seconds']<R['correction_seconds'] or self.body.hp<=0 or self.body.destroyed:raise ValueError('unfinished correction')
        if roll is not None and (type(roll) is not int or not 1<=roll<=100):raise ValueError('valid common roll required')
        success=True if roll is None else grade(R['target'],roll)>0
        self.job['running']=False;self.suspended=not success
        return success
    def ooc_wait(self,seconds):
        if seconds<0:raise ValueError('negative OOC')

@dataclass
class Processor:
    body:Body=field(default_factory=Body)
    active:str='B-F1'
    installed:str='B-F1'
    installed_ok:bool=True
    approved:bool=True
    network:bool=True
    account:bool=True
    receiver:bool=True
    source:bool=True
    permission:bool=True
    memory_used:int=0
    flares:int=C['flare_budget']
    branches:int=C['branch_budget']
    seconds:int=0
    outputs:dict=field(default_factory=dict)
    used:set=field(default_factory=set)
    def connected(self):
        return self.active==self.installed and self.installed_ok and self.approved and can_submit(self.active,self.installed,self.installed_ok,True,self.approved,self.network,self.account,self.receiver)
    def compute(self,event_id):
        if not event_id or event_id in self.used or not self.connected() or not self.source or not self.permission or self.body.hp<=0 or self.body.destroyed or self.body.main<1 or self.memory_used+C['output_memory_letters']>C['memory_capacity_letters'] or self.flares<C['task_flares'] or self.branches<C['task_branches']:
            raise ValueError('actual source/receiver/connected body and finite batch required')
        self.body.main-=1;self.seconds+=5;self.memory_used+=C['output_memory_letters'];self.flares-=C['task_flares'];self.branches-=C['task_branches']
        self.outputs[event_id]={'source':'DATA-F1','receiver':'DESK-F1','letters':C['output_memory_letters']};self.used.add(event_id)
    def erase(self,event_id,authorized=True):
        if event_id not in self.outputs or not authorized or not self.connected() or self.body.hp<=0 or self.body.destroyed or self.body.main<1:raise ValueError('actual authorized deletion required')
        self.body.main-=1;self.seconds+=5;self.memory_used-=self.outputs.pop(event_id)['letters']
    def ooc_wait(self,seconds):
        if seconds<0:raise ValueError('negative OOC')


class RecordLab:
    """REC-F1을 지원하는 지정 정상 절차만 검산한다."""
    def __init__(self):
        self.person=Person();self.seconds=0;self.events=set();self.operations=[]
        self.items={'REC-F1':{'kind':'original','holder':'접수처','sealed':False,'hazard':'BLK-REC-F1'}}
    def _ready(self,event_id):
        b=self.person.bodies[self.person.active]
        if not event_id or event_id in self.events or self.person.active in self.person.stored or b.hp<=0 or b.destroyed or b.main<1:
            raise ValueError('actual new available body action required')
    def _commit(self,event_id,operation):
        self.person.bodies[self.person.active].main-=1
        self.seconds+=profile['record_containment']['seconds_per_operation'];self.events.add(event_id);self.operations.append(operation)
    def metadata(self,event_id,external_device=True,authorized=True):
        self._ready(event_id)
        if not external_device or not authorized:raise ValueError('supported separate metadata access required')
        self._commit(event_id,'metadata')
        return tuple(profile['record_containment']['safe_metadata_fields'])
    def pack(self,event_id,item='REC-F1',container=True,physical_access=True,authorized=True):
        self._ready(event_id)
        if item not in self.items or not all((container,physical_access,authorized)):
            raise ValueError('supported actual replay-path block required')
        self._commit(event_id,'pack');self.items[item]['sealed']=True
    def copy(self,event_id,new_id,source='REC-F1',device=True,authorized=True,capacity=True,isolated=True,receiver_approved=True):
        self._ready(event_id)
        if source not in self.items or not new_id or new_id in self.items or not all((device,authorized,capacity,isolated,receiver_approved)):
            raise ValueError('non-replaying supported full-copy destination required')
        self._commit(event_id,'copy')
        self.items[new_id]={'kind':'copy','holder':'격리 저장처','sealed':True,'hazard':self.items[source]['hazard']}
    def handover(self,event_id,item='REC-F1',receiver='검사소',arrival=True,physical_access=True,export_authorized=True,receiver_approved=True):
        self._ready(event_id)
        if item not in self.items or not self.items[item]['sealed'] or not receiver or not all((arrival,physical_access,export_authorized,receiver_approved)):
            raise ValueError('wrapped original actual arrival/access and agreed handover required')
        self._commit(event_id,'handover');self.items[item]['holder']=receiver
    def erase_copy(self,event_id,item,actual_access=True,authorized=True):
        self._ready(event_id)
        if item not in self.items or self.items[item]['kind']!='copy' or not actual_access or not authorized:
            raise ValueError('actual authorized one-copy deletion required')
        self._commit(event_id,'erase_copy');del self.items[item]
    def open_path(self,event_id,item,actual_access=True,authorized=True):
        self._ready(event_id)
        if item not in self.items or not self.items[item]['sealed'] or not actual_access or not authorized:
            raise ValueError('actual authorized replay-path opening required')
        self._commit(event_id,'open_path');self.items[item]['sealed']=False
    def replay(self,event_id,item,roll,actual_access=True,authorized=True,device=True):
        self._ready(event_id)
        if item not in self.items or self.items[item]['sealed'] or self.person.active!=profile['record_containment']['eligible_replay_body'] or not all((actual_access,authorized,device)):
            raise ValueError('actual unblocked supported declared body replay required')
        # contact() validates the roll and consumes the one same body action.
        result=self.person.contact(event_id,'REC-F1' if self.items[item]['kind']=='original' else 'COPY-F1',roll)
        self.events.add(event_id);self.seconds+=E['seconds'];self.operations.append('replay')
        return result
    def next_round(self):new_round(self.person.bodies[self.person.active])
    def ooc_wait(self,seconds):self.person.ooc_wait(seconds)

def run():
    checks=[]
    def check(n,a,b):assert a==b,(n,a,b);checks.append(n)
    def reject(n,obj,fn):
        before=deepcopy(obj.__dict__)
        try:fn()
        except ValueError:pass
        else:raise AssertionError(n+' accepted')
        check(n+' preserves current state',obj.__dict__,before)
    check('same engine',profile['engine'],'P-FEWK-0.2')
    check('same unified term',profile['unified_action_term'],'인터랙션')
    check('no creation track or new stats',(profile['creation_origin_tracks'],profile['new_universal_stats']),(False,[]))
    person=Person();old_skills=deepcopy(person.skills);person.contact('C1','REC-F1',71)
    check('failed current body contact actual damage',(person.bodies['B-F1'].hp,person.grips['B-F1'],person.seconds,person.bodies['B-F1'].main),(10,False,5,0))
    check('original ego skills bans not changed',(person.bodies['B-F0'].hp,person.ego,person.skills,person.bans),(9,6,old_skills,[]))
    check('P/L shield does not block this contact',person.bodies['B-F1'].charges,2)
    check('actual grasp requirements',[person.function_available('B-F1',r) for r in ('left','both','right')],[False,False,True])
    reject('same event no double contact',person,lambda:person.contact('C1','REC-F1',71))
    new_round(person.bodies['B-F1']);person.contact('C2','COPY-F1',71)
    check('actual complete copy contact same condition',person.bodies['B-F1'].hp,8)
    person.select_supported_IO_result('B-F0');check('new selected body no copied injury',person.function_available('B-F0','left'),True)
    check('old body injury retained',(person.bodies['B-F1'].hp,person.grips['B-F1']),(8,False))
    person=Person();reject('safe metadata not direct harmful content',person,lambda:person.contact('META','META-F1',71))
    reject('wrapped transport not direct replay',person,lambda:person.contact('BOX','WRAPPED-REC-F1',71))
    reject('permission missing no actual content operation',person,lambda:person.contact('NO-PERM','REC-F1',71,access=False))
    reject('support missing no actual content operation',person,lambda:person.contact('NO-DEVICE','REC-F1',71,device_supported=False))
    person.bodies['B-F1'].hp=0;reject('incapacitated body cannot voluntary replay',person,lambda:person.contact('DOWN','REC-F1',71))
    exposure_cases=0
    for armor,roll in product((0,1,3,5),range(1,101)):
        x=Person();x.bodies['B-F1'].armor=armor;success=x.contact('E','REC-F1',roll)
        assert success==(roll<=50) and x.bodies['B-F1'].hp==12-(0 if success else max(0,3-armor)) and x.grips['B-F1']==success
        assert (x.bodies['B-F0'].hp,x.ego,x.bodies['B-F1'].charges)==(9,6,2);exposure_cases+=1
    check('current armor and all d100 exposure cases',exposure_cases,400)
    clinic=Clinic(person=Person());clinic.person.contact('C','REC-F1',71)
    aid(clinic.person.bodies['B-F1'],1,True)
    check('HP aid alone no grip cure',(clinic.person.bodies['B-F1'].hp,clinic.person.grips['B-F1']),(12,False))
    clinic.person.bodies['B-F1'].hp=5;clinic.start('T');clinic.progress(120)
    check('start and partial treatment actual cost',(clinic.supply,clinic.job['seconds'],clinic.person.grips['B-F1']),(0,120,False))
    before=deepcopy(clinic.__dict__);clinic.ooc_wait(86400);check('OOC not treatment progress',clinic.__dict__,before)
    clinic.held=True;reject('held treatment no progress',clinic,lambda:clinic.progress(180));clinic.held=False
    reject('early treatment completion',clinic,lambda:clinic.finish(0));clinic.progress(21480);clinic.finish(0)
    check('supported six hours restore grip and shared HP',(clinic.person.grips['B-F1'],clinic.person.bodies['B-F1'].hp,clinic.person.bodies['B-F1'].recovery_window),(True,9,0))
    reject('same completed visit no duplicate recovery',clinic,lambda:clinic.finish(0))
    clinic=Clinic();b=clinic.person.bodies['B-F1'];b.hp=5;b.recovery_window=0;clinic.person.grips['B-F1']=False;clinic.start('T');clinic.progress(21600)
    check('same HP window can restore designated function only',(clinic.finish(0),b.hp,clinic.person.grips['B-F1']),(False,5,True))
    clinic=Clinic();clinic.person.bodies['B-F1'].hp=0;clinic.person.grips['B-F1']=False;clinic.start('T');clinic.progress(21600);clinic.finish(0)
    check('actual clinic at zero uses common stabilization',(clinic.person.bodies['B-F1'].hp,clinic.person.grips['B-F1']),(1,True))
    clinic=Clinic();clinic.person.bodies['B-F1'].hp=5;clinic.person.grips['B-F1']=False;clinic.start('T');clinic.progress(21600);clinic.finish(0,False)
    check('failed risky visit no function or HP recovery',(clinic.person.bodies['B-F1'].hp,clinic.person.grips['B-F1'],clinic.person.bodies['B-F1'].recovery_window,clinic.supply),(5,False,-1,0))
    clinic.supply=1;clinic.start('T2');clinic.progress(21600);clinic.finish(0)
    check('new actual supported visit after failure',(clinic.supply,clinic.person.bodies['B-F1'].hp,clinic.person.grips['B-F1']),(0,9,True))
    clinic=Clinic();clinic.person.stored.add('B-F1');reject('stored body not treated',clinic,lambda:clinic.start('S'))
    clinic=Clinic();clinic.person.bodies['B-F1'].destroyed=True;reject('destroyed body not cured',clinic,lambda:clinic.start('D'))
    treatment_cases=0
    for conditions in product((False,True),repeat=4):
        x=Clinic();before=deepcopy(x.__dict__)
        try:x.start('T',**dict(zip(('provider','access','compatible','support'),conditions)));got=True
        except ValueError:got=False
        assert got==all(conditions)
        if not got:assert x.__dict__==before
        treatment_cases+=1
    check('actual clinic start boundaries',treatment_cases,16)
    relay=Relay();relay.force('F');new_round(relay.body);relay.start('S');relay.progress(120)
    check('actual correction resource and partial time',(relay.buffer,relay.job['seconds'],relay.suspended,relay.seconds),(20000,120,True,125))
    before=deepcopy(relay.__dict__);relay.ooc_wait(86400);check('OOC not correction budget or time',relay.__dict__,before)
    relay.held=True;reject('held correction does not progress',relay,lambda:relay.progress(180));relay.held=False
    reject('partial correction not repaired',relay,lambda:relay.finish());relay.progress(180);relay.finish()
    check('safe correction current output only',(relay.buffer,relay.suspended,relay.body.hp,relay.body.charges),(20000,False,12,2))
    reject('same job not completed again',relay,lambda:relay.finish())
    relay=Relay();relay.force('F');reject('same suspended output cannot add free action',relay,lambda:relay.force('F2'))
    new_round(relay.body);relay.start('S');relay.progress(300);relay.finish(100)
    check('failed risky correction cost remains',(relay.buffer,relay.suspended,relay.job['seconds']),(20000,True,300))
    new_round(relay.body);relay.start('S2');relay.progress(300);relay.finish(50)
    check('new paid correction can actually retry',(relay.buffer,relay.suspended,relay.seconds),(0,False,605))
    correction_cases=0
    for available,elapsed,roll in product((19999,20000,40000),(0,120,299,300),(1,50,51,100)):
        x=Relay(buffer=available);x.force('F');new_round(x.body);before=deepcopy(x.__dict__)
        if available<20000:
            try:x.start('S')
            except ValueError:pass
            else:raise AssertionError('missing Byte start')
            assert x.__dict__==before
        else:
            x.start('S');x.progress(elapsed);before=deepcopy(x.__dict__)
            if elapsed<300:
                try:x.finish(roll)
                except ValueError:pass
                else:raise AssertionError('early correction')
                assert x.__dict__==before
            else:assert x.finish(roll)==(roll<=50) and x.suspended==(roll>50)
            assert x.buffer==available-20000
        correction_cases+=1
    check('actual finite correction cost time and percentile boundaries',correction_cases,48)
    processor=Processor();processor.compute('J1');new_round(processor.body);processor.compute('J2')
    check('two actual outputs finite batch',(processor.memory_used,processor.flares,processor.branches,processor.seconds),(1024,0,0,10))
    check('real output sources and receivers',[(v['source'],v['receiver'],v['letters']) for v in processor.outputs.values()],[('DATA-F1','DESK-F1',512)]*2)
    new_round(processor.body);processor.erase('J1')
    check('delete memory not previous computation',(processor.memory_used,processor.flares,processor.branches,processor.seconds,processor.body.main),(512,0,0,15,0))
    new_round(processor.body);reject('cleared space not unused flares branches',processor,lambda:processor.compute('J3'))
    reject('erased old ID not new job',processor,lambda:processor.compute('J1'))
    before=deepcopy(processor.__dict__);processor.ooc_wait(86400);check('OOC no new batch',processor.__dict__,before)
    processor=Processor(active='B-F0');reject('original connector not current local device',processor,lambda:processor.compute('J1'))
    processor=Processor();processor.body.hp=0;reject('incapacitated operator no compute',processor,lambda:processor.compute('J1'))
    processor=Processor();processor.compute('J1');reject('same turn no second compute',processor,lambda:processor.compute('J2'))
    processor=Processor();processor.compute('J1');new_round(processor.body);reject('deletion requires actual permission',processor,lambda:processor.erase('J1',False))
    compute_conditions=0
    fields=('installed_ok','approved','network','account','receiver','source','permission')
    for conditions in product((False,True),repeat=7):
        x=Processor(**dict(zip(fields,conditions)));before=deepcopy(x.__dict__)
        try:x.compute('JOB');got=True
        except ValueError:got=False
        assert got==all(conditions)
        if not got:assert x.__dict__==before
        else:assert (x.memory_used,x.flares,x.branches,x.body.main)==(512,8,1,0)
        compute_conditions+=1
    check('actual connection permission source prerequisite cases',compute_conditions,128)
    compute_resources=0
    for used,flares,branches in product((0,512,513,1024),(0,7,8,16),(0,1,2)):
        x=Processor(memory_used=used,flares=flares,branches=branches);before=deepcopy(x.__dict__)
        try:x.compute('JOB');got=True
        except ValueError:got=False
        expected=used+512<=1024 and flares>=8 and branches>=1;assert got==expected
        if got:assert (x.memory_used,x.flares,x.branches)==(used+512,flares-8,branches-1)
        else:assert x.__dict__==before
        compute_resources+=1
    check('finite independent memory flare branch cases',compute_resources,48)
    check('eight device contexts read',len(profile['device_contexts']),8)
    check('actual human evidence absent',(profile['actual_participant_reading'],profile['actual_participant_playtest'],profile['actual_async_community_test']),(False,False,False))
    lab=RecordLab();before_items=deepcopy(lab.items)
    check('declared separate metadata fields',lab.metadata('M'),('자료ID','발견 장소','보관자','위험 표지','인계 연락처'))
    check('metadata no direct exposure',(lab.person.bodies['B-F1'].hp,lab.person.grips['B-F1'],lab.items),(12,True,before_items))
    reject('same body turn not free packaging',lab,lambda:lab.pack('P'))
    lab.next_round();lab.pack('P');lab.next_round();lab.handover('H')
    check('safe inquiry packaging actual handover',(lab.items,lab.seconds,lab.person.bodies['B-F1'].hp,lab.person.bodies['B-F0'].hp,lab.person.ego),({'REC-F1':{'kind':'original','holder':'검사소','sealed':True,'hazard':'BLK-REC-F1'}},15,12,9,6))
    lab.next_round();reject('same submitted event not repeated',lab,lambda:lab.handover('H'))
    reject('wrapped item not direct replay',lab,lambda:lab.replay('R','REC-F1',71))
    snapshot=deepcopy(lab.__dict__);lab.ooc_wait(604800);check('OOC not exposure transfer or deletion',lab.__dict__,snapshot)
    lab.copy('COPY1','COPY-Q1');lab.next_round();lab.copy('COPY2','COPY-Q2')
    check('full copy same hazard original remains',[(k,x['hazard'],x['sealed']) for k,x in lab.items.items()],[('REC-F1','BLK-REC-F1',True),('COPY-Q1','BLK-REC-F1',True),('COPY-Q2','BLK-REC-F1',True)])
    lab.next_round();reject('duplicate copy identity not overwrite',lab,lambda:lab.copy('DUP','COPY-Q1'))
    lab.erase_copy('DEL','COPY-Q1');check('one copy removed only',list(lab.items),['REC-F1','COPY-Q2'])
    lab.next_round();reject('original not permitted deletion in assignment',lab,lambda:lab.erase_copy('DEL-O','REC-F1'))
    reject('deleted copy no replay',lab,lambda:lab.replay('GONE','COPY-Q1',71))
    lab.open_path('OPEN','COPY-Q2');lab.next_round();lab.replay('REPLAY','COPY-Q2',71)
    check('actual unblocked copied content same one exposure',(lab.person.bodies['B-F1'].hp,lab.person.grips['B-F1'],lab.person.bodies['B-F1'].main,lab.person.seconds),(10,False,0,5))
    lab.next_round();lab.erase_copy('DELETE-EXPOSED','COPY-Q2')
    check('delete no retroactive body cure',(lab.person.bodies['B-F1'].hp,lab.person.grips['B-F1'],list(lab.items)),(10,False,['REC-F1']))
    copy_conditions=0
    for conditions in product((False,True),repeat=5):
        x=RecordLab();before=deepcopy(x.__dict__)
        try:x.copy('C','COPY-Q1',**dict(zip(('device','authorized','capacity','isolated','receiver_approved'),conditions)));got=True
        except ValueError:got=False
        assert got==all(conditions)
        if not got:assert x.__dict__==before
        else:assert len(x.items)==2 and x.items['REC-F1']['holder']=='접수처' and x.items['COPY-Q1']['sealed'] and x.person.bodies['B-F1'].hp==12
        copy_conditions+=1
    check('actual non-replaying full copy conditions',copy_conditions,32)
    handover_conditions=0
    for conditions in product((False,True),repeat=4):
        x=RecordLab();x.pack('P');x.next_round();before=deepcopy(x.__dict__)
        try:x.handover('H',**dict(zip(('arrival','physical_access','export_authorized','receiver_approved'),conditions)));got=True
        except ValueError:got=False
        assert got==all(conditions)
        if not got:assert x.__dict__==before
        else:assert len(x.items)==1 and x.items['REC-F1']['holder']=='검사소'
        handover_conditions+=1
    check('arrival access export receiver conditions',handover_conditions,16)
    x=RecordLab();reject('unwrapped object not safe handover route',x,lambda:x.handover('H'))
    for flag in ('container','physical_access','authorized'):
        x=RecordLab();reject('pack missing '+flag,x,lambda:x.pack('P',**{flag:False}))
    x=RecordLab();reject('safe metadata actual supported device',x,lambda:x.metadata('M',external_device=False))
    reject('safe metadata actual authority',x,lambda:x.metadata('M',authorized=False))
    x=RecordLab();x.person.bodies['B-F1'].hp=0;reject('incapacitated operator no copy',x,lambda:x.copy('C','COPY-Q1'))
    x=RecordLab();x.person.stored.add('B-F1');reject('stored operator no copy',x,lambda:x.copy('C','COPY-Q1'))
    x=RecordLab();x.person.select_supported_IO_result('B-F0');reject('profile does not invent original-body exposure',x,lambda:x.replay('R','REC-F1',71))
    x=RecordLab();reject('invalid roll no partial record or action',x,lambda:x.replay('R','REC-F1',101))
    check('copy containment no creation progression',(profile['record_containment']['all_matting_transformation_and_treatment_complete'],profile['creation_origin_tracks']),(False,False))
    ledger=json.loads((here/'제5판_이관검수.json').read_text());hashes={ledger['files'][i]['source']:hashlib.sha256((p/ledger['files'][i]['source']).read_bytes()).hexdigest() for i in profile['source_indices']}
    for i in profile['source_indices']:assert hashes[ledger['files'][i]['source']]==ledger['files'][i]['observed_sha256']
    for e in ledger['local_effect_computation_topic_sources']:
        hashes[e['path']]=hashlib.sha256((p/e['path']).read_bytes()).hexdigest();assert hashes[e['path']]==e['sha256']
    names=['10_CoreRulebook.md','11_WorldLorebook.md','12_룰시트와캐릭터시트.md']+['검증/'+n for n in ['몸노출_계산프로필.json','백분율_코어검증.py','일반플레이_검증.py','입문_프로필.json','임플란트_검증.py','임플란트_프로필.json']]
    artifacts={n:hashlib.sha256((o/n).read_bytes()).hexdigest() for n in names};artifacts[str(Path(__file__).relative_to(o))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {'date':'2026-10-06','profile':profile['id'],'scope':'REC-QUAR-F1의 지정 안전목록/지원차단·복사/인계·삭제와 기존 신규4예만: 같은 저항/피해·몸손기능과지정매개 접촉/사본·지원처치/동일HP창·릴레이출력/보정자원/실제작업·장치연결/망/계정/자료권한과한계산배치의독립공간/연산/분기/삭제. 모든현화/영구손상/현실의료·재난/먹개비·계의물리/실제IO/8상품전부·독자/전투균형/실제참가자검증아님.','checks_passed':len(checks),'checks':checks,'non_replaying_copy_condition_cases':copy_conditions,'record_handover_condition_cases':handover_conditions,'record_containment_profile':profile['record_containment']['id'],'exposure_armor_percentile_cases':exposure_cases,'clinic_start_condition_cases':treatment_cases,'correction_cost_time_roll_cases':correction_cases,'computation_prerequisite_cases':compute_conditions,'computation_resource_cases':compute_resources,'source_sha256':hashes,'artifacts_sha256':artifacts,'all_ability_exposure_injury_paradox_device_profiles_complete':False,'full_encounter_balance_verified':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}

if __name__=='__main__':
 r=run();Path(__file__).with_name('몸노출_계산검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('profile','checks_passed','exposure_armor_percentile_cases','clinic_start_condition_cases','correction_cost_time_roll_cases','computation_prerequisite_cases','computation_resource_cases','actual_participant_playtest')},ensure_ascii=False))
