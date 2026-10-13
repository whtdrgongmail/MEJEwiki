#!/usr/bin/env python3
"""NEW 통신/외부연결 정비의 제한된 상태 모형. 지정 보조장치 생애주기와 통신/서비스연결. 전체 의료/상품·참가자 시험 아님."""
from pathlib import Path
from itertools import product
from copy import deepcopy
import json,hashlib
from 백분율_코어검증 import grade,target
here=Path(__file__).parent
p=json.loads((here/'임플란트_프로필.json').read_text())

def can_submit(active,installed_body,installed_ok,external,approved,network,account,contact):
    terminal=(active==installed_body and installed_ok) or (external and approved)
    return bool(terminal and network and account and contact)

def start(state,consent=True,access=True,tools=True,compatible=True):
    if state['running'] or state['normal'] or not all([consent,access,tools,compatible]) or state['spares']<1:return False
    state.update(running=True,elapsed=0,spares=state['spares']-1,spent=state['spent']+1)
    return True

def advance(state,seconds,safe=True,roll=None):
    if not state['running'] or seconds<0:raise ValueError('actual work and nonnegative duration required')
    state['elapsed']=min(p['repair']['work_seconds'],state['elapsed']+seconds)
    if state['elapsed']<p['repair']['work_seconds']:return 'pending'
    if not safe and roll is None:raise ValueError('one completion roll required')
    state['normal']=safe or grade(p['repair']['target'],roll)>0
    state['running']=False
    return 'complete' if state['normal'] else 'failed'


class ClinicalService:
    """지정 보조 장치/단일 기반의 예약·기능·실제 작업 모형."""
    def __init__(self,registry=None):
        self.body='B-C0';self.hp=9;self.bp=80;self.bp_current=True;self.ddogg=False
        self.framework='F-COM';self.framework_device='FW-COM-C1';self.framework_normal=True
        self.devices={'COMM-01':{'slot':'aux_comm','requires':'F-COM','normal':True},'CALC-C1':{'slot':'calc','requires':'F-WORK','normal':True}}
        self.stock={'COMM-C2':{'kind':'comm','slot':'aux_comm','requires':'F-COM'},'FW-WORK-C1':{'kind':'framework','framework':'F-WORK'}}
        self.work_items={};self.removed={};self.kits=2;self.spent=0;self.jobs=set();self.job=None;self.held=False
        self.registry={'DOC-C1':None,'DOC-C2':None} if registry is None else registry
        self.provider_skills={'DOC-C1':50,'DOC-C2':70};self.provider_bodies={'DOC-C1':'B-D1','DOC-C2':'B-D2'}
        self.other_body_HP=12;self.ego=6;self.learned={'공학':50,'관찰':70};self.account=False
    def start(self,job_id,mode,provider='DOC-C1',old_device='COMM-01',new_device='COMM-C2',bp_after=80,consent=True,physical=True,clinical_support=True,learned=True,compatible=True,provider_present=True,work_item_inspected=False):
        c=p['clinical_service']
        if self.held or not job_id or job_id in self.jobs or self.job and self.job['running'] or mode not in c['modes'] or self.hp<=0 or provider not in self.provider_skills or self.provider_bodies[provider]==self.body or self.registry.get(provider) is not None or self.kits<c['kit_cost_on_start'] or not all((consent,physical,clinical_support,learned,compatible,provider_present)) or type(bp_after) is not int or not 0<=bp_after<=100:
            raise ValueError('actual supported and assessed distinct available provider required')
        if mode in ('replace','remove') and old_device not in self.devices:raise ValueError('actual existing device required')
        if mode in ('install','replace','framework'):
            origin=self.stock if new_device in self.stock else self.work_items if work_item_inspected and new_device in self.work_items else None
            if origin is None:raise ValueError('one inspected actual new device required')
            module=origin[new_device]
            if mode=='framework':
                if module['kind']!='framework':raise ValueError('actual one-framework module required')
            else:
                if module['kind']!='comm' or (module['requires']!=self.framework or not self.framework_normal):raise ValueError('actual supported module required')
                occupied=[k for k,d in self.devices.items() if d['slot']==module['slot']]
                if mode=='install' and occupied or mode=='replace' and occupied!=[old_device]:raise ValueError('one actual matching slot required')
        else:origin=None;module=None
        if module is not None:reserved=origin.pop(new_device)
        else:reserved=None
        self.kits-=c['kit_cost_on_start'];self.spent+=c['kit_cost_on_start'];self.jobs.add(job_id);self.registry[provider]=job_id
        if mode in ('replace','remove'):self.devices[old_device]['normal']=False
        self.bp_current=False
        self.job={'id':job_id,'mode':mode,'provider':provider,'old':old_device,'new':new_device,'reserved':reserved,'bp_after':bp_after,'seconds':0,'running':True}
    def progress(self,seconds):
        if self.held or not self.job or not self.job['running'] or self.hp<=0 or type(seconds) is not int or seconds<0 or self.registry.get(self.job['provider'])!=self.job['id']:
            raise ValueError('actual available assigned procedure time required')
        self.job['seconds']=min(p['clinical_service']['work_seconds'],self.job['seconds']+seconds)
    def handover(self,provider,consent=True,support=True):
        if self.held or not self.job or not self.job['running'] or provider not in self.provider_skills or self.registry.get(provider) is not None or not consent or not support or self.provider_bodies[provider]==self.body:
            raise ValueError('actual qualified available handover required')
        self.registry[self.job['provider']]=None;self.registry[provider]=self.job['id'];self.job['provider']=provider
    def finish(self,safe=True,roll=None):
        if self.held or not self.job or not self.job['running'] or self.hp<=0 or self.job['seconds']<p['clinical_service']['work_seconds'] or self.registry.get(self.job['provider'])!=self.job['id']:
            raise ValueError('actual completed supported procedure required')
        if not safe and (type(roll) is not int or not 1<=roll<=100):raise ValueError('one common completion roll required')
        j=self.job;success=safe or grade(self.provider_skills[j['provider']],roll)>0
        j['running']=False;self.registry[j['provider']]=None
        if not success:
            self.hp=max(0,self.hp-p['clinical_service']['failed_uncertain_procedure_direct_HP_damage'])
            if j['reserved'] is not None:self.work_items[j['new']]=j['reserved']
            if j['mode']=='framework':self.framework_normal=False
            return False
        if j['mode'] in ('replace','remove'):self.removed[j['old']]=self.devices.pop(j['old'])
        if j['mode'] in ('install','replace'):
            self.devices[j['new']]={'slot':j['reserved']['slot'],'requires':j['reserved']['requires'],'normal':True}
        if j['mode']=='framework':
            self.removed[self.framework_device]={'kind':'framework','framework':self.framework}
            self.framework=j['reserved']['framework'];self.framework_device=j['new'];self.framework_normal=True
        self.bp=j['bp_after'];self.bp_current=True
        if self.bp<100:self.ddogg=False
        return True
    def available(self,device):
        if self.hp<=0 or self.job and self.job['running'] or device not in self.devices:return False
        d=self.devices[device];return d['normal'] and self.framework_normal and d['requires']==self.framework
    def ooc_wait(self,seconds):
        if type(seconds) is not int or seconds<0:raise ValueError('nonnegative OOC wait required')

def run():
    checks=[]
    def check(name,a,b):assert a==b,(name,a,b);checks.append(name)
    c,r=p['comm'],p['repair']
    check('common engine/action',(p['engine'],p['unified_action_term']),('P-FEWK-0.2','인터랙션'))
    check('shared repair target',(r['skill'],r['target']),('공학',50))
    check('one existing main action',(c['main_actions'],c['seconds']),(1,5))
    check('one actual part/time',(r['part_cost_on_start'],r['work_seconds']),(1,300))
    check('common skill success count',sum(grade(50,i)>0 for i in range(1,101)),50)
    check('common conditions',tuple(target(50,x) for x in (-20,0,20)),(30,50,70))
    check('no new person stats/creation tracks',(p['new_universal_stats'],p['creation_origin_tracks']),([],False))
    check('no forced reply/realm network',(c['reply_forced'],c['cross_dimension_network_default']),(False,False))
    cases=0
    for active,working,ext,approved,net,account,contact in product(('B-C0','B-C1'),*( (False,True),)*6):
        actual=can_submit(active,'B-C0',working,ext,approved,net,account,contact)
        # independent terminal eligibility list; account/route/contact are separately required.
        eligible=[]
        if working:eligible.append('B-C0')
        if ext and approved:eligible.extend(['B-C0','B-C1'])
        expected=active in eligible and net and account and contact
        assert actual==expected
        cases+=1
    check('finite body/network cases',cases,128)
    check('stored implant is not local terminal',can_submit('B-C1','B-C0',True,False,False,True,True,True),False)
    check('approved external local terminal',can_submit('B-C1','B-C0',False,True,True,True,True,True),True)
    person={'contacts':['P-C2'],'공학':50};bodies={'B-C0':{'normal':False},'B-C1':{'normal':True}}
    original=deepcopy((person,bodies))
    for active in ('B-C0','B-C1','B-C0'):
        can_submit(active,'B-C0',bodies['B-C0']['normal'],active=='B-C1',True,True,True,bool(person['contacts']))
    check('travel does not heal/copy or lose learned contacts',(person,bodies),original)
    def state():return {'normal':False,'running':False,'elapsed':0,'spares':2,'spent':0,'HP':5,'BP':80,'Ego':6,'account':False}
    s=state();preserved={k:s[k] for k in ['HP','BP','Ego','account']}
    check('start consumes once',start(s),True)
    check('part consumption',(s['spares'],s['spent']),(1,1))
    check('concurrent same job rejected',start(s),False)
    check('120sec is unfinished',advance(s,120),'pending')
    check('interrupted job retains state',(s['elapsed'],s['normal'],s['spent']),(120,False,1))
    check('resume 180sec completes',advance(s,180),'complete')
    check('no second part at resume',(s['elapsed'],s['normal'],s['spent'],s['spares']),(300,True,1,1))
    check('function repair not HP/BP/Ego/account', {k:s[k] for k in preserved},preserved)
    check('already normal no new job',start(s),False)
    # Actual elapsed boundary arithmetic is independently checked over split times.
    time_cases=0
    for a,b in product((0,5,120,299),(0,1,5,180,300)):
        s=state();start(s);out=advance(s,a);assert out=='pending';out=advance(s,b)
        assert s['normal']==(a+b>=300) and s['spent']==1 and s['elapsed']==min(300,a+b)
        assert s['normal']==(out=='complete')
        time_cases+=1
    check('split-time cases',time_cases,20)
    rejected_cases=0
    for consent,access,tools,compatible in product((False,True),repeat=4):
        s=state();old=deepcopy(s);ok=start(s,consent,access,tools,compatible)
        if not ok:assert s==old;rejected_cases+=1
        else:assert all((consent,access,tools,compatible))
    check('no start no consumption combinations',rejected_cases,15)
    s=state();start(s);check('unsafe common failure',advance(s,300,False,51),'failed')
    check('failure spends part',(s['normal'],s['spent'],s['spares']),(False,1,1))
    check('new attempt needs next part',start(s),True)
    check('new successful completion',advance(s,300,False,50),'complete')
    check('two attempts two actual parts',(s['spent'],s['spares']),(2,0))
    s=state();s['spares']=0;old=deepcopy(s);check('no part cannot start',start(s),False);check('rejection preserves',s,old)
    check('not complete medicine/participant',(p['all_implants_and_medicine_complete'],p['actual_participant_playtest']),(False,False))
    def reject(name,obj,fn):
        before=deepcopy(obj.__dict__)
        try:fn()
        except ValueError:pass
        else:raise AssertionError(name+' accepted')
        check(name+' preserves state',obj.__dict__,before)
    clinic=ClinicalService();clinic.devices['COMM-01']['normal']=False;preserved=(clinic.hp,clinic.other_body_HP,clinic.ego,deepcopy(clinic.learned),clinic.account)
    clinic.start('J','replace');clinic.progress(7200)
    check('replacement device reserved and one kit',(clinic.kits,clinic.spent,'COMM-C2' in clinic.stock,clinic.available('COMM-01')),(1,1,False,False))
    snapshot=deepcopy(clinic.__dict__);clinic.ooc_wait(604800);check('OOC no clinical progress',clinic.__dict__,snapshot)
    clinic.held=True;reject('held procedure cannot progress',clinic,lambda:clinic.progress(14400));clinic.held=False
    reject('incomplete procedure cannot finish',clinic,lambda:clinic.finish())
    clinic.progress(14400);clinic.finish()
    check('safe replace and detached old device',(clinic.available('COMM-C2'),list(clinic.removed),clinic.spent,clinic.job['seconds']),(True,['COMM-01'],1,21600))
    check('installation not HP ego learned or account healing',(clinic.hp,clinic.other_body_HP,clinic.ego,clinic.learned,clinic.account),preserved)
    reject('same completed operation cannot finish again',clinic,lambda:clinic.finish())
    reject('same job identity cannot start new procedure',clinic,lambda:clinic.start('J','remove',old_device='COMM-C2'))
    clinic=ClinicalService();clinic.start('FW','framework',new_device='FW-WORK-C1');clinic.progress(21600);clinic.finish()
    check('one new framework and old hardware stored',(clinic.framework,clinic.framework_device,list(clinic.removed)),('F-WORK','FW-WORK-C1',['FW-COM-C1']))
    check('old function unsupported hardware remains',(clinic.available('COMM-01'),clinic.available('CALC-C1'),'COMM-01' in clinic.devices),(False,True,True))
    reject('incompatible comm install under new framework',clinic,lambda:clinic.start('BAD','replace'))
    clinic=ClinicalService();clinic.start('FW-FAIL','framework',new_device='FW-WORK-C1');clinic.progress(21600);clinic.finish(False,51)
    check('failed base not damaged peripheral device',(clinic.framework_normal,clinic.devices['COMM-01']['normal'],clinic.available('COMM-01')),(False,True,False))
    reject('failed base not supported normal comm install',clinic,lambda:clinic.start('COMM-RETRY','replace'))
    clinic.stock['FW-COM-C2']={'kind':'framework','framework':'F-COM'};clinic.start('FW-REPAIR','framework',new_device='FW-COM-C2');clinic.progress(21600);clinic.finish()
    check('actual base replacement restores supported normal peripheral',(clinic.framework_normal,clinic.devices['COMM-01']['normal'],clinic.available('COMM-01')),(True,True,True))
    clinic=ClinicalService();clinic.start('REMOVE','remove');clinic.progress(21600);clinic.finish()
    check('removal no phantom original organ or device',(clinic.available('COMM-01'),'COMM-01' in clinic.devices,'COMM-01' in clinic.removed,clinic.hp),(False,False,True,9))
    clinic=ClinicalService();del clinic.devices['COMM-01'];clinic.start('INSTALL','install');clinic.progress(21600);clinic.finish()
    check('one actual installation with new identity',(clinic.available('COMM-C2'),list(clinic.removed),clinic.spent),(True,[],1))
    clinic=ClinicalService();clinic.start('RISK','replace');clinic.progress(21600);clinic.finish(False,51)
    check('failed procedure target and reserved work item',(clinic.hp,clinic.other_body_HP,clinic.ego,clinic.available('COMM-01'),list(clinic.work_items),clinic.kits,clinic.bp_current),(7,12,6,False,['COMM-C2'],1,False))
    reject('failed new device cannot blindly reuse',clinic,lambda:clinic.start('RETRY','replace'))
    clinic.start('RETRY','replace',work_item_inspected=True);clinic.progress(21600);clinic.finish(False,50)
    check('inspected same work item new kit and actual new attempt',(clinic.available('COMM-C2'),clinic.hp,clinic.spent,clinic.kits,len(clinic.work_items)),(True,7,2,0,0))
    clinic=ClinicalService();clinic.start('HAND','replace');clinic.progress(7200);clinic.handover('DOC-C2');clinic.progress(14400);clinic.finish(False,60)
    check('current completing provider skill determines outcome',(clinic.available('COMM-C2'),clinic.provider_skills['DOC-C2'],clinic.registry),(True,70,{'DOC-C1':None,'DOC-C2':None}))
    registry={'DOC-C1':None,'DOC-C2':None};first=ClinicalService(registry);second=ClinicalService(registry)
    first.start('FIRST','replace');reject('same provider cannot run simultaneous second job',second,lambda:second.start('SECOND','replace'))
    second.start('SECOND','replace',provider='DOC-C2');reject('busy provider cannot receive handover',first,lambda:first.handover('DOC-C2'))
    clinic=ClinicalService();clinic.provider_bodies['DOC-C1']=clinic.body;reject('operated body not own working surgeon',clinic,lambda:clinic.start('SELF','replace'))
    clinic=ClinicalService();clinic.hp=0;reject('zero HP patient needs stabilization first',clinic,lambda:clinic.start('ZERO','replace'))
    clinical_condition_cases=0
    fields=('consent','physical','clinical_support','learned','compatible','provider_present')
    for flags in product((False,True),repeat=6):
        x=ClinicalService();before=deepcopy(x.__dict__)
        try:x.start('J','replace',**dict(zip(fields,flags)));got=True
        except ValueError:got=False
        assert got==all(flags)
        if not got:assert x.__dict__==before
        else:assert x.spent==1 and 'COMM-C2' not in x.stock
        clinical_condition_cases+=1
    check('clinical physical consent support qualification conditions',clinical_condition_cases,64)
    clinical_completion_cases=0
    for mode,elapsed,roll in product(('install','replace','remove','framework'),(0,7200,21599,21600),range(1,101)):
        x=ClinicalService()
        if mode=='install':del x.devices['COMM-01']
        x.start('J',mode,new_device='FW-WORK-C1' if mode=='framework' else 'COMM-C2');x.progress(elapsed);before=deepcopy(x.__dict__)
        if elapsed<21600:
            try:x.finish(False,roll)
            except ValueError:pass
            else:raise AssertionError('early clinical completion')
            assert x.__dict__==before
        else:
            success=x.finish(False,roll);assert success==(roll<=50)
            assert x.hp==(9 if success else 7) and x.spent==1 and x.other_body_HP==12 and x.ego==6
            if mode in ('install','replace'):assert x.available('COMM-C2')==success
            if mode=='remove':assert ('COMM-01' in x.removed)==success
            if mode=='framework':assert (x.framework=='F-WORK')==success
        clinical_completion_cases+=1
    check('four lifecycle modes actual time all percentile results',clinical_completion_cases,1600)
    assessment_cases=0
    for after in (0,1,50,80,99,100):
        x=ClinicalService();del x.devices['COMM-01'];x.bp=100;x.ddogg=True;x.start('J','install',bp_after=after);x.progress(21600);x.finish()
        assert x.bp==after and x.bp_current and x.ddogg==(after==100) and x.hp==9 and x.ego==6;assessment_cases+=1
    check('prepared assessment not item-count formula',assessment_cases,6)
    x=ClinicalService();x.bp=100;x.ddogg=False;del x.devices['COMM-01'];x.start('J','install',bp_after=100);x.progress(21600);x.finish();check('BP100 does not resurrect vanished DDOGG',x.ddogg,False)
    for value in (-1,101,True,None):
        x=ClinicalService();reject('invalid prepared BP '+str(value),x,lambda:x.start('J','replace',bp_after=value))
    x=ClinicalService();x.start('J','replace');x.progress(21600);reject('invalid completion roll no partial clinical result',x,lambda:x.finish(False,101))
    files=[here.parent/'10_CoreRulebook.md',here.parent/'12_룰시트와캐릭터시트.md',here/'임플란트_프로필.json',here/'백분율_코어검증.py',Path(__file__)]
    return {'date':'2026-10-06','profile':p['id'],'scope':'IMPLANT-SERVICE-C1의 지정 보조장치 설치/교체/제거·단일기반 변경/중단/작업물/현담당자·몸손상과 기존 두 NEW 규격의 몸 귀속/망 조건·기존 공통 판정·작업 시간/부품 보존을 제한된 모형으로 검산한다. 전체 이식/의료·부작용·실제 기능/참가자 검증 아님.','checks_passed':len(checks),'checks':checks,'clinical_condition_cases':clinical_condition_cases,'clinical_completion_cases':clinical_completion_cases,'body_assessment_cases':assessment_cases,'body_network_cases':cases,'split_time_cases':time_cases,'rejected_start_cases':rejected_cases,'artifacts_sha256':{str(f.relative_to(here.parent)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'all_implants_and_medicine_complete':False,'actual_participant_playtest':False}
if __name__=='__main__':
    result=run();Path(__file__).with_name('임플란트_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['profile','checks_passed','body_network_cases','split_time_cases','actual_participant_playtest']},ensure_ascii=False))
