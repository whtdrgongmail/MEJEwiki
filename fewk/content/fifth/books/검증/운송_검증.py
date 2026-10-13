#!/usr/bin/env python3
"""Two declared road vehicles: worksheet state, shared attacks and bounded movement checks.
This is neither a VTT implementation nor participant evidence.
"""
from pathlib import Path
from dataclasses import dataclass,field,asdict
from itertools import product
from copy import deepcopy
import hashlib,json
from 백분율_코어검증 import grade,target,contest
from 일반플레이_검증 import Body,attack,new_round

HERE=Path(__file__).parent
P=json.loads((HERE/'운송_프로필.json').read_text())

@dataclass
class Rider(Body):
    id:str='B-R1'
    dim:str='D-R'
    position:int=0
    active:bool=True
    known_drive:bool=True
    permitted:bool=True
    life:int=50
    carried:bool=False

@dataclass
class Vehicle(Body):
    id:str='R-B1'
    model:str='ROAD-BIKE-01'
    dim:str='D-R'
    position:int=0
    power_id:str='POWER-R1'
    power:int=1000
    riders:list=field(default_factory=list)
    cargo:dict=field(default_factory=lambda:{'BOX-R1':20000})
    moved:bool=False
    stopped:bool=True
    stored:bool=False
    repair_open:bool=False

def vehicle(model='ROAD-BIKE-01',**kw):
    c=P['vehicles'][model]
    return Vehicle(model=model,hp=c['max_hp'],armor=c['armor'],charges=0,shield_types=(),**kw)

def round_start(v):
    v.moved=False
    for b in v.riders:
        new_round(b);b.carried=False

def drive(v,b,distance,fast=False,risk=False,roll=None,situation=0,
          safe_prefix=None,collision=False,block=None,block_roll=None,stop=False,route_open=True):
    c=P['vehicles'][v.model]
    max_distance=c['fast_move_m' if fast else 'normal_move_m']
    cost=P['drive']['fast_cost_cells' if fast else 'normal_cost_cells']
    needs_roll=fast or risk or block is not None
    if not (b in v.riders and b.active and b.hp>0 and not b.destroyed
            and b.known_drive and b.permitted and b.dim==v.dim and b.main==1
            and b.move==10 and not b.carried and v.hp>0 and not v.destroyed
            and not v.stored and not v.moved and not v.repair_open
            and len(v.riders)<=c['seats'] and all(isinstance(x,int) and x>=0 for x in v.cargo.values()) and sum(v.cargo.values())<=c['cargo_limit_g']
            and route_open and all(x.dim==v.dim and x.position==v.position for x in v.riders)
            and 0<distance<=max_distance and v.power>=cost):
        raise ValueError('drive infeasible')
    if safe_prefix is None:safe_prefix=distance
    if not 0<=safe_prefix<=distance:raise ValueError('invalid route failure point')
    if needs_roll and (roll is None or not 1<=roll<=100):raise ValueError('roll required')
    if block is not None and (not block['ready'] or block_roll is None or not 1<=block_roll<=100):
        raise ValueError('block not prepared')
    # All conditions are checked before actual action/resource consumption.
    b.main-=1;b.move=0;v.power-=cost;v.moved=True
    t=target(b.life,situation)
    if block is not None:
        success=contest(t,roll,block['target'],block_roll)==1
        block['ready']=False
    else:success=not needs_roll or grade(t,roll)>0
    moved=distance if success else (min(distance,safe_prefix,c['fast_failure_max_m']) if fast else 0)
    v.position+=moved;v.stopped=stop
    for rider in v.riders:
        rider.position=v.position;rider.move=0;rider.carried=True
    if not success and collision:
        impact(v,P['collision']['raw_vehicle_damage'])
        for rider in v.riders:impact(rider,P['collision']['raw_rider_damage'])
    return moved,success

def impact(obj,raw):
    amount=max(0,raw-obj.armor)
    if amount and obj.hp==0:obj.destroyed=True
    obj.hp=max(0,obj.hp-amount)
    return amount

def prepare_block(body,situation=0):
    if body.main!=1 or body.hp==0 or not body.active or not body.known_drive:
        raise ValueError('cannot prepare road block')
    body.main-=1
    return {'body_id':body.id,'target':target(body.life,situation),'ready':True}

def dismount(v,b,extra_walk=0):
    if not v.stopped or b not in v.riders or b.main!=1 or b.hp==0 or not b.active or not 0<=extra_walk<=10:
        raise ValueError('cannot dismount')
    b.main-=1;v.riders.remove(b);b.position=v.position+extra_walk
    # No reset of the body's spent basic movement.

def swap(v,worker,reserve,cell_id,compatible=True):
    if (not v.stopped or v.stored or v.destroyed or worker.main!=1 or worker.hp==0
            or not worker.active or not compatible or cell_id not in reserve
            or cell_id==v.power_id or not isinstance(reserve[cell_id],int) or reserve[cell_id]<0):raise ValueError('cannot swap')
    amount=reserve.pop(cell_id);reserve[v.power_id]=v.power
    v.power_id=cell_id;v.power=amount;worker.main-=1

def store(v,support=False):
    if not support or v.riders or not v.stopped or v.stored or v.repair_open:
        raise ValueError('storage conditions absent')
    v.stored=True
    record={'id':v.id,'model':v.model,'dim':v.dim,'position':v.position,'stopped':v.stopped,
            'hp':v.hp,'destroyed':v.destroyed,'power_id':v.power_id,'power':v.power,
            'cargo':deepcopy(v.cargo)}
    v.saved_fingerprint=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
    return record

def restore(v,record,support=False):
    if not support or not v.stored or record['id']!=v.id or hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()!=v.saved_fingerprint:
        raise ValueError('restore conditions absent')
    # The same stored object is made available, not copied into two locations.
    for k in ('model','dim','position','stopped','hp','destroyed','power_id','power','cargo'):
        setattr(v,k,deepcopy(record[k]))
    v.stored=False

@dataclass
class Work:
    vehicle_id:str
    elapsed:int=0
    completed:bool=False
    active:bool=True

def begin_repair(v,parts,part_id):
    if (v.stored or v.destroyed or v.moved or v.repair_open or part_id not in parts
            or v.hp>=P['vehicles'][v.model]['max_hp']):raise ValueError('repair infeasible')
    parts.remove(part_id);v.repair_open=True
    return Work(v.id)

def advance(v,w,seconds,safe=True,roll=None,skill=50):
    if not w.active or w.completed or w.vehicle_id!=v.id or v.stored or v.destroyed or v.moved:
        raise ValueError('work infeasible')
    if seconds<0 or w.elapsed+seconds>P['repair']['actual_work_seconds']:
        raise ValueError('invalid work time')
    ending=w.elapsed+seconds==P['repair']['actual_work_seconds']
    if ending and not safe and (roll is None or not 1<=roll<=100):raise ValueError('completion roll required')
    w.elapsed+=seconds
    if not ending:return False
    w.completed=True;w.active=False;v.repair_open=False
    if safe or grade(target(skill,0),roll)>0:
        v.hp=min(P['vehicles'][v.model]['max_hp'],v.hp+P['repair']['hp_restored'])
        return True
    return False

def pause(v,w):
    if w.completed or not w.active:raise ValueError('work already ended')
    w.active=False;v.repair_open=False

def resume(v,w):
    if w.completed or w.active or v.stored or v.destroyed or v.moved:
        raise ValueError('resume infeasible')
    w.active=True;v.repair_open=True

def rejected(fn):
    try:fn()
    except ValueError:return True
    return False

# 신규 두 수단만 다루는 상태 계산. 참가자 경험이나 전 항공 물리를 입증하지 않는다.
@dataclass
class Crew(Rider):
    specialty:str='항해'
    gun_trained:bool=True
    protection_trained:bool=True
    engineering_trained:bool=True
    exposed:bool=False
    repair_permitted:bool=True
    repair_tools:bool=True
    engineering_skill:int=50
    work_id:str=""

@dataclass
class Vessel(Vehicle):
    model:str='SEA-LINK-01'
    deck_offsets:dict=field(default_factory=dict)
    medium:str='water'
    altitude:int=0
    docked:bool=True
    closed:bool=True
    cabin_intact:bool=True
    cabin_supported:bool=True
    float_intact:bool=True
    protected:bool=False
    protection_used:bool=False
    gun_used:bool=False
    mount_ammo:int=6
    repair_job_id:str=""


def vessel(model='SEA-LINK-01',**kw):
    c=P['vessels']['models'][model]
    a=Vessel(model=model,hp=c['max_HP'],armor=c['armor'],charges=0,
             shield_types=(),medium=c['medium'],**kw)
    a.deck_offsets={b.id:0 for b in a.riders}
    return a


def aboard(a,b):
    return (b in a.riders and b.active and b.hp>0 and not b.destroyed and b.dim==a.dim
            and b.id in a.deck_offsets and b.position==a.position+a.deck_offsets[b.id])


def vessel_round(a):
    a.moved=False;a.protection_used=False;a.protected=False;a.gun_used=False
    new_round(a)
    for b in a.riders:
        new_round(b)
        if b.work_id:b.main=0;b.move=0


def navigate(a,b,distance,fast=False,risk=False,roll=None,safe_prefix=None,
             collision=False,route_supported=True,situation=0):
    c=P['vessels']['models'][a.model];q=P['vessels']['drive']
    cost=q['fast_cells' if fast else 'normal_cells']
    limit=c['fast_m' if fast else 'normal_m']
    if safe_prefix is None:safe_prefix=distance
    if not (aboard(a,b) and b.main==1 and b.move==10 and b.known_drive and b.permitted
            and b.specialty==c['specialty'] and a.medium==c['medium'] and route_supported
            and a.hp>0 and not a.destroyed and not a.stored and not a.moved and not a.repair_open
            and len({x.id for x in a.riders})==len(a.riders)<=c['seats']
            and all(aboard(a,x) for x in a.riders)
            and all(0<=x<=c['deck_length_m'] for x in a.deck_offsets.values())
            and all(isinstance(x,int) and x>=0 for x in a.cargo.values())
            and sum(a.cargo.values())<=c['cargo_limit_g'] and a.power>=cost
            and 0<distance<=limit and 0<=safe_prefix<=distance):raise ValueError('운항 조건 부족')
    needs_roll=fast or risk
    if needs_roll and (roll is None or not 1<=roll<=100):raise ValueError('운항 굴림 필요')
    success=not needs_roll or grade(target(b.life,situation),roll)>0
    moved=distance if success else min(safe_prefix,c['fast_failed_m']) if fast else 0
    b.main-=1;b.move=0;a.power-=cost;a.moved=True;a.docked=False;a.stopped=False
    a.position+=moved
    for x in a.riders:x.position+=moved
    if not success and collision:
        impact(a,P['collision']['raw_vehicle_damage'])
        # 이 시험에서는 갑판 노출 승객만 충격의 지정 대상이다.
        for x in a.riders:
            if x.exposed:impact(x,P['collision']['raw_rider_damage'])
    return moved,success


def deck_walk(a,b,destination):
    c=P['vessels']['models'][a.model]
    if not aboard(a,b) or a.stored or not 0<=destination<=c['deck_length_m']:
        raise ValueError('갑판 통로 부족')
    distance=abs(destination-a.deck_offsets[b.id])
    if distance>b.move:raise ValueError('몸 이동 예산 부족')
    b.move-=distance;b.position=a.position+destination;a.deck_offsets[b.id]=destination


def cabin_protection(a,b):
    if not (aboard(a,b) and b.main==1 and b.protection_trained and a.hp>0
            and not a.destroyed and not a.stored and a.closed and a.cabin_intact
            and a.cabin_supported and not a.protection_used
            and a.power>=P['vessels']['protection']['cost_cells']):raise ValueError('보호 조건 부족')
    b.main-=1;a.power-=P['vessels']['protection']['cost_cells']
    a.protected=True;a.protection_used=True


def black_contact_blocked(a,kind='시험흑공접촉',external=True):
    return bool(a.protected and a.closed and a.cabin_intact and a.cabin_supported
                and not a.stored and external and kind=='시험흑공접촉')


def mount_fire(a,b,victim,distance,roll=1,skill=50,scale_supported=False,
               line_open=True,adverse=False,use_shield=True):
    q=P['vessels']['gun']
    if not (aboard(a,b) and b.main==1 and b.gun_trained and not a.stored
            and a.hp>0 and not a.destroyed and not a.gun_used and a.mount_ammo>0
            and (isinstance(victim,Vessel) or scale_supported) and line_open and 0<=distance<=q['max_m']
            and 1<=roll<=100):raise ValueError('포대 조건 부족')
    b.main-=1;a.mount_ammo-=1;a.gun_used=True
    t=target(skill,-20 if adverse or distance>q['normal_m'] else 0)
    if not grade(t,roll):return 'miss',0
    if use_shield and '프로젝타일' in victim.shield_types and victim.charges>0 and not victim.blocked:
        victim.charges-=1;victim.blocked=True;return 'shield',0
    return 'damage',impact(victim,q['damage'])


def dock_vessel(a,platform_altitude,route_supported=True):
    if not (not a.stored and route_supported and platform_altitude==a.altitude
            and (a.hp>0 or a.float_intact)):
        raise ValueError('실제 접안 지원 부족')
    a.docked=True;a.stopped=True


def vessel_exit(a,b):
    if not (a.docked and a.stopped and not a.stored and aboard(a,b)
            and b.main==1 and a.deck_offsets[b.id]==0):raise ValueError('승하선 조건 부족')
    b.main-=1;a.riders.remove(b);del a.deck_offsets[b.id]


def vessel_enter(a,b):
    c=P['vessels']['models'][a.model]
    if not (a.docked and a.stopped and not a.stored and b not in a.riders
            and b.id not in a.deck_offsets and b.active and b.hp>0 and not b.destroyed
            and b.main==1 and b.position==a.position and b.dim==a.dim
            and len(a.riders)<c['seats']):raise ValueError('탑승 조건 부족')
    b.main-=1;a.riders.append(b);a.deck_offsets[b.id]=0


@dataclass
class VesselWork(Work):
    worker_id:str=''
    part_id:str=''
    job_id:str=''
    handover_seconds:int=0
    abandoned:bool=False


def repair_worker_ready(a,b):
    return (b.active and b.hp>0 and not b.destroyed and b.engineering_trained
            and b.repair_permitted and b.repair_tools and b.dim==a.dim and b.position==a.position)


def vessel_repair_start(a,b,parts,part_id):
    if not (a.docked and a.stopped and not a.stored and not a.destroyed
            and not a.repair_open and repair_worker_ready(a,b) and b.main==1 and not b.work_id
            and part_id in parts and a.hp<P['vessels']['models'][a.model]['max_HP']):
        raise ValueError('접안 정비 조건 부족')
    job_id=a.id+':'+part_id
    b.main-=1;b.move=0;b.work_id=job_id;parts.remove(part_id);a.repair_open=True;a.repair_job_id=job_id
    return VesselWork(a.id,worker_id=b.id,part_id=part_id,job_id=job_id)


def vessel_repair_advance(a,w,seconds,worker,safe=True,roll=None):
    q=P['vessels']['repair']
    if not (a.docked and a.stopped and not a.stored and not a.destroyed and a.repair_open
            and w.vehicle_id==a.id and w.job_id==a.repair_job_id and not w.abandoned and w.active and not w.completed
            and repair_worker_ready(a,worker) and worker.id==w.worker_id and worker.work_id==w.job_id
            and isinstance(seconds,int) and seconds>0 and seconds%P['round_seconds']==0
            and seconds<=q['seconds']-w.elapsed):raise ValueError('작업 진행 조건 부족')
    ending=w.elapsed+seconds==q['seconds']
    if ending and not safe and (roll is None or not 1<=roll<=100):raise ValueError('정비 굴림 필요')
    w.elapsed+=seconds
    if not ending:return False
    w.completed=True;w.active=False;a.repair_open=False;a.repair_job_id='';worker.work_id=''
    success=safe or grade(target(worker.engineering_skill,0),roll)>0
    if success:a.hp=min(P['vessels']['models'][a.model]['max_HP'],a.hp+q['HP_gain'])
    return bool(success)


def vessel_repair_pause(a,w,worker):
    if not (w.vehicle_id==a.id and w.job_id==a.repair_job_id and not w.abandoned and w.active and not w.completed
            and w.worker_id==worker.id and worker.work_id==w.job_id):
        raise ValueError('중단할 실제 작업 없음')
    w.active=False;worker.work_id=''
    # 소모품/진행을 갖는 열린 작업은 보관/새 정비와 중복되지 않는다.


def vessel_repair_resume(a,w,worker):
    if not (w.vehicle_id==a.id and w.job_id==a.repair_job_id and not w.abandoned and not w.active and not w.completed and a.repair_open
            and a.docked and a.stopped and not a.stored and not a.destroyed
            and worker.id==w.worker_id and repair_worker_ready(a,worker)
            and worker.main==1 and not worker.work_id):raise ValueError('작업 재개 조건 부족')
    worker.main-=1;worker.move=0;worker.work_id=w.job_id;w.active=True


def vessel_repair_handover(a,w,old_worker,new_worker):
    if not (w.vehicle_id==a.id and w.job_id==a.repair_job_id and not w.abandoned and not w.active and not w.completed and a.repair_open
            and a.docked and a.stopped and not a.stored and not a.destroyed
            and old_worker.id==w.worker_id and not old_worker.work_id
            and new_worker.id!=old_worker.id and repair_worker_ready(a,new_worker)
            and new_worker.main==1 and not new_worker.work_id):
        raise ValueError('작업 인계 조건 부족')
    new_worker.main-=1;new_worker.move=0
    w.worker_id=new_worker.id;w.handover_seconds+=P['round_seconds']
    # 인계5초는 실제 시간이며 작업 진행량/회복으로 세지 않는다.



def vessel_repair_abandon(a,w,worker):
    if not (w.vehicle_id==a.id and w.job_id==a.repair_job_id and not w.abandoned and a.repair_open and not w.completed and not w.abandoned
            and w.worker_id==worker.id):raise ValueError('종료할 열린 작업 없음')
    w.active=False;w.abandoned=True;a.repair_open=False;a.repair_job_id='';worker.work_id=''
    # 기록/쓴 부품/누적 시간은 유지한다. 새 행동을 소급 지급하지 않는다.


def vessel_store(a,support=False):
    if not (support and a.docked and a.stopped and not a.riders and not a.deck_offsets
            and not a.stored and not a.repair_open):raise ValueError('함선 보관 지원 부족')
    record=asdict(a);record['stored']=True
    a.stored=True
    a.saved_fingerprint=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
    return record


def vessel_restore(a,record,support=False):
    if not (support and a.stored and record['id']==a.id
            and hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()==a.saved_fingerprint):
        raise ValueError('함선 복원 지원 부족')
    for k,value in record.items():setattr(a,k,deepcopy(value))
    a.stored=False


def run_vessels():
    checks=[]
    def check(name,actual,expected):
        assert actual==expected,(name,actual,expected);checks.append(name)
    crew=[Crew(id=f'P-V{i}') for i in range(1,5)];a=vessel(id='SEA-V1',riders=crew)
    check('추가 능력치 없음',P['vessels']['new_universal_stats'],[])
    check('원고의 안전 운항',navigate(a,crew[0],20),(20,True))
    cabin_protection(a,crew[1]);enemy=vessel(id='ENEMY')
    check('같은 백분율 포격',mount_fire(a,crew[2],enemy,100),('damage',6))
    deck_walk(a,crew[3],2)
    check('원고의 한 장면',(a.position,a.power,a.mount_ammo,crew[3].position,crew[3].move),(20,988,5,22,8))
    check('운항자와 승객 예산',(crew[0].main,crew[0].move,crew[3].main,crew[3].reaction),(0,0,1,1))
    check('선체 피해가 승객에게 전달되지 않음',[x.hp for x in crew],[12]*4)
    snap=asdict(a)
    check('승무원 교체 뒤 두 번째 운항 불가',rejected(lambda:navigate(a,crew[3],20)),True)
    check('승무원 교체 뒤 두 번째 포격 불가',rejected(lambda:mount_fire(a,crew[3],enemy,100)),True)
    check('승무원 교체 뒤 두 번째 보호 불가',rejected(lambda:cabin_protection(a,crew[3])),True)
    check('거절된 사용은 상태 불변',asdict(a),snap)
    check('지원 흑공만 차단',black_contact_blocked(a),True)
    check('P 사격은 흑공 보호 범위 밖',black_contact_blocked(a,'P'),False)
    check('L 사격은 흑공 보호 범위 밖',black_contact_blocked(a,'L'),False)
    check('내부 위험은 보호 범위 밖',black_contact_blocked(a,external=False),False)
    a.closed=False;check('열린 선실은 보호 범위 밖',black_contact_blocked(a),False);a.closed=True
    vessel_round(a)
    check('다음 라운드는 자원과 갑판 위치 유지',(a.power,a.mount_ammo,a.deck_offsets[crew[3].id],crew[3].move),(988,5,2,10))
    check('다음 라운드는 보호 유지 비용 필요',black_contact_blocked(a),False)
    navigate(a,crew[0],20)
    check('몸의 갑판 위치와 공간 위치 구분',(a.position,crew[3].position,a.deck_offsets[crew[3].id]),(40,42,2))
    check('갑판 밖 걷기 불가',rejected(lambda:deck_walk(a,crew[3],7)),True)
    check('운항자는 이동 예산 소진',rejected(lambda:deck_walk(a,crew[0],1)),True)
    cases=0
    for model,skill,roll in product(P['vessels']['models'],(10,30,50,70,95),range(1,101)):
        c=P['vessels']['models'][model];b=Crew(life=skill,specialty=c['specialty']);x=vessel(model,riders=[b])
        moved,success=navigate(x,b,c['fast_m'],fast=True,roll=roll,safe_prefix=c['fast_m'])
        assert moved==(c['fast_m'] if roll<=skill else c['fast_failed_m'])
        assert success==(roll<=skill) and x.power==985 and b.main==0 and b.move==0
        cases+=1
    check('두 수단의 모든 급행 결과',cases,1000)
    feasible=0
    for trained,permission,power,medium,route,used,main in product((False,True),repeat=7):
        b=Crew(known_drive=trained,permitted=permission,main=int(main))
        x=vessel(riders=[b],power=10 if power else 9,moved=used)
        if not medium:x.medium='unsupported'
        snapshot=asdict(x);valid=all((trained,permission,power,medium,route,main)) and not used
        refused=rejected(lambda:navigate(x,b,20,route_supported=route))
        assert refused!=valid
        if refused:assert asdict(x)==snapshot
        feasible+=1
    check('운항 조건 조합과 무소모 거절',feasible,128)
    for label,change in [('잘못된 전문',{'specialty':'운전'}),('개인 이동 사용',{'move':9})]:
        b=Crew(**change);x=vessel(riders=[b]);snap=asdict(x)
        check(label,rejected(lambda:navigate(x,b,20)),True);check(label+' 무소모',asdict(x),snap)
    x=vessel(riders=[Crew()],cargo={'X':500001});check('화물 한도',rejected(lambda:navigate(x,x.riders[0],20)),True)
    x=vessel(riders=[Crew(id=str(i)) for i in range(7)]);check('정원 한도',rejected(lambda:navigate(x,x.riders[0],20)),True)
    protected_cases=0
    for closed,intact,supported,trained,power,used,main in product((False,True),repeat=7):
        b=Crew(protection_trained=trained,main=int(main))
        x=vessel(riders=[b],closed=closed,cabin_intact=intact,cabin_supported=supported,
                 power=2 if power else 1,protection_used=used)
        snap=asdict(x);valid=all((closed,intact,supported,trained,power,main)) and not used
        assert rejected(lambda:cabin_protection(x,b))!=valid
        if not valid:assert asdict(x)==snap
        else:assert x.power==0 and b.main==0 and black_contact_blocked(x)
        protected_cases+=1
    check('밀봉 지원과 보호 비용의 조건 조합',protected_cases,128)
    b,pas=Crew(),Crew(id='EXPOSED',exposed=True);x=vessel(riders=[b,pas]);deck_walk(x,pas,1)
    navigate(x,b,20,risk=True,roll=100,collision=True)
    check('선체와 노출 몸의 충격 대상 구분',(x.hp,b.hp,pas.hp),(36,12,10))
    check('충격은 개인 P 방호 소모 없음',pas.charges,2)
    for model in P['vessels']['models']:
        c=P['vessels']['models'][model];b=Crew(specialty=c['specialty']);x=vessel(model,riders=[b])
        check(model+' 실패가 자동 충돌 아님',navigate(x,b,c['fast_m'],fast=True,roll=100),(c['fast_failed_m'],False))
        check(model+' 실패 후 선체 유지',x.hp,c['max_HP'])
    b=Crew();x=vessel(riders=[b]);victim=vessel();victim.charges=2;victim.shield_types=('프로젝타일',)
    check('포대의 실제 P 방호',mount_fire(x,b,victim,100),('shield',0))
    check('포대 방호 비용',(victim.charges,x.mount_ammo),(1,5))
    b=Crew();x=vessel(riders=[b]);check('개인 몸에 함포 환산 불가',rejected(lambda:mount_fire(x,b,Body(),1,scale_supported=False)),True)
    check('포격 불리 중복 없이 적용',mount_fire(x,b,vessel(),130,roll=31,adverse=True),('miss',0))
    check('포격 실패도 한 번 소비',(b.main,x.mount_ammo,x.gun_used),(0,5,True))
    x=vessel(riders=[Crew()]);x.hp=0
    check('선체0은 추진 불가',rejected(lambda:navigate(x,x.riders[0],20)),True)
    check('선체0은 승객과 부력 유지',(x.riders[0].hp,x.float_intact),(12,True))
    dock_vessel(x,0);check('남은 독립 부력으로 접안 지원',x.docked,True)
    x=vessel('AIR-LINK-01',altitude=20)
    check('고도 다른 부두로 자동 접안 불가',rejected(lambda:dock_vessel(x,0)),True)
    check('거절된 접안은 고도 유지',x.altitude,20)
    dock_vessel(x,20);check('실제 고도 맞는 플랫폼',x.altitude,20)
    b=Crew();x=vessel(riders=[b]);vessel_exit(x,b)
    check('하선의 기존 주요 행동 사용',(b.main,len(x.riders)),(0,0))
    new_round(b);vessel_enter(x,b);check('승선은 같은 몸 유지',(len(x.riders),b.hp,b.main),(1,12,0))
    repair_cases=0
    for model in P['vessels']['models']:
        for hp in range(P['vessels']['models'][model]['max_HP']):
            x=vessel(model);x.hp=hp;b=Crew();parts={'PART'};w=vessel_repair_start(x,b,parts,'PART')
            vessel_repair_advance(x,w,120,b);vessel_repair_pause(x,w,b)
            check_pause=(w.elapsed,x.hp,x.power,len(parts))
            assert check_pause==(120,hp,1000,0)
            assert rejected(lambda:vessel_repair_advance(x,w,180,b))
            new_round(b);vessel_repair_resume(x,w,b);assert vessel_repair_advance(x,w,180,b)
            assert x.hp==min(P['vessels']['models'][model]['max_HP'],hp+4)
            assert x.power==1000 and b.hp==12 and not parts
            assert rejected(lambda:vessel_repair_advance(x,w,0,b));repair_cases+=1
    check('모든 미파괴 선체 HP의 중단 재개 정비',repair_cases,72)
    x=vessel();x.hp=0;x.destroyed=True
    check('파괴된 선체의 간이 정비 불가',rejected(lambda:vessel_repair_start(x,Crew(),{'PART'},'PART')),True)
    x=vessel(power=988,mount_ammo=5,altitude=0);x.hp=17
    check('지원 없는 함선 보관 불가',rejected(lambda:vessel_store(x)),True)
    record=vessel_store(x,True);changed=deepcopy(record);changed['mount_ammo']=6
    check('보관 포탄 무료 복원 불가',rejected(lambda:vessel_restore(x,changed,True)),True)
    vessel_restore(x,record,True)
    check('보관 상태 승계',(x.hp,x.power,x.mount_ammo,x.cargo),(17,988,5,{'BOX-R1':20000}))
    check('같은 기록의 이중 복원 불가',rejected(lambda:vessel_restore(x,record,True)),True)
    return {'vessel_profile':P['vessels']['id'],'vessel_checks_passed':len(checks),
            'vessel_checks':checks,'vessel_movement_roll_cases':cases,
            'vessel_feasibility_cases':feasible,'vessel_repair_HP_cases':repair_cases,
            'vessel_protection_cases':protected_cases,
            'vessel_total_boundary_cases':cases+feasible+protected_cases+repair_cases,
            'all_ships_aircraft_and_vehicle_IO_complete':False,
            'vessel_actual_participant_playtest':False}

def run_vessel_handover():
    checks=[]
    def check(name,actual,expected):
        assert actual==expected,(name,actual,expected);checks.append(name)
    a=vessel(power=988,mount_ammo=5);a.hp=17
    first=Crew(id='TECH-A',engineering_skill=70);second=Crew(id='TECH-B',engineering_skill=30)
    parts={'PART-A','PART-B'};w=vessel_repair_start(a,first,parts,'PART-A')
    check('작업자/부품의 실제 귀속',(w.worker_id,w.part_id,parts),('TECH-A','PART-A',{'PART-B'}))
    check('완료 전 회복 없음',vessel_repair_advance(a,w,120,first),False)
    before=(asdict(a),asdict(w),asdict(second))
    check('미인계 작업자 진행 거절',rejected(lambda:vessel_repair_advance(a,w,180,second)),True)
    check('미인계 시도 상태 불변',(asdict(a),asdict(w),asdict(second)),before)
    vessel_repair_pause(a,w,first)
    check('중단한 시간 유지',(w.elapsed,w.active,a.repair_open),(120,False,True))
    check('중단 중 함선 보관 거절',rejected(lambda:vessel_store(a,True)),True)
    check('중단 중 중복 정비 거절',rejected(lambda:vessel_repair_start(a,second,parts,'PART-B')),True)
    invalid_cases=0
    for changes in [{'active':False},{'hp':0},{'engineering_trained':False},{'repair_permitted':False},{'repair_tools':False},{'dim':'OTHER'},{'position':1},{'main':0},{'work_id':'OTHER-JOB'}]:
        candidate=Crew(id='TECH-C',**changes);snap=(asdict(a),asdict(w),asdict(candidate),set(parts))
        assert rejected(lambda:vessel_repair_handover(a,w,first,candidate))
        assert (asdict(a),asdict(w),asdict(candidate),set(parts))==snap;invalid_cases+=1
    check('인계의 몸/학습/권한/공구/위치/예산 경계',invalid_cases,9)
    vessel_repair_handover(a,w,first,second)
    check('인계5초가 진행/부품을 늘리지 않음',(w.elapsed,w.handover_seconds,w.worker_id,parts),(120,5,'TECH-B',{'PART-B'}))
    new_round(first);check('전 작업자 재개 거절',rejected(lambda:vessel_repair_resume(a,w,first)),True)
    check('인계 직후 같은 주요 행동 재개 불가',rejected(lambda:vessel_repair_resume(a,w,second)),True)
    new_round(second);vessel_repair_resume(a,w,second)
    check('재개 담당자 행동 예약',(second.main,second.move,second.work_id),(0,0,w.job_id))
    check('인계받은30숙련으로40은 실패',vessel_repair_advance(a,w,180,second,safe=False,roll=40),False)
    check('이전70숙련/동력/포탄/몸HP 승계 안함',(a.hp,a.power,a.mount_ammo,first.hp,second.hp,w.elapsed,w.completed),(17,988,5,12,12,300,True))
    check('완료한 작업의 재인계 거절',rejected(lambda:vessel_repair_handover(a,w,second,first)),True)
    check('완료한 작업의 재회복 거절',rejected(lambda:vessel_repair_advance(a,w,5,second)),True)
    new_round(second);w2=vessel_repair_start(a,second,parts,'PART-B')
    check('새 부품/새 실제 작업으로 성공',vessel_repair_advance(a,w2,300,second,safe=False,roll=30),True)
    check('각 작업의 회복은 한번',(a.hp,parts,w2.elapsed),(21,set(),300))
    a2=vessel(riders=[Crew(id='ONBOARD')]);a2.hp=17;b=a2.riders[0]
    w3=vessel_repair_start(a2,b,{'PART-C'},'PART-C');vessel_round(a2)
    check('작업 중 라운드 갱신 추가 주요 행동 없음',(b.main,b.move),(0,0))
    check('작업 중 포격 거절',rejected(lambda:mount_fire(a2,b,vessel(),20)),True)
    check('작업 중 다른 운항 거절',rejected(lambda:navigate(a2,b,20)),True)
    vessel_repair_pause(a2,w3,b);vessel_round(a2)
    check('중단 후 다음 라운드 인물 행동 복귀',(b.main,b.move),(1,10))
    vessel_repair_abandon(a2,w3,b)
    w4=vessel_repair_start(a2,b,{'PART-D'},'PART-D');vessel_repair_advance(a2,w4,60,b)
    vessel_repair_abandon(a2,w4,b)
    check('철수 위한 작업 포기와 기록 유지',(a2.repair_open,w4.active,w4.abandoned,w4.elapsed,a2.hp),(False,False,True,60,17))
    check('포기 작업 재개 불가',rejected(lambda:vessel_repair_resume(a2,w4,b)),True)
    new_round(b);w5=vessel_repair_start(a2,b,{'PART-E'},'PART-E');vessel_repair_pause(a2,w5,b);new_round(b)
    before=(asdict(a2),asdict(w4),asdict(w5),asdict(b))
    check('새 작업이 열려도 이전 포기 작업 재개 불가',rejected(lambda:vessel_repair_resume(a2,w4,b)),True)
    check('이전 작업 시도 새 작업 상태 불변',(asdict(a2),asdict(w4),asdict(w5),asdict(b)),before)
    vessel_repair_abandon(a2,w5,b)
    vessel_round(a2);check('포기 뒤 실제 다음 운항',navigate(a2,b,20),(20,True))
    return {'vessel_handover_checks_passed':len(checks),'vessel_handover_checks':checks,
            'vessel_handover_infeasible_cases':invalid_cases,'vessel_handover_example':{'work_seconds':300,'handover_seconds':5,'first_skill':70,'current_skill':30,'roll':40,'repair_HP_gain':0},
            'vessel_handover_scope':'두 시험 선박의 작업자/몸·학습/도구/권한과 실제로 선언한 작업 구간만 계산. 모든 세계의 신단출력/공정·실제참가자/작업 중 전 행동의 런타임은 입증하지 않는다.',
            'vessel_handover_actual_participant_playtest':False}

def run():
    checks=[]
    def check(name,actual,expected):
        assert actual==expected,(name,actual,expected);checks.append(name)
    check('common engine and skill',(P['engine'],P['drive_skill'],P['drive_specialty_required']),('P-FEWK-0.2','생활','운전'))
    check('no added universal stats',P['new_universal_stats'],[])
    d,passenger=Rider(),Rider(id='B-R2',known_drive=False)
    v=vehicle(riders=[d,passenger])
    check('safe normal no roll',drive(v,d,40),(40,True))
    check('positions move together',(v.position,d.position,passenger.position),(40,40,40))
    check('driver spent main and movement',(d.main,d.move,v.power),(0,0,990))
    check('passenger keeps main and personal reaction',(passenger.main,passenger.reaction,passenger.move),(1,1,0))
    check('driver cannot fire same main',rejected(lambda:attack(d,Body(),'권총',distance=20)),True)
    before=asdict(v)
    check('driver change no second movement',rejected(lambda:drive(v,passenger,40)),True)
    check('invalid attempt no mutation',asdict(v),before)
    check('no free dismount on moving vehicle',rejected(lambda:dismount(v,passenger)),True)
    # The shared attack model proves a passenger uses the ordinary ammunition/main/shield rules.
    victim=Body()
    check('passenger shared gun against body',attack(passenger,victim,'권총',roll=20,skill=50,distance=20),('shield',0))
    check('passenger has one shot',(passenger.main,passenger.ammo,victim.hp,victim.charges),(0,11,12,1))
    round_start(v)
    check('round resets only action flags',(v.moved,d.main,d.move,passenger.main,v.power,v.position),(False,1,10,1,990,40))
    check('same vehicle and fuel after reset',(v.id,v.power_id),('R-B1','POWER-R1'))
    check('fast positive movement',drive(v,d,60,fast=True,roll=34),(60,True))
    check('fast consumption',(v.position,v.power),(100,975))
    round_start(v)
    check('failed fast capped by safe prefix',drive(v,d,60,fast=True,roll=74,safe_prefix=12),(12,False))
    check('failed use not refunded',(v.position,v.power),(112,960))
    check('failure not automatic crash',(v.hp,d.hp,passenger.hp),(16,12,12))
    round_start(v)
    d.charges=2;passenger.charges=2
    check('declared collision on failure',drive(v,d,40,risk=True,roll=80,collision=True),(0,False))
    check('collision armor applied once',(v.hp,d.hp,passenger.hp),(10,10,10))
    check('P shields do not block impact',(d.charges,passenger.charges),(2,2))
    van=vehicle('ROAD-VAN-01',id='R-V1',riders=[Rider()])
    check('van fast failure ceiling',drive(van,van.riders[0],50,fast=True,roll=100,collision=True),(10,False))
    check('van and rider armor separate',(van.hp,van.riders[0].hp),(19,10))
    # Feasibility combinations prove no partial resource/action spend on rejected starts.
    matrix=0;valid=0
    for active,hp_ok,known,permission,dim_ok,power_ok,stored,moved,main_ok,cargo_ok,route_open in product((False,True),repeat=11):
        b=Rider(active=active,hp=12 if hp_ok else 0,known_drive=known,permitted=permission,
                dim='D-R' if dim_ok else 'OTHER',main=1 if main_ok else 0)
        a=vehicle(riders=[b],power=10 if power_ok else 9,stored=stored,moved=moved,
                  cargo={'BOX':30000 if cargo_ok else 30001})
        before=asdict(a)
        feasible=all((active,hp_ok,known,permission,dim_ok,power_ok,main_ok,cargo_ok,route_open)) and not stored and not moved
        result=rejected(lambda:drive(a,b,40,route_open=route_open))
        assert result!=feasible
        if not feasible:assert asdict(a)==before
        else:assert (a.position,a.power,b.main,b.move)==(40,0,0,0);valid+=1
        matrix+=1
    check('start feasibility matrix',matrix,2048)
    check('exact fully prepared state',valid,1)
    b=Rider();a=vehicle(riders=[b],power=15)
    check('exact fast fuel',drive(a,b,60,fast=True,roll=1),(60,True))
    check('exact exhaustion',a.power,0)
    for name,distance,move,main,nriders,cargo in [('too far',61,10,1,1,0),('already walked',40,9,1,1,0),('no main',40,10,0,1,0),('too many seats',40,10,1,3,0),('too much cargo',40,10,1,1,30001)]:
        b=Rider(move=move,main=main);a=vehicle(riders=[b]+[Rider(id=str(i)) for i in range(nriders-1)],cargo={'X':cargo})
        snap=asdict(a);check(name,rejected(lambda:drive(a,b,distance,fast=True,roll=1)),True);check(name+' no spend',asdict(a),snap)
    b=Rider(position=100);a=vehicle(riders=[b]);snap=asdict(a)
    check('absent listed rider cannot teleport',rejected(lambda:drive(a,b,40)),True)
    check('absent rider no spend',asdict(a),snap)
    # Existing percentile contest, with a previously spent major action, never an extra free reaction.
    blocker=Rider(id='BLOCK');block=prepare_block(blocker)
    check('block uses existing major',blocker.main,0)
    b=Rider();a=vehicle(riders=[b]);drive(a,b,40,roll=40,block=block,block_roll=60,safe_prefix=0)
    check('successful contested route',(a.position,block['ready']),(40,False))
    blocker=Rider(id='BLOCK');block=prepare_block(blocker)
    b=Rider();a=vehicle(riders=[b]);check('both fail no passage',drive(a,b,40,roll=60,block=block,block_roll=70,safe_prefix=0),(0,False))
    check('contest costs once',(b.main,blocker.main,a.power),(0,0,990))
    check('exact contest tie',contest(50,20,50,20),0)
    block={'target':50,'ready':False};b=Rider();a=vehicle(riders=[b]);snap=asdict(a)
    check('spent block cannot be reused',rejected(lambda:drive(a,b,40,roll=1,block=block,block_roll=80)),True)
    # Test all roll outcomes against fixed speed/energy caps, not differences times grids.
    roll_cases=0
    for model,t,mode,r in product(P['vehicles'],(10,30,50,70,95),('normal','fast'),range(1,101)):
        b=Rider(life=t);a=vehicle(model,riders=[b]);c=P['vehicles'][model]
        fast=mode=='fast';distance=c['fast_move_m' if fast else 'normal_move_m']
        moved,success=drive(a,b,distance,fast=fast,risk=True,roll=r)
        expected=distance if r<=t else (c['fast_failure_max_m'] if fast else 0)
        assert moved==expected and success==(r<=t)
        assert a.power==1000-(15 if fast else 10) and b.main==0 and b.move==0
        roll_cases+=1
    check('full declared percentile movement cases',roll_cases,2000)
    # Independently calculated three-round reader example and fuel arithmetic.
    d,pas=Rider(),Rider(id='B-R2');e=vehicle(riders=[d,pas]);pd=Rider(id='PUR');pur=vehicle(id='R-P',position=-20,riders=[pd])
    pd.position=-20;records=[]
    for r in (34,74,18):
        round_start(e);round_start(pur);drive(e,d,60,fast=True,roll=r);drive(pur,pd,40)
        records.append([e.position,pur.position,e.power])
    check('three round worksheet',records,[[60,20,985],[80,60,970],[140,100,955]])
    check('independent total fuel',e.power,1000-3*15)
    check('declared garage reaches exit',e.position>=120 and pur.position<120,True)
    check('contact does not automatically capture',P['pursuit']['contact_is_not_automatic_capture'],True)
    # Target/cover: the same attack must never damage two bodies by naming one vehicle.
    van=vehicle('ROAD-VAN-01');rider=Rider();van.riders=[rider]
    gunner=Body()
    check('closed cabin no direct rider shot',rejected(lambda:attack(gunner,rider,'카빈',roll=20,skill=50,distance=20,cover='full')),True)
    check('infeasible closed shot ammo intact',gunner.ammo,12)
    gunner=Body()
    check('open hatch partial cover same target',attack(gunner,rider,'카빈',roll=31,skill=50,distance=20,cover='partial',use_shield=False),('miss',0))
    check('hatch miss still spends ammo',gunner.ammo,11)
    gunner=Body()
    check('shoot vehicle not rider',attack(gunner,van,'카빈',roll=20,skill=50,distance=20,use_shield=False),('damage',4))
    check('no automatic transfer',(van.hp,rider.hp),(20,12))
    bike=vehicle();bike.hp=4;bike.riders=[Rider()]
    check('vehicle reaches zero',attack(Body(),bike,'권총',roll=1,distance=10,use_shield=False),('damage',4))
    check('vehicle zero not passenger damage',(bike.hp,bike.destroyed,bike.riders[0].hp),(0,False,12))
    check('HP0 cannot drive',rejected(lambda:drive(bike,bike.riders[0],40)),True)
    check('second positive hit destroys vehicle',attack(Body(),bike,'권총',roll=1,distance=10,use_shield=False),('damage',4))
    check('destroyed still not automatic explosion',(bike.destroyed,bike.riders[0].hp),(True,12))
    melee=Body();victim=Rider();a=vehicle(riders=[melee])
    check('melee at actual contact',attack(melee,victim,'동력 근접 도구',roll=1,skill=50,distance=1,use_shield=False),('damage',5))
    check('noncontact melee infeasible',rejected(lambda:attack(Body(),Rider(),'동력 근접 도구',distance=2)),True)
    # Cell swap conserves amounts and IDs; safe removal does not charge the old cell.
    a=vehicle(power=970);worker=Rider();reserve={'POWER-NEW':600}
    swap(a,worker,reserve,'POWER-NEW')
    check('swap IDs/amount',(a.power_id,a.power,reserve),('POWER-NEW',600,{'POWER-R1':970}))
    check('sum power conserved',a.power+sum(reserve.values()),1570)
    check('swap costs main',worker.main,0)
    a.moved=True;a.stopped=False;snap=(asdict(a),deepcopy(reserve))
    check('no swap while driving',rejected(lambda:swap(a,Rider(),reserve,'POWER-R1')),True)
    check('invalid swap unchanged',(asdict(a),reserve),snap)
    driver,passenger=Rider(),Rider(id='B-R2')
    a=vehicle(riders=[driver,passenger]);drive(a,driver,40,stop=True)
    check('moved but now stopped',(a.moved,a.stopped),(True,True))
    dismount(a,passenger,extra_walk=10)
    check('dismount includes paid extra walk',(passenger.position,passenger.main,passenger.move),(50,0,0))
    check('dismount no vehicle second movement',a.position,40)
    # Actual partial work + used part persist through interruption and do not restore fuel/body HP.
    a=vehicle(power=970);a.hp=0;parts={'PART-1','PART-2'};w=begin_repair(a,parts,'PART-1')
    check('part consumed on start',parts,{'PART-2'})
    check('first partial work',advance(a,w,120),False)
    check('no early heal',(a.hp,w.elapsed),(0,120))
    pause(a,w);check('paused time remains',w.elapsed,120);resume(a,w)
    check('remaining work completes',advance(a,w,180),True)
    check('HP0 repair and unchanged fuel',(a.hp,a.power,parts),(4,970,{'PART-2'}))
    check('same completed work no repeat',rejected(lambda:advance(a,w,0)),True)
    w2=begin_repair(a,parts,'PART-2');check('failed completion',advance(a,w2,300,safe=False,roll=80),False)
    check('failure consumes part/time no heal',(a.hp,a.power,parts,w2.elapsed),(4,970,set(),300))
    restored=0
    for start,model in product(range(25),P['vehicles']):
        maximum=P['vehicles'][model]['max_hp']
        if start>=maximum:continue
        a=vehicle(model);a.hp=start;parts={'PART'};w=begin_repair(a,parts,'PART');advance(a,w,300)
        assert a.hp==min(maximum,start+4) and a.power==1000 and not parts
        restored+=1
    check('bounded repair from all declared HP values',restored,40)
    a=vehicle();a.destroyed=True;a.hp=0
    check('destroyed not repaired by cheap part',rejected(lambda:begin_repair(a,{'PART'},'PART')),True)
    # Stored/active access is mutually exclusive and retains exactly one ID and all resource state.
    a=vehicle(power=970);a.hp=12;a.position=80
    check('unsupported storage rejected',rejected(lambda:store(a)),True)
    record=store(a,support=True)
    check('no duplicate record contains person skill','life' in record,False)
    driver=Rider(position=80);a.riders=[driver]
    check('stored cannot drive',rejected(lambda:drive(a,driver,40)),True)
    a.riders=[]
    check('stored cannot repair',rejected(lambda:begin_repair(a,{'PART'},'PART')),True)
    modified=deepcopy(record);modified['hp']=16;modified['power']=1000
    check('modified stored state rejected',rejected(lambda:restore(a,modified,support=True)),True)
    restore(a,record,support=True)
    check('saved HP/fuel/cargo not reset',(a.id,a.hp,a.power_id,a.power,a.cargo,a.position),('R-B1',12,'POWER-R1',970,{'BOX-R1':20000},80))
    check('same stored record cannot restore twice',rejected(lambda:restore(a,record,support=True)),True)
    next_driver=Rider(life=30,position=80);a.riders=[next_driver]
    check('new driver uses own skill',drive(a,next_driver,60,fast=True,roll=34),(20,False))
    check('vehicle data has no old driver ability',next_driver.life,30)
    check('Kiwa not universal import',P['storage']['Kiwa_cross_dimension_allowed'],False)
    files=[HERE/'운송_프로필.json',Path(__file__),HERE.parent/'10_CoreRulebook.md',HERE.parent/'11_WorldLorebook.md',HERE.parent/'12_룰시트와캐릭터시트.md',HERE/'입문_프로필.json',HERE/'일반플레이_검증.py',HERE/'백분율_코어검증.py']
    return {**run_vessels(),**run_vessel_handover(),'date':'2026-10-06','profile':P['id'],'checks_passed':len(checks),'checks':checks,
        'feasibility_cases':matrix,'movement_roll_cases':roll_cases,'repair_HP_cases':restored,
        'three_round_positions_power':records,'scope':'두 NEW 도로 차량의 제한된 워크시트 상태/행동/동력/공통 공격 대응 검산',
        'actual_participant_playtest':False,'full_transport_or_vehicle_IO_verified':False,
        'production_VTT_implementation':False,'all_vehicle_physics_and_balance_verified':False,
        'limits':['도로 차량 두 규격과 신규 연락선/작업비행선 두 규격만 검사한다. 전설적 함선·전 항공/잠수·완전한 차량 IO는 별도다.',
            '추격의 도로 분기/관측/거점 권한과 차단 예약의 만료는 장면 담당자가 실제 지도/IC순서에 따라 확인해야 한다.',
            '실제 참가자의 선택·운전/탑승 역할 체감·비동기 처리/재미·최고속도 물리를 입증하지 않는다.'],
        'artifacts_sha256':{str(f.relative_to(HERE.parent)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}

if __name__=='__main__':
    result=run()
    (HERE/'운송_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['checks_passed','feasibility_cases','movement_roll_cases','repair_HP_cases','actual_participant_playtest']},ensure_ascii=False))
