from pathlib import Path
from dataclasses import dataclass,field
from copy import deepcopy
from itertools import product
import json,hashlib
from 백분율_코어검증 import target,grade
from 일반플레이_검증 import Body,new_round
from 임플란트_검증 import can_submit
here=Path(__file__).resolve().parent
p=json.loads((here/'팀지원_프로필.json').read_text())

@dataclass
class Sender:
    body:Body=field(default_factory=Body)
    active:str='B-T2'
    installed:str='B-T2'
    installed_ok:bool=True
    external:bool=False
    approved:bool=False
    network:bool=True
    account:bool=True
    contact:bool=True
    facts:set=field(default_factory=lambda:{'MANUAL-T1'})
    sent:set=field(default_factory=set)
    seconds:int=0
    def send(self,event_id,source):
        eligible=can_submit(self.active,self.installed,self.installed_ok,self.external,self.approved,self.network,self.account,self.contact)
        if not eligible or source not in self.facts or self.body.hp<=0 or self.body.destroyed or self.body.main<1 or event_id in self.sent:
            raise ValueError('actual sender, known information, route and main action required')
        self.body.main-=1;self.seconds+=5;self.sent.add(event_id)
        return {'source':source,'seconds':self.seconds}

def prepared_for_attempt(base,has_terminal,access,delivered_before,adverse=False):
    if not has_terminal or not access:raise ValueError('receiver prerequisites absent')
    favourable=bool(delivered_before)
    situation=0 if favourable==adverse else (20 if favourable else -20)
    return target(base,situation)

@dataclass
class Receiver:
    body:Body=field(default_factory=Body)
    messages:list=field(default_factory=list)
    history:dict=field(default_factory=dict)
    seconds:int=0
    def receive(self,message,at):
        if at<message['seconds']:raise ValueError('not received before actual transmission')
        self.messages.append(dict(message,received_at=at))
    def act(self,event_id,roll,at):
        if event_id in self.history or self.body.main<1 or at<self.seconds:
            raise ValueError('new available action at current IC time required')
        before=[m for m in self.messages if m['received_at']<=at]
        t=prepared_for_attempt(50,True,True,before)
        self.body.main-=1;self.seconds=at+5
        result={'target':t,'roll':roll,'success':grade(t,roll)>0,'spent_action':1,'elapsed':5,'start_at':at}
        self.history[event_id]=result
        return deepcopy(result)

@dataclass
class Learner:
    skills:dict=field(default_factory=lambda:{'해킹':50,'생활':30})
    credited:set=field(default_factory=set)
    HP:int=5
    ammo:int=3
    Ego:int=6
    realm_bans:tuple=('C-OLD',)
    def grow(self,unit,skill,evidence):
        if not unit or unit in self.credited or not evidence or skill not in self.skills or self.skills[skill]>=95:
            raise ValueError('one actual learned skill per story unit')
        self.skills[skill]=min(95,self.skills[skill]+5);self.credited.add(unit)
    def prepared_in_body(self,skill,body_bonus=0):return self.skills[skill]+body_bonus

def run():
    checks=[]
    def check(name,a,b):assert a==b,(name,a,b);checks.append(name)
    def reject(name,obj,fn):
        before=deepcopy(obj.__dict__)
        try:fn()
        except ValueError:pass
        else:raise AssertionError(name)
        check(name+' no partial change',obj.__dict__,before)
    check('common engine',p['engine'],'P-FEWK-0.2')
    check('same shared skill/target',(p['remote_example']['shared_skill'],p['remote_example']['base_target']),('해킹',50))
    check('same BODY-COMM action/time',(p['remote_example']['message_main_actions'],p['remote_example']['message_seconds']),(1,5))
    sender=Sender();message=sender.send('SEND-01','MANUAL-T1')
    check('real sender spends main once',(sender.body.main,sender.seconds),(0,5))
    check('message references actual source',message['source'],'MANUAL-T1')
    reject('duplicate event',sender,lambda:sender.send('SEND-01','MANUAL-T1'))
    reject('second message same action budget',sender,lambda:sender.send('SEND-02','MANUAL-T1'))
    t=prepared_for_attempt(50,True,True,[message])
    check('actual help target',t,70)
    check('r62 succeeds with delivered help',grade(t,62)>0,True)
    check('r62 fails without help',grade(prepared_for_attempt(50,True,True,[]),62)>0,False)
    receiver=Receiver();first_result=receiver.act('TRY-01',62,0)
    original=deepcopy(receiver.history)
    receiver.receive(message,5)
    check('late assistance preserves prior failure',receiver.history,original)
    check('prior failure actually used no help',(first_result['target'],first_result['success']),(50,False))
    reject('new attempt requires new main action',receiver,lambda:receiver.act('TRY-02',62,5))
    new_round(receiver.body);second=receiver.act('TRY-02',62,5)
    check('new action uses new time and received help',(second['target'],second['success'],receiver.seconds,receiver.body.main),(70,True,10,0))
    check('new action does not alter previous result',receiver.history['TRY-01'],first_result)
    check('duplicate helpers never stack',prepared_for_attempt(50,True,True,[message]*5),70)
    check('favourable and adverse cancel',prepared_for_attempt(50,True,True,[message],True),50)
    check('adverse alone uses shared target',prepared_for_attempt(50,True,True,[],True),30)
    for terminal,access in [(False,False),(False,True),(True,False)]:
        try:prepared_for_attempt(99,terminal,access,[message]*10)
        except ValueError:pass
        else:raise AssertionError('help fabricated receiver condition')
    check('receiver feasibility before target',True,True)
    sender=Sender(facts=set());reject('unknown information cannot be sent',sender,lambda:sender.send('UNKNOWN','MANUAL-T1'))
    sender=Sender(active='B-T3');reject('stored original terminal not local',sender,lambda:sender.send('NO-LOCAL','MANUAL-T1'))
    sender=Sender(active='B-T3',external=True,approved=True)
    check('actual approved local substitute terminal',sender.send('LOCAL','MANUAL-T1')['source'],'MANUAL-T1')
    sender=Sender(network=False);reject('cross dimension route not automatic',sender,lambda:sender.send('NO-NET','MANUAL-T1'))
    sender=Sender(body=Body(hp=0));reject('incapacitated sender',sender,lambda:sender.send('DOWN','MANUAL-T1'))
    cases=0
    # Eligibility is independently enumerated as a list of actual usable terminals.
    for active,working,external,approved,net,account,contact,known in product(('B-T2','B-T3'),*((False,True),)*7):
        usable=[]
        if working:usable.append('B-T2')
        if external and approved:usable+=['B-T2','B-T3']
        expected=active in usable and net and account and contact and known
        sender=Sender(active=active,installed_ok=working,external=external,approved=approved,network=net,account=account,contact=contact,facts={'MANUAL-T1'} if known else set())
        before=deepcopy(sender.__dict__)
        try:sender.send('SEND','MANUAL-T1');actual=True
        except ValueError:actual=False
        assert actual==expected
        if not actual:assert sender.__dict__==before
        else:assert sender.body.main==0 and sender.seconds==5
        cases+=1
    check('finite sender body/route/source combinations',cases,256)
    target_cases=0
    for base,helpers,adverse in product((1,10,30,50,70,90,99),(0,1,2,5),(False,True)):
        actual=prepared_for_attempt(base,True,True,[message]*helpers,adverse)
        delta=20 if helpers and not adverse else -20 if adverse and not helpers else 0
        expected=max(1,min(99,base+delta))
        assert actual==expected;target_cases+=1
    check('bounded shared assistance situations',target_cases,56)
    learner=Learner();resources=(learner.HP,learner.ammo,learner.Ego,learner.realm_bans)
    learner.grow('ARC-WORKSHOP-01','해킹','승인 복구와 후속 조사')
    check('one story learned skill increment',learner.skills,{'해킹':55,'생활':30})
    reject('same story copied to another log',learner,lambda:learner.grow('ARC-WORKSHOP-01','생활','같은 이야기 요약'))
    reject('missing learning evidence',learner,lambda:learner.grow('ARC-02','해킹',''))
    reject('not-yet-learned special technique',learner,lambda:learner.grow('ARC-02','심상전이','일반 조사만 수행'))
    check('body changes use same person skill',tuple(learner.prepared_in_body('해킹',b) for b in (0,20,0)),(55,75,55))
    check('body switch does not repeat growth',learner.skills['해킹'],55)
    check('growth does not heal or remove named realm ban',(learner.HP,learner.ammo,learner.Ego,learner.realm_bans),resources)
    growth_cases=0
    for value in range(1,95):
        learner=Learner(skills={'해킹':value});learner.grow('UNIT','해킹','학습')
        assert learner.skills['해킹']==min(value+5,95);growth_cases+=1
    learner=Learner(skills={'해킹':95});reject('cap does not exceed95',learner,lambda:learner.grow('CAP','해킹','학습'))
    check('finite growth boundaries',growth_cases,94)
    check('no mandatory role/trust stats',(p['new_universal_stats'],p['mandatory_six_team_roles'],p['mandatory_contact_trust_score']),([],False,False))
    check('no flashback paradox or forced final war',(p['flashback_causes_automatic_paradox'],p['long_campaign_requires_global_war_or_retirement']),(False,False))
    check('human evidence not fabricated',(p['actual_participant_playtest'],p['actual_async_community_test']),(False,False))
    files=[here.parent/'10_CoreRulebook.md',here.parent/'12_룰시트와캐릭터시트.md',here/'팀지원_프로필.json',here/'백분율_코어검증.py',here/'일반플레이_검증.py',here/'임플란트_검증.py',here/'임플란트_프로필.json',Path(__file__)]
    return {'date':'2026-10-05','profile':p['id'],'scope':'NEW 공방 예의 실제 송신 몸/망/자료·주요 행동/5초·공통 도움1회/상황상쇄·늦은 지원/성장 중복과 자원 보존을 제한된 모형으로 검산. 모든 협력/콘택트·회상서사 판단/캠페인 균형·플랫폼/실제 참가자 검증 아님.','checks_passed':len(checks),'checks':checks,'sender_condition_cases':cases,'support_target_cases':target_cases,'growth_boundary_cases':growth_cases,'all_contacts_and_team_roles_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False,'artifacts_sha256':{str(f.relative_to(here.parent)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
if __name__=='__main__':
    r=run();Path(__file__).with_name('팀지원_검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('profile','checks_passed','sender_condition_cases','support_target_cases','growth_boundary_cases','actual_participant_playtest')},ensure_ascii=False))
