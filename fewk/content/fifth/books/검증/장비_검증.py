#!/usr/bin/env python3
"""두 NEW 장비 규격의 수량/호환/행동과 공통 피해 경계를 검산한다."""
from pathlib import Path
from fractions import Fraction
from itertools import product
import json,hashlib
from copy import deepcopy
from 백분율_코어검증 import grade,target
from 일반플레이_검증 import Body,attack,new_round,reload,PROFILE

here=Path(__file__).parent
p=json.loads((here/'장비_프로필.json').read_text())

def device_use(amount,compatible=True,permission=True,startable=True):
    if not compatible or not permission or not startable or amount<500:return amount,False
    return amount-500,True

def movable(mass,distance,held=False,fixed=False,cover=False):
    return 0<mass<=100 and 0<=distance<=10 and not (held or fixed or cover)

def shot(power,actor,body,**kw):
    if power<250:raise ValueError('actual power needed')
    # 실제 사격 조건/행동·탄약은 공통 모형에 위임. 시작 불가는 소모 전에 거절한다.
    result=attack(actor,body,'S-UTILITY-01',**kw)
    return power-250,result

def v_suppress(actor,body,marks,body_id,source_id,source_turn,**kw):
    if not body_id or not source_id or source_turn<0:raise ValueError('actual scene identifiers needed')
    result=attack(actor,body,'V-SUPPRESS-01',suppress=True,**kw)
    if result[0]=='suppression':
        marks.setdefault(body_id,{})[source_id]=source_turn+1
    return result

def suppression_situation(marks,body_id,current_source_turns,live_pressure_sources,full_cover=False):
    if full_cover:marks.pop(body_id,None);return 0
    actual=marks.get(body_id,{})
    for source,expiry in list(actual.items()):
        if current_source_turns.get(source,0)>=expiry or source not in live_pressure_sources:
            del actual[source]
    if not actual:marks.pop(body_id,None);return 0
    return -20

def rejected(fn):
    try:fn()
    except ValueError:return True
    return False


class SmartGun:
    """원전 공급 순서를 신규 출력에 연결. 탄/셀은 총별 실물 기록."""
    def __init__(self,ammo=1,gun_cells=1000,implant_cells=500,air=True,loose_projectiles=1):
        self.ammo=ammo;self.gun_cells=gun_cells;self.implant_cells=implant_cells;self.air=air;self.loose_projectiles=loose_projectiles;self.magazine_present=True
        self.connector=True;self.framework='F-CROC';self.bound_body='B-G1';self.person='P-G1'
        self.connected=True;self.locked=False;self.destroyed=False;self.stored=False;self.resync_seconds=0;self.held=False
        self.reserved=None;self.spare_magazines=[];self.location='B-G1';self._in_trigger=False
    def source(self):
        cost=p['crocodile']['energy_cost_cells']
        if any(type(x) is not int or x<0 for x in (self.ammo,self.gun_cells,self.implant_cells)) or self.ammo>p['crocodile']['magazine_capacity']:raise ValueError('valid actual gun resources required')
        if self.ammo:return 'ammo'
        if self.gun_cells>=cost:return 'gun_cells'
        if self.implant_cells>=cost:return 'implant_cells'
        if self.air:return 'air'
        raise ValueError('no feasible source')
    def ready(self,body,person):
        if self.destroyed or self.stored or self.locked or not self.connected or not self.connector or self.framework!='F-CROC' or body!=self.bound_body or person!=self.person:
            raise ValueError('actual matching live gun/body/connection required')
    def fire(self,actor,defender,body='B-G1',person='P-G1',_reserved=False,**kw):
        self.ready(body,person);source=self.source()
        if _reserved and not self._in_trigger:raise ValueError('reserved attack only via actual declared trigger')
        if actor.hp<=0 or actor.destroyed or actor.main<1 and not _reserved:raise ValueError('actual available operator action required')
        for field in ('roll','defense_roll'):
            value=kw.get(field,1 if field=='roll' else None)
            if value is not None and (type(value) is not int or not 1<=value<=100):raise ValueError('valid declared common roll required')
        distance=kw.get('distance',1)
        if type(distance) not in (int,float) or distance<0:raise ValueError('actual nonnegative distance required')
        data=p['crocodile']['outputs'][source];weapon='CROC-'+source
        PROFILE['weapons'][weapon]={**data,'capacity':1}
        # General combat expects an ammo counter on Body; adapt this selected gun only.
        saved_actor,saved_defender=deepcopy(actor.__dict__),deepcopy(defender.__dict__)
        saved_unselected_ammo_field=actor.ammo;actor.ammo=1
        if _reserved:actor.main=1
        try:result=attack(actor,defender,weapon,**kw)
        except Exception:
            actor.__dict__.clear();actor.__dict__.update(saved_actor);defender.__dict__.clear();defender.__dict__.update(saved_defender)
            raise
        actor.ammo=saved_unselected_ammo_field
        if source=='ammo':self.ammo-=1
        elif source in ('gun_cells','implant_cells'):setattr(self,source,getattr(self,source)-p['crocodile']['energy_cost_cells'])
        return source,result
    def reserve(self,actor,target_id,turn,body='B-G1',person='P-G1'):
        self.ready(body,person);source=self.source()
        if self.reserved is not None or actor.hp<=0 or actor.destroyed or actor.main<1 or not target_id or type(turn) is not int or turn<0:raise ValueError('one actual declared reserved attack required')
        actor.main-=1;self.reserved={'target':target_id,'expiry':turn+1,'source':source,'body':body,'person':person}
    def trigger(self,actor,defender,target_id,turn,condition=True,**kw):
        r=self.reserved
        if r is None or not condition or target_id!=r['target'] or type(turn) is not int or turn>=r['expiry'] or actor.main!=0 or self.source()!=r['source']:raise ValueError('actual still-valid declared reservation required')
        self._in_trigger=True
        try:result=self.fire(actor,defender,r['body'],r['person'],_reserved=True,**kw)
        finally:self._in_trigger=False
        self.reserved=None
        return result
    def expire(self,turn):
        if type(turn) is not int or turn<0:raise ValueError('actual source turn required')
        if self.reserved and turn>=self.reserved['expiry']:self.reserved=None
    def detach(self,actor,forced=False):
        if self.stored or self.destroyed:raise ValueError('actual device unavailable')
        if not forced:
            if actor.hp<=0 or actor.destroyed or actor.main<1:raise ValueError('actual normal disconnect action required')
            actor.main-=1
        self.connected=False;self.reserved=None
        if forced:self.locked=True;self.resync_seconds=0
    def bind(self,actor,body='B-G1',person='P-G1',supported=True,authorized=True):
        if self.stored or self.destroyed or self.locked or body!=self.location or not supported or not authorized or not self.connector or self.framework!='F-CROC' or person!=self.person or actor.hp<=0 or actor.destroyed or actor.main<1:
            raise ValueError('actual supported authorized matching connection required')
        actor.main-=1;self.bound_body=body;self.location=body;self.connected=True
    def resync(self,seconds,supported=True,authorized=True):
        if self.held or self.stored or self.destroyed or not self.locked or not supported or not authorized or type(seconds) is not int or seconds<0:raise ValueError('actual supported safe synchronization work required')
        self.resync_seconds=min(p['crocodile']['safe_resync_seconds'],self.resync_seconds+seconds)
        if self.resync_seconds==p['crocodile']['safe_resync_seconds']:self.locked=False
    def confirmed_death(self,body,verified=False,identified=False):
        if body!=self.bound_body or not verified or not identified:return False
        self.destroyed=True;self.connected=False;self.reserved=None;return True
    def remove_magazine(self,actor):
        if self.stored or self.destroyed or not self.magazine_present or actor.hp<=0 or actor.destroyed or actor.main<1:raise ValueError('actual magazine handling action required')
        actor.main-=1;self.spare_magazines.append(self.ammo);self.ammo=0;self.magazine_present=False
    def emergency_load(self,actor,actual_projectile=True):
        if self.stored or self.destroyed or not actual_projectile or type(self.loose_projectiles) is not int or self.loose_projectiles<1 or self.ammo!=0 or actor.hp<=0 or actor.destroyed or actor.main<1:raise ValueError('one available physical projectile loading action required')
        actor.main-=1;self.ammo=1;self.loose_projectiles-=1
    def supported_IO_store(self):
        if self.stored:raise ValueError('same device cannot be stored twice')
        self.stored=True;self.connected=False;self.reserved=None;self.location='IO-STORE'
    def supported_IO_restore(self,location):
        if not self.stored or not location:raise ValueError('one actual stored device IO result required')
        self.stored=False;self.location=location
    def ooc_wait(self,seconds):
        if type(seconds) is not int or seconds<0:raise ValueError('nonnegative OOC duration required')

class WristAxes:
    def __init__(self):
        self.body='B-G2';self.functional={'left':True,'right':True};self.drawn={'left':False,'right':False};self.stored=False
    def usable(self,hand,body):return not self.stored and body==self.body and hand in self.functional and self.functional[hand] and self.drawn[hand]
    def draw(self,actor,hands=('left','right'),opened=True,body='B-G2'):
        if self.stored or body!=self.body or actor.hp<=0 or actor.destroyed or actor.main<1 or not hands or len(set(hands))!=len(hands) or any(h not in self.functional or not self.functional[h] for h in hands):raise ValueError('actual available installed hands required')
        actor.main-=1
        for h in hands:self.drawn[h]=opened
    def free_hand(self,hand,body='B-G2'):
        return not self.stored and body==self.body and self.functional.get(hand,False) and not self.drawn.get(hand,False)
    def strike(self,actor,defender,hand='left',body='B-G2',**kw):
        if not self.usable(hand,body):raise ValueError('one actual deployed usable axe required')
        for field in ('roll','defense_roll'):
            value=kw.get(field,1 if field=='roll' else None)
            if value is not None and (type(value) is not int or not 1<=value<=100):raise ValueError('valid declared common roll required')
        return attack(actor,defender,'WRIST-AXE-C1',**kw)
    def block(self,attacker,defender,weapon,hand='left',body='B-G2',**kw):
        if not self.usable(hand,body) or PROFILE['weapons'][weapon]['type']!='근접' or kw.get('defense_roll') is None:raise ValueError('deployed contact block with one personal defense required')
        for field in ('roll','defense_roll'):
            value=kw.get(field,1 if field=='roll' else None)
            if value is not None and (type(value) is not int or not 1<=value<=100):raise ValueError('valid declared common roll required')
        return attack(attacker,defender,weapon,**kw)

def run():
    checks=[]
    def check(name,result,expected):
        assert result==expected,(name,result,expected);checks.append(name)
    c,g=p['cell'],p['gun']
    PROFILE['weapons']['S-UTILITY-01']={'type':'프로젝타일','damage':g['damage'],'normal_range_m':g['basic_range_m'],'max_range_m':g['maximum_range_m'],'capacity':1}
    check('common engine/term',(p['engine'],p['unified_action_term']),('P-FEWK-0.2','인터랙션'))
    check('separate model and shield axis',(g['classification'],g['damage_type']),('S','P'))
    check('same skill target',(g['pull_skill'],g['shot_skill'],g['target']),('공학','사격',50))
    check('exact ordinary success counts',tuple(sum(grade(t,r)>0 for r in range(1,101)) for t in (30,50,70)),(30,50,70))
    check('range situation',(target(50,0),target(50,-20)),(50,30))
    check('three distinct main actions',g['pull_main_actions']+g['load_main_actions']+g['shot_main_actions'],3)
    check('initial/nominal differ',(c['initial_amount'],c['device_nominal']),(10000,11000))
    check('adapter adds no energy',c['capacity_increase_from_adapter'],0)
    check('work and maintenance scope',(c['safe_install_seconds'],c['install_part_cost'],c['warranty_after_adapter'],c['liquid_extraction_allowed']),(300,1,False,False))
    # 셀 표시/용액량 원문 표와 독립적 정수 환산을 대조한다. 실제 물리 효율은 검증하지 않는다.
    masses=[1,10,100,1000,10000,20000,200000]
    nominal=[10000,100000,1000000,10000000,100000000,200000000,2000000000]
    check('display quantity table',[m*p['canonical_display_cells_per_solution_g'] for m in masses],nominal)
    check('largest case separates solution',200000*2,400000)
    thermal=Fraction(100000*4184,3600000)
    check('kcal to kWh independent conversion',thermal,Fraction(1046,9))
    check('raw interpretation conflict',thermal==1,False)
    check('not silently applying inconsistent power',p['kw_h_not_used_as_global_output_rule'],True)
    count=0
    for amount,compatible,permission,startable in product((0,1,499,500,501,1000,10000),(False,True),(False,True),(False,True)):
        left,ran=device_use(amount,compatible,permission,startable)
        spent=amount-left
        assert spent==500*int(ran) and left>=0
        assert ran==(compatible and permission and startable and amount>=500)
        count+=1
    check('device boundary combinations',count,56)
    check('two actual uses',device_use(device_use(10000)[0])[0],9000)
    check('exact exhaustion',device_use(500),(0,True))
    check('insufficient power unchanged',device_use(499),(499,False))
    # 같은 셀ID의 접속/분리를 보관 위치의 이동으로 검산한다.
    inventory={'POWER-01':10000};installed={}
    installed['DEV-01']=('POWER-01',inventory.pop('POWER-01'))
    check('installed cell removed from spare',inventory,{})
    cid,amount=installed['DEV-01'];installed['DEV-01']=(cid,device_use(amount)[0])
    cid,amount=installed.pop('DEV-01');inventory[cid]=amount
    check('remove keeps actual ID/amount',(installed,inventory),({}, {'POWER-01':9500}))
    count=0
    for mass,distance,held,fixed,cover in product((0,1,100,101),(0,10,11),(False,True),(False,True),(False,True)):
        result=movable(mass,distance,held,fixed,cover)
        if result:assert mass in (1,100) and distance in (0,10) and not any((held,fixed,cover))
        count+=1
    check('pull condition combinations',count,96)
    check('exact mass/range allowed',movable(100,10),True)
    check('actual held target not generic movement',movable(40,4,held=True),False)
    check('through wall blocked',movable(40,4,cover=True),False)
    # 공통 전투 처리를 새 무기 규격에 적용하고 대상 상태와 소비를 독립 확인한다.
    a,b=Body(ammo=1),Body()
    power,result=shot(2000,a,b,skill=50,roll=50,distance=10)
    check('same projectile shield hit',(power,result,a.ammo,b.hp,b.charges),(1750,('shield',0),0,12,1))
    a,b=Body(ammo=1),Body(shield_types=('레이저',))
    power,result=shot(2000,a,b,skill=50,roll=50,distance=10)
    check('S does not imply laser shield',(power,result,b.hp,b.charges),(1750,('damage',3),9,2))
    a,b=Body(ammo=1),Body()
    power,result=shot(2000,a,b,skill=50,roll=51,distance=10)
    check('miss spends projectile/power, no shield',(power,result,a.ammo,b.hp,b.charges),(1750,('miss',0),0,12,2))
    a,b=Body(ammo=1),Body(charges=0)
    check('beyond basic unfavorable',shot(2000,a,b,skill=50,roll=31,distance=11),(1750,('miss',0)))
    a,b=Body(ammo=1),Body()
    check('out of maximum not started',rejected(lambda:shot(2000,a,b,distance=21)),True)
    check('out of range no body/ammo/main change',(a.main,a.ammo,b.hp),(1,1,12))
    check('no power not started',rejected(lambda:shot(249,a,b)),True)
    check('no power no body/ammo/main change',(a.main,a.ammo,b.hp),(1,1,12))
    a,b=Body(ammo=0),Body()
    check('no local ammo is not free generation',rejected(lambda:shot(2000,a,b)),True)
    check('successful move and shot actual energy',2000-g['pull_cost_cells']-g['shot_cost_cells'],1500)
    check('no persistent universal stats',p['new_universal_stats'],[])
    v_start=len(checks);vg=p['vgun']
    PROFILE['weapons'][vg['id']]={'type':'프로젝타일','damage':0,'normal_range_m':vg['normal_range_m'],'max_range_m':vg['max_range_m'],'capacity':vg['capacity']}
    check('V model and actual shield axis',(vg['classification'],vg['damage_type'],vg['actual_physical_projectiles']),('V','P',True))
    check('same existing suppression and actual budget',(vg['ammo_per_action'],vg['main_actions'],vg['hp_damage'],vg['forced_emotion_or_Ego_damage']),(3,1,0,False))
    a,b=Body(ammo=6),Body(shield_types=('레이저',));marks={}
    result=v_suppress(a,b,marks,'B-V2','P-V1',4,skill=70,roll=62,distance=20)
    check('declared body-only suppression example',(result,a.ammo,a.main,b.hp,b.charges,marks),(('suppression',0),3,0,12,2,{'B-V2':{'P-V1':5}}))
    a,b=Body(ammo=6),Body();marks={}
    result=v_suppress(a,b,marks,'B-V2','P-V1',4,skill=70,roll=62,distance=20)
    check('P blocks V projectiles without status',(result,a.ammo,b.hp,b.charges,marks),(('shield',0),3,12,1,{}))
    a,b=Body(ammo=6),Body();marks={}
    result=v_suppress(a,b,marks,'B-V2','P-V1',4,skill=50,roll=51,distance=20)
    check('miss spends three and no shield/status',(result,a.ammo,b.charges,marks),(('miss',0),3,2,{}))
    a,b=Body(ammo=6),Body(charges=0);marks={}
    check('beyond basic uses the same unfavorable band',v_suppress(a,b,marks,'B-V2','P-V1',4,skill=50,roll=31,distance=21),('miss',0))
    a,b=Body(ammo=6),Body(charges=0);marks={}
    v_suppress(a,b,marks,'B-V2','P-V1',4);new_round(a);v_suppress(a,b,marks,'B-V2','P-V1',5)
    check('two actual actions exhaust six without HP damage',(a.ammo,a.main,b.hp),(0,0,12))
    a,b=Body(ammo=2),Body();marks={};before=deepcopy((a,b,marks))
    check('insufficient ammo rejects without mutation',rejected(lambda:v_suppress(a,b,marks,'B-V2','P-V1',4)) and (a,b,marks)==before,True)
    a=Body(ammo=3);reserve=[6];reload(a,reserve,capacity=6)
    check('V reload uses the actual six-round capacity',(a.ammo,a.main,reserve,a.ammo+sum(reserve)),(6,0,[3],9))
    a,b=Body(ammo=7),Body();marks={};before=deepcopy((a,b,marks))
    check('V capacity overflow rejects without mutation',rejected(lambda:v_suppress(a,b,marks,'B-V2','P-V1',4)) and (a,b,marks)==before,True)
    marks={'B-V2':{'P-V1':5}}
    check('actual next source turn ends status',(suppression_situation(marks,'B-V2',{'P-V1':5},{'P-V1'}),marks),(0,{}))
    marks={'B-V2':{'P-V1':5}}
    check('OOC waiting does not advance actual source turn',suppression_situation(marks,'B-V2',{'P-V1':4},{'P-V1'}),-20)
    check('full cover ends actual pressure',(suppression_situation(marks,'B-V2',{'P-V1':4},{'P-V1'},True),marks),(0,{}))
    marks={'B-V2':{'P-V1':5,'P-V3':8}}
    check('multiple sources remain one unfavorable reason',(suppression_situation(marks,'B-V2',{'P-V1':5,'P-V3':7},{'P-V1','P-V3'}),marks),(-20,{'B-V2':{'P-V3':8}}))
    check('other body does not inherit suppression',suppression_situation(marks,'B-ORIGINAL',{'P-V3':7},{'P-V3'}),0)
    check('actual pressure removal clears the body mark',(suppression_situation(marks,'B-V2',{'P-V3':7},set()),marks),(0,{}))
    v_cases=0
    for ammo,hp,main,cover,distance,roll,shield_type,charges,used in product((2,3,6),(0,12),(0,1),('none','partial','full'),(20,21,40,41),(30,31,50,51),('프로젝타일','레이저'),(0,2),(False,True)):
        a,b=Body(ammo=ammo,hp=hp,main=main),Body(shield_types=(shield_type,),charges=charges,blocked=used);marks={};before=deepcopy((a,b,marks))
        feasible=hp>0 and main>0 and cover!='full' and distance<=40 and ammo>=3
        if not feasible:
            assert rejected(lambda:v_suppress(a,b,marks,'B-V2','P-V1',4,skill=50,roll=roll,distance=distance,cover=cover)) and (a,b,marks)==before
        else:
            result=v_suppress(a,b,marks,'B-V2','P-V1',4,skill=50,roll=roll,distance=distance,cover=cover)
            t=30 if cover=='partial' or distance>20 else 50
            hit=roll<=t;blocked=hit and shield_type=='프로젝타일' and charges>0 and not used
            expected='miss' if not hit else ('shield' if blocked else 'suppression')
            assert result==(expected,0) and a.ammo==ammo-3 and a.main==0 and b.hp==12
            assert b.charges==charges-int(blocked) and bool(marks)==(hit and not blocked)
        v_cases+=1
    check('V range/body/ammo/shield finite boundary cases',v_cases,4608)
    v_checks=len(checks)-v_start
    def reject_state(name,gun,actor,defender,fn):
        before=deepcopy((gun.__dict__,actor.__dict__,defender.__dict__))
        try:fn()
        except ValueError:pass
        else:raise AssertionError(name+' accepted')
        check(name+' state preserved',(gun.__dict__,actor.__dict__,defender.__dict__),before)
    cg=p['crocodile'];ax=p['wrist_axes'];PROFILE['weapons'][ax['id']]={'type':'근접','damage':ax['damage'],'normal_range_m':1,'max_range_m':1,'capacity':0}
    gun=SmartGun();a,b=Body(),Body();source,result=gun.fire(a,b,skill=70,roll=62,distance=30)
    check('physical first source and P shield',(source,result,gun.ammo,gun.gun_cells,gun.implant_cells,b.hp,b.charges),('ammo',('shield',0),0,1000,500,12,1))
    new_round(a);new_round(b);source,result=gun.fire(a,b,skill=70,roll=62,distance=30)
    check('next declared energy L bypasses P only',(source,result,gun.ammo,gun.gun_cells,gun.implant_cells,b.hp,b.charges),('gun_cells',('damage',3),0,500,500,9,1))
    new_round(a);new_round(b);gun.fire(a,b,skill=70,roll=100,distance=30)
    check('energy miss actual supply spent no charge',(gun.gun_cells,gun.implant_cells,b.hp,b.charges),(0,500,9,1))
    new_round(a);new_round(b);source,_=gun.fire(a,b,skill=70,roll=100,distance=30)
    check('actual implant cell fallback',(source,gun.implant_cells),('implant_cells',0))
    new_round(a);new_round(b);source,result=gun.fire(a,b,skill=70,roll=1,distance=10,use_shield=False)
    check('available air low output same actual action',(source,result,a.main,b.hp),('air',('damage',1),0,8))
    source_cases=0
    for ammo,gcell,icell,air in product((0,1,12),(0,499,500,1000),(0,499,500,1000),(False,True)):
        gun=SmartGun(ammo,gcell,icell,air)
        expected='ammo' if ammo else 'gun_cells' if gcell>=500 else 'implant_cells' if icell>=500 else 'air' if air else None
        try:actual=gun.source()
        except ValueError:actual=None
        assert actual==expected;source_cases+=1
    check('finite actual source priority including partial cells',source_cases,96)
    fire_cases=0
    starts={'ammo':(1,1000,500,True),'gun_cells':(0,1000,500,True),'implant_cells':(0,499,500,True),'air':(0,499,499,True)}
    for source,distance,cover,shield,roll in product(starts,(1,10,20,30,60,61),('none','partial','full'),('프로젝타일','레이저','none'),range(1,101)):
        gun=SmartGun(*starts[source]);a,b=Body(),Body(shield_types=(shield,));before=deepcopy((gun.__dict__,a.__dict__,b.__dict__))
        limit=20 if source=='air' else 60;normal=10 if source=='air' else 30
        if cover=='full' or distance>limit:
            try:gun.fire(a,b,skill=70,roll=roll,distance=distance,cover=cover)
            except ValueError:pass
            else:raise AssertionError('infeasible smart shot')
            assert (gun.__dict__,a.__dict__,b.__dict__)==before
        else:
            actual,result=gun.fire(a,b,skill=70,roll=roll,distance=distance,cover=cover)
            assert actual==source
            hit=roll<=(50 if cover=='partial' or distance>normal else 70)
            output_type='프로젝타일' if source in ('ammo','air') else '레이저';blocked=hit and shield==output_type
            damage=0 if not hit or blocked else (1 if source=='air' else 3)
            assert result==('miss' if not hit else 'shield' if blocked else 'damage',damage)
            assert b.hp==12-damage and b.charges==2-int(blocked) and a.main==0 and a.ammo==12
            assert gun.ammo==starts[source][0]-int(source=='ammo') and gun.gun_cells==starts[source][1]-500*int(source=='gun_cells') and gun.implant_cells==starts[source][2]-500*int(source=='implant_cells')
        fire_cases+=1
    check('actual output range cover d100 matching shield cases',fire_cases,21600)
    gun=SmartGun(0,499,499,False);a,b=Body(),Body();reject_state('no source no free shot',gun,a,b,lambda:gun.fire(a,b))
    for field,value in [('connector',False),('framework','F-WORK'),('locked',True),('connected',False),('stored',True),('destroyed',True)]:
        gun=SmartGun();setattr(gun,field,value);a,b=Body(),Body();reject_state('actual smart condition '+field,gun,a,b,lambda:gun.fire(a,b))
    gun=SmartGun();a,b=Body(),Body();reject_state('different local body no borrowed original connector',gun,a,b,lambda:gun.fire(a,b,body='B-G0'))
    reject_state('other person not synchronized owner',gun,a,b,lambda:gun.fire(a,b,person='P-OTHER'))
    reject_state('invalid roll not actual shot',gun,a,b,lambda:gun.fire(a,b,roll=101))
    gun=SmartGun();a,b=Body(),Body();gun.reserve(a,'B-T1',4);check('AI reservation spends one same main',(a.main,gun.ammo),(0,1))
    reject_state('AI cannot fire free ordinary second shot',gun,a,b,lambda:gun.fire(a,b))
    source,result=gun.trigger(a,b,'B-T1',4,skill=70,roll=1,distance=30);check('AI trigger not additional attack',(a.main,gun.ammo,gun.reserved,source),(0,0,None,'ammo'))
    reject_state('same AI reservation not trigger twice',gun,a,b,lambda:gun.trigger(a,b,'B-T1',4))
    gun=SmartGun();a,b=Body(),Body();gun.reserve(a,'B-T1',4);before=deepcopy(gun.__dict__);gun.ooc_wait(86400);check('OOC no expired or fired AI reservation',gun.__dict__,before);gun.expire(5)
    check('actual next turn expires spent reservation',(gun.reserved,a.main,gun.ammo),(None,0,1))
    gun=SmartGun();a,b=Body(),Body();gun.detach(a,forced=True);reject_state('air does not bypass forced stop',gun,a,b,lambda:gun.fire(a,b))
    gun.resync(120);before=deepcopy(gun.__dict__);gun.ooc_wait(86400);check('OOC no resync work',gun.__dict__,before);gun.resync(180)
    check('300sec safe resync preserves actual stock',(gun.locked,gun.connected,gun.ammo,gun.gun_cells,gun.implant_cells),(False,False,1,1000,500));gun.bind(a)
    check('actual reconnect action required',(gun.connected,a.main),(True,0))
    gun=SmartGun();a,b=Body(hp=0),Body();check('HP0 alone not death signal',gun.confirmed_death('B-G1'),False)
    check('other body confirmed death not registered body',gun.confirmed_death('B-G0',True,True),False)
    check('actual named user body and identification',gun.confirmed_death('B-G1',True,True),True)
    reject_state('dead AI core not 300sec resync',gun,a,b,lambda:gun.resync(300))
    gun=SmartGun();a,b=Body(),Body();gun.remove_magazine(a);check('magazine actual ID count not duplicated',(gun.ammo,gun.spare_magazines),(0,[1]))
    new_round(a);gun.emergency_load(a);check('one emergency actual loading action',(gun.ammo,a.main,gun.spare_magazines),(1,0,[1]))
    new_round(a);reject_state('removed magazine not duplicated by another unload',gun,a,b,lambda:gun.remove_magazine(a))
    check('emergency projectile actual finite reserve consumed',gun.loose_projectiles,0)
    gun.ammo=0;reject_state('no physical emergency reserve cannot load',gun,a,b,lambda:gun.emergency_load(a))
    gun=SmartGun(0,499,0,False);a,b=Body(),Body();gun.supported_IO_store();snapshot=deepcopy((gun.ammo,gun.gun_cells,gun.implant_cells,gun.locked,gun.destroyed));reject_state('stored gun cannot operate',gun,a,b,lambda:gun.fire(a,b));gun.supported_IO_restore('REALM-RECEIVER')
    check('supported IO preserves gun identity resources flags',(gun.ammo,gun.gun_cells,gun.implant_cells,gun.locked,gun.destroyed),snapshot)
    reject_state('same stored gun cannot be restored twice',gun,a,b,lambda:gun.supported_IO_restore('OTHER'))
    gun=SmartGun();a,b=Body(main=0),Body();reject_state('forged reserved flag not free AI shot',gun,a,b,lambda:gun.fire(a,b,_reserved=True))
    gun=SmartGun();a,b=Body(),Body();gun.reserve(a,'B-T1',4);reject_state('reservation still requires actual trigger',gun,a,b,lambda:gun.fire(a,b,_reserved=True))
    gun=SmartGun();a,b=Body(),Body();reject_state('new body not instant gun delivery',gun,a,b,lambda:gun.bind(a,body='B-G2'))
    gun.supported_IO_store();gun.supported_IO_restore('B-G2');gun.bind(a,body='B-G2')
    check('actual supported delivery then matched connection',(gun.bound_body,gun.location,gun.ammo,gun.gun_cells,a.main),('B-G2','B-G2',1,1000,0))
    axes=WristAxes();a,b=Body(),Body(shield_types=('프로젝타일','레이저'));reject_state('folded axe not attack',axes,a,b,lambda:axes.strike(a,b))
    axes.draw(a);check('two axes one deployment action',(a.main,axes.drawn,axes.free_hand('left')),(0,{'left':True,'right':True},False))
    new_round(a);result=axes.strike(a,b,skill=70,roll=1,distance=1);check('one melee hit high damage P L do not block',(result,b.hp,b.charges,a.main),(('damage',5),7,2,0))
    reject_state('second axe not free second attack',axes,a,b,lambda:axes.strike(a,b,hand='right'))
    a,b=Body(),Body();axes.functional['left']=False;reject_state('damaged left axe not attack',axes,a,b,lambda:axes.strike(a,b));result=axes.strike(a,b,hand='right',roll=1);check('actual other hand may act',(result,a.main),(('damage',5),0))
    axes=WristAxes();a,b=Body(),Body();axes.draw(b,hands=('left',));new_round(b)
    result=axes.block(a,b,'WRIST-AXE-C1',roll=100,defense_roll=1);check('axe block one reaction no automatic counterattack',(result,b.reaction,b.main,a.hp),(('miss',0),0,1,12))
    a=Body();reject_state('personal block cannot be used twice',axes,a,b,lambda:axes.block(a,b,'WRIST-AXE-C1',roll=1,defense_roll=1))
    axes=WristAxes();a,b=Body(),Body();axes.draw(a);new_round(a);reject_state('invalid axe attack does not spend state',axes,a,b,lambda:axes.strike(a,b,roll=101))
    reject_state('invalid axe defense does not spend reaction',axes,a,b,lambda:axes.block(a,b,'WRIST-AXE-C1',roll=1,defense_roll=101))
    axe_condition_cases=0
    for deployed,functional,same_body,stored in product((False,True),repeat=4):
        x=WristAxes();x.drawn['left']=deployed;x.functional['left']=functional;x.stored=stored
        assert x.usable('left','B-G2' if same_body else 'B-G0')==(deployed and functional and same_body and not stored);axe_condition_cases+=1
    check('wrist deployed functional current body stored boundaries',axe_condition_cases,16)
    files=[here.parent/'10_CoreRulebook.md',here.parent/'12_룰시트와캐릭터시트.md',here/'장비_프로필.json',here/'일반플레이_검증.py',here/'백분율_코어검증.py',Path(__file__)]
    return {'date':'2026-10-06','profile':p['id'],'scope':'CROC-C1의 지정 공급/출력·연결/예약·보관과 WRIST-AXE-C1의 손별 전개·행동/반응 및 CAMP-CELL-01/S-UTILITY-01/V-SUPPRESS-01의 유한 자원·몸별억제/실제차례/사선종료·연결·행동·공통 피해 경계/표시단위만 검산. 전체 무기/임플란트·현물 물리/효율·실제 참가자 검증 아님.','checks_passed':len(checks),'checks':checks,'smart_source_cases':source_cases,'smart_fire_cases':fire_cases,'wrist_axe_condition_cases':axe_condition_cases,'v_suppression_checks':v_checks,'v_suppression_boundary_cases':v_cases,'v_model':vg['id'],'all_V_guns_verified':False,'device_boundary_cases':56,'pull_condition_cases':96,'thermal_reference_kWh_for_100000_cells':str(thermal),'artifacts_sha256':{str(f.relative_to(here.parent)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'all_guns_and_implants_complete':False,'actual_participant_playtest':False}

if __name__=='__main__':
    result=run()
    Path(__file__).with_name('장비_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['profile','checks_passed','device_boundary_cases','pull_condition_cases','actual_participant_playtest']},ensure_ascii=False))
