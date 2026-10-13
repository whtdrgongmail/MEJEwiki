"""One NEW facility; common attacks and a real local deadline, no participant claims."""
from pathlib import Path
from copy import deepcopy
from itertools import product
import json,hashlib
from 일반플레이_검증 import Body,attack,new_round
from 백분율_코어검증 import target,grade

here=Path(__file__).resolve().parent
profile=json.loads((here/'대형시설_프로필.json').read_text())

class Facility:
    def __init__(self,facility_id='F-L01'):
        if not isinstance(facility_id,str) or not facility_id:raise ValueError('facility identity needed')
        self.id=facility_id;self.clock=0;self.state='running';self.deadline=None;self.alarm_started_at=None;self.leak_at=None;self.deployed=True
        self.parts={name:Body(hp=data['max_hp'],armor=data['armor'],charges=0,shield_types=(),main=0,reaction=0,ammo=0,move=0) for name,data in profile['parts'].items()}

    def refresh(self):
        if self.parts['tank'].hp==0:
            if self.leak_at is None:self.leak_at=self.clock
            self.state='leaking'
        if self.state=='running':
            if self.parts['cooling_a'].hp==self.parts['cooling_b'].hp==0 and self.deadline is None:
                self.alarm_started_at=self.clock;self.deadline=self.clock+profile['overheat']['seconds_to_leak']
            if self.deadline is not None and self.clock>=self.deadline:
                self.state='leaking';self.leak_at=self.deadline

    def advance_to(self,ic_seconds):
        if type(ic_seconds) is not int or ic_seconds<self.clock:raise ValueError('actual monotonic IC time needed')
        self.refresh();self.clock=ic_seconds;self.refresh()

    def wait_ooc(self,seconds):
        if type(seconds) is not int or seconds<0:raise ValueError('OOC duration needed')
        # A posted waiting interval is not time in the shared fictional world.
        return self.snapshot()

    def hit_part(self,actor,name,weapon,active=True,**kwargs):
        if not self.deployed or not active or name not in self.parts:raise ValueError('actual deployed part and acting body needed')
        result=attack(actor,self.parts[name],weapon,**kwargs)
        self.refresh()
        return result

    def shutdown(self,actor,active=True,access=True,trained=True,manual=True,distance=1,fault=False,roll=None,skill=50,situation=0):
        if not self.deployed or self.state!='running' or self.parts['tank'].hp==0 or self.parts['console'].hp==0:
            raise ValueError('actual operable installation needed')
        if actor.hp==0 or actor.destroyed or actor.main==0 or not all((active,access,trained,manual)) or not 0<=distance<=profile['shutdown']['distance_m']:
            raise ValueError('actual local body, permission, trained procedure and manual handle needed')
        success=True
        if fault:
            if type(roll) is not int:raise ValueError('declared faulty command uses common d100')
            success=grade(target(skill,situation),roll)>0
        actor.main-=1
        self.advance_to(self.clock+profile['shutdown']['actual_work_seconds'])
        if self.state=='leaking':return 'too_late'
        if success:
            self.state='stopped';self.deadline=None
            return 'stopped'
        return 'failed'

    def snapshot(self):
        return {'id':self.id,'clock':self.clock,'state':self.state,'deadline':self.deadline,'alarm_started_at':self.alarm_started_at,'leak_at':self.leak_at,'deployed':self.deployed,'parts':{name:{'hp':body.hp,'destroyed':body.destroyed} for name,body in self.parts.items()}}

    @classmethod
    def restore(cls,data):
        required={'id','clock','state','deadline','alarm_started_at','leak_at','deployed','parts'}
        if set(data)!=required or type(data['clock']) is not int or data['clock']<0 or data['state'] not in ('running','stopped','leaking') or type(data['deployed']) is not bool or set(data['parts'])!=set(profile['parts']):
            raise ValueError('complete current facility state needed')
        for key in ('deadline','alarm_started_at','leak_at'):
            if data[key] is not None and (type(data[key]) is not int or data[key]<0):raise ValueError('invalid recorded time')
        for name,row in data['parts'].items():
            if set(row)!={'hp','destroyed'} or type(row['hp']) is not int or not 0<=row['hp']<=profile['parts'][name]['max_hp'] or type(row['destroyed']) is not bool or (row['destroyed'] and row['hp']!=0):raise ValueError('invalid current part state')
        if data['deadline'] is not None and (data['alarm_started_at'] is None or data['deadline']!=data['alarm_started_at']+60):raise ValueError('recorded first deadline changed')
        if data['state']=='running' and data['parts']['cooling_a']['hp']==data['parts']['cooling_b']['hp']==0 and (data['deadline'] is None or data['clock']>=data['deadline']):raise ValueError('expired or absent live deadline')
        if data['state']=='stopped' and data['deadline'] is not None:raise ValueError('stopped command retains live deadline')
        if data['alarm_started_at'] is not None and data['alarm_started_at']>data['clock']:raise ValueError('future alarm is not a current event')
        if data['leak_at'] is not None and data['leak_at']>data['clock']:raise ValueError('future leak is not a current event')
        if data['state']=='running' and (data['leak_at'] is not None or data['parts']['tank']['hp']==0 or (data['alarm_started_at'] is not None and data['deadline'] is None)):raise ValueError('running record lost actual damage or deadline')
        if data['state']=='leaking' and (data['leak_at'] is None or (data['parts']['tank']['hp']>0 and (data['deadline'] is None or data['clock']<data['deadline'] or data['leak_at']!=data['deadline']))):raise ValueError('leak record needs its actual breach or deadline')
        if data['state']=='stopped' and (data['parts']['tank']['hp']==0 or data['leak_at'] is not None):raise ValueError('stop does not undo leak')
        f=cls(data['id'])
        for key in required-{'id','parts'}:setattr(f,key,data[key])
        for name,row in data['parts'].items():f.parts[name].hp=row['hp'];f.parts[name].destroyed=row['destroyed']
        f.refresh()
        if f.snapshot()!=data:raise ValueError('contradictory stored state')
        return f

def overheated(now=0):
    f=Facility();f.parts['cooling_a'].hp=f.parts['cooling_b'].hp=0;f.refresh();f.advance_to(now);return f

def run():
    checks=[]
    def check(name,got,want):
        assert got==want,(name,got,want);checks.append(name)
    def rejects(name,f,actor,fn):
        before=(f.snapshot(),deepcopy(actor))
        try:fn()
        except ValueError:check(name,(f.snapshot(),actor),before)
        else:raise AssertionError('accepted '+name)
    f=Facility();actor=Body();operator=Body(hp=9)
    check('same engine and unified term',(profile['engine'],profile['unified_action_term']),('P-FEWK-0.2','인터랙션'))
    check('four actual parts with independent fixed armor',[(name,b.hp,b.armor,b.charges) for name,b in f.parts.items()],[('tank',12,1,0),('console',6,0,0),('cooling_a',8,0,0),('cooling_b',8,0,0)])
    check('no extra total hull or automatic body damage',(profile['parts_sum_is_hull_HP'],profile['part_hit_automatically_damages_operators_or_base']),(False,False))
    check('existing pistol attacks one part',f.hit_part(actor,'tank','권총',roll=50,skill=50,distance=20),('damage',3))
    check('actual one shot action and unchanged operator',(actor.main,actor.ammo,f.parts['tank'].hp,operator.hp),(0,11,9,9))
    rejects('same main cannot attack another part',f,actor,lambda:f.hit_part(actor,'console','권총',roll=50,skill=50,distance=20))
    check('other parts remain intact',[(name,f.parts[name].hp) for name in ('console','cooling_a','cooling_b')],[('console',6),('cooling_a',8),('cooling_b',8)])
    f=Facility();f.parts['cooling_a'].hp=0;f.refresh();check('one cooler does not start two-cooler alarm',f.deadline,None)
    f.parts['cooling_b'].hp=0;f.refresh();check('first actual alarm fixes time',(f.alarm_started_at,f.deadline),(0,60))
    f.advance_to(50);f.refresh();check('repeated reading does not reset deadline',(f.clock,f.deadline),(50,60))
    before=f.snapshot();check('one week OOC waiting is not IC advancement',f.wait_ooc(604800),before)
    restored=Facility.restore(json.loads(json.dumps(before)));check('JSON current state retains exact first alarm and damaged parts',restored.snapshot(),before)
    bad=deepcopy(before);bad['deadline']=110
    try:Facility.restore(bad)
    except ValueError:check('restore rejects silently extended alarm',True,True)
    else:raise AssertionError('extended alarm accepted')
    for label,change in [('missing first deadline',{'deadline':None}),('future alarm',{'alarm_started_at':70,'deadline':130}),('false leak without cause',{'state':'leaking','leak_at':40}),('leak without time',{'state':'leaking','leak_at':None}),('live state invents prior leak',{'leak_at':40}),('expired live state',{'clock':60}),('damaged part over maximum',{'parts':dict(before['parts'],tank={'hp':13,'destroyed':False})})]:
        bad=deepcopy(before);bad.update(change)
        try:Facility.restore(bad)
        except ValueError:check('current state rejects '+label,True,True)
        else:raise AssertionError('invalid state accepted '+label)
    f=overheated(50);actor=Body(hp=9,ammo=7)
    check('safe manual command does not require dice',f.shutdown(actor), 'stopped')
    check('actual work stops at55 but preserves damage and resources',(f.clock,f.deadline,f.parts['cooling_a'].hp,f.parts['cooling_b'].hp,actor.hp,actor.ammo,actor.main),(55,None,0,0,9,7,0))
    f.advance_to(120);check('stopped flow does not resume alarm automatically',(f.state,f.clock,f.parts['tank'].hp),('stopped',120,12))
    f=overheated(50);actor=Body();check('fault uses same50plus20/r62',f.shutdown(actor,fault=True,roll=62,skill=50,situation=20),'stopped')
    f=overheated(50);actor=Body();check('fault r71 failure costs action and five real seconds',f.shutdown(actor,fault=True,roll=71,skill=50,situation=20),'failed')
    check('failed command retains original live deadline',(f.clock,f.deadline,actor.main),(55,60,0))
    f=overheated(55);actor=Body();check('completion at deadline is too late',f.shutdown(actor),'too_late')
    check('deadline leak has exact time and no invented body harm',(f.clock,f.state,f.leak_at,actor.main,actor.hp),(60,'leaking',60,0,12))
    new_round(actor);rejects('new turn does not cure leaked material',f,actor,lambda:f.shutdown(actor))
    f=Facility();actor=Body();f.parts['console'].hp=0;rejects('broken handle cannot be replaced by high skill',f,actor,lambda:f.shutdown(actor,fault=True,skill=95,roll=1))
    f=Facility();actor=Body();f.parts['tank'].hp=0;f.refresh();check('actual tank breach is immediate leak',(f.state,f.leak_at),('leaking',0))
    f=Facility();actor=Body();rejects('inactive body cannot issue shutdown',f,actor,lambda:f.shutdown(actor,active=False))
    rejects('backwards IC time rejected without state mutation',f,actor,lambda:f.advance_to(-1))
    rejects('invalid die rejected before spending time or action',f,actor,lambda:f.shutdown(actor,fault=True,roll=101))
    f.deployed=False;rejects('stored installation is not a remote active target',f,actor,lambda:f.hit_part(actor,'tank','권총',roll=1,skill=70,distance=1))
    command_cases=0
    for active,access,trained,manual,live,main,control,tank,dist,now,roll,fault in product((False,True),(False,True),(False,True),(False,True),(False,True),(False,True),(0,6),(0,12),(0,1,1.01),(0,50,55,60),(50,51),(False,True)):
        f=overheated(now);f.parts['console'].hp=control;f.parts['tank'].hp=tank;f.refresh();actor=Body(hp=12 if live else 0,main=1 if main else 0)
        before=(f.snapshot(),deepcopy(actor));valid=all((active,access,trained,manual,live,main,control>0,tank>0,dist<=1,now<60))
        try:result=f.shutdown(actor,active=active,access=access,trained=trained,manual=manual,distance=dist,fault=fault,roll=roll)
        except ValueError:assert not valid and (f.snapshot(),actor)==before
        else:
            assert valid and actor.main==0 and actor.hp==before[1].hp and actor.ammo==before[1].ammo and f.clock==now+5
            expected='too_late' if now+5>=60 else 'failed' if fault and roll>50 else 'stopped'
            assert result==expected
            assert all(f.parts[name].hp==before[0]['parts'][name]['hp'] for name in f.parts)
        command_cases+=1
    check('local command prerequisites and exact real deadline combinations',command_cases,12288)
    attack_cases=0
    for hp,main,ammo,weapon,distance,cover,roll,name in product((0,12),(0,1),(0,1,12),('권총','동력 근접 도구'),(1,2,30,31,60,61),('none','partial','full'),(30,31,50,51),profile['parts']):
        f=Facility();actor=Body(hp=hp,main=main,ammo=ammo);before=(f.snapshot(),deepcopy(actor));melee=weapon=='동력 근접 도구';valid=hp>0 and main>0 and cover!='full' and distance<=(1 if melee else 60) and (melee or ammo>0)
        try:result=f.hit_part(actor,name,weapon,roll=roll,skill=50,distance=distance,cover=cover)
        except ValueError:assert not valid and (f.snapshot(),actor)==before
        else:
            assert valid and actor.main==0 and actor.ammo==ammo-(0 if melee else 1)
            threshold=30 if cover=='partial' or (not melee and distance>30) else 50
            damage=max(0,(6 if melee else 4)-profile['parts'][name]['armor']) if roll<=threshold else 0
            assert f.parts[name].hp==profile['parts'][name]['max_hp']-damage and result==(('damage',damage) if roll<=threshold else ('miss',0))
            assert all(f.parts[other].hp==profile['parts'][other]['max_hp'] for other in f.parts if other!=name)
            assert f.clock==0 and actor.hp==hp
        attack_cases+=1
    check('all four parts use common projectile/melee conditions and actual resources',attack_cases,6912)
    rolls=0
    for skill,situation,expected in [(30,-20,10),(30,0,30),(30,20,50),(50,-20,30),(50,0,50),(50,20,70),(70,-20,50),(70,0,70),(70,20,90)]:
        successes=0
        for roll in range(1,101):
            f=overheated(50);actor=Body();result=f.shutdown(actor,fault=True,roll=roll,skill=skill,situation=situation)
            assert (result=='stopped')==(roll<=expected);successes+=result=='stopped';rolls+=1
        assert successes==expected
    check('faulty command same percent chances for nine declared conditions',rolls,900)
    files=[here/'대형시설_프로필.json',here/'입문_프로필.json',here/'일반플레이_검증.py',here/'백분율_코어검증.py',Path(__file__),here.parent/'10_CoreRulebook.md',here.parent/'11_WorldLorebook.md',here.parent/'12_룰시트와캐릭터시트.md']
    return {'date':'2026-10-06','id':profile['id'],'model':profile['model'],'scope':'NEW시설1의4부품·기존사격/격투/자원·제어조건/고정실제기한·OOC와JSON상태·안전무판정/고장d100을유한경우로검사한다. 전신수/촉수/군용/흑공정사/유체피해/대피·실제병행진행/균형/참가자검증이아니다.','checks_passed':len(checks),'checks':checks,'command_boundary_cases':command_cases,'common_attack_boundary_cases':attack_cases,'percentile_cases':rolls,'actual_IC_deadline_is_not_success_clock':True,'all_large_entity_profiles_complete':False,'all_black_material_or_facility_effects_complete':False,'new_universal_stats':[],'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False,'artifacts_sha256':{str(q.relative_to(here.parent)):hashlib.sha256(q.read_bytes()).hexdigest() for q in files}}

if __name__=='__main__':
    result=run();Path(__file__).with_name('대형시설_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({key:result[key] for key in ['checks_passed','command_boundary_cases','common_attack_boundary_cases','percentile_cases','actual_participant_playtest']},ensure_ascii=False))
