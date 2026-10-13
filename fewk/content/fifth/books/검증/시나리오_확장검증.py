from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from itertools import product
from copy import deepcopy
import json,hashlib,re
from 일반플레이_검증 import Body,move,new_round,attack
from 스페셜_검증 import cost
from 장면운영_검증 import Scene,start_event,put,snapshot
from 진행자_검증 import Case
from 팀지원_검증 import Sender

here=Path(__file__).resolve().parent;o=here.parent;p=o.parent
profile=json.loads((here/'시나리오_확장프로필.json').read_text())
ledger=json.loads((here/'제5판_이관검수.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()

def tables(text):
    """실제 Markdown의 첫 열 d100/d20 표만 추출한다. 서술의 효과는 실행하지 않는다."""
    found=[];active=None
    for line in text.splitlines():
        if not line.lstrip().startswith('|'):
            active=None;continue
        cells=[x.strip() for x in line.strip().strip('|').split('|')]
        if cells[0] in ('d100','d20'):
            active={'die':int(cells[0][1:]),'ranges':[]};found.append(active);continue
        if active is None or re.fullmatch(r'[:\-\s]+',cells[0]):continue
        m=re.fullmatch(r'(\d+)(?:[~\-](\d+))?',cells[0])
        if not m:raise ValueError('unsupported table row: '+line)
        lo=int(m[1]);hi=int(m[2] or m[1])
        if active['die']==100:
            if lo==0:lo=100
            if hi==0:hi=100
        if not 1<=lo<=hi<=active['die']:raise ValueError('invalid die bounds')
        active['ranges'].append((lo,hi))
    return found

def run():
    checks=[]
    def check(name,a,b):assert a==b,(name,a,b);checks.append(name)
    def reject(name,obj,fn):
        before=deepcopy(obj)
        try:fn()
        except ValueError:pass
        else:raise AssertionError(name+' accepted')
        check(name+' preserves state',obj,before)
    check('same common engine',profile['engine'],'P-FEWK-0.2')
    check('no universal new stats',profile['new_universal_stats'],[])
    story=(o/'13_입문시나리오.md').read_text()
    identity=json.loads((here/'이전설계_통합검토.json').read_text())['intro_identity_evidence_review']
    prior=identity['prior_intro_v04']['text'];sep='## 다음 장면을 위한 시나리오 도구'
    check('archived v04 text integrity',hashlib.sha256(prior.encode()).hexdigest(),identity['prior_intro_v04']['text_sha256'])
    old=prior.split(sep,1)[0].replace('초안 v0.4','초안 v0.2',1).replace('<a id="fewk-intro"></a>\n\n','')
    check('historical v04 main story prefix retained v02',hashlib.sha256(old.encode()).hexdigest(),profile['prior_intro_text_sha256'])
    finalization=json.loads((here/'러너와튜터리얼_대조.json').read_text())
    frozen=json.loads((here/'이전/독자편집전_20261007.json').read_text())
    previous=next(x for x in frozen['files'] if x['path']=='13_입문시나리오.md')
    check('frozen pre-edit main retains reviewed identity scope',hashlib.sha256(previous['text'].split(sep,1)[0].encode()).hexdigest(),identity['current_intro_main_text_sha256'])
    check('historical scenario tools appendix integrity',previous['text'].split(sep,1)[1],prior.split(sep,1)[1])
    check('current main story has reviewed editorial changes',hashlib.sha256(story.split(sep,1)[0].encode()).hexdigest(),finalization['intro_main_text_sha256'])
    check('current scenario tools has reviewed S1 card contract',hashlib.sha256(story.split(sep,1)[1].encode()).hexdigest(),finalization['intro_scenario_tools_text_sha256'])
    texts={i:(p/ledger['files'][i]['source']).read_text() for i in profile['source_indices']}
    legacy=tables(texts[100])+tables(texts[104])
    check('source100 nine actual tables',len(tables(texts[100])),9)
    check('source104 sixteen actual tables',len(tables(texts[104])),16)
    check('legacy die types',Counter(t['die'] for t in legacy),Counter({100:13,20:12}))
    covered=0
    for i,t in enumerate(legacy):
        values=[n for a,b in t['ranges'] for n in range(a,b+1)]
        check('old table covers each die result once '+str(i),sorted(values),list(range(1,t['die']+1)))
        covered+=len(values)
    check('legacy table outcomes',covered,1540)
    sections=re.split(r'^## 2-[BCD]\.',texts[99],flags=re.M)[1:]
    durations=[sum(map(int,re.findall(r'^\*\*[^\n]*?\((\d+)분\)\*\*:',s,flags=re.M))) for s in sections]
    check('legacy nominal stage duration sums',durations,[180,190,190])
    check('nominal duration inside3to4h all',all(180<=x<=240 for x in durations),True)
    check('old appearance motive secret raw choices',20**3,8000)
    contradictory=[l for l in texts[104].splitlines() if '정적 분출 (압력 0)' in l]
    check('source pressure title and column disagree',[(l.split('|')[2].strip(),l.split('|')[3].strip()) for l in contradictory],[('정적 분출 (압력 0)','1')])
    # 신규 두 표: 표의 값을 고르는 것이 PC 상태 사건을 실행하지 않는다.
    new=tables(story.split('### 생활 촉발 표',1)[1]);check('new inspiration tables',len(new),2)
    for i,t in enumerate(new):
        check('written ranges match declared profile '+str(i),[list(x) for x in t['ranges']],profile['inspiration_tables'][i]['bounds'])
        check('new d100 coverage once '+str(i),[n for a,b in t['ranges'] for n in range(a,b+1)],list(range(1,101)))
    check('inspiration alone does not change state',profile['table_choice_changes_PC_state_by_itself'],False)

    # S2: 기존 Body의 이동 예산과 Special의 정확한 에고 소모식을 실제 호출한다.
    s2=profile['one_shots']['S2'];body=Body();travel=0
    for i in range(15):
        if i:new_round(body)
        move(body,10);travel+=5
        assert body.move==0 and body.main==1
    check('safe150m fifteen actual basic rounds',(travel,15*10),(75,s2['detour_distance_m']))
    new_round(body);body.main-=1
    safe_end=s2['elapsed_at_open_seconds']+travel+s2['reception_after_arrival_seconds']
    check('basic detour reaches late',(safe_end,body.main),(21640,0))
    fast=Body();distance=0;seconds=0
    while distance<s2['detour_distance_m']:
        if seconds:new_round(fast)
        step=min(10,s2['detour_distance_m']-distance);move(fast,step);distance+=step
        if distance<s2['detour_distance_m']:
            step=min(10,s2['detour_distance_m']-distance);move(fast,step,extra=True);distance+=step
        seconds+=5
    check('extra movement budget cannot make safe detour on time',s2['elapsed_at_open_seconds']+seconds+5,21605)
    check('late rebooking actual payer/cost/delay',(s2['late_rebooking_default_payer'],s2['late_rebooking_cost_team_oyat'],s2['late_rebooking_delay_seconds']),('하람',1,1200))
    check('late waiting additional ego loss',cost(F(1,3),'lower3','runner'),F(5,18))
    # 직선 협상5초+기본20m이동10초+다음 접수5초.
    end=s2['elapsed_at_open_seconds']+s2['direct_negotiation_seconds']+10+5
    check('direct normal route finishes359m40s',end,21580)
    check('equality accepted and later missed',[end+d<=s2['booking_deadline_seconds'] for d in s2['delay_examples_seconds']],[True,True,False])
    check('deadline20sec equality',end+20,21600)
    check('deadline25sec late',end+25,21605)
    check('ego six actual hours loss',cost(F(6),'lower3','runner'),F(5))
    check('ego six actual hours remaining',F(10)-cost(F(6),'lower3','runner'),F(5))
    check('ego6h5s loss',cost(F(21605,3600),'lower3','runner'),F(5)+F(1,864))
    split=0
    for a,b in product((0,5,15,20,21560),(0,5,20,25)):
        assert cost(F(a+b,3600),'lower3','runner')==cost(F(a,3600),'lower3','runner')+cost(F(b,3600),'lower3','runner');split+=1
    check('actual split time additivity',split,20)
    check('booking deadline not automatic death or Dropout',s2['deadline_auto_original_damage_or_Ego_zero_or_Dropout'],False)
    actor=Body();move(actor,10)
    reject('melee after first10m still out of contact',actor,lambda:attack(actor,Body(),'동력 근접 도구',distance=10))
    first,second=Body(),Body()
    check('separate guards each own shield',[(attack(Body(),b,'권총',roll=20,distance=20),b.charges,b.main) for b in (first,second)],[(('shield',0),1,1),(('shield',0),1,1)])
    check('second same round hit reaches actual guard',attack(Body(),first,'권총',roll=20,distance=20),('damage',3))
    check('other guard unchanged',(second.hp,second.charges,second.blocked),(12,1,True))
    actor=Body();reject('opaque detour blocks direct fire',actor,lambda:attack(actor,Body(),'권총',cover='full',distance=20))
    check('melee specified damage exceeds handgun',attack(Body(),Body(),'동력 근접 도구',distance=1),('damage',5))

    # S1: 공통 전달/단서 모형을 지정 파일에 한정해 재사용. 모든 파일의 Byte 규칙이 아니다.
    s1=profile['one_shots']['S1'];sender=Sender(facts={'COPY-S1'});msg=sender.send('S1-COPY','COPY-S1')
    check('one file actual transmission action',(sender.body.main,msg['seconds'],msg['source']),(0,s1['copy_seconds'],'COPY-S1'))
    reject('same copy event not sent twice',sender,lambda:sender.send('S1-COPY','COPY-S1'))
    check('source record retained in sender',sender.facts,{'COPY-S1'})
    absent=Sender(facts=set());reject('unknown actual source cannot be copied',absent,lambda:absent.send('ABSENT','COPY-S1'))
    check('specified copy capacity only',s1['copy_capacity_files'],1)
    check('source record not removed',s1['source_record_moved'],False)
    case=Case();case.optional_terminal(50,100);case.obtain_receipt();case.verify()
    check('failed optional access preserves receipt route',case.suspected,False)
    case=Case();case.optional_terminal(50,100);case.contact_issuer();case.verify()
    check('failed optional access preserves issuer route',case.suspected,False)

    # S3:기존 기능 수리 예에 별도 실물ID를 사용한다. 전체 카페/HP 회복이 아니다.
    scene=Scene();scene.initial['parts']=['PART-S3'];scene.state=deepcopy(scene.initial)
    event=start_event(part='PART-S3');put(scene,'S3-START',event)
    put(scene,'S3-PARTIAL',{'kind':'progress','seconds':120,'depends':['S3-START']})
    check('S3 actual partial repair',(scene.state['job']['seconds'],scene.state['normal'],scene.state['spent']),(120,False,['PART-S3']))
    before=snapshot(scene);scene.ooc_wait(86400);scene.session_boundary();check('S3 OOC no progress',snapshot(scene),before)
    put(scene,'S3-REST',{'kind':'progress','seconds':180,'depends':['S3-PARTIAL']})
    put(scene,'S3-DONE',{'kind':'complete','depends':['S3-REST']})
    check('S3 approved function repaired once',(scene.state['job']['seconds'],scene.state['normal'],scene.state['spent']),(300,True,['PART-S3']))
    check('S3 not HP Ego ammo healing',tuple(scene.state[k] for k in ('HP','Ego','ammo')),(5,6,4))
    prior=snapshot(scene)
    try:scene.correct(['S3-PARTIAL'],scene.version)
    except ValueError:pass
    else:raise AssertionError('dependent completion not covered')
    check('S3 dependent correction rejected atomically',snapshot(scene),prior)
    scene.correct(['S3-PARTIAL','S3-REST','S3-DONE'],scene.version)
    check('S3 correction preserves actual started cost',(scene.state['spent'],scene.state['normal']),(['PART-S3'],False))
    check('S3 no forced death Dropout Matting',profile['one_shots']['S3']['mandatory_death_Dropout_or_matting'],False)
    check('actual participant evidence absent',tuple(profile[k] for k in ('actual_participant_reading','actual_participant_playtest','actual_async_community_test')),(False,False,False))
    source_hashes={ledger['files'][i]['source']:sha(p/ledger['files'][i]['source']) for i in profile['source_indices']}
    for e in ledger['scenario_tools_topic_sources']:source_hashes[e['path']]=sha(p/e['path']);assert source_hashes[e['path']]==e['sha256']
    for i in profile['source_indices']:assert source_hashes[ledger['files'][i]['source']]==ledger['files'][i]['observed_sha256']
    names=['10_CoreRulebook.md','11_WorldLorebook.md','12_룰시트와캐릭터시트.md','13_입문시나리오.md']
    names+=['검증/'+n for n in ['시나리오_확장프로필.json','일반플레이_검증.py','입문_프로필.json','스페셜_검증.py','스페셜_프로필.json','장면운영_검증.py','장면운영_프로필.json','팀지원_검증.py','팀지원_프로필.json','진행자_검증.py','진행자_장면프로필.json','임플란트_검증.py','임플란트_프로필.json','백분율_코어검증.py']]
    artifacts={n:sha(o/n) for n in names};artifacts[str(Path(__file__).relative_to(o))]=sha(Path(__file__))
    return {'date':'2026-10-08','profile':profile['id'],'scope':'과거v0.4 입문 본문 보존/현재v0.5 편집 대조·편집 전 시나리오 도구 보존/현재 S1 선택 타롯/S2 우회150m·추가 이동·지연 접수 계약 대조·구판25표의1540결과 범위/명목시간 합·NEW2생활표/200결과·현재 Body/Special/Scene/전달/기본단서 모형의 시간/접수·장기거주/엄폐·행동/방호/복사·부분수리 경계. 실제 전체 시나리오 재현/전술 최적화·전투 균형/독해/매력·신규 전체 IO/배경 인물 검증 아님.','checks_passed':len(checks),'checks':checks,'legacy_tables':25,'legacy_die_outcomes':covered,'legacy_nominal_minutes':durations,'legacy_NPC_raw_combinations':8000,'new_inspiration_tables':2,'new_inspiration_die_outcomes':200,'split_IC_time_cases':split,'original_main_story_prefix_verified':False,'historical_v04_main_story_prefix_verified':True,'current_main_story_editorially_updated':True,'historical_scenario_tools_appendix_unchanged':True,'scenario_tools_appendix_unchanged':False,'current_scenario_tools_editorially_reviewed':True,'source_sha256':source_hashes,'artifacts_sha256':artifacts,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False,'full_encounter_balance_verified':False,'all_original_scenario_and_campaign_consequences_complete':False}

if __name__=='__main__':
    r=run();Path(__file__).with_name('시나리오_확장검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('profile','checks_passed','legacy_tables','legacy_die_outcomes','new_inspiration_die_outcomes','split_IC_time_cases','actual_participant_playtest')},ensure_ascii=False))
