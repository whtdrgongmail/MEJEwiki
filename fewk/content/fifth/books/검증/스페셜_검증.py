#!/usr/bin/env python3
"""Explicit special-profile math/state evidence. No participant or canon-wide validation."""
from pathlib import Path
from fractions import Fraction as F
from dataclasses import dataclass,field
from copy import deepcopy
import json,hashlib
from 백분율_코어검증 import grade
HERE=Path(__file__).parent
P=json.loads((HERE/'스페셜_프로필.json').read_text())
H={k:F(v) for k,v in P['layer_full_capacity_hours'].items()}

def cost(hours,layer,mode):
    hours=F(hours)
    if hours<0:raise ValueError('negative time')
    if layer=='material' or mode=='settled':return F(0)
    if layer not in H or mode not in P['modes']:raise ValueError('unsupported profile')
    return F(P['ego_max'])*P['modes'][mode]*hours/H[layer]

def spend(ego,value):return max(F(0),F(ego)-F(value))
def chain_cost(root_hours,nodes):
    # Each node gives H and local hours per common-clock hour.
    return max((cost(F(root_hours)*F(ratio),layer,'flyer') for layer,ratio in nodes),default=F(0))

@dataclass
class Stay:
    ego:F=F(10)
    last_method:str=''
    repetition:int=0
    methods:dict=field(default_factory=dict)
    def activity(self,method,layer,mode,success=True):
        if self.ego==0:raise ValueError('ordinary boost unavailable')
        self.ego=spend(self.ego,cost(1,layer,mode))
        if self.ego==0:return False
        if not success:return False
        self.methods[method]=self.methods.get(method,0)+1
        self.repetition=self.methods[method]
        self.last_method=method
        gain=F(P['support']['same_method_uses_gains'][min(self.repetition,3)-1])
        self.ego=min(F(10),self.ego+gain)
        return True
    def material(self,hours):
        if F(hours)<0:raise ValueError('negative time')
        if self.ego==0:return False
        self.ego=min(F(10),self.ego+F(hours))
        if self.ego==10:self.last_method='';self.repetition=0;self.methods={}
        return True
    def restore(self,resources,link=True,success=True):
        if self.ego!=0 or resources<1 or not link:raise ValueError('restoration conditions absent')
        resources-=1
        if success:self.ego=F(1)
        return resources

@dataclass
class Traveller:
    active:str='B2'
    ego:F=F(10)
    skill:int=70
    bodies:dict=field(default_factory=lambda:{
        'B0':{'realm':'material','hp':12,'items':['receiver']},
        'B1':{'realm':'A','hp':9,'items':['relay']},
        'B2':{'realm':'B','hp':12,'items':['file']}})
    links:dict=field(default_factory=lambda:{'L1':{'parent':'B0','child':'B1','open':True},'L2':{'parent':'B1','child':'B2','open':True}})
    banned:set=field(default_factory=set)
    stored:dict=field(default_factory=dict)
    def back(self,parent,assisted=False):
        child=self.active
        if self.bodies[child]['hp']==0 and not assisted:raise ValueError('incapacitated body needs support')
        link=next((x for x in self.links.values() if x['parent']==parent and x['child']==child),None)
        if not link or not link['open']:raise ValueError('unsupported or broken return')
        if self.bodies[parent]['realm'] in self.banned:raise ValueError('realm re-entry banned')
        if self.ego==0:raise ValueError('restoration required')
        self.stored[child]=deepcopy(self.bodies[child]);self.active=parent
    def direct(self,pack,approved):
        if pack<1 or not approved:raise ValueError('unprepared direct return')
        if self.ego==0:raise ValueError('restoration required')
        self.stored[self.active]=deepcopy(self.bodies[self.active]);self.active='B0'
        return pack-1
    def can_reenter(self,realm):return realm not in self.banned

def pioneer(body,entry,success):
    if entry<1:raise ValueError('no entry device')
    entry-=1
    if success:body['realm']='NEW'
    return entry

def charted(coordinates,localization,return_record,received,reviewed):
    return all((coordinates,localization,return_record,received,reviewed))

def detonate(tr,device,success,export_received,return_open):
    # SPL-DROP-TEST is a local-terminal operation by an active, capable local body.
    # A remote controller needs a separately declared profile, not this shortcut.
    local=tr.active
    if local not in tr.bodies:raise ValueError('no active local operator')
    body=tr.bodies[local]
    if body['realm']=='material' or body.get('destroyed') or body['hp']<=0:
        raise ValueError('local terminal operation conditions absent')
    if device<1:raise ValueError('no device')
    if not export_received:raise ValueError('trial export requirement absent')
    device-=1
    if not success:return device,'failed_before_activation'
    tr.bodies[local]['hp']=0;tr.bodies[local]['items']=[];tr.bodies[local]['destroyed']=True
    tr.banned.add(tr.bodies[local]['realm'])
    tr.active='B0' if return_open else ''
    return device,'returned' if return_open else 'rescue_required'

def rejects(fn):
    try:fn()
    except ValueError:return True
    return False

def frac(x):return {'numerator':x.numerator,'denominator':x.denominator,'display':round(float(x),2)}

def run():
    cases=[]
    def check(name,truth):
        assert truth,name
        cases.append(name)
    check('물질계 시간 감소 없음',cost(2400,'material','runner')==0)
    check('조건을 충족한 현지 정착 시간 감소 없음',cost(2400,'lower1','settled')==0)
    for layer,h in H.items():
        check(layer+' 워커 전체 한계',cost(h,layer,'walker')==10)
        check(layer+' 러너 절반 시간 한계',cost(h/2,layer,'runner')==10)
        check(layer+' 플라이어1/3시간 한계',cost(h/3,layer,'flyer')==10)
        for ratio in [F(1,100),F(1,7),F(1,3),F(2,3),F(7,11)]:
            assert cost(h*ratio,layer,'runner')+cost(h*(1-ratio),layer,'runner')==cost(h,layer,'runner')
    a=cost(24,'lower1','runner');b=cost(2,'lower2','runner');left=spend(10,a+b)
    check('본문24시간+2시간 예시 정확값',a==F(1,5) and b==F(1,6) and left==F(289,30))
    check('분할 로그 소수 소모 보존',sum(cost(F(1,60),'lower1','runner') for _ in range(1440))==a)
    check('매 로그 최소1 강제 아님',cost(F(1,60),'lower1','runner')==F(1,7200))
    check('HP/능력치와 독립한 체류',cost(8,'lower3','flyer')==10)
    check('초과 경과에도 음수 에고 없음',spend(10,cost(9,'lower3','flyer'))==0)
    check('지원 안 된 계층 자동 추정 안 함',rejects(lambda:cost(1,'lower6','runner')))
    check('음수 시간 반전 회복 안 함',rejects(lambda:cost(-1,'lower1','runner')))
    chain=chain_cost(2,[('lower1',1),('lower2',1)])
    check('본문 플라잉2시간 최대값 한 번',chain==F(1,4) and chain<F(1,4)+F(1,40))
    check('서로 다른 현지 시간 환산 후 최대',chain_cost(2,[('lower1',10),('lower2',1)])==F(1,4))
    check('빠른 중간계가 최대 부담일 수 있음',chain_cost(2,[('lower1',20),('lower2',1)])==F(1,2))
    whole=chain_cost(7,[('lower1',1),('lower2',1)])
    split=chain_cost(2,[('lower1',1),('lower2',1)])+chain_cost(5,[('lower1',1),('lower2',1)])
    check('고정 조건 플라잉 구간 분할 불변',whole==split)
    # Changing clock ratios switches the bottleneck. Max must be per segment.
    segments=chain_cost(1,[('lower1',10),('lower2',1)])+chain_cost(1,[('lower1',1),('lower2',10)])
    collapsed=max(cost(11,'lower1','flyer'),cost(11,'lower2','flyer'))
    check('시간 변화 경계별 계산 보존',segments==F(11,8) and collapsed==F(11,8))
    crossing=chain_cost(1,[('lower1',20),('lower2',1)])+chain_cost(1,[('lower1',1),('lower2',2)])
    collapsed=max(cost(21,'lower1','flyer'),cost(3,'lower2','flyer'))
    check('경계 전후 최대를 전체 합의 최대와 혼동 안 함',crossing==F(1,2) and collapsed==F(3,8))
    s=Stay(F(5));s.activity('공방 작업','material','runner');s.activity('공방 작업','material','runner');s.activity('공방 작업','material','runner')
    check('같은 지원 반복2/1/0',s.ego==8 and s.repetition==3)
    s.activity('동료 의례','material','runner')
    check('실제 새 원천의 반복 단계',s.ego==10 and s.repetition==1)
    s=Stay(F(1))
    for method in ['A','B']*4:s.activity(method,'lower2','runner')
    check('지원교대는원천별내성초기화않음',s.methods=={'A':4,'B':4} and s.ego==F(19,3))
    check('회복음수시간허용않음',rejects(lambda:s.material(-1)))
    s=Stay(F(5));s.activity('공방 작업','lower2','runner')
    check('지원 시간의 실제 체류 먼저 차감',s.ego==F(83,12))
    s=Stay(F(1));done=s.activity('공방 작업','lower4','runner')
    check('종료 전에0이면 일반 부스팅 실패',not done and s.ego==0 and s.repetition==0)
    check('에고0 자동 물질계 충전 없음',not s.material(10) and s.ego==0)
    check('에고0 일반 부스팅 없음',rejects(lambda:s.activity('의례','material','runner')))
    check('연결 없는 외부 복원 불가',rejects(lambda:s.restore(1,False)))
    resources=s.restore(1)
    check('복원은 자원1·에고1',resources==0 and s.ego==1)
    s.material(9)
    check('정상 물질계 회복은 최대/내성 해제',s.ego==10 and s.last_method=='' and s.repetition==0 and s.methods=={})
    s=Stay(F(5));s.activity('경연','lower2','runner',False)
    check('지원 판정 실패는 시간 결과만 남음',s.ego==F(59,12) and s.repetition==0)
    tr=Traveller(ego=F(39,4));tr.back('B1')
    check('L2귀환은 중간HP와 에고 유지',tr.active=='B1' and tr.bodies['B1']['hp']==9 and tr.ego==F(39,4))
    tr.back('B0')
    check('두 링크 정상 역순 귀환',tr.active=='B0' and tr.bodies['B0']['hp']==12 and tr.stored['B1']['hp']==9 and tr.stored['B2']['items']==['file'])
    tr=Traveller()
    check('별도경로 없는 조상 귀환 건너뛰기 금지',rejects(lambda:tr.back('B0')) and tr.active=='B2')
    tr.links['L2']['open']=False
    check('끊긴L2로 정상 귀환 불가',rejects(lambda:tr.back('B1')) and tr.bodies['B0']['hp']==12)
    check('준비하지 않은 직접 귀환 금지',rejects(lambda:tr.direct(1,False)))
    pack=tr.direct(1,True)
    check('실제 승인/자원 직접 경로',pack==0 and tr.active=='B0')
    tr=Traveller();tr.links['L1']['open']=False;tr.back('B1')
    check('L1단절은B1귀환 후 실제 장애',rejects(lambda:tr.back('B0')) and tr.active=='B1' and tr.bodies['B0']['hp']==12)
    tr=Traveller();tr.bodies['B1']['hp']=0;tr.back('B1')
    check('손상된중간몸귀환시HP0유지',tr.active=='B1' and tr.bodies['B1']['hp']==0)
    check('HP0중간몸직접단말조작없음',rejects(lambda:tr.back('B0')))
    tr.back('B0',assisted=True)
    check('명시구조지원은HP완치없이귀환',tr.active=='B0' and tr.stored['B1']['hp']==0)
    tr=Traveller();tr.banned.add('A')
    check('중간계금지는그곳재현지화차단',rejects(lambda:tr.back('B1')) and tr.can_reenter('B'))
    check('동일IO다른차원도일괄금지아님',tr.can_reenter('A-SIBLING'))
    tr=Traveller(ego=F(0));hp=deepcopy(tr.bodies)
    check('에고0은무료귀환아님',rejects(lambda:tr.back('B1')) and tr.bodies==hp and not tr.banned)
    check('에고0은본체/현지HP변경아님',tr.bodies['B0']['hp']==12 and tr.bodies['B2']['hp']==12)
    body={'id':'B-PIO','realm':'material','hp':9,'items':['record']};start=deepcopy(body)
    n=pioneer(body,1,False)
    check('개척실패출발자원소모·동일몸위치유지',n==0 and body==start)
    n=pioneer(body,1,True)
    check('개척전신이동은동일ID/HP/물품',n==0 and body['id']=='B-PIO' and body['realm']=='NEW' and body['hp']==9 and body['items']==['record'])
    check('도착만으로IO등록아님',not charted(True,False,False,False,False))
    check('자료수신만으로IO등록아님',not charted(True,True,True,True,False))
    check('검증범위충족한IO만등록',charted(True,True,True,True,True))
    for missing in range(5):
        args=[True]*5;args[missing]=False;assert not charted(*args)
    tr=Traveller();before=deepcopy(tr.bodies)
    n,result=detonate(tr,1,False,True,True)
    check('작동전실패는장치소모·금지/소실없음',n==0 and result=='failed_before_activation' and tr.bodies==before and not tr.banned)
    tr=Traveller();before=deepcopy(tr.bodies)
    check('사전반출안된시험결행금지',rejects(lambda:detonate(tr,1,True,False,True)) and tr.bodies==before)
    n,result=detonate(tr,1,True,True,True)
    check('결행성공은현지몸/장비소실·해당계금지',n==0 and tr.bodies['B2']['destroyed'] and not tr.bodies['B2']['items'] and tr.banned=={'B'})
    check('독립귀환확보시본체손상없이복귀',result=='returned' and tr.active=='B0' and tr.bodies['B0']['hp']==12 and tr.ego==10 and tr.skill==70)
    check('다른몸/시트가같은인물금지를해제않음',not tr.can_reenter('B') and tr.can_reenter('A'))
    tr=Traveller();n,result=detonate(tr,1,True,True,False)
    check('귀환경로고장은자동귀환없음',result=='rescue_required' and tr.active=='' and tr.bodies['B0']['hp']==12)
    dropout_extended_start=len(cases)
    tr=Traveller(active='');before=deepcopy(tr.bodies)
    check('결행 몸 없음은 현지 단말 작동 불가',rejects(lambda:detonate(tr,1,True,True,True)) and tr.bodies==before and not tr.banned)
    tr=Traveller(active='B0');before=deepcopy(tr.bodies)
    check('물질계 본체에서 현지 자폭 재실행 불가',rejects(lambda:detonate(tr,1,True,True,True)) and tr.bodies==before and not tr.banned)
    tr=Traveller();tr.bodies['B2']['hp']=0;tr.bodies['B2']['destroyed']=True;before=deepcopy(tr.bodies)
    check('이미 소실된 현지 몸의 결행 불가',rejects(lambda:detonate(tr,1,True,True,True)) and tr.bodies==before and not tr.banned)
    tr=Traveller();tr.bodies['B2']['hp']=0;before=deepcopy(tr.bodies)
    check('행동 불능 현지 몸의 직접 단말 결행 불가',rejects(lambda:detonate(tr,1,True,True,True)) and tr.bodies==before and not tr.banned)
    def prepared_wounded():
        tr=Traveller();tr.bodies['B0']['hp']=9;tr.bodies['B2']['hp']=4
        tr.bodies['B3']={'realm':'B','hp':7,'items':['stored_tool']}
        tr.stored['B3']=deepcopy(tr.bodies['B3']);tr.banned.add('A')
        return tr
    tr=prepared_wounded();stored=deepcopy(tr.stored)
    n,result=detonate(tr,1,True,True,True)
    check('부상한 본체HP9는 자폭 귀환 뒤에도9',n==0 and result=='returned' and tr.active=='B0' and tr.bodies['B0']['hp']==9 and tr.skill==70)
    check('폭발 대상 밖의 저장 몸과 공구는 보존',tr.stored==stored and tr.bodies['B3']==stored['B3'] and tr.stored['B3']['hp']==7)
    check('이전 금지와 새 금지는 인물에 함께 유지',tr.banned=={'A','B'} and not tr.can_reenter('B') and tr.can_reenter('C'))
    before=deepcopy(tr.bodies)
    check('성공 귀환 뒤 새 장치로 같은 결행 반복 불가',rejects(lambda:detonate(tr,1,True,True,True)) and tr.bodies==before and tr.banned=={'A','B'})
    tr=prepared_wounded();before=deepcopy(tr.bodies);stored=deepcopy(tr.stored)
    n,result=detonate(tr,1,False,True,True)
    check('작동 전 실패는 부상과 보관/기존 금지 유지',n==0 and result=='failed_before_activation' and tr.active=='B2' and tr.bodies==before and tr.stored==stored and tr.banned=={'A'})
    tr=prepared_wounded();n,result=detonate(tr,1,True,True,False)
    check('귀환 경로 고장도 본체HP9와 저장 몸7 보존',n==0 and result=='rescue_required' and tr.active=='' and tr.bodies['B0']['hp']==9 and tr.bodies['B3']['hp']==7 and tr.banned=={'A','B'})
    before=deepcopy(tr.bodies)
    check('구조 대기 상태는 자동 새 결행/귀환 불가',rejects(lambda:detonate(tr,1,True,True,True)) and tr.bodies==before and tr.active=='')
    dropout_campaign_checks=len(cases)-dropout_extended_start
    files=[HERE.parent/x for x in ['10_CoreRulebook.md','11_WorldLorebook.md','12_룰시트와캐릭터시트.md','01_텀블벅_이지룰_초안.md']]+[HERE/'스페셜_프로필.json',Path(__file__)]
    return {'date':'2026-10-05','profile':'SPL-RES-01 / SPL-PIO-TEST / SPL-FLY-TEST / SPL-DROP-TEST','checks_passed':len(cases),'cases':cases,'dropout_campaign_checks':dropout_campaign_checks,'dropout_campaign_scope':'SPL-DROP-TEST의 직접 현지 결행·부상한 본체·범위 밖 저장 자산·기존 금지와 실패/귀환 경계. 원격 결행이나 모든 드랍아웃/폭발 규격의 검증은 아님.',
        'exact_examples':{'runner_24h_plus_2h':frac(left),'flying_2h_debit':frac(chain),'flying_2h_remaining':frac(F(10)-chain),'changing_bottleneck_segments':frac(crossing),'wrong_collapsed_bottleneck':frac(collapsed)},
        'artifacts_sha256':{str(f.relative_to(HERE.parent)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
        'actual_participant_playtest':False,'all_world_profiles_verified':False,
        'limits':['명시된 시험 수단·체류H·에고/링크/반출 조건의 계산과 상태 검증이다.','원전의 모든 기술/차원/인물·현화/시간역행·제조/상용 가격을 검증한 것이 아니다.','참가자 이해·실시간/비동기 진행·지원 활동 체감과 FEWK 정서는 실제 검증이 필요하다.']}

if __name__=='__main__':
    result=run()
    (HERE/'스페셜_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'checks_passed':result['checks_passed'],'exact_examples':result['exact_examples'],'real_playtest':False},ensure_ascii=False))
