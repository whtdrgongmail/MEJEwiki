from pathlib import Path
from dataclasses import dataclass,field
from fractions import Fraction
from copy import deepcopy
from itertools import product
import json,hashlib
from 백분율_코어검증 import grade
from 일반플레이_검증 import Body,recover
here=Path(__file__).resolve().parent;o=here.parent;p=o.parent
profile=json.loads((here/'시간이동_프로필.json').read_text());train=profile['train'];walk=profile['walk']

@dataclass
class Traveler:
    body:Body=field(default_factory=lambda:Body(hp=10,ammo=7,recovery_window=0))
    original:Body=field(default_factory=lambda:Body(hp=9,ammo=3))
    skills:dict=field(default_factory=lambda:{'공학':50,'생활':70})
    ego:Fraction=Fraction(6)
    seconds:int=0
    body_age_seconds:int=730000000
    location:str='D0'
    route:str='RETURN-T1'
    tickets:int=2
    credits:int=10
    goods:dict=field(default_factory=dict)
    events:set=field(default_factory=set)
    history:list=field(default_factory=list)
    bans:list=field(default_factory=lambda:['WORLD-OLD'])
    interaction:bool=True
    tool:bool=True
    tool_calibrated:bool=True
    stored:bool=False
    branch_choice:bool=False

    def can_act(self):return not self.stored and self.body.hp>0 and not self.body.destroyed and self.ego>0
    def advance(self,seconds,rate=Fraction(0),OOC=False):
        if type(seconds) is not int or seconds<0 or rate<0:raise ValueError('invalid interval')
        if OOC:return
        if self.ego<rate*Fraction(seconds,3600):raise ValueError('specified route requires support before full interval')
        self.seconds+=seconds;self.body_age_seconds+=seconds;self.ego-=rate*Fraction(seconds,3600)
    def rail(self,event,returning=False,route_open=True,admission=True):
        expected='D-1' if returning else 'D0'
        if not event or event in self.events or not self.can_act() or not route_open or not admission or self.tickets<1 or self.location!=expected:raise ValueError('rail prerequisites')
        if returning and self.branch_choice and self.route!='RETURN-T1B':raise ValueError('old return route lost')
        self.tickets-=train['tickets'];self.events.add(event);self.advance(train['seconds'])
        self.location='D0B' if returning and self.branch_choice else 'D0' if returning else 'D-1'
        self.history.append({'event':event,'arrival':self.location,'elapsed':self.seconds,'body':id(self.body)})
    def buy(self,event,part='PART-T1'):
        if not event or event in self.events or not self.can_act() or self.location!='D-1' or self.credits<3 or part in self.goods:raise ValueError('purchase prerequisites')
        self.events.add(event);self.credits-=3;self.advance(900);self.goods[part]={'purchase':event,'date':'D-1','count':1}
    def step(self,event,roll,residence=Fraction(0)):
        if type(roll) is not int or not 1<=roll<=100:raise ValueError('invalid common roll')
        rate=max(Fraction(walk['ego_loss_per_hour_with_calibrated_tool']) if self.tool_calibrated else Fraction(walk['ego_loss_per_hour_unprotected']),residence)
        if not event or event in self.events or not self.can_act() or not self.interaction or not self.tool or self.location!='D0' or self.body.main<1 or self.ego<rate*Fraction(walk['setup_seconds']+walk['seconds'],3600):raise ValueError('actual function/tool/action/support required')
        self.body.main-=1;self.events.add(event);self.advance(walk['setup_seconds'],rate)
        ok=grade(self.skills['공학'],roll)>0
        if ok:self.advance(walk['seconds'],rate);self.location='D-1'
        self.history.append({'event':event,'success':ok,'elapsed':self.seconds})
        return ok
    def change_choice(self,event):
        if not event or event in self.events or self.location!='D-1' or not self.can_act() or self.branch_choice:raise ValueError('actual new declared choice required')
        self.events.add(event);self.branch_choice=True;self.route='RETURN-T1B'
        self.history.append({'event':event,'cause':profile['causal_event']['trigger'],'route':self.route})

def run():
    checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    def rejects_without_change(t,action):
        before=deepcopy(t)
        try:action()
        except ValueError:return t==before
        return False
    t=Traveler();body=t.body;original=deepcopy(t.original);age=t.body_age_seconds
    t.rail('R1');t.buy('BUY1');t.rail('R2',returning=True)
    check('왕복4500초/표2장/부품1개/대금1회',t.seconds==4500 and t.body_age_seconds==age+4500 and t.tickets==0 and t.credits==7 and len(t.goods)==1)
    check('도착날짜는몸상태스냅샷아님',t.location=='D0' and t.body is body and t.body.hp==10 and t.body.ammo==7 and t.body.charges==2 and t.body.recovery_window==0 and t.ego==6)
    check('같은인물숙련/본체/차원금지유지',t.original==original and t.skills=={'공학':50,'생활':70} and t.bans==['WORLD-OLD'])
    check('달력귀환으로같은회복창을재사용하지않음',not recover(t.body,t.seconds//86400) and t.body.hp==10)
    before=deepcopy(t);t.advance(604800,OOC=True);check('게시일주일대기는몸시간/에고/회복창에0',t==before)
    check('귀환후같은구입사건/물품재발급없음',rejects_without_change(t,lambda:t.buy('BUY1')))
    conditions=0
    for hp,stored,tickets,open_route,admission in product((0,10),(False,True),(0,2),(False,True),(False,True)):
        z=Traveler();z.body.hp=hp;z.stored=stored;z.tickets=tickets;before=deepcopy(z)
        valid=hp>0 and not stored and tickets>0 and open_route and admission
        try:z.rail('ENTRY',route_open=open_route,admission=admission);ok=True
        except ValueError:ok=False
        assert ok==valid
        if not valid:assert z==before
        conditions+=1
    check('32개철도접근/입장경계에서불가능시무변경',conditions==32)
    z=Traveler();z.rail('R1');check('같은승차사건은재소비/복제없음',rejects_without_change(z,lambda:z.rail('R1')))
    z=Traveler();z.rail('R1');z.buy('BUY1');snapshot=deepcopy(z);other_PC={'memory':['약속'],'choice':'원래선택','goods':['OTHER-PART']};others=deepcopy(other_PC)
    z.change_choice('POST-X1');z.route='RETURN-T1'
    check('바뀐과거의구귀환경로는이장면에서불가',rejects_without_change(z,lambda:z.rail('R2',returning=True)))
    z.route='RETURN-T1B';z.rail('R2',returning=True)
    check('실제다른경로귀환/현재자원과이력보존',z.location=='D0B' and z.goods==snapshot.goods and z.credits==snapshot.credits and len(z.events)==4 and z.ego==6)
    check('다른PC기억/선택/물건과드랍아웃자동변경없음',other_PC==others and z.bans==snapshot.bans and z.original==snapshot.original)
    z=Traveler();check('과거현지아닌선택은보상/분기없음',rejects_without_change(z,lambda:z.change_choice('POST-X1')))
    z=Traveler();z.step('STEP1',31)
    check('도보305초지원율정확61/1440소모',z.seconds==305 and z.ego==Fraction(8579,1440) and z.location=='D-1' and z.body.main==0)
    check('시간도보몸/HP/본체/물품/인물스킬불변',z.body.hp==10 and z.body.ammo==7 and z.original.hp==9 and z.skills['공학']==50 and not z.goods)
    z=Traveler();z.step('STEP1',71)
    check('도보준비실패5초와해당부담/행동만확정',z.location=='D0' and z.seconds==5 and z.ego==6-Fraction(1,1440) and z.body.main==0)
    check('실패후같은행동/사건자동재굴림없음',rejects_without_change(z,lambda:z.step('STEP1',31)))
    prereqs=0
    for function,tool,active,alive,action,ego in product((False,True),repeat=6):
        z=Traveler();z.interaction=function;z.tool=tool;z.stored=not active;z.body.hp=10 if alive else 0;z.body.main=int(action);z.ego=Fraction(6 if ego else 0);before=deepcopy(z)
        valid=all((function,tool,active,alive,action,ego))
        try:z.step('S',31);ok=True
        except ValueError:ok=False
        assert ok==valid
        if not valid:assert z==before
        prereqs+=1
    check('64개기능/도구/몸/행동/지원조건공학만으로대체못함',prereqs==64)
    for bad in (0,101,1.5,True,'31'):
        z=Traveler();assert rejects_without_change(z,lambda:z.step('S',bad))
    check('백분율범위와정수형검증통합',True)
    z=Traveler();z.ego=Fraction(1,1000);check('불충분존재지원은출발전계획수정무소비',rejects_without_change(z,lambda:z.step('S',31)))
    successes=0
    for r in range(1,101):
        z=Traveler();ok=z.step('S',r);assert ok==(r<=50)
        assert z.seconds==(305 if ok else 5)
        assert z.ego==6-Fraction(z.seconds,7200)
        successes+=ok
    check('공통공학50실제d100전수50성공50실패',successes==50)
    z=Traveler();z.tool_calibrated=False;z.step('S',31)
    check('같은도구미보정은지정존재보호없음',z.ego==6-Fraction(305,3600))
    rate_cases=0
    for residence in (Fraction(0),Fraction(1,10),Fraction(1,2),Fraction(3,4),Fraction(1),Fraction(2)):
        z=Traveler();z.step('S',31,residence);assert z.ego==6-max(Fraction(1,2),residence)*Fraction(305,3600)
        rate_cases+=1
    check('같은구간도보/체류율은최대하나로만소모',rate_cases==6)
    splits=0
    for cut in range(0,306):
        z=Traveler();z.advance(cut,Fraction(1,2));z.advance(604800,OOC=True);z.advance(305-cut,Fraction(1,2))
        assert z.seconds==305 and z.ego==Fraction(8579,1440)
        splits+=1
    check('306개분할에서시간/에고분수누적같음',splits==306)
    z=Traveler();z.advance(1800,Fraction(1,2));z.advance(1800,Fraction(1));check('서로다른구간은각각누적',z.seconds==3600 and z.ego==Fraction(21,4))
    z=Traveler();z.advance(43200,Fraction(1,2));check('에고0존재유지중단은몸HP/금지와별개',z.ego==0 and not z.can_act() and z.body.hp==10 and z.bans==['WORLD-OLD'])
    check('에고0은정상승차시무료존재복원아님',rejects_without_change(z,lambda:z.rail('R')))
    for invalid in (-1,True,1.5):
        z=Traveler();assert rejects_without_change(z,lambda:z.advance(invalid))
    check('음수/비정수몸경과는적용하지않음',True)
    core=(o/'10_CoreRulebook.md').read_text();sheet=(o/'12_룰시트와캐릭터시트.md').read_text();world=(o/'11_WorldLorebook.md').read_text()
    check('본문에같은도보/철도예시와정확시간/존재수치',all(x in core for x in ['FEWK-TIME-01','61/1440','8579/1440','75분','TIME-PATH-T1']) and '8579/1440' in sheet)
    check('세계근거의단위/작자/경계출처지위정정',all(x in world for x in ['금손 용하선생','自起曆','집단 지성의 존재 단위','시간여행 항목은 미래 경계를 사건 월풍','실제 사용자 발언 원문까지 확보한 것은 아닙니다']))
    ledger=json.loads((here/'제5판_이관검수.json').read_text());sources={}
    for i in profile['source_indices']:
        e=ledger['files'][i];assert e['semantic_review']=='focused_review' and e['whole_document_read'] is True
        sources[e['source']]=hashlib.sha256((p/e['source']).read_bytes()).hexdigest();assert sources[e['source']]==e['observed_sha256']
    for e in ledger['time_travel_topic_sources']:
        sources[e['path']]=hashlib.sha256((p/e['path']).read_bytes()).hexdigest();assert sources[e['path']]==e['sha256']
    check('시간4개참고본문과주제원전/구판의실제해시일치',len(sources)==7)
    names=['10_CoreRulebook.md','11_WorldLorebook.md','12_룰시트와캐릭터시트.md','검증/시간이동_프로필.json','검증/시간이동_검증.py','검증/백분율_코어검증.py','검증/일반플레이_검증.py','검증/입문_프로필.json']
    artifacts={n:hashlib.sha256((o/n).read_bytes()).hexdigest() for n in names}
    return {'date':'2026-10-05','profile':profile['id'],'checks_passed':len(checks),'checks':checks,'rail_prerequisite_cases':conditions,'walk_prerequisite_cases':prereqs,'percentile_outcomes':100,'split_elapsed_time_cases':splits,'concurrent_rate_cases':rate_cases,'source_sha256':sources,'artifacts_sha256':artifacts,'scope':'명시한NEW철도왕복/지원도보/귀환경로변경 예의 실제 몸/인물·표/물품/에고/누적시간 경계만. 모든 시간 물리/전설/토템·자유여행/역사개변/일반상대성/실제참가자·커뮤·전체전투균형 검증 아님.','all_time_physics_and_related_novels_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}

if __name__=='__main__':
    r=run();Path(__file__).with_name('시간이동_검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['profile','checks_passed','rail_prerequisite_cases','walk_prerequisite_cases','percentile_outcomes','split_elapsed_time_cases','actual_participant_playtest']},ensure_ascii=False))
