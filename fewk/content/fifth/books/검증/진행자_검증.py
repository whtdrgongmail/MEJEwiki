from pathlib import Path
from dataclasses import dataclass,field
from copy import deepcopy
from itertools import product
import hashlib,json
from 백분율_코어검증 import grade
from 일반플레이_검증 import Body
from 팀지원_검증 import Sender
here=Path(__file__).resolve().parent
p=json.loads((here/'진행자_장면프로필.json').read_text())

@dataclass
class Followup:
    elapsed:int=0
    confirmed:bool=False
    at_desk:bool=True
    held:bool=False
    events:set=field(default_factory=set)
    sent:dict=field(default_factory=dict)
    sender:Sender=field(default_factory=lambda:Sender(active='B-G1',installed='B-G1',facts={'CAM-01'}))
    def advance(self,event_id,seconds):
        if self.held or event_id in self.events or type(seconds) is not int or seconds<0:
            raise ValueError('one actual nonnegative IC interval while active')
        self.elapsed+=seconds;self.events.add(event_id)
    def ooc_wait(self,seconds):
        if seconds<0:raise ValueError('negative wait')
    def session_boundary(self):pass
    def ready(self):
        s=self.sender
        return bool(not self.confirmed and not self.held and self.elapsed>=p['followup']['deadline_IC_seconds'] and self.at_desk and s.active==s.installed and s.installed_ok and s.network and s.account and s.contact and s.body.hp>0 and not s.body.destroyed and s.body.main>=1 and 'CAM-01' in s.facts and not self.sent)
    def dispatch(self,event_id):
        if event_id in self.sent or not self.ready():raise ValueError('actual followup conditions required')
        candidate=deepcopy(self.sender);candidate.seconds=self.elapsed
        message=candidate.send(event_id,'CAM-01')
        message.update(effect='request_confirmation_only',known_fields=['local_appearance','box_id'])
        self.sender=candidate;self.elapsed=message['seconds'];self.sent[event_id]=message
        return deepcopy(message)

@dataclass
class Case:
    holder_has_receipt:bool=True
    authorized_receiver:bool=True
    issuer_route:bool=True
    knows:set=field(default_factory=lambda:{'CAM-01'})
    operations_seen:set=field(default_factory=set)
    history:list=field(default_factory=list)
    suspected:bool=True
    def obtain_receipt(self):
        if not self.holder_has_receipt or not self.authorized_receiver:raise ValueError('actual receipt and permission required')
        self.knows.add('RECEIPT-01');self.history.append('approved_workshop_receipt')
    def contact_issuer(self):
        if not self.issuer_route:raise ValueError('actual issuer route required')
        self.knows.add('ISSUER-CONFIRM-01');self.history.append('actual_contact_with_issuer')
    def optional_terminal(self,t,r):
        ok=grade(t,r)>0
        if ok:self.knows.add('EXTRA-01')
        self.history.append(('locked_extra_terminal',ok))
        return ok
    def view_operations(self,note):self.operations_seen.add(note)
    def verify(self):
        allowed=set(p['clue_paths']['permission_evidence'])
        if not allowed & self.knows:raise ValueError('obtained valid permission evidence required')
        self.suspected=False;self.history.append('permission_confirmed')

def run():
    checks=[]
    def check(name,a,b):assert a==b,(name,a,b);checks.append(name)
    def reject(name,obj,fn):
        original=deepcopy(obj)
        try:fn()
        except ValueError:pass
        else:raise AssertionError(name)
        check(name+' preserves current state',obj,original)
    check('same common engine',p['engine'],'P-FEWK-0.2')
    check('message uses existing main action and5sec',(p['followup']['main_actions'],p['followup']['message_seconds']),(1,5))
    f=Followup();f.advance('TIME-01',120)
    check('actual120sec before deadline',(f.elapsed,f.ready()),(120,False))
    old=deepcopy(f);f.held=True;hold=deepcopy(f);f.ooc_wait(2*86400);f.session_boundary()
    check('OOC wait and session ending preserve held state',f,hold)
    reject('held scene does not advance IC work',f,lambda:f.advance('FAKE-WAIT',180))
    f.held=False;check('resume preserves actual elapsed',f.elapsed,old.elapsed)
    f.advance('TIME-02',180);check('actual300sec eligibility',(f.elapsed,f.ready()),(300,True))
    reject('same actual time not applied twice',f,lambda:f.advance('TIME-02',180))
    reject('negative IC duration',f,lambda:f.advance('NEG',-1))
    reject('nonintegral malformed duration',f,lambda:f.advance('STR','180'))
    before_body=deepcopy(f.sender.body);m=f.dispatch('FOLLOWUP-01')
    check('real confirmation sends one message',(f.elapsed,f.sender.body.main,m['effect']),(305,0,'request_confirmation_only'))
    check('message contains acquired local fields',m['known_fields'],['local_appearance','box_id'])
    check('message does not damage/charge/heal body',(f.sender.body.hp,f.sender.body.charges,f.sender.body.ammo),(before_body.hp,before_body.charges,before_body.ammo))
    reject('same followup cannot send twice',f,lambda:f.dispatch('FOLLOWUP-01'))
    f.confirmed=True;check('late permission does not erase transmitted request','FOLLOWUP-01' in f.sent,True)
    f=Followup(elapsed=300,confirmed=True);reject('confirmation closes pending followup',f,lambda:f.dispatch('CLOSED'))
    f=Followup(elapsed=300,at_desk=False);reject('sender actually absent',f,lambda:f.dispatch('ABSENT'))
    f=Followup(elapsed=300);f.sender.active='OTHER-BODY';reject('stored original terminal is not local',f,lambda:f.dispatch('STORED'))
    f=Followup(elapsed=300);f.sender.body.hp=0;reject('incapacitated clerk cannot send',f,lambda:f.dispatch('DOWN'))
    f=Followup(elapsed=300);f.sender.body.main=0;reject('used action cannot send',f,lambda:f.dispatch('NO-ACTION'))
    f=Followup(elapsed=300);f.sender.facts=set();reject('unknown source cannot be sent',f,lambda:f.dispatch('NO-SOURCE'))
    combinations=0
    for seconds,desk,terminal,network,account,contact in product((0,5,299,300,301),*((False,True),)*5):
        f=Followup(elapsed=seconds,at_desk=desk);f.sender.installed_ok=terminal;f.sender.network=network;f.sender.account=account;f.sender.contact=contact
        expected=seconds>=300 and all((desk,terminal,network,account,contact))
        before=deepcopy(f)
        try:f.dispatch('CHECK');actual=True
        except ValueError:actual=False
        assert actual==expected
        if actual:assert f.elapsed==seconds+5 and f.sender.body.main==0
        else:assert f==before
        combinations+=1
    check('finite time/location/terminal/route combinations',combinations,160)
    split_cases=0
    for a,b in product((0,5,120,299),(0,1,5,180,300)):
        f=Followup();f.advance('A',a);f.ooc_wait(86400);f.advance('B',b)
        assert f.elapsed==a+b and f.ready()==(a+b>=300)
        split_cases+=1
    check('finite actual split-time boundaries',split_cases,20)
    c=Case();c.obtain_receipt();c.verify()
    check('approved base receipt path needs no compulsory roll',(c.suspected,c.knows),(False,{'CAM-01','RECEIPT-01'}))
    c=Case();c.contact_issuer();c.verify();check('alternative issuer path remains usable',c.suspected,False)
    c=Case();check('optional terminal genuinely fails',c.optional_terminal(50,62),False)
    c.obtain_receipt();c.verify();check('optional failure does not lock baseline goal',c.suspected,False)
    check('failed access kept in actual history',('locked_extra_terminal',False) in c.history,True)
    c=Case();c.optional_terminal(50,20)
    reject('extra information is not forged permission',c,c.verify)
    c=Case();c.view_operations('planned_reveal_in_session20');reject('operating memo is not PC permission proof',c,c.verify)
    c.obtain_receipt();c.verify();check('earlier legitimate acquisition retained',c.suspected,False)
    check('video remains after permission correction','CAM-01' in c.knows,True)
    check('no physical identity or other realm location inference',all(x not in c.knows for x in ('physical_identity','other_dimension_location')),True)
    missing_cases=0
    for exists,approved in product((False,True),repeat=2):
        c=Case(holder_has_receipt=exists,authorized_receiver=approved)
        if exists and approved:c.obtain_receipt();assert 'RECEIPT-01' in c.knows
        else:
            before=deepcopy(c)
            try:c.obtain_receipt()
            except ValueError:pass
            else:raise AssertionError('absent or unapproved receipt')
            assert c==before
        missing_cases+=1
    check('actual receipt prerequisite cases',missing_cases,4)
    check('five-stage3h sum',sum((30,60,30,45,15)),180)
    check('legacy printed product error',180*50000*40,360000000)
    check('d10 five raw roll axes',10**5,100000)
    check('distinct category count different from roll weight',10*10*10*4*6,24000)
    check('faction count bounds',(5*1,10*3),(5,30))
    check('example average tier',sum((2,3,2,2))/4,2.25)
    check('no new universal stats',p['new_universal_stats'],[])
    check('human and balance remain unverified',(p['actual_participant_playtest'],p['actual_async_community_test'],p['full_encounter_balance_verified']),(False,False,False))
    files=[here.parent/'10_CoreRulebook.md',here.parent/'12_룰시트와캐릭터시트.md',here/'진행자_장면프로필.json',here/'팀지원_검증.py',here/'팀지원_프로필.json',here/'임플란트_검증.py',here/'임플란트_프로필.json',here/'일반플레이_검증.py',here/'입문_프로필.json',here/'백분율_코어검증.py',Path(__file__)]
    ledger=json.loads((here/'제5판_이관검수.json').read_text());root=here.parent.parent
    sources=[root/ledger['files'][i]['source'] for i in (76,77,78,80,81,82,83,84,85,86,87,88,89,90)]
    for i,q in zip((76,77,78,80,81,82,83,84,85,86,87,88,89,90),sources):assert hashlib.sha256(q.read_bytes()).hexdigest()==ledger['files'][i]['observed_sha256']
    return {'date':'2026-10-05','profile':p['id'],'scope':'NEW 공방 사례의 실제IC시간·멈춤/중복·송신 몸/망/행동·정상단서 두 경로와 선택추가접근실패·숨은정보/운영메모 구분과 구판 일부 산술 대조. 모든GM준비/정보분류·사람의지식/관계/안전운영·전투균형/플랫폼·실제참가자 검증 아님.','checks_passed':len(checks),'checks':checks,'followup_condition_cases':combinations,'split_IC_time_cases':split_cases,'receipt_condition_cases':missing_cases,'all_GM_online_and_information_topics_verified':False,'full_encounter_balance_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False,'artifacts_sha256':{str(q.relative_to(here.parent)):hashlib.sha256(q.read_bytes()).hexdigest() for q in files},'source_sha256':{str(q.relative_to(root)):hashlib.sha256(q.read_bytes()).hexdigest() for q in sources}}
if __name__=='__main__':
    r=run();Path(__file__).with_name('진행자_검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('profile','checks_passed','followup_condition_cases','split_IC_time_cases','receipt_condition_cases','actual_participant_playtest')},ensure_ascii=False))
