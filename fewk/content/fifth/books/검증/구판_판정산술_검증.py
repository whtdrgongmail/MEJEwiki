from pathlib import Path
from fractions import Fraction as F
from itertools import product
from collections import Counter
import os
import json,hashlib,re,unicodedata,csv,io
here=Path(__file__).resolve().parent
ledger=json.loads((here/'제5판_이관검수.json').read_text());root=here.parent.parent

def sum_threshold(n,faces,tn):
    # Unlimited explosions: a single die has k maxima then r<faces.
    # All terms with value>=TN can be omitted from the failure convolution exactly.
    single={k*faces+r:F(1,faces**(k+1)) for k in range(tn//faces+1) for r in range(1,faces) if k*faces+r<tn}
    dist={0:F(1)}
    for _ in range(n):
        nd={}
        for a,pa in dist.items():
            for b,pb in single.items():
                if a+b<tn:nd[a+b]=nd.get(a+b,F(0))+pa*pb
        dist=nd
    return 1-sum(dist.values())

def packed(f):return {'numerator':f.numerator,'denominator':f.denominator,'decimal':float(f)}

def run():
    checks=[]
    def check(name,got,want):assert got==want,(name,got,want);checks.append(name)
    rows=[]
    for stat,n,faces,tn in [(2,2,4,5),(4,4,4,10),(6,4,6,15),(9,5,8,25),(13,7,10,40),(17,9,12,60),(21,8,20,100)]:
        probability=sum_threshold(n,faces,tn)
        basic=F(n*(faces+1),2);exploding=basic*F(faces,faces-1)
        assert probability!=F(1,2) and exploding>basic
        rows.append({'stat':stat,'dice':f'{n}d{faces}','TN':tn,'ordinary_nonexploding_mean':packed(basic),'unlimited_exploding_mean':packed(exploding),'sum_at_least_TN_probability':packed(probability),'separate_chain_critical_promotion_included':False})
    check('seven old fifty-percent labels are not exact sum thresholds',len(rows),7)
    # Small independent nonexploding enumeration: explosive faces4 already pass TN5 for two dice.
    check('2d4 TN5 independent enumeration',sum_threshold(2,4,5),F(sum(a+b>=5 for a,b in product(range(1,5),repeat=2)),16))
    check('6d6 basic mean',F(6*7,2),F(21))
    check('5d8 minus6d6 basic mean',F(5*9,2)-F(6*7,2),F(3,2))
    check('example INT9 sum',(3+5+2+7+8+4)+(4+1-2),32)
    check('example Grade ace sum',2+3+5+6+4+6+6+4+3,39)
    check('example critical chain sum',2+5+6+3+6+6+4,32)
    check('pool example six hits',sum(x>=5 for x in (6,5,2,6,4,5,3,1,6,5)),6)
    check('1d4 all-one fumble',F(1,4),F(25,100))
    check('6d8 all-one fumble',F(1,8**6),F(1,262144))
    check('five legacy tier cost differences',tuple(b-a for a,b in [(9,15),(33,45),(69,85),(115,135),(174,200)]),(6,12,16,20,26))
    # Recheck the actual legacy examples; these are errors to resolve, not fifth-edition builds.
    indices=[5,19,21,22,25,64,11,16,24,39,63,102,103]
    files=[root/ledger['files'][i]['source'] for i in indices]
    for i,f in zip(indices,files):assert hashlib.sha256(f.read_bytes()).hexdigest()==ledger['files'][i]['observed_sha256']
    texts={i:(root/ledger['files'][i]['source']).read_text() for i in indices}
    skill_part=texts[11].split('## 3-E.')[1].split('## 3-F.')[0]
    skill_rows=[list(map(int,re.findall(r'\+(\d+)',line))) for line in skill_part.splitlines() if line.startswith('- ') and re.search(r'\+\d+',line)]
    declared_skills=list(map(int,re.findall(r'총: (\d+)p',skill_part)))
    skill_costs=[sum(sum(range(1,n+1)) for n in row) for row in skill_rows]
    check('four actual legacy skill level sums match labels',list(map(sum,skill_rows)),declared_skills)
    check('four actual legacy skill cumulative costs',skill_costs,[36,51,55,58])
    check('legacy skill p labels are not actual purchase costs',all(x!=y for x,y in zip(skill_costs,declared_skills)),True)
    build_blocks=texts[16].split('### 빌드 ')[1:]
    stat_costs=[];build_skill_costs=[]
    for block in build_blocks:
        stat_region=block.split('BOD ',1)[1].split('합:',1)[0]
        stat_costs.append(sum(map(int,re.findall(r'\((\d+)p\)',stat_region))))
        line=next(line for line in block.splitlines() if line.startswith('스킬:'))
        levels=list(map(int,re.findall(r'\+(\d+)',line)))
        build_skill_costs.append(sum(sum(range(1,n+1)) for n in levels))
    check('five actual legacy stat subtotals',stat_costs,[120,139,112,120,124])
    check('all five labeled standard100 builds exceed100 before skills',all(x>100 for x in stat_costs),True)
    check('five actual legacy build skill cumulative costs',build_skill_costs,[35,44,47,43,40])
    fumble_percent=F(100,6**10)
    printed_fumble=F(re.search(r'10d6 Pool: ([0-9.]+)%',texts[24])[1])
    check('10d6 actual all-one percent differs from printed value',fumble_percent!=printed_fumble,True)
    grade8_percent=F(100,8**6);printed_grade8=F(re.search(r'6d8: ([0-9.]+)%',texts[24])[1])
    check('6d8 actual all-one percent differs from printed value',grade8_percent!=printed_grade8,True)
    ego_times=[int(re.search(pattern,texts[39])[1]) for pattern in [r'공단계 (\d+)시간 체류',r'광제사직계 (\d+)시간 체류',r'공단계 추가 (\d+)시간']]
    ego_unrounded=F(ego_times[0]+ego_times[2],24)+F(ego_times[1],1)/F('2.5')
    check('legacy ego example exact time sum under its own periods',ego_unrounded,F(103,60))
    saved=int(re.findall(r'총 저장 (\d+)p',texts[63])[-1]);delta_a,delta_b=map(int,re.search(r'승급 \((\d+) − (\d+) =',texts[63]).groups())
    incremental_balance=saved-(delta_a-delta_b)
    check('legacy stored85 spends incremental7 not entire52',incremental_balance,78)
    old_last_start=int(re.search(r'잔여 (\d+)p',texts[63])[1]);last_earned=int(re.search(r'세션 16~20.*?= (\d+)p',texts[63])[1])
    check('legacy own33 plus50 minus7 minus8 arithmetic',old_last_start+last_earned-7-8,68)
    scenario_minutes={i:list(map(int,re.findall(r'### [①-⑤].*?\((\d+)분\)',texts[i]))) for i in [102,103]}
    check('legacy scenario103 nominal minutes',sum(scenario_minutes[102]),180)
    check('legacy scenario104 nominal minutes',sum(scenario_minutes[103]),270)
    source_example_recheck={'legacy_skill_levels':skill_rows,'legacy_skill_declared_p':declared_skills,'legacy_skill_cumulative_costs':skill_costs,'legacy_creation_stat_subtotals':stat_costs,'legacy_creation_skill_cumulative_costs':build_skill_costs,'all_one_6d8_percent':packed(grade8_percent),'all_one_10d6_percent':packed(fumble_percent),'legacy_ego_unrounded_under_its_own_periods':packed(ego_unrounded),'legacy_saved85_after_incremental7':incremental_balance,'legacy_own33_plus50_minus7_minus8':old_last_start+last_earned-7-8,'legacy_scenario_nominal_minutes':{str(i):sum(x) for i,x in scenario_minutes.items()},'100p_builds_rewritten':False,'source_combat_missing_explosion_or_injury_rules_repaired':False,'actual_play_durations_verified':False}

    archive=json.loads((here/'이전설계_통합검토.json').read_text())['older_framework_archive_review']
    archive_sources=[]
    for snapshot in archive['snapshots']:
        text=snapshot['text'];digest=hashlib.sha256(text.encode()).hexdigest()
        f=here.parent/snapshot['path_relative_to_fifth']
        assert digest==snapshot['sha256']==hashlib.sha256(f.read_bytes()).hexdigest()
        archive_sources.append(f)
    professional=next(e['text'] for e in archive['snapshots'] if e['name']=='_Professional_Review_v0.1.md')
    assert '1d10) × 10' in professional and '10d10' in professional and '3d10' in professional
    before_archive=len(checks)
    def ordinary_sum(n,faces):
        distribution=Counter({0:1})
        for _ in range(n):
            updated=Counter()
            for total,count in distribution.items():
                for face in range(1,faces+1):updated[total+face]+=count
            distribution=updated
        return {total:F(count,faces**n) for total,count in distribution.items()}
    def moments(distribution):
        mean=sum(value*probability for value,probability in distribution.items())
        variance=sum((value-mean)**2*probability for value,probability in distribution.items())
        return mean,variance
    multiplied10={face*10:F(1,10) for face in range(1,11)}
    summed10=ordinary_sum(10,10)
    multiplied3={face*3:F(1,10) for face in range(1,11)}
    summed3=ordinary_sum(3,10)
    check('배수와 합산의 평균은 같아도 분산은 다름',moments(multiplied10),(F(55),F(825)))
    check('10d10의 실제 분산',moments(summed10),(F(55),F(165,2)))
    check('1d10×10에 없는 중간 눈15',15 in multiplied10,False)
    check('10d10에는 중간 눈15가 있음',summed10[15]>0,True)
    check('1d10×3의 평균과 분산',moments(multiplied3),(F(33,2),F(297,4)))
    check('3d10의 평균과 분산',moments(summed3),(F(33,2),F(99,4)))
    check('근접 예시의 실제 나눗셈 범위',(F(1+1,10),F(6+1,10)),(F(1,5),F(7,10)))
    check('구판+14 DV29 문턱',F(sum(face+14>=29 for face in range(1,21)),20),F(3,10))
    check('축소된+11 DV29 문턱',F(sum(face+11>=29 for face in range(1,21)),20),F(3,20))
    check('구판+14 AC17은 모든 눈 통과가 아님',F(sum(face+14>=17 for face in range(1,21)),20),F(9,10))
    prices=[10]
    for _ in range(4):prices.append((prices[-1]*3+1)//2)
    check('단계별 올림의 다섯 가격',prices,[10,15,23,35,53])
    check('Lv5 단일 배수가격',F(10)*F(3,2)**4,F(405,8))
    check('다섯 구매총액과 단일가격 구분',sum(prices),136)
    check('구판50개 이슈 집계',5+14+11+12+8,50)
    check('구판 해결 주장44개 집계',5+12+11+10+6,44)
    check('44/50의 비율',F(44,50),F(22,25))
    check('반 단위 효과의 표시합',F(1,2)+1,F(3,2))
    framework_archive_arithmetic={'documents':4,'checks_passed':len(checks)-before_archive,
        'multiplied_1d10_by10':{'mean':packed(moments(multiplied10)[0]),'variance':packed(moments(multiplied10)[1])},
        'sum_10d10':{'mean':packed(moments(summed10)[0]),'variance':packed(moments(summed10)[1])},
        'multiplied_1d10_by3':{'mean':packed(moments(multiplied3)[0]),'variance':packed(moments(multiplied3)[1])},
        'sum_3d10':{'mean':packed(moments(summed3)[0]),'variance':packed(moments(summed3)[1])},
        'scope':'구판 검토 보고서의 순수 비폭발 피해분포·문턱/가격/집계 산술. 자연1/20·방호·사망·확률 전체 룰/FEWK 신규 균형을 검증하지 않음',
        'physical_damage_variance_is_ego_or_dropout_cost':False,'actual_external_expert_evidence':False,'actual_participant_playtest':False}
    files+=archive_sources
    second_review=json.loads((here/'이전설계_통합검토.json').read_text())['second_edition_reader_review']
    second_sources=[here.parent/e['path_relative_to_fifth'] for e in second_review['snapshots']]
    for entry,path in zip(second_review['snapshots'],second_sources):
        assert entry['whole_document_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
    before_second=len(checks)
    # 구판 문체 표본과 편집 추정의 실제 산술만 대조한다.
    check('70kg의 질량 표준 환산은7양',F(70*1000,10000),F(7))
    check('60~90kg의 자 단위 범위',(60*1000,90*1000),(60000,90000))
    check('2판 목차 주제 절 합계',sum([3,7,8,5,8,3]),34)
    check('2판 제안 페이지 합계',sum([8,7,15,17,22,24,14,35,14,4]),160)
    check('구판10편의 줄 수 합계',sum([116,156,123,152,145,168,238,206,239,647]),2190)
    check('개별 선집 분량의 합계 범위',(sum([3,4,4,4,4,5,4,4,5,7]),sum([4,4,4,4,4,5,4,4,6,9])),(44,48))
    check('독립 현화 구간은 항상100이 아님',(92+1+1,98+5+3),(94,106))
    check('인수인계의10000배 밀도 표준',[10**24//10000**i for i in range(7)],[10**24,10**20,10**16,10**12,10**8,10**4,1])
    check('정확한1/10의1일 이후 분 단위',(F(24*60,10),F(24*60,100)),(F(144),F(72,5)))
    doubled={face*2:F(1,10) for face in range(1,11)}
    check('대본1d10×2의 평균과 분산',moments(doubled),(F(11),F(33)))
    check('대본2d10은 배수와 다른 분산',moments(ordinary_sum(2,10)),(F(11),F(33,2)))
    editorial=second_review['editorial_arithmetic']
    check('구판 조판 영역과 두 단폭',(182-18-13,257-16-18,F(182-18-13-10,2)),(151,223,F(141,2)))
    check('T06의 두 카드와 간격은 영역 초과',(75*2+10,75*2+10>151),(160,True))
    check('T15는 간격 없이도 가로와 세로 초과',(80*2,120*2,80*2>151,120*2>223),(160,240,True,True))
    check('T23의 제안 폭과 실제 세 단폭',(56*3+5*2,F(151-5*2,3)),(178,F(47)))
    page_rows=editorial['page_rows']
    check('편집규칙 본편 표의 실제 합계',(sum(e['A4'] for e in page_rows[:-1]),sum(e['B5'] for e in page_rows[:-1])),(128,144))
    check('여유분을 포함한 실제 합계',(sum(e['A4'] for e in page_rows),sum(e['B5'] for e in page_rows)),(129,161))
    check('T20의 실제 축소 여백 영역',(182-10-10,257-8-10),(162,239))
    second_edition_reader_arithmetic={'documents':9,'checks_passed':len(checks)-before_second,'scope':'구판 문체의 질량 표준과 목차·선집 분량 추정·현화 확률 범위 합계, 인수인계 밀도/시간과 대본 피해 분포, 편집규칙의 영역/카드/단폭·페이지 합계. 실제 조판·사회 통계·사망 판정/새 엔진 균형 검증이 아님','current_engine_changed':False,'actual_publication_pages_verified':False,'actual_participant_playtest':False}
    files+=second_sources

    current_review=json.loads((here/'이전설계_통합검토.json').read_text())['current_framework_spec_review']
    current_sources=[here.parent/e['path_relative_to_fifth'] for e in current_review['snapshots']]
    for entry,path in zip(current_review['snapshots'],current_sources):
        assert entry['whole_document_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
    spec=current_review['snapshots'][0]['text']
    report=current_review['snapshots'][2]['text']
    before_current=len(checks)
    table=spec.split('### 2-2.',1)
    table=table[1].split('### 2-3.',1)[0]
    cost_rows=[tuple(map(int,m)) for m in re.findall(r'^\| (\d+) \| .*? \| (\d+)p',table,re.M)]
    check('현재 명세의 스탯 비용25행',len(cost_rows),25)
    costs=dict(cost_rows)
    states={0:0}
    for _ in range(6):
        next_states={}
        for total,cost in states.items():
            for stat,price in cost_rows:
                combined=total+stat
                next_states[combined]=min(next_states.get(combined,10**9),cost+price)
        states=next_states
    check('구판 평균6~8의 최소 스탯 비용',min(cost for total,cost in states.items() if 36<=total<=48),120)
    check('정정된 스킬0에서7의 누적 비용',sum(range(1,8)),28)
    check('보고서의 현재값 두 배를 문자대로 합산',sum(2*x for x in range(7)),42)
    check('보고서2/8/14 예시의 다음값 두 배 합산',sum(2*(x+1) for x in range(7)),56)
    status=report.split('## 8. 개별 파일 Status',1)[1].split('## 9.',1)[0]
    status_rows=[line for line in status.splitlines() if line.startswith('| **')]
    check('정합성 보고 상태 표의 실제 문서 수',len(status_rows),18)
    check('정합성 보고 표의 정정 대상 실제 수',sum(not line.endswith('| ✅ |') for line in status_rows),6)
    check('현재 명세4d4의 비폭발 평균',F(4*5,2),F(10))
    check('현재 명세4d4의 무한 폭발 평균',F(4*5,2)*F(4,3),F(40,3))
    check('차이+20은 모든 음수 차이를20으로 만들지 않음',-30+20,-10)
    bod=6
    check('명세의 빈사와 진사 사이 미지정 HP',tuple(h for h in range(-2*bod,0) if not (-bod<=h<=-1 or h<=-2*bod)),(-11,-10,-9,-8,-7))
    check('명세4d4 모두1 확률의 퍼센트',F(100,4**4),F(25,64))
    current_framework_spec_arithmetic={'documents':3,'checks_passed':len(checks)-before_current,'minimum_stat_cost_for_old_six_stat_mean_6_to_8':120,'old_budget':100,'report_actual_status_rows':18,'report_actual_correction_rows':6,'ordinary_4d4_mean':packed(F(10)),'unlimited_exploding_4d4_mean':packed(F(40,3)),'scope':'현재 구판 명세/검토 문서의 비용·분포 평균·집계와 상태 구간의 제한 대조. 구판 엔진 재현·100p 빌드 작성·제5판 수치 변경·실제 참가자 시험이 아님','current_engine_changed':False,'old_100point_build_rewritten':False,'actual_participant_playtest':False}
    files+=current_sources

    first_review=json.loads((here/'이전설계_통합검토.json').read_text())['first_edition_character_review']
    first_sources=[here.parent/e['path_relative_to_fifth'] for e in first_review['snapshots']]+[root/e['path_relative_to_plan'] for e in first_review['related_novels_reviewed']]
    for entry,path in zip(first_review['snapshots']+first_review['related_novels_reviewed'],first_sources):
        assert entry['whole_document_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
    novel065=first_review['related_novels_reviewed'][2]['text']
    assert '2,400만' in novel065 and '7만 2천' in novel065 and '시체 한 구당 50크레딧' in novel065 and '500크레딧' in novel065
    before_first=len(checks)
    check('소설065의 탈출 인원 비율',F(72000,24000000),F(3,1000))
    check('소설065의 스틱값과 운반 건수',F(500,50),F(10))
    first_character_source_arithmetic={'character_documents':4,'related_novels':3,'checks_passed':len(checks)-before_first,'novel065_escape_fraction':packed(F(3,1000)),'scope':'확장 소설065의 지정 인원 비율과 스틱/운반 가격의 산술만 대조. 도시/인구·임금·출력·심박·공연 효과를 정사나 공통 규칙으로 검증하지 않음','current_engine_changed':False,'actual_participant_playtest':False}
    files+=first_sources

    physics_review=json.loads((here/'이전설계_통합검토.json').read_text())['world_physics_byte_review']
    physics_sources=[root/e['path_relative_to_plan'] for e in physics_review['snapshots']]
    for entry,path in zip(physics_review['snapshots'],physics_sources):
        assert entry['whole_document_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    byte_text=next(e['text'] for e in physics_review['snapshots'] if e['name'].startswith('01_'))
    overview_text=next(e['text'] for e in physics_review['snapshots'] if e['name']=='00_Overview.md')
    for phrase in ['0.7양','6만경','1.5해','1자 = 10^24','§1-Addendum','A-2.','A-3.','A-5.']:
        assert phrase in byte_text,phrase
    assert '0.7양' in overview_text
    value_text=next(e['text'] for e in physics_review['wiki_topic_recheck']['topics'] if e['name']=='가치.txt')
    value_rows=[line for line in value_text.splitlines() if line.startswith('  * ') and any(term in line for term in ['Meterial','Spiritual','Info.','Wills','Pipe','Stackable','Rarity','Cite'])]
    before_physics=len(checks);jaa=10**24;yang=10**28
    check('물리 엔진의7대 가치라는 제목과 실제8범주',len(value_rows),8)
    check('원전 만자=양의 기본 단위',10000*jaa,yang)
    check('70kg의 표준 물질 바이트',70*1000*jaa,7*10**28)
    check('70kg의 양 표기',F(70*1000*jaa,yang),F(7))
    check('구판0.7양 표기의 열 배 차이',F(7,F(7,10)),F(10))
    check('400g 책의 순수 물질 바이트',400*jaa,4*10**26)
    check('1.5톤 자동차의 그램 수',F(15,10)*1000*1000,F(1500000))
    check('자동차의 순수 물질 바이트',1500000*jaa,15*10**29)
    check('자동차의 양 표기',F(1500000*jaa,yang),F(150))
    check('100만명60kg의 물질 바이트',1000000*60*1000*jaa,6*10**34)
    check('구판6만경 표기의 자릿수 차이',F(6*10**34,60000*10**16),F(10**14))
    check('네 차례 밀도 감쇠의 상대 비율',F(1,10000**4),F(1,10**16))
    check('네 차례 감쇠의 절대 표준 바이트',jaa//10000**4,10**8)
    check('초기0042의20자와30배 산술',20*30,600)
    check('위키21자를30배로 문자대로 계산',21*30,630)
    check('6만자30배의 구판 예시 산술',60000*30,1800000)
    check('6만자와21자의 정확한 구성량 비율',F(60000,21),F(20000,7))
    world_physics_byte_arithmetic={'documents':3,'checks_passed':len(checks)-before_physics,'actual_value_categories':8,'mass_70kg_yang':packed(F(7)),'initial_subject_20jaa_times30':600,'wiki_subject_21jaa_times30':630,'scope':'원전의 물질계1g1자와 만자=양, 구판 표/후속 패치의 제한 산술을 대조한다.20자/21자 모델·약600 표현의 차이는 보존한다. 이동 요금·혼백 계측/불멸·21그램/21만자의 등치, 모든 차원/존재/게임 효과를 검증하지 않는다.','current_engine_changed':False,'actual_participant_playtest':False}
    files+=physics_sources

    dimension_ego=json.loads((here/'이전설계_통합검토.json').read_text())['world_physics_dimension_ego_review']
    dimension_ego_sources=[root/e['path_relative_to_plan'] for e in dimension_ego['snapshots']]
    for entry,path in zip(dimension_ego['snapshots'],dimension_ego_sources):
        assert entry['whole_document_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    dimension_text=next(e['text'] for e in dimension_ego['snapshots'] if e['name'].startswith('02_'))
    ego_text=next(e['text'] for e in dimension_ego['snapshots'] if e['name'].startswith('05_'))
    for phrase in ['Day 5: 귀환 · 에고 -2.5','T+30m   목표 달성 · 에고 -2 (2.5h 한계 80%)','2-Addendum','2-X. PHYS-D09','0.7양']:
        assert phrase in dimension_text,phrase
    for phrase in ['8 × (6/24)','BP% 30, 에고 Max 8','체류 한계 × (현재 에고 / 10)','31~50 구간','공격적 RP 강제']:
        assert phrase in ego_text,phrase
    before_dimension_ego=len(checks)
    check('구판2계층10일 한계의5일 에고 소모',F(10)*F(5,10),F(5))
    check('구판2계층5일 후 에고 잔여',F(10)-F(10)*F(5,10),F(5))
    check('구판4계층150분 중30분 소모',F(10)*F(30,150),F(2))
    check('30분에 사용한 비율',F(30,150),F(1,5))
    check('30분 후 잔여 비율',1-F(30,150),F(4,5))
    check('구판4계층90분 소모',F(10)*F(90,150),F(6))
    check('구판4계층120분 소모',F(10)*F(120,150),F(8))
    check('구판4계층120분 후 남은 시간',150-120,30)
    check('정확한24시간의십분의일',F(24*60,10),F(144))
    check('구판150분 근사와 정확144분의 차이',150-F(24*60,10),F(6))
    scaled_horizon=F(24)*F(8,10)
    check('기준10의24시간에서 잔여8의 한계',scaled_horizon,F(96,5))
    consistent_six_hours=F(8)*F(6,scaled_horizon)
    check('같은 기준시간 정의를 쓴 에고8의6시간 소모',consistent_six_hours,F(5,2))
    old_unscaled_six_hours=F(8)*F(6,24)
    check('구판 고정24시간 모델 자체의 산술',old_unscaled_six_hours,F(2))
    check('구판 고정 한계와 비례 한계를 혼용한 소모 차이',consistent_six_hours-old_unscaled_six_hours,F(1,2))
    check('같은 기준을 적용한 에고8의6시간 후 잔여',F(8)-consistent_six_hours,F(11,2))
    bp_section=ego_text.split('## §5-6.')[1].split('## §5-7.')[0]
    bp_rows=[]
    for line in bp_section.splitlines():
        cells=[x.strip() for x in line.split('|')[1:-1]]
        if cells and re.fullmatch(r'\d+~\d+',cells[0]):
            low,high=map(int,cells[0].split('~'))
            if low<=30<=high:bp_rows.append(cells)
    assert len(bp_rows)==1
    check('구판BP30의 실제 표 구간',bp_rows[0][1],'Broken')
    check('구판BP30의 실제 표 사회 수정치',bp_rows[0][2],'-3')
    check('구판BP30의 실제 표 샤이닝 수정치',bp_rows[0][3],'-10')
    check('구판BP30의 실제 표 매팅 수정치',bp_rows[0][4],'-15')
    check('같은1g 기준의 물질계와 하위1 밀도비',F(10**24,10**20),F(10000))
    world_physics_dimension_ego_arithmetic={'documents':2,'checks_passed':len(checks)-before_dimension_ego,'five_day_ego_loss':packed(F(5)),'thirty_minute_fraction_used':packed(F(1,5)),'ego8_consistent_remaining_hours':packed(scaled_horizon),'ego8_consistent_six_hour_loss':packed(consistent_six_hours),'ego8_unscaled_six_hour_loss':packed(old_unscaled_six_hours),'BP30_actual_old_band':bp_rows[0][1:],'scope':'구판의 명시한 시간·비례모델·BP 구간을 제한 대조한다. 근삿값은 정확1/10과 구분하며 구판BP/강제내면/형성트랙을 제5판에 채택하지 않는다. 밀도비는 같은 질량 기준이며 총량/밀도 비교로 상향 이동 불가나 사후 상태를 증명하지 않는다.','current_engine_changed':False,'actual_participant_playtest':False}
    files+=dimension_ego_sources

    sinki=json.loads((here/'이전설계_통합검토.json').read_text())['world_physics_sinki_review']
    sinki_sources=[root/e['path_relative_to_plan'] for e in sinki['snapshots']]
    for entry,path in zip(sinki['snapshots'],sinki_sources):
        assert entry['whole_document_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    sinki_text=sinki['snapshots'][0]['text']
    for phrase in ['21자 ×10^6 = 2.1×10^25','생물 가치 LCC 적용 후 21양','1 만셀     = 신사 초심자 기본 신기용량','한 끼 식사 칼로리만큼의 신기']:
        assert phrase in sinki_text,phrase
    unit_source=sinki['wiki_topic_recheck']
    unit_path=root/unit_source['source_path_relative_to_plan']
    assert hashlib.sha256(unit_path.read_bytes()).hexdigest()==unit_source['source_sha256']
    unit=next(t for t in unit_source['topics'] if t['topic']=='동력단위.txt')
    assert unit['whole_topic_read'] and hashlib.sha256(unit['text'].encode()).hexdigest()==unit['sha256'] and unit['text'] in unit_path.read_text()
    for phrase in ['1셀은 통상 1k칼로리','1천셀','차이는 있지만 통상 1만셀']:
        assert phrase in unit['text'],phrase
    before_sinki=len(checks);jaa=10**24;yang=10**28
    subject=21*jaa;scaled_subject=subject*10**6
    check('21자의 바이트 표기',subject,21*10**24)
    check('21자 백만 배의 실제 바이트 표기',scaled_subject,21*10**30)
    check('백만 배 등식의 누락 배수',F(scaled_subject,subject),F(1000000))
    check('21자 백만 배의 양 표기',F(scaled_subject,yang),F(2100))
    check('21양 자체의 바이트 표기',21*yang,21*10**28)
    check('LCC 전2100양과 명시한21양의 비율',F(scaled_subject,21*yang),F(100))
    check('위키 근사1셀1kcal을 적용한1만셀 비교',10000*1,10000)
    check('위키 근사오얏1000셀을 적용한1만셀 비교',F(10000,1000),F(10))
    world_physics_sinki_arithmetic={'documents':1,'wiki_unit_topics':1,'checks_passed':len(checks)-before_sinki,'subject21jaa_bytes':subject,'million_times_subject_bytes':scaled_subject,'million_times_subject_yang':packed(F(2100)),'unadjusted_to_printed_21yang_ratio':packed(F(100)),'comparison_10000cell_kcal':10000,'comparison_10000cell_OYAT':packed(F(10)),'scope':'지정한 구판 등식과 위키의 읽기용 근사 단위만 대조한다. LCC의 배수가 명시되지 않아 적용 후21양을 계산 검증으로 인정하지 않는다. 실제 혼백/질량·영양·신앙·장치 출력과 시간·행동 비용·전원 신사 용량을 검증하지 않는다.','post_LCC_21yang_verified':False,'real_nutrition_or_soul_measurement_verified':False,'current_engine_changed':False,'actual_participant_playtest':False}
    files+=sinki_sources+[unit_path]

    power_review=json.loads((here/'이전설계_통합검토.json').read_text())['world_physics_power_artificial_review']
    power_sources=[root/e['path_relative_to_plan'] for e in power_review['snapshots']]
    for entry,path in zip(power_review['snapshots'],power_sources):
        assert entry['whole_document_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    power=next(e['text'] for e in power_review['snapshots'] if e['name'].startswith('08_'))
    unit_source=power_review['wiki_topic_recheck'];unit_path=root/unit_source['source_path_relative_to_plan']
    assert hashlib.sha256(unit_path.read_bytes()).hexdigest()==unit_source['source_sha256']
    unit=next(t for t in unit_source['topics'] if t['topic']=='흑공파워셀.txt')
    assert unit['whole_topic_read'] and hashlib.sha256(unit['text'].encode()).hexdigest()==unit['sha256'] and unit['text'] in unit_path.read_text()
    for phrase in ['돌칩 셀 6규격','흑공말통 200kg','전투 한 번에 3~4개 소모','1g 흑공정제용액 = 1만셀']:
        assert phrase in power,phrase
    for phrase in ['이억셀','20kg','이십억셀','200kg','케이스 포함 400kg']:
        assert phrase in unit['text'],phrase
    table=power.split('### 8-6-B.',1)[1].split('### 8-6-C.',1)[0]
    rows=[line for line in table.splitlines() if re.match(r'\| \*\*(?:AA|[A-F])형\*\*',line)]
    c_row=next(line for line in rows if line.startswith('| **C형**'))
    c_price=F(c_row.split('|')[3].strip().split()[0])
    before_power=len(checks)
    check('구판6규격이라는 표의 실제 규격 행 수',len(rows),7)
    check('구판 규격행과 제목6의 차이',len(rows)-6,1)
    check('위키이억셀의 정제용액 kg',F(200000000,10000*1000),F(20))
    check('위키이십억셀의 정제용액 kg',F(2000000000,10000*1000),F(200))
    check('구판 말통200kg과 위키20kg의 비율',F(200,20),F(10))
    check('위키드럼 케이스 포함과 용액의 무게비',F(400,200),F(2))
    check('구판C형3개라는 소비예의 가격 합',c_price*3,F(9))
    check('구판C형4개라는 소비예의 가격 합',c_price*4,F(12))
    world_physics_power_arithmetic={'documents':2,'wiki_unit_topics':1,'checks_passed':len(checks)-before_power,'old_Dolchip_actual_spec_rows':7,'old_Dolchip_printed_spec_count':6,'wiki_canister_solution_kg':packed(F(20)),'wiki_drum_solution_kg':packed(F(200)),'old_canister_mass_mismatch_ratio':packed(F(10)),'old_C_cell_consumption_price_range_OYAT':[packed(F(9)),packed(F(12))],'scope':'구판의 규격 표7행/제목6·말통/드럼 혼동과 명시한C형 소비예의 가격 합을 제한 대조한다. 구판7판매규격/가격·전투필수소비·충전시간/자동신단충전을 제5판 공통 값으로 채택하지 않는다. 위키의 보통1g1만셀/케이스 비는 해당 동력 비교이며 돌칩 질량당 용량이나 혼백/모든 IO를 검증하지 않는다.','current_engine_changed':False,'actual_participant_playtest':False}
    files+=power_sources+[unit_path]

    causal_time=json.loads((here/'이전설계_통합검토.json').read_text())['world_physics_causal_time_review']
    causal_time_sources=[root/e['path_relative_to_plan'] for e in causal_time['snapshots']]
    for entry,path in zip(causal_time['snapshots'],causal_time_sources):
        assert entry['whole_document_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    advanced=next(e['text'] for e in causal_time['snapshots'] if e['name'].startswith('09_'))
    for phrase in ['60~90만 자 ≈ 성인 1인(0.7양) 바이트 총량의 매우 작은 일부','96-00 (Consumption)','스탯 영구 -1']:
        assert phrase in advanced,phrase
    before_causal_time=len(checks);jaa=10**24;yang=10**28
    printed_adult_jaa=F(7,10)*yang/jaa
    corrected_70kg_jaa=70000
    check('구판심화의0.7양을 자로 환산',printed_adult_jaa,F(7000))
    check('구판0.7양 대비60만자의 비율',F(600000,printed_adult_jaa),F(600,7))
    check('구판0.7양 대비90만자의 비율',F(900000,printed_adult_jaa),F(900,7))
    check('정정70kg7만자 대비60만자 비율',F(600000,corrected_70kg_jaa),F(60,7))
    check('정정70kg7만자 대비90만자 비율',F(900000,corrected_70kg_jaa),F(90,7))
    table=advanced.split('### 9-4-B.',1)[1].split('### 9-4-C.',1)[0]
    intervals=[(int(a),100 if b=='00' else int(b)) for a,b in re.findall(r'^\s*-\s+(\d{2})-(\d{2}) \(',table,re.M)]
    check('구판먹개비 표의 실제6구간 너비',tuple(b-a+1 for a,b in intervals),(20,20,20,20,15,5))
    check('구판먹개비 표의1~100 전체 포함',tuple(sorted({x for a,b in intervals for x in range(a,b+1)})),tuple(range(1,101)))
    check('구판Consumption 구간의 표상 비율',F(intervals[-1][1]-intervals[-1][0]+1,100),F(1,20))
    world_physics_causal_time_arithmetic={'documents':3,'checks_passed':len(checks)-before_causal_time,'printed_adult_jaa':packed(printed_adult_jaa),'old_cost_range_to_printed_mass_ratio':[packed(F(600,7)),packed(F(900,7))],'old_cost_range_to_corrected_70kg_ratio':[packed(F(60,7)),packed(F(90,7))],'old_Mokgaebi_table_widths':[b-a+1 for a,b in intervals],'old_Consumption_table_fraction':packed(F(1,20)),'scope':'구판0.7양/60~90만자라는 지정수량의 크기 비교와 명시한d100 구간의 수량만 대조한다. 영혼/생명량·광전/전원 이동료·실제 포식/PC상실 확률·구판 전엔진 재현이나 강제 드랍아웃/6능력치를 검증하거나 제5판에 채택하지 않는다.','current_engine_changed':False,'actual_participant_playtest':False}
    files+=causal_time_sources

    index_audit=json.loads((here/'이전설계_통합검토.json').read_text())['world_physics_index_audit_review']
    index_sources=[root/e['path_relative_to_plan'] for e in index_audit['snapshots']]
    for entry,path in zip(index_audit['snapshots'],index_sources):
        assert entry['whole_document_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    index_text=next(e['text'] for e in index_audit['snapshots'] if e['name'].startswith('11_'))
    readme=next(e['text'] for e in index_audit['snapshots'] if e['name']=='README.md')
    report=next(e['text'] for e in index_audit['snapshots'] if e['name']=='_Consistency_Check.md')
    def region(text,start,end):return text.split(start,1)[1].split(end,1)[0]
    def data_rows(text):
        lines=[line for line in text.splitlines() if line.startswith('|')]
        rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in lines]
        return [r for r in rows if not all(re.fullmatch(r'[-: ]+',c) for c in r)][1:]
    base_entries=re.findall(r'^\|\s*`(PHYS-[A-Z]\d{2})`\s*\|\s*([^|]+)\|',region(index_text,'### 11-1-C.','## §11-2.'),re.M)
    added_entries=re.findall(r'^\|\s*\*\*(PHYS-[A-Z]\d{2})\*\*\s*\|\s*([^|]+)\|',region(index_text,'### 신규 법칙 코드','### 신규·재정의 용어'),re.M)
    indexed=base_entries+added_entries;codes=[code for code,name in indexed]
    label_rows=data_rows(region(report,'### V-3.','## §VI.'))
    labeled_codes={f'PHYS-{code}' for row in label_rows for code in re.findall(r'(?<![A-Z])([A-Z]\d{2})',row[0])}
    citation_rows=data_rows(region(report,'### V-1.','### V-2.'))
    source_folder=index_sources[0].parent
    physics_body=[path for path in source_folder.glob('*.md') if re.match(r'^(0[1-9]|10)_',path.name)]
    tn_lines=[(path.name,i,line) for path in physics_body for i,line in enumerate(path.read_text().splitlines(),1) if re.search(r'(?<![A-Za-z])TN(?![A-Za-z])',line)]
    before_index=len(checks)
    check('역사 보고87개 그룹 합계',sum([7,8,9,10,9,15,9,20]),87)
    check('현재 색인 기본 코드 행',len(base_entries),99)
    check('현재 색인 추가 코드 행',len(added_entries),3)
    check('현재 색인 고유 코드 수',len(set(codes)),102)
    check('현재 색인 그룹별 코드 분포',dict(Counter(code[5] for code in codes)),{'B':9,'D':10,'T':10,'S':10,'E':9,'C':25,'N':9,'M':20})
    check('기본 색인 통계99의 그룹 합계',sum([7,10,9,10,9,25,9,20]),99)
    check('현재 물리 계열 실제 문서 수',len(list(source_folder.glob('*.md'))),16)
    check('역사 보고 범위 표의 실제 파일 행',len(data_rows(region(report,'### 0-1.','### 0-2.'))),15)
    check('README 파일 표의 실제 행',len(data_rows(region(readme,'## §B. 파일 구조','### B-1.'))),14)
    check('외부 비유 대응 표의 행',len(data_rows(region(index_text,'## §11-3.','## §11-4.'))),19)
    check('원전 인용 표의 실제 행',len(citation_rows),17)
    check('원전 인용 검증 승계 행',sum('검증 승계' in row[-1] for row in citation_rows),16)
    check('원전 인용 신규 행',sum('신규 인용' in row[-1] for row in citation_rows),1)
    check('추론 확장 라벨 표의 행',len(label_rows),19)
    check('추론 확장 라벨의 개별 코드',len(labeled_codes),22)
    check('01~10의 TN 독립 토큰 존재 줄',len(tn_lines),3)
    check('README의 PHYS-A 할당 잔존',bool(re.search(r'^\| `PHYS-A##`',readme,re.M)),True)
    check('현재 이관표와 색인의 코드 이름 대응',sorted((e['code'],e['name']) for e in index_audit['legacy_code_map']),sorted((code,name.strip()) for code,name in indexed))
    world_physics_index_counts={'documents':3,'checks_passed':len(checks)-before_index,'metrics':index_audit['metrics'],'index_code_mappings':len(index_audit['legacy_code_map']),'scope':'원문 해시와 현재 파일/색인/표의 행·개별 코드·독립 TN 토큰만 재계수한다. 라인 재검증 면제·grep0·코드 연결·Clean 선언은 원전 전체의 의미 정합이나 실제 참가자 검증을 증명하지 않는다. 수량 검산을 구판 엔진 채택/완전 재현으로 합산하지 않는다.','current_engine_changed':False,'actual_participant_playtest':False}
    files+=index_sources

    pack_review=json.loads((here/'이전설계_통합검토.json').read_text())['cyberpunk_pack_foundations_review']
    pack_sources=[root/e['path_relative_to_plan'] for e in pack_review['snapshots']]
    for entry,path in zip(pack_review['snapshots'],pack_sources):
        assert entry['whole_document_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    spec=next(e['text'] for e in pack_review['snapshots'] if e['name']=='_Pack_Spec.md')
    bp=next(e['text'] for e in pack_review['snapshots'] if e['name']=='02_BP_Body_Purity.md')
    old_report=next(e['text'] for e in pack_review['snapshots'] if e['name']=='_v0.3_Review_Report.md')
    for phrase in ['임플란트 Lv N 이식 → -5×N %','시작 BP%: 90% (뇌네 인터페이스 Lv 1, -10%)','시작 BP%: 75% (근육 강화 Lv 2, 피부 강화 Lv 1)','현재 구간: 안정 (Stable, 71~90)','50% 회복','BP% -2% 추가 부담','70% 환급']:
        assert phrase in bp,phrase
    tree=re.findall(r'^[├└]── (.+?\.md)',region(spec,'## 12. 파일 구조','## 13.'),re.M)
    catalog=[]
    for group,start,end in [('능력','### 4-1.','### 4-2.'),('기술','### 4-2.','### 4-3.'),('기능','### 4-3.','### 4-4.')]:
        catalog.extend((group,row[0]) for row in data_rows(region(spec,start,end)))
    costs=data_rows(region(bp,'### 2-3-A.','### 2-3-B.'))
    bp_costs={int(re.search(r'Lv (\d+)',row[0])[1]):int(re.search(r'-(\d+)%',row[1])[1]) for row in costs}
    fumble_rows=data_rows(region(bp,'### 2-5-D.','## 2-6.'))
    fumble_widths=[]
    for row in fumble_rows:
        match=re.search(r'd100 = (\d+)(?:~(\d+))?',row[1]);low=int(match[1]);high=int(match[2] or match[1]);fumble_widths.append(high-low+1)
    severity_region=region(old_report,'### Critical 12건','### 조건부 통과')
    severity_rows=data_rows(severity_region)
    unconditional=sum('✅ 통과' in row[-1] for row in severity_rows)
    conditional=sum('조건부' in row[-1] for row in severity_rows)
    before_pack=len(checks)
    check('Pack 명세 카탈로그 그룹별 실제 행',dict(Counter(group for group,name in catalog)),{'능력':15,'기술':12,'기능':12})
    check('Pack 명세 카탈로그 실제 고유 항목',len(set(catalog)),39)
    check('Pack 실제 디렉토리 문서 수',len(list(pack_sources[0].parent.glob('*.md'))),21)
    check('Pack 명세 파일트리의 실제 문서 항목',len(tree),19)
    check('구판 BP 레벨별 실제 감소 표',tuple(bp_costs[n] for n in range(1,6)),(5,10,15,20,30))
    check('구판 BP 요약식의 Lv5 감소',5*5,25)
    check('구판 Lv5 감소 표와 요약식의 차이',bp_costs[5]-5*5,5)
    check('구판 Lv1 표 적용의 시작 BP',100-bp_costs[1],95)
    check('구판 하얀여우 시작90과 표 적용의 차이',100-bp_costs[1]-90,5)
    check('구판 민 Lv2와Lv1 적용의 시작 BP',100-bp_costs[2]-bp_costs[1],85)
    check('구판 민 시작75와 표 적용의 차이',100-bp_costs[2]-bp_costs[1]-75,10)
    check('구판 하얀여우 표시 변경량의 산술',90-10-2-1+5,82)
    check('구판 Lv2 제거 절반 회수와 수술 부담의 순합',F(bp_costs[2],2)-2,F(3))
    check('구판 Lv2 비용10p의70퍼센트 환급',F(10*70,100),F(7))
    check('구판 SEN7 에고저항3 지정 목표 예시',7*5+3*5,50)
    check('구판 BP별 명시된 d100 펌블 구간의 너비',tuple(fumble_widths),(1,2,5,10,20))
    check('구판 보고 심각도 선언의63 합계',12+23+11+17,63)
    check('구판 보고 Critical12의 실제 조건부 분리',(len(severity_rows),unconditional,conditional),(12,10,2))
    cyberpunk_pack_foundation_arithmetic={'documents':4,'checks_passed':len(checks)-before_pack,'spec_catalog_counts':dict(Counter(group for group,name in catalog)),'spec_file_tree_entries':len(tree),'actual_pack_documents':21,'BP_costs_by_level':[bp_costs[n] for n in range(1,6)],'level5_formula_difference':5,'level1_table_starting_BP':95,'two_implants_table_starting_BP':85,'printed_hacker_change_total':82,'level2_removal_net_BP':packed(F(3)),'level2_point_refund':packed(F(7)),'old_d100_fumble_band_widths':fumble_widths,'reported_critical_split':[len(severity_rows),unconditional,conditional],'scope':'구판 명세/예시의 지정 행·레벨·변경량·표상 구간을 재계수·검산한다. 같은 합계는 레벨업 차액·치료조건·권리/정체성·구판 전체 엔진 정합을 증명하지 않는다.100p/프리셋을 재작성하거나 BP인간성/사회감점·형성트랙·강제은퇴·옛 비용/대실패를 제5판에 채택하지 않는다.','current_engine_changed':False,'actual_participant_playtest':False}
    files+=pack_sources

    catalog_review=json.loads((here/'이전설계_통합검토.json').read_text())['cyberpunk_pack_interaction_catalog_review']
    detailed={e['name']:e['text'] for e in catalog_review['snapshots']}
    powers=detailed['05_Interactions_Powers.md'];skills=detailed['06_Interactions_Skills.md'];functions=detailed['07_Interactions_Functions.md']
    for e in catalog_review['snapshots']:
        path=root/e['path_relative_to_plan']
        assert e['whole_document_read'] and hashlib.sha256(e['text'].encode()).hexdigest()==e['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
        files.append(path)
    for e in catalog_review['focused_framework_excerpts']:
        path=root/e['path_relative_to_plan'];assert e['excerpt'] in path.read_bytes().decode() and hashlib.sha256(path.read_bytes()).hexdigest()==e['sha256'];files.append(path)
    for phrase in ['3 + 5 + 6 + 5 + 2 + 4 = 25','27','차이값 +11 (Great)','경호대 HP 30','30 + 10 - 5 = **35**','17 + 2 = 19','차이값 +4 → Partial','28 ≤ 35','65 → **55**','-5 → -10']:
        assert phrase in powers,phrase
    for phrase in ['추가 -5%만 적용','+7.5% → 올림 +8%','10.5p → 내림 10p','선언된 Lv의 d6 Pool 소모','Hit 수(4~6)가 실제 흡수량']:
        assert phrase in functions,phrase
    assert '정화 의식 시간 -1 (기본 1 세션 → 0.5 세션)' in skills
    assert '0 ~ 4' in catalog_review['focused_framework_excerpts'][0]['excerpt'] and '10 ~ 19' in catalog_review['focused_framework_excerpts'][0]['excerpt']
    assert 'Hit 수 = 5~6 개수' in catalog_review['focused_framework_excerpts'][1]['excerpt']
    band_rows=data_rows(region(bp,'### 2-5-A.','### 2-5-B.'))
    band=next(row for row in band_rows if row[0]=='51~70');actual_modifier=int(band[4])
    shield_rows=data_rows(region(functions,'### 7-9-B.','### 7-9-C.'));last_shield=next(row for row in shield_rows if row[0]=='5')
    shield_dice=int(re.search(r'Pool (\d+)d6',last_shield[1])[1])
    from math import ceil,floor
    outcomes=list(product(range(1,7),repeat=3))
    before_catalog=len(checks)
    check('구판 샤이닝 예시 폭발 포함 합',sum([3,5,6,5,2,4]),25)
    check('구판 샤이닝 예시 최종 판정',25+2,27)
    check('구판 샤이닝 예시 발동 차이',27-15,12)
    check('구판 샤이닝 예시 실제 사격 차이',(15+3)-12+5,11)
    check('구판 샤이닝 예시 표시 피해',5+4+2,11)
    check('구판 샤이닝 예시 피해 뒤 남는 HP',30-11,19)
    check('구판 매팅 예시 저항 목표',6*5+2*5-5,35)
    check('구판 매팅 예시 폭발 포함 합',sum([5,3,6,1,2]),17)
    check('구판 매팅 예시 최종 판정',17+2,19)
    check('구판 매팅 예시 차이',19-15,4)
    check('구판 매팅 예시 저항 성공',28<=35,True)
    check('구판 매팅 예시 트랙 합',4+2,6)
    check('구판 매팅 예시 변경 후 BP',65-10,55)
    check('구판 BP55의 실제 표상 매팅 수정',actual_modifier,-5)
    check('구판 Lv1에서Lv2로 올리는 BP 차액',bp_costs[2]-bp_costs[1],5)
    check('구판 Lv3 제거 회수 올림',ceil(F(bp_costs[3],2)),8)
    check('구판 Lv3 제거 순회수',ceil(F(bp_costs[3],2))-2,6)
    check('구판 Lv3 포인트 환급 내림',floor(F(15*70,100)),10)
    check('구판 기능 Lv2/Lv1/Lv3 합산 감소',bp_costs[2]+bp_costs[1]+bp_costs[3],30)
    check('구판 기능 Lv2/Lv1/Lv3 장착 후 BP',100-30,70)
    check('구판 의식 시간 문자 그대로1 감소',F(1)-F(1),F(0))
    check('구판 의식 시간 절반 적용',F(1,2),F(1,2))
    check('구판 실드 Lv5 표상 소비',shield_dice,6)
    check('구판 실드 Lv와 소비 표의 차이',shield_dice-5,1)
    check('구판 4이상Hit와Core5이상Hit의 한 주사위 확률',(F(3,6),F(2,6)),(F(1,2),F(1,3)))
    check('구판 같은3d6 모든216경우의 평균Hit 차이',(F(sum(sum(n>=4 for n in row) for row in outcomes),len(outcomes)),F(sum(sum(n>=5 for n in row) for row in outcomes),len(outcomes))),(F(3,2),F(1)))
    cyberpunk_pack_catalog_arithmetic={'documents':3,'checks_passed':len(checks)-before_catalog,'detailed_entries':39,'same_three_dice_outcomes':len(outcomes),'actual_shooting_margin':11,'remaining_example_HP':19,'BP55_actual_legacy_matting_modifier':actual_modifier,'level3_removal_net_BP':6,'level3_point_refund':10,'shield_level5_table_dice':shield_dice,'scope':'상세 카탈로그의 지정 예시·표·차액·반올림·의식 시간·실드 소비/Hit 해석을 원문에 한정해 검산한다. 차이값 표와Ace 자동승격의 결합·치명상 조건·구판 전체 엔진의 의미/승률은 미검증이다. 같은 숫자나 평균은 원전 기능·현재 프로필·실제 참가자 적합성의 합격을 뜻하지 않는다. 형성 트랙/BP/Lv비용/Pool을 제5판에 채택하지 않는다.','current_engine_changed':False,'actual_participant_playtest':False}

    character_tracks=json.loads((here/'이전설계_통합검토.json').read_text())['cyberpunk_pack_character_tracks_review']
    source_texts={e['name']:e['text'] for e in character_tracks['snapshots']}
    tags=source_texts['03_Runner_Tags.md'];presets=source_texts['04_Presets.md'];tracks=source_texts['08_Tracks_Shining_Matting.md']
    for e in character_tracks['snapshots']:
        path=root/e['path_relative_to_plan'];assert hashlib.sha256(path.read_bytes()).hexdigest()==e['sha256']==hashlib.sha256(e['text'].encode()).hexdigest() and e['whole_document_read'];files.append(path)
    groups=Counter(int(n) for n in re.findall(r'(?m)^### 3-([123])-\d+\.',tags))
    costs=dict((int(n),int(cost)) for n,cost in re.findall(r'(\d+) = (\d+)p',region(presets,'### 4-0-D.','### 4-0-E.')))
    package_totals=[];stat_sets=[];stat_sums=[]
    for n in range(1,10):
        pkg=data_rows(region(presets,f'### 4-{n}-C.',f'### 4-{n}-D.'))
        entries=[row for row in pkg if '합계' not in row[0]]
        # A function can show both its two component prices and their sum.
        package_totals.append(sum(int(re.findall(r'(\d+)p',row[-1])[-1]) for row in entries))
        stat_rows=[row for row in data_rows(region(presets,f'### 4-{n}-B.',f'### 4-{n}-C.')) if row[0] in ['BOD','REF','INT','SEN','PRE','LCK']]
        stats={row[0]:int(row[1]) for row in stat_rows};assert len(stats)==6 and all(costs[stats[row[0]]]==int(row[-1].rstrip('p')) for row in stat_rows)
        stat_sets.append(stats);stat_sums.append(sum(costs[value] for value in stats.values()))
    first=stat_sets[0]
    print_block=region(presets,'### 4-1-F.','### 4-1-G.')
    printed=(int(re.search(r'에고 Max:\s+(\d+)',print_block)[1]),int(re.search(r'DSR Max:\s+(\d+)',print_block)[1]),int(re.search(r'd6 Pool 한도:\s+(\d+)',print_block)[1]))
    assert '시작 BP% 80% 이하' in tags and '**95%**' in region(presets,'### 4-7-E.','### 4-7-F.')
    assert '은밀 +1 (1p) · 해킹 +2 (3p)' in region(presets,'### 4-10-B.','### 4-10-C.')
    assert '샤이닝 트라우마 -5 + 생존자 +10 + 순수 BP% +5' in presets
    trauma_headers=re.findall(r'(?m)^#### (\d+)\. (.+)$',region(tracks,'### 8-5-B.','### 8-5-C.'))
    d100_ranges=[]
    for start,end in [('### 8-1-G.','## 8-2.'),('### 8-2-H.','## 8-3.'),('### 8-3-H.','## 8-4.')]:
        bands=[]
        for row in data_rows(region(tracks,start,end)):
            match=re.search(r'(\d{2})-(\d{2})',row[0]);assert match,row[0]
            low,high=map(int,match.groups());bands.append((low,100 if high==0 else high))
        d100_ranges.append(bands)
    assert '**d100 테이블 없음**' in tracks and '10단계 d100 임계 테이블 4종' in tracks
    assert 'd100 62 (심각)' in tracks and '**61-80** | 위기 (Flare)' in tracks
    assert 'DSR 자연 증가 **+50%** (일반 차원 +1 → +2, 오지 차원 +2 → +3)' in tracks
    assert '에고 20 → 각 계층 체류 한계 **2배**' in tracks and '소모량 = (현재 에고 Max) × (T / 체류 한계)' in tracks and '12 × (60/150) = **-4.8**' in tracks
    before_character=len(checks)
    check('구판 실제 태그 세 그룹의 항목 수',tuple(groups[n] for n in range(1,4)),(10,10,10))
    check('구판 실제 태그 총수',sum(groups.values()),30)
    check('구판9프리셋 각 상세 패키지 합',tuple(package_totals),(30,)*9)
    check('구판9프리셋 각 원안 능력치 비용 합',tuple(stat_sums),(68,70,68,72,77,68,68,66,66))
    check('구판G0 실제 표의PRE/SEN',(first['PRE'],first['SEN']),(3,4))
    check('구판G0 표를 적용한에고/DSR/Pool',(max(first['PRE']*2,4),8+first['PRE'],first['BOD']+first['PRE']),(6,11,9))
    check('구판G0 파생 블록에 실제 인쇄된값',printed,(4,10,8))
    check('구판G3 LCK4를3으로 낮춘 조정 합',stat_sums[3]-costs[4]+costs[3],68)
    check('구판G4 INT7을6/LCK2를1로 낮춘 조정 합',stat_sums[4]-costs[7]+costs[6]-costs[2]+costs[1],69)
    check('구판G6의BP95와배경태그 최대80 조건 충족',95<=80,False)
    check('구판G8 형성후유증 포함 순 저항 수정',5+10-5,10)
    check('구판G1 교체 예의 실제 합',3+2+2+10+10+1+3,31)
    check('구판G1 교체 예와30 표기의 차이',31-30,1)
    check('구판 후유증 실제 카탈로그 항목 수',len(trauma_headers),8)
    check('구판 실제 d100 결과표 수',len(d100_ranges),3)
    check('구판 실제3결과표 각각1에서100까지중복없이포괄',tuple([n for low,high in bands for n in range(low,high+1)]==list(range(1,101)) for bands in d100_ranges),(True,True,True))
    check('구판 샤이닝 로그62의 실제 위기행 번호',next(i for i,(low,high) in enumerate(d100_ranges[0],1) if low<=62<=high),4)
    check('구판 차원실조50퍼센트 증가의 올림 전 값',(F(1)*F(3,2),F(2)*F(3,2)),(F(3,2),F(3)))
    check('구판 에고12 선형시간의4계층 한계분',F(150)*F(12,10),F(180))
    check('구판 에고12 선형시간 적용의1시간 소모',F(12)*F(60,180),F(4))
    check('구판 에고12 기본150분 적용의1시간 소모',F(12)*F(60,150),F(24,5))
    check('구판 에고12의 두 시간식 결과 차이',F(24,5)-F(4),F(4,5))
    cyberpunk_pack_character_track_arithmetic={'documents':3,'checks_passed':len(checks)-before_character,'tags_by_group':dict(groups),'tags_total':30,'package_totals':package_totals,'original_stat_cost_totals':stat_sums,'G0_stat_table_PRE_SEN':[first['PRE'],first['SEN']],'G0_correct_legacy_derived_values':[6,11,9],'G0_printed_derived_values':list(printed),'G3_adjusted_stat_total':68,'G4_adjusted_stat_total':69,'G6_BP_tag_requirement_met':False,'G8_net_resistance_modifier':10,'G1_replacement_total':31,'trauma_catalog_items':8,'actual_d100_result_tables':3,'shining_log62_actual_band':4,'ego12_scaled_horizon_minutes':180,'ego12_scaled_hour_loss':packed(F(4)),'ego12_unscaled_hour_loss':packed(F(24,5)),'scope':'구판 태그/프리셋/트랙의 지정 행·예시·자격/합계·분포 포괄·시간식 두 가지를 제한 대조한다. 합30은 같은 인물/자격/효과/플레이 균형을 증명하지 않으며 새로운100p 캐릭터를 작성하지 않는다. 올림 미명시와 로그 발생 경로의 공백·현재 모든 직능/기능·참가자 적합성은 별도다. 구판의 형성 트랙/사회HP·감정/행동 강제·PRE/DSR/Pool/Lv를 현재 규칙으로 승계하지 않는다.','current_engine_changed':False,'old_100point_build_rewritten':False,'actual_participant_playtest':False}

    dsr_drop=json.loads((here/'이전설계_통합검토.json').read_text())['cyberpunk_pack_dsr_dropout_review']
    sources={e['name']:e['text'] for e in dsr_drop['snapshots']}
    for e in dsr_drop['snapshots']:
        path=root/e['path_relative_to_plan'];assert hashlib.sha256(path.read_bytes()).hexdigest()==e['sha256']==hashlib.sha256(e['text'].encode()).hexdigest() and e['whole_document_read'];files.append(path)
    dsr=sources['09_DSR_Detail.md'];drop=sources['10_Dropout.md']
    campaign=region(dsr,'### 9-3-E.','## 9-4.')
    changes=[int(value) for value in re.findall(r'→ DSR ([+-]\d+)',campaign)]
    assert changes==[1,1,1,-1,1,-2,-1] and '세션 순 변동: +1' in campaign
    assert '만트라 건 등 Pack 특수 장비는 +1 추가' in dsr
    assert 'pool_before: 13' in dsr and 'increase: +1' in region(dsr,'### 9-7-D.','### 9-7-E.')
    dashboard=region(dsr,'### 9-7-E.','## 9-8.')
    increase=F(re.search(r'average_dsr_per_session_increase: ([\d.]+)',dashboard)[1]);decrease=F(re.search(r'average_dsr_per_session_decrease: ([\d.]+)',dashboard)[1])
    max_dsr=int(re.search(r'dsr_max: (\d+)',dashboard)[1]);current_dsr=int(re.search(r'current_dsr: (\d+)',dashboard)[1])
    samples=region(drop,'### 10-9-A.','## 10-10.')
    assert '피해: 1d8+2 × 3 = 26' in samples and 'HP 12 → -14' in samples
    assert 'PRE 9 Grade 6d6' in samples and '패러독스 트랙 10 → 8' in samples and '-3 총계' in samples
    prior_tracks=source_texts['08_Tracks_Shining_Matting.md']
    paradox=region(prior_tracks,'### 8-3-H.','## 8-4.')
    paradox_bands=[]
    for row in data_rows(paradox):
        m=re.search(r'(\d{2})-(\d{2})',row[0]);assert m
        low,high=map(int,m.groups());paradox_bands.append((low,100 if high==0 else high,row[2]))
    band67=next((i,text) for i,(low,high,text) in enumerate(paradox_bands,1) if low<=67<=high)
    assert '시간선을 먹음' in band67[1] and '시야 공유' in samples
    grade_ref=dsr_drop['prior_sources_reused']['framework_grade_9'];path=root/grade_ref['path_relative_to_plan'];text=path.read_text()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==grade_ref['sha256'] and grade_ref['focused_text'] in text;files.append(path)
    grade9=re.search(r'(?m)^\| 9 \| (\dd\d+) \|',text)[1]
    chart=region(drop,'### 10-2-B.','### 10-2-C.');assert 'HP -1 ~ -BOD' in chart and 'HP ≤ -(BOD × 2)' in chart
    before_dsr_dropout=len(checks)
    check('구판DSR 캠페인에 기록된 순변동',sum(changes),0)
    check('구판DSR 표시 순변동1과 로그합 차이',1-sum(changes),1)
    check('구판DSR 만트라 특수장비추가1까지 적용한 순변동',sum(changes)+1,1)
    check('구판Pool 변화와말미3에필요한미기록시작값',((5-5+4-10),3-(5-5+4-10)),(-6,9))
    check('구판DSR Max13 현재12 증가3의넘침/잔여',divmod(12+3,13),(1,2))
    check('구판YAML Max14가정 현재13 증가1의넘침/잔여',divmod(13+1,14),(1,0))
    check('구판확장본문비용3을Max14현재13에적용한넘침/잔여',divmod(13+3,14),(1,2))
    net=increase-decrease
    check('구판대시보드 순증가와일정속도 조건부세션수',(net,F(max_dsr-current_dsr)/net),(F(1,2),F(10)))
    check('구판샘플A HP감산과선언경계도달',(12-26,-6*2,(12-26)<=-6*2),(-14,-12,True))
    check('구판샘플A 에고감산',9-4,5)
    check('구판샘플A 인쇄주사위합/보정과TN차이',(5+3+4+6+2,5+3+4+6+2-15),(20,5))
    check('구판샘플B 패러독스발동값',9+1,10)
    check('구판샘플B d10067의실제패러독스표 행',band67[0],4)
    check('구판공통명세의능력치9 Grade',grade9,'5d8')
    check('구판샘플B 인쇄주사위합/보정과TN차이',(2+3+1+4+2+5+3,2+3+1+4+2+5+3-15),(20,5))
    check('구판샘플B 에고감산',12-5,7)
    check('구판샘플B 선언된정화2와의식1뒤패러독스',10-2-1,7)
    check('구판샘플B 표시8과감산7의차이',8-(10-2-1),1)
    gap=[hp for hp in range(-14,2) if not (hp>=1 or hp==0 or -7<=hp<=-1 or hp<=-14)]
    check('구판BOD7 지정HP표의미지정구간',tuple(gap),tuple(range(-13,-7)))
    expanded=any(a+b+c+6==26 for a,b,c in product(range(1,9),repeat=3))
    single=any((a+2)*3==26 for a in range(1,9))
    check('구판26피해를3d8합/단일d8전체삼배로해석할때가능여부',(expanded,single),(True,False))
    standalone_tables=re.findall(r'(?m)^\|[^\n|]*\d{2}[-~]\d{2}[^\n|]*\|',drop)
    check('구판드랍아웃 자체d100 임계행 실제수',len(standalone_tables),0)
    cyberpunk_pack_dsr_dropout_arithmetic={'documents':2,'checks_passed':len(checks)-before_dsr_dropout,'logged_DSR_net':0,'special_gear_qualified_DSR_net':1,'inferred_unwritten_opening_d6_pool':9,'extended_flashback_source_YAML_increase':1,'extended_flashback_body_increase':3,'conditional_dashboard_sessions':10,'sample_A_HP_after_damage':-14,'sample_A_ego_after_loss':5,'sample_B_actual_d10067_band':4,'legacy_stat9_grade':'5d8','sample_B_declared_paradox_after_losses':7,'sample_B_printed_paradox':8,'BOD7_omitted_HP_values':gap,'ambiguous_26_damage_has_expanded_reading':True,'own_numeric_d100_threshold_rows':0,'scope':'09/10의지정로그·대시보드·초과잔여·샘플A/B·BOD7표와이전08/공통명세의참조행을제한검산한다. 시작Pool9·Max14·일정속도10세션은조건/추론값이며완전플레이검증이나현재DSR채택이아니다.26피해는해석을구분하고폭발주사위/보정자격·부족한진행로그를미상수치로메우지않는다. 신단/정비/관조의서로다른규격과재진입/사망묶음은이관판단으로따로남긴다.','current_engine_changed':False,'actual_participant_playtest':False}

    weapon_review=json.loads((here/'이전설계_통합검토.json').read_text())['cyberpunk_pack_weapon_review']
    weapon_source=weapon_review['snapshots'][0];weapon=weapon_source['text'];path=root/weapon_source['path_relative_to_plan']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==weapon_source['sha256']==hashlib.sha256(weapon.encode()).hexdigest() and weapon_source['whole_document_read'];files.append(path)
    headings=re.findall(r'(?m)^## (.+)$',weapon)
    catalog=weapon_review['catalog_rows'];counts=weapon_review['catalog_counts']
    bad=next(e for e in catalog if e['legacy_name']=='전투 활 (신기 강화)')
    kits=data_rows(region(weapon,'### 11-11-D.','## 11-12.'))
    kit_totals=[int(re.sub(r'[^0-9]','',row[3])) for row in kits]
    a=region(weapon,'### 11-13-A.','### 11-13-B.');b=region(weapon,'### 11-13-B.','### 11-13-C.');c=region(weapon,'### 11-13-C.','## 11-14.')
    assert '3+5+4+6+2+1 = 21' in a and '차이: +12' in a and '4+3 = 7 + 2 = 9' in a
    assert '2+5+3+6+4 = 20' in b and '6d4 = 평균 15' in b
    assert '5+5+4+6+5+3 = 28 + 9 = 37' in c and '8+11+7 = 26' in c
    assert '1 오얏 ≈ 1만원 ≈ 1크레딧' in weapon and '1 오얏 = 10,000 크레딧' in weapon
    deck=region(weapon,'### 11-15-C.','### 11-15-D.')
    deck_counts=tuple(len(data_rows(region(deck,f'#### 11-15-C-{n}.',f'#### 11-15-C-{n+1}.'))) if n<4 else len(data_rows(deck[deck.index('#### 11-15-C-4.'):])) for n in range(1,5))
    cells=data_rows(region(weapon,'### 11-7-B.','### 11-7-C.'))[:6]
    assert [int(re.sub(r'[^0-9]','',row[-1])) for row in cells[:3]]==[15,15,15]
    before_weapon=len(checks)
    check('구판장비 실제 대분류제목 수',len(headings),18)
    check('구판장비 중복11-15 제목 수',sum(h.startswith('11-15.') for h in headings),2)
    check('구판무기9개 주표그룹 실제행수',tuple(counts[k] for k in 'ABCDEFGHI'),(26,12,15,7,5,6,15,9,5))
    check('구판무기 주표행수 합',sum(counts.values()),100)
    check('구판주표100과별도크로코다일1 합',len(catalog)+1,101)
    check('구판v02취득선언110과현재주카탈로그101 차이',110-(len(catalog)+1),9)
    check('구판전투활 상세표 실제열수와표머리열수',(bad['actual_columns'],bad['expected_columns']),(7,8))
    check('구판8무장세트에표시한가격하한합',tuple(kit_totals),(420,400,1150,900,1700,2500,2500,50000))
    check('구판외장단말4분류 사양수',deck_counts,(3,3,3,3))
    check('구판까마귀의인쇄공격/방어/차이',(3+5+4+6+2+1+5,4+2+5+3,26-14),(26,14,12))
    check('구판까마귀9피해의독립2d6/단일d6전체배수 해석',(any(x+y+2==9 for x,y in product(range(1,7),repeat=2)),any(2*(x+1)==9 for x in range(1,7))),(True,False))
    check('구판까마귀 두배수해석의평균/분산',(F(9),4*F(35,12),2*F(35,12)),(F(9),F(35,3),F(35,6)))
    check('구판벽사종 인쇄공격합/TN차이',(2+5+3+6+4+3,23-15),(23,8))
    check('구판벽사종 두배수해석의평균/분산',(F(15),4*3*F(15,12),6*F(15,12)),(F(15),F(15),F(15,2)))
    check('구판새매 인쇄공격/방어/TN차이',(5+5+4+6+5+3+9,4+3,37-7),(37,7,30))
    check('구판새매26피해의독립3d12/단일d12전체배수 해석',(any(x+y+z==26 for x,y,z in product(range(1,13),repeat=3)),any(3*x==26 for x in range(1,13))),(True,False))
    check('구판새매 두배수해석의평균/분산',(3*F(13,2),9*F(143,12),3*F(143,12)),(F(39,2),F(429,4),F(143,4)))
    check('구판돌칩표준탄12발 가격',12*F(3,10),F(18,5))
    check('구판500세션비의표준12발탄창가 대비배수',F(500)/F(18,5),F(1250,9))
    check('구판부록오얏환산의개인/공용/월유지비 크레딧',(5000*10000,100*10000,200*10000),(50000000,1000000,2000000))
    check('구판보험월500과제시월수입200/300의비율',(F(500,200),F(500,300)),(F(5,2),F(5,3)))
    check('구판A/B/C형 전원표가격',tuple(int(re.sub(r'[^0-9]','',row[-1])) for row in cells[:3]),(15,15,15))
    check('구판본문1크레딧비교와부록1만크레딧비교 차이배수',10000//1,10000)
    cyberpunk_pack_weapon_arithmetic={'documents':1,'checks_passed':len(checks)-before_weapon,'major_headings':18,'duplicated_11_15_headings':2,'main_catalog_table_rows':100,'with_standalone_crocodile':101,'declared_prior_v02_inventory':110,'malformed_battle_bow_columns':[7,8],'weapon_set_lower_bounds':kit_totals,'external_deck_variants_by_type':list(deck_counts),'damage_multiplier_interpretations_not_same_distribution':True,'flat_ammo_fee_to_standard_magazine_ratio':packed(F(1250,9)),'own_core_damage_multipliers_adopted':False,'current_engine_changed':False,'scope':'무기/장비1086줄의지정행/표구조·무장세트가격하한·단말사양수·인쇄공격합·피해주사위배수두해석·탄약비/보험비교·구판부록환산을제한검산한다.원전110개전체검토나현재101제품의성능/가격검증·구매가능/전투균형·현실화폐환산을증명하지않는다. 피해배수는독립주사위와한번굴린피해전체배수의분포를구분하며현재규칙으로승계하지않는다.','actual_participant_playtest':False}

    before_npc=len(checks)
    npc_review=json.loads((here/'이전설계_통합검토.json').read_text())['cyberpunk_pack_NPC_review']
    npc_source=root/npc_review['snapshots'][0]['path_relative_to_plan'];npc_text=npc_source.read_text();files.append(npc_source)
    blocks=[]
    headings=list(re.finditer(r'^### (12-[1-5]-[B-Z])\. (.*)$',npc_text,re.M))
    for match in headings:
        nxt=re.search(r'^#{2,3} ',npc_text[match.end():],re.M);end=match.end()+nxt.start() if nxt else len(npc_text)
        b=npc_text[match.start():end]
        stats={s:(int(n),dice) for s,n,dice in re.findall(r'\b(BOD|REF|INT|SEN|PRE|LCK)\s+(\d+)\s*=\s*(\d+d\d+)',b)}
        hp,ego,resist=map(int,re.search(r'HP (\d+) / 에고 Max (\d+) / 에고 저항 (\d+)',b).groups())
        dsr,luck,pool=map(int,re.search(r'DSR Max (\d+) / 운 토큰 Max (\d+) / d6 Pool 한도 (\d+)',b).groups())
        printed_init=F(re.search(r'Initiative =[^\n]*평균 ([\d.]+)',b)[1])
        computed_init=sum(F(int(d.split('d')[0])*(int(d.split('d')[1])+1),2) for d in [stats['REF'][1],stats['SEN'][1]])
        blocks.append({'section':match[1],'stats':stats,'HP':hp,'Ego':ego,'resistance':resist,'DSR':dsr,'luck':luck,'pool':pool,'printed_init':printed_init,'computed_init':computed_init,'text':b})
    check('구판NPC 실물블록수',len(blocks),17)
    check('구판NPC 창작/원전이름기반 분리',(sum(b['section'][3]!='5' for b in blocks),sum(b['section'][3]=='5' for b in blocks)),(13,4))
    check('구판NPC 실제절별블록수',tuple(sum(b['section'][3]==str(i) for b in blocks) for i in range(1,6)),(3,3,3,4,4))
    check('구판NPC17 HP인쇄식 검산',[b['HP'] for b in blocks],[b['stats']['BOD'][0]*5 for b in blocks])
    check('구판NPC17 에고Max인쇄식 검산',[b['Ego'] for b in blocks],[max(b['stats']['PRE'][0]*2,4) for b in blocks])
    check('구판NPC17 에고저항인쇄식 검산',[b['resistance'] for b in blocks],[b['Ego']//3 for b in blocks])
    check('구판NPC17 DSR인쇄식 검산',[b['DSR'] for b in blocks],[8+b['stats']['PRE'][0] for b in blocks])
    check('구판NPC17 운토큰인쇄식 검산',[b['luck'] for b in blocks],[b['stats']['LCK'][0]*2 for b in blocks])
    check('구판NPC17 Pool인쇄식 검산',[b['pool'] for b in blocks],[b['stats']['BOD'][0]+b['stats']['PRE'][0] for b in blocks])
    check('구판NPC17 Initiative인쇄평균 검산',[b['printed_init'] for b in blocks],[b['computed_init'] for b in blocks])
    grade_path=root/dsr_drop['prior_sources_reused']['framework_grade_9']['path_relative_to_plan']
    grade_map={int(n):dice for n,dice in re.findall(r'^\| (\d+) \| (\d+d\d+) \|',grade_path.read_text(),re.M)}
    grade_differences=[(b['section'],s,n,dice,grade_map[n]) for b in blocks for s,(n,dice) in b['stats'].items() if dice!=grade_map[n]]
    check('구판NPC102스탯중 Grade명세와다른2행',grade_differences,[('12-5-D','BOD',9,'6d6','5d8'),('12-5-E','LCK',13,'8d10','7d10')])
    bounds={'1':(2,4),'2':(5,7),'3':(8,11),'4':(12,17)}
    outside=[(b['section'],s,n) for b in blocks if b['section'][3] in bounds for s,(n,dice) in b['stats'].items() if not bounds[b['section'][3]][0]<=n<=bounds[b['section'][3]][1]]
    check('구판NPC등급스탯이탈절대금지와실제19행',len(outside),19)
    header=re.search(r'\*\*분야\*\*:.*4등급 (\d+)종',npc_text)
    check('구판NPC헤더샘플12와실제13 차이',13-int(header[1]),1)
    late=re.search(r'본 카탈로그 (\d+)\+(\d+)종',npc_text)
    check('구판NPC후반12더하기3과실제17 차이',17-sum(map(int,late.groups())),2)
    check('구판하얀모자 평균9.5대12의실제차이',F(3*(4+1),2)+2-12,F(-5,2))
    check('구판한씨사회예의정확한성공수와분모',(sum(sum(d)+2>=10 for d in product(range(1,5),repeat=3)),4**3),(32,64))
    check('구판Critical확정의반례 최소사격차이',(9+7-24,9+6-22),(-8,-7))
    cyberpunk_pack_NPC_arithmetic={'documents':1,'checks_passed':len(checks)-before_npc,'NPC_blocks':17,'sample_blocks':13,'original_name_based_blocks':4,'derived_value_groups_checked':6,'derived_value_cells_checked':102,'initiative_means_checked':17,'grade_map_cells_checked':102,'grade_differences':[list(x) for x in grade_differences],'outside_declared_stat_range':outside,'legacy_number_derivation_is_current_adoption':False,'source_critical_guarantee_counterexamples':[-8,-7],'current_engine_changed':False,'scope':'17블록의인쇄파생6값·평균/Grade명세·등급범위·제시수량·지정확률/평균/확정Critical반례를독립추출/제한검산. 전NPC전투력/원전정사/현재자동환산·균형·실제참가자검증아님.','actual_participant_playtest':False}

    before_large=len(checks)
    large_review=json.loads((here/'이전설계_통합검토.json').read_text())['cyberpunk_pack_large_entity_review']
    large_path=root/large_review['snapshots'][0]['path_relative_to_plan'];large_text=large_path.read_text();files.append(large_path)
    heads=list(re.finditer(r'^### (13-[2-6]-[A-Z])\. (.*)$',large_text,re.M));large_blocks={}
    for match in heads:
        nxt=re.search(r'^#{2,3} ',large_text[match.end():],re.M);end=match.end()+nxt.start() if nxt else len(large_text)
        large_blocks[match[1]]=large_text[match.start():end]
    check('구판대형 실제블록수',len(large_blocks),11)
    check('구판대형 대분류수',len(re.findall(r'^## ',large_text,re.M)),10)
    check('구판대형 절별4/2/3/1/1 구성',tuple(sum(code[3]==str(i) for code in large_blocks) for i in range(2,7)),(4,2,3,1,1))
    def part_values(code):
        block=large_blocks[code];start=block.index('다중 HP 블록');stop=block.index('\n저격 포인트',start)
        return [int(n) for n in re.findall(r'^\s*\[[^\n]+?\]:\s*(?:각\s*)?(?:HP\s*)?(\d+)',block[start:stop],re.M)]
    weights={'13-2-A':[1,1,2,4,1],'13-2-B':[1,1,6,2,4],'13-2-C':[1,2,1,1,1],'13-4-A':[1,1,6,1,1],'13-4-B':[1,1,1,4],'13-4-C':[1,1,1,1,2,1],'13-6-A':[1,2,1,2,1]}
    part_sums={}
    for code,multiplicities in weights.items():
        values=part_values(code);assert len(values)==len(multiplicities),(code,values)
        part_sums[code]=sum(n*k for n,k in zip(values,multiplicities))
    check('구판대형7블록의인쇄부품수량합',list(part_sums.values()),[1230,1060,950,890,1170,200,1550])
    white=part_values('13-2-D');assert len(white)==7
    check('구판백무의서로다른형태HP합',(white[0],white[1]+white[2]+white[3]+6*white[4],white[5]+white[6]),(150,860,450))
    plant=large_blocks['13-4-B'];coolers=part_values('13-4-B')[-1]
    check('구판플랜트4냉각부합',4*coolers,320)
    first_timeout=int(re.search(r'2 이상 파손.*?(\d+) 라운드 후 사고',plant)[1]);second_timeout=int(re.search(r'과열 폭발.*?(\d+) 라운드 카운트다운',plant,re.S)[1])
    check('구판동일플랜트5/10회차기한의60초기준초',(first_timeout*60,second_timeout*60),(300,600))
    fat=large_text[large_text.index('### 13-7-C.'):large_text.index('### 13-7-D.')]
    b=re.search(r'Scale B PC = (\d+)~(\d+) 라운드 \((\d+)~(\d+)초',fat);bround=tuple(map(int,b.groups()[:2]));seconds=tuple(map(int,b.groups()[2:]));durations=[rounds*sec for rounds,sec in product(bround,seconds)]
    check('구판FatRound_B양끝조합이60초인경우와아닌경우',(sum(n==60 for n in durations),sorted(durations)),(2,[40,60,60,90]))
    a=re.search(r'Scale A PC.*?= (\d+) 라운드 \((\d+)초',fat);rounds,secs=map(int,a.groups());current_round=json.loads((here/'운송_프로필.json').read_text())['round_seconds']
    check('구판FatRound_A와현재공통5초10회차',(rounds*secs,rounds*current_round),(60,50))
    tide=large_blocks['13-5-A'];speed=int(re.search(r'이동 속도 (\d+)km/h',tide)[1])
    meters_per_second=F(speed*1000,3600)
    check('구판해일30kmh의초당거리',meters_per_second,F(25,3))
    check('구판해일5초와60초동안의이동거리',(meters_per_second*5,meters_per_second*60),(F(125,3),F(500)))
    check('구판50m이상격자의3/5/2넉백하한',(3*50,5*50,2*50),(150,250,100))
    clock_rows=re.findall(r'^\s*\[[^\]]+\]\s+([█░]+)\s*\((\d+)/6\)',large_text,re.M)
    check('구판대형도주/위험도안표행',len(clock_rows),17)
    mismatches=[(diagram,int(number)) for diagram,number in clock_rows if diagram.count('█')!=int(number)]
    check('구판위험도안채움과분자상충행수',len(mismatches),14)
    check('구판공중탈출마이너스3은6에서0이아님',6-3,3)
    guard=json.loads((here/'NPC_프로필.json').read_text())['templates'][3]['body']
    old_raw_min=5+15;after_armor=max(0,old_raw_min-guard['armor'])
    check('구판적룡브레스최저값을그대로옮길때현재N04HP',(old_raw_min,after_armor,max(0,guard['hp_max']-after_armor)),(20,19,0))
    check('구판부품합과인쇄본체HP의상이한비율',(F(part_sums['13-4-C'],80),F(part_sums['13-4-A'],300)),(F(5,2),F(89,30)))
    cyberpunk_pack_large_arithmetic={'documents':1,'checks_passed':len(checks)-before_large,'entity_blocks':11,'major_sections':10,'part_HP_sums':part_sums,'part_sums_are_current_whole_body_HP':False,'white_form_part_sums':[150,860,450],'plant_conflicting_deadline_seconds_at_60s_round':[300,600],'clock_rows':17,'clock_diagram_mismatches':14,'old_A_rounds_at_6s_and_current_5s':[60,50],'tide_meters_per_second':packed(meters_per_second),'minimum_old_breath_damage_on_current_guard':[20,19,0],'current_engine_changed':False,'legacy_damage_values_adopted':False,'scope':'11개 블록의지정부품수량/인쇄HP합·동일시설기한상충·FatRound동기/속도/격자·위험도표기·자동안전권과피해환산반례를제한검산한다. 원전정사/대형물리/현재전체HP·신수균형이나참가자검증을증명하지않는다.','actual_participant_playtest':False}

    before_glossary=len(checks)
    glossary_review=json.loads((here/'이전설계_통합검토.json').read_text())['cyberpunk_pack_glossary_review']
    texts={}
    for row in glossary_review['snapshots']:
        path=root/row['path_relative_to_plan'];texts[row['name']]=path.read_bytes().decode();files.append(path)
    glossary=texts['14_Pack_Glossary.md'];readme=texts['README.md']
    in_fence=False;area='';actual_h3=[];term_titles=[];by_area=[0]*5
    for line in glossary.splitlines():
        if line.lstrip().startswith('```'):in_fence=not in_fence
        if in_fence:continue
        if line.startswith('## '):area=line[3:]
        if line.startswith('### '):
            actual_h3.append(line[4:])
            match=re.match(r'14-([1-5])\.',area)
            if match:term_titles.append(line[4:]);by_area[int(match[1])-1]+=1
    check('구판용어실제표제별칭폐기약어포함',len(term_titles),259)
    check('구판용어정렬영역별표제수',by_area,[42,49,64,81,23])
    check('구판용어코드예문제외3단제목수',len(actual_h3),277)
    check('구판용어대분류수',len(re.findall(r'^## ',glossary,re.M)),11)
    matrix=glossary[glossary.index('## 14-6.'):glossary.index('## 14-7.')]
    matrix_rows=[line for line in matrix.splitlines() if line.startswith('|') and not line.startswith('|---')][1:]
    check('구판용어교차참조본문행',len(matrix_rows),31)
    distribution=glossary[glossary.index('### FEWK 전용 용어 분포'):glossary.index('### FEWK Pack 고유 장치')]
    values=[int(re.search(r'(?:약 )?(\d+)',line.split('|')[2])[1]) for line in distribution.splitlines() if line.startswith('|') and not line.startswith('|---') and '용어 수' not in line and '**합계**' not in line]
    nominal=int(re.search(r'\| \*\*합계\*\*.*?약 (\d+)',distribution)[1])
    check('구판용어근사분류표의행수합과별도표시합계',(len(values),sum(values),nominal),(16,193,190))
    unit_block=glossary[glossary.index('### 자·해·경·조·만·양'):glossary.index('### 1오얏 체감표')]
    unit_exps={name:int(exp) for name,exp in re.findall(r'- \*\*(양|자|해|경|조|만) \([^)]*\)\*\*: 10\^(\d+)',unit_block)}
    assert len(unit_exps)==6 and '**1 바이트**: 10^0' in unit_block
    layer_block=glossary[glossary.index('### 차원 계층 0~6층'):glossary.index('### 축적계 →')]
    layer_exps=[]
    for i in range(7):
        line=next(line for line in layer_block.splitlines() if line.startswith(f'- **{i}층**'))
        unit=re.search(r'1(양|자|해|경|조|만) 바이트',line)
        layer_exps.append(unit_exps[unit[1]] if unit else 0)
    check('구판차원0부터6의인쇄단위지수',layer_exps,[24,20,16,12,4,0,28])
    lower_ratios=[10**(layer_exps[i]-layer_exps[i+1]) for i in range(5)]
    check('구판하위층인접밀도비와조에서만의누락',lower_ratios,[10000,10000,10000,100000000,10000])
    check('구판6층고차원은0층기준1만배',10**(layer_exps[6]-layer_exps[0]),10000)
    code_block=glossary[glossary.index('### 코드 크레딧'):glossary.index('### 코핀 (')]
    code_oyat=int(re.search(r'1 코드 = (\d+) 오얏',code_block)[1]);patch_credits=int(re.search(r'1 오얏 = ([\d,]+) 크레딧',glossary)[1].replace(',',''))
    check('구판코드와패치크레딧을동일단위라가정할때역환산불일치비',F(code_oyat,1)*patch_credits,F(100000))
    files_section=readme[readme.index('## 파일 구조'):readme.index('## 독서 순서')]
    files_rows=[line for line in files_section.splitlines() if line.startswith('|') and not line.startswith('|---') and '| 파일 | 내용 |' not in line and '| # | 파일 | 내용 |' not in line]
    declared=int(re.search(r'## 파일 구조 \((\d+)개\)',readme)[1])
    pack_files=[entry for entry in json.loads((here/'이전설계_통합검토.json').read_text())['bounded_older_source_inventory']['files'] if 'Cyberpunk Pack' in entry['path_relative_to_plan']]
    check('구판README파일표행현재파일수표제선언',(len(files_rows),len(pack_files),declared),(19,21,18))
    check('구판README대분류수',len(re.findall(r'^## ',readme,re.M)),9)
    critical=readme[readme.index('### v0.3 Critical 12건'):readme.index('### Major 23')]
    check('구판README완료표시12개와63건합',(len(re.findall(r'^- \[x\]',critical,re.M)),12+23+11+17),(12,63))
    alpha=int(re.search(r'Alpha 플레이테스트 (\d+)회',readme)[1]);planned_alpha=int(re.search(r'Alpha 플레이테스트 (\d+) 세션',readme)[1]);planned_beta=int(re.search(r'Beta 테스트 (\d+) 세션',readme)[1])
    check('구판README실제0회와계획10/30회구분',(alpha,planned_alpha,planned_beta),(0,10,30))
    cyberpunk_pack_glossary_arithmetic={'documents':2,'checks_passed':len(checks)-before_glossary,'term_heading_entries':len(term_titles),'term_entries_by_area':by_area,'actual_H3_outside_fences':len(actual_h3),'major_sections':[11,9],'cross_reference_rows':len(matrix_rows),'approximate_distribution_values_sum':sum(values),'approximate_declared_total':nominal,'all_term_headings_are_distinct_canonical_terms':False,'layer_printed_unit_exponents':layer_exps,'lower_adjacent_density_ratios':lower_ratios,'assumed_same_code_credit_unit_contradiction_factor':packed(F(code_oyat,1)*patch_credits),'code_and_credit_are_same_unit_proven':False,'README_file_table_rows':len(files_rows),'current_pack_files':len(pack_files),'README_declared_files':declared,'README_checked_Critical_rows':12,'old_review_count_sum':63,'README_actual_playtest_count':alpha,'planned_alpha_beta':[planned_alpha,planned_beta],'current_engine_changed':False,'legacy_currency_conversion_adopted':False,'all_source_canonical_facts_verified':False,'scope':'표제/행/명세 집계·표준 단위표의 밀도비·가정된 코드/크레딧 역환산 상충·과거 검사 선언과 플레이시험0회를 제한 검산. 근사분류 합193/표시190과 실제표제259는 고유 정사용어 수의 증명이 아니며 실제 통화 동일성·전세계 이동물리/시세·참가자 시험을 증명하지 않는다.','actual_participant_playtest':False}

    before_deck_audit=len(checks)
    deck_review=json.loads((here/'이전설계_통합검토.json').read_text())['cyberpunk_pack_deck_audit_review']
    deck_texts={}
    for row in deck_review['snapshots']:
        path=root/row['path_relative_to_plan'];deck_texts[row['name']]=path.read_bytes().decode();files.append(path)
    waiting=next(text for name,text in deck_texts.items() if name!='_Consistency_Check_Pack_v0.1.md');audit=deck_texts['_Consistency_Check_Pack_v0.1.md']
    section_counts=[len(re.findall(r'^## ',text,re.M)) for text in [waiting,audit]]
    check('대기문서와검사이력주요절',section_counts,[12,15])
    conditions=waiting[waiting.index('### 11-C.'):waiting.index('## 12.')]
    checked=len(re.findall(r'^- \[x\]',conditions,re.M));unchecked=len(re.findall(r'^- \[ \]',conditions,re.M))
    check('처리완료표시와실제세조건중두체크한미처리',(checked,unchecked,checked+unchecked),(2,1,3))
    pending=waiting[waiting.index('### 12-B.'):waiting.index('### 12-C.')]
    pending_rows=re.findall(r'^\d+\. ',pending,re.M)
    check('처리완료이후명시된미처리항목',len(pending_rows),5)
    concept_counts=[]
    for a,b in [('### 3-1.','### 3-2.'),('### 3-2.','### 3-3.'),('### 3-3.','## 4.')]:
        block=waiting[waiting.index(a):waiting.index(b)]
        concept_counts.append(len(re.findall(r'^\| \*\*',block,re.M)))
    check('대기문서차원바이트존재개념목록',concept_counts,[16,9,5])
    todo=waiting[waiting.index('### 7-A.'):waiting.index('### 7-B.')]
    check('누락개념체크리스트항목과바이트밀도중복',(len(re.findall(r'^- \[ \]',todo,re.M)),todo.count('**바이트 밀도**')),(18,2))
    units=waiting[waiting.index('### 2-2.'):waiting.index('## 3.')]
    exps=[int(x) for x in re.findall(r'\| 10\^(\d+) \|',units)]
    check('대기문서밀도표인쇄지수',exps,[24,20,16,12,4,0,28])
    check('대기문서조에서만의인접밀도비',10**(exps[3]-exps[4]),100000000)
    # 60kg is a stated counterexample assumption, not a source body profile or travel rule.
    example_mass_grams=60000;example_ratio=F(example_mass_grams*10**exps[0],10**exps[6])
    check('전신량과1g단위비교는g당밀도비와다름',(F(10**exps[0],10**exps[6]),example_ratio),(F(1,10000),F(6)))
    scope=audit[audit.index('### 0-1.'):audit.index('### 0-2.')]
    read_modes=[line.split('|')[2].strip() for line in scope.splitlines() if line.startswith('| `')]
    read_counts={'whole':sum(mode=='전문' for mode in read_modes),'partial':sum(mode not in ['전문','스킵 (공식 Grep)','**MISSING**'] for mode in read_modes),'skipped':sum(mode=='스킵 (공식 Grep)' for mode in read_modes),'missing':sum(mode=='**MISSING**' for mode in read_modes)}
    check('검사초기범위전문부분스킵미존재',(len(read_modes),read_counts),(17,{'whole':9,'partial':6,'skipped':1,'missing':1}))
    initial=tuple(int(x) for x in re.search(r'Critical (\d+)건·Major (\d+)건·Minor (\d+)건 잔존',audit).groups())
    check('과거초기미처리등급과합',(initial,sum(initial)),((3,9,8),20))
    initial_patch=tuple(int(x) for x in re.search(r'Critical (\d+)건·Major 주요 (\d+)건·Minor (\d+)건 = 총 (\d+)건',audit).groups())
    remaining=tuple(int(x) for x in re.search(r'Major (\d+)건 \+ Minor (\d+)건 = (\d+)건',audit).groups())
    check('부록C정정합과부록D잔여합',(initial_patch,sum(initial_patch[:3]),remaining,sum(remaining[:2])),((3,5,2,10),10,(4,6,10),10))
    final_total=sum([12,23,11,17]);claimed_total=int(re.search(r'수정리스트1.md의 (\d+)건',audit)[1])
    check('부록E선언등급별건수합과별도63건표시',(final_total,claimed_total),(63,63))
    cyberpunk_pack_deck_audit_arithmetic={'documents':2,'checks_passed':len(checks)-before_deck_audit,'major_sections':section_counts,'completion_checkboxes_checked':checked,'completion_checkboxes_pending':unchecked,'explicit_pending_rows':len(pending_rows),'concept_inventory_counts':concept_counts,'TODO_concept_rows':18,'byte_density_repeated_rows':2,'printed_density_exponents':exps,'jo_to_man_printed_density_ratio':100000000,'illustrative_mass_grams':example_mass_grams,'illustrative_body_to_one_high_gram_byte_ratio':packed(example_ratio),'illustrative_mass_is_source_canonical_profile':False,'illustrative_ratio_is_travel_permission':False,'initial_audit_scope_rows':len(read_modes),'initial_read_modes':read_counts,'initial_issue_count':sum(initial),'appendix_C_changed_count':10,'appendix_D_remaining_count':10,'appendix_E_claimed_count':claimed_total,'all_audit_completion_claims_verified':False,'current_engine_changed':False,'old_100point_build_rewritten':False,'scope':'두 자료의 절·항목·체크 상태와 과거 건수를 제한 검산. g당 밀도와 전신량을 섞은 주장은 가정한60kg 반례로 구분하며 실제 이동 허가·신체 구성·시세 또는 과거 완료 선언 전체를 증명하지 않는다.','actual_participant_playtest':False}

    before_world_correction=len(checks)
    wc_review=json.loads((here/'이전설계_통합검토.json').read_text())['cyberpunk_pack_world_correction_review'];wc_texts={}
    for row in wc_review['snapshots']:
        path=root/row['path_relative_to_plan'];wc_texts[row['name']]=path.read_bytes().decode();files.append(path)
    background=wc_texts['01_World_Background.md'];correction=next(text for name,text in wc_texts.items() if name!='01_World_Background.md')
    check('세계배경본문후속패치와수정목록대분류', [len(re.findall(r'^## ',x,re.M)) for x in [background,correction]],[18,9])
    summary=correction[correction.index('### 0-3.'):correction.index('## 1.')]
    counts=[int(x) for x in re.findall(r'^\| (?:Critical|Major|Minor|Pack 창작 라벨 누락) \| (\d+) \|',summary,re.M)]
    check('수정목록초기분류코드수와표시합계',(counts,sum(counts)),([12,23,11,17],63))
    issue_codes=re.findall(r'^### ((?:C|M|m)-\d+(?:~\d+)?)\.',correction,re.M)
    actual_heading_counts=[sum(code.startswith(prefix) for code in issue_codes) for prefix in ['C-','M-','m-']]
    expanded_codes=[]
    for code in issue_codes:
        prefix,values=code.split('-');a,*b=values.split('~');expanded_codes.extend(f'{prefix}-{n:02}' for n in range(int(a),int(b[0])+1 if b else int(a)+1))
    check('수정목록상세소제목과묶음코드분해수',(len(issue_codes),actual_heading_counts,len(expanded_codes),len(set(expanded_codes))),(39,[12,16,11],46,46))
    labels=correction[correction.index('## 5.'):correction.index('## 6.')]
    label_lines=[line for line in labels.splitlines() if line.startswith('| L-')]
    passed_labels=[line.split('|')[1].strip() for line in label_lines if '✓ 합격' in line]
    check('누락라벨표에이미합격두행포함',(len(label_lines),passed_labels,len(label_lines)-len(passed_labels)),(17,['L-12','L-13'],15))
    c1=correction[correction.index('### C-01.'):correction.index('### C-02.')]
    assert all(phrase in c1 for phrase in ['2120','2003','261','144','213','233']) and '대사력(大使曆) 97년' in background and '신년(新年, (주)신성 창립력) 117년' in background
    check('시점이동서기수평대사력신년의각기다른차',(2120-2003,261-144,213-97,233-117),(117,117,116,116))
    m10=correction[correction.index('### m-10.'):correction.index('### m-11.')];assert '261-28+1 = 234' in m10 and '117년' in m10
    check('원년포함가정신년구표기233와정정234및117',(261-28+1,144-28+1,(261-28+1)-233),(234,117,1))
    assert '검은 수평선 사건 이후 144년' in background and '수평 1년 = 디디 4227년' in background
    check('수평1사건에서144의경과연수와표시144차이',(144-1,144-(144-1)),(143,1))
    main_layers=background[background.index('#### 1-2-E-2.'):background.index('#### 1-2-E-3.')]
    main_layer_lines=[line for line in main_layers.splitlines() if line.startswith('| **')]
    check('세계배경본문0에서6의실제행수',len(main_layer_lines),7)
    appendix=background[background.index('### A-1.'):background.index('### A-2.')]
    appendix_lines=[line for line in appendix.splitlines() if line.startswith('|') and not line.startswith('|---')][1:]
    check('상하8계층표제와실제밀도행수',(int(re.search(r'상하 (\d+)계층',appendix)[1]),len(appendix_lines)),(8,9))
    exponent_by_unit={'1억자':32,'1만자':28,'1자':24,'1해':20,'1경':16,'1조':12,'1억':8,'1만':4,'1':0}
    appendix_exponents=[]
    for line in appendix_lines:
        unit=line.split('|')[2].strip().replace('**','');appendix_exponents.append(exponent_by_unit[unit])
    check('후속9행단위밀도지수와인접비',(appendix_exponents,[10**(a-b) for a,b in zip(appendix_exponents,appendix_exponents[1:])]),([32,28,24,20,16,12,8,4,0],[10000]*8))
    time_minutes=[]
    for line in main_layer_lines[1:6]:
        field=line.split('|')[3].replace('**','');match=re.search(r'([\d.]+)(일|시간|분)',field);value=F(match[1])*{'일':1440,'시간':60,'분':1}[match[2]];time_minutes.append(value)
    check('구판에고10표의100일10일1일2점5시간15분과인접비',(time_minutes,[a/b for a,b in zip(time_minutes,time_minutes[1:])]),([F(144000),F(14400),F(1440),F(150),F(15)],[F(10),F(10),F(48,5),F(10)]))
    glossary=background[background.index('## 1-14.'):background.index('## 1-15.')]
    check('세계배경30선실제용어행',len(re.findall(r'^\| \*\*',glossary,re.M)),30)
    prices=correction[correction.index('### M-02.'):correction.index('### M-03.')]
    ratios=[]
    for label in ['까마귀','여우','백학 S-50 (=새매)','벽사종']:
        line=next(line for line in prices.splitlines() if line.startswith('| '+label+' |'));cells=line.split('|');old_price=int(cells[2].strip().replace(',','').replace('**',''));new_price=int(cells[3].strip().replace(',','').replace('**',''));ratios.append(F(old_price,new_price))
    check('무기표의1점5배두건과4배10배',ratios,[F(3,2),F(3,2),F(4),F(10)])
    insurance=correction[correction.index('### M-23.'):correction.index('## 3.')];assert '500' in insurance and '월 5오얏' in insurance
    check('서로다른보험상품의월납액만비교한500대5',F(500,5),F(100))
    assert '오얏주 1잔: 3 오얏' in background and '오얏주 반 잔' in background
    check('오얏주3과1오얏가능반잔서술의분량상충',(F(1,3),F(1,2)*3),(F(1,3),F(3,2)))
    stat_section=correction[correction.index('### 8-1.'):correction.index('### 8-2.')];assert all(phrase in stat_section for phrase in ['250','170','46','34','68%','18%','14%'])
    shares=[F(value*100,250) for value in [170,46,34]]
    check('보고서근사일치불일치창작분포의명목합계와반올림',(170+46+34,shares,[round(x) for x in shares]),(250,[F(68),F(92,5),F(68,5)],[68,18,14]))
    cyberpunk_pack_world_correction_arithmetic={'documents':2,'checks_passed':len(checks)-before_world_correction,'major_sections':[18,9],'declared_correction_class_counts':counts,'declared_correction_code_total':sum(counts),'detailed_issue_heading_count':len(issue_codes),'detailed_issue_heading_counts':actual_heading_counts,'expanded_C_M_m_codes':len(expanded_codes),'label_rows':len(label_lines),'already_passing_label_rows':passed_labels,'label_rows_other_than_already_passing':15,'main_layer_rows':len(main_layer_lines),'appendix_declared_layers':8,'appendix_actual_density_rows':len(appendix_lines),'appendix_printed_density_exponents':appendix_exponents,'old_Ego10_limits_minutes':[packed(x) for x in time_minutes],'old_weapon_price_ratios':[packed(x) for x in ratios],'old_insurance_monthly_price_ratio':packed(F(100)),'same_insurance_product_proven':False,'nominal_report_sample':250,'nominal_report_shares':[packed(x) for x in shares],'all_63_reported_codes_are_distinct_actual_errors':False,'all_audit_completion_claims_verified':False,'all_nominal_sample_items_revalidated':False,'canonical_current_year_fixed':False,'legacy_price_layer_or_track_parameters_adopted':False,'current_engine_changed':False,'old_100point_build_rewritten':False,'scope':'두 자료의 표/상태/코드집계와 지정 연호·물가·밀도·구판체류한계만 제한 검산. 근사분모250은 실제샘플항목대조가 아니며 이미일치/합격인코드를포함한63건은독립오류총수의증명이 아니다. 현재연도/환율·실제보험보장·이동물리/지원·정사/프로필·참가자검증은별도다.','actual_participant_playtest':False}

    before_foundation=len(checks)
    fw_review=json.loads((here/'이전설계_통합검토.json').read_text())['framework_foundation_review'];fw_texts={}
    for row in fw_review['snapshots']:
        path=root/row['path_relative_to_plan'];fw_texts[row['name']]=path.read_bytes().decode();files.append(path)
    overview=fw_texts['00_Overview.md'];principles=fw_texts['01_Core_Principles.md'];dice=fw_texts['02_Dice_System.md'];resolution=fw_texts['06_Resolution_System.md']
    check('Framework개요원칙주사위결과해석대분류',[len(re.findall(r'^## ',x,re.M)) for x in [overview,principles,dice,resolution]],[8,7,11,14])
    door=principles[principles.index('### 1-1-E.'):principles.index('## 1-2.')]
    assert all(x in door for x in ['22 + 3 = 25 vs TN 15','23+3=26 vs TN 25','23+2=25','최종 30'])
    check('같은문해킹층별예의달라진TN과차이',[(25,15,25-15),(26,25,26-25),(25,25,25-25),(30,25,30-25)],[(25,15,10),(26,25,1),(25,25,0),(30,25,5)])
    ace=dice[dice.index('### 2-1-E.'):dice.index('### 2-1-F.')]
    assert '2+4+6+4 = 16' in ace and '3+5+8+8+7+2+6 = 39' in ace
    check('구판폭발3d6와5d8의표시합',(sum([2,4,6,4]),sum([3,5,8,8,7,2,6])),(16,39))
    examples=dice[dice.index('### 2-1-G.'):dice.index('## 2-2.')]
    assert '3+1+2+4 = 10 + 2 = **12**' in examples
    check('4d4초보예미완료폭발전합과최소추가',(sum([3,1,2,4])+2,sum([3,1,2,4])+2+1),(12,13))
    assert '6+3+8+5+2 = 24 + 3 = **27**' in examples and '누적 27 + 5 = 32' in examples
    check('중견해커의폭발전후와TN25차이',(sum([6,3,8,5,2])+3,sum([6,3,8,5,2])+3+5,32-25),(27,32,7))
    assert '평균 78 + 7 = 85' in examples and '자동 Great (차이 +25)' in examples and '20+' in resolution
    legend_mean=12*F(13,2)+7;legend_minimum=12+7
    check('평균85의차이25는Critical구간이나최솟값은19',(legend_mean,legend_mean-60,legend_minimum,legend_minimum<60),(F(85),F(25),19,True))
    assert '스탯 9 → TN 25' in principles and '| **9** | **5d8**' in dice
    nonexploding_mean=5*F(9,2);exploding_mean=5*F(9,2)*F(8,7)
    check('스탯9의비폭발폭발평균과TN25의비일치',(nonexploding_mean,exploding_mean,nonexploding_mean==25,exploding_mean==25),(F(45,2),F(180,7),False,False))
    assert '1d10 피해 × 6 = 6d10 피해' in dice
    variance_single=36*F(10**2-1,12);variance_sum=6*F(10**2-1,12)
    check('1d10곱하기6과6d10의평균은같지만분산과가능합은다름',(6*F(11,2),6*F(11,2),variance_single,variance_sum,7 in [6*x for x in range(1,11)],sum([1,1,1,1,1,2])),(F(33),F(33),F(297),F(99,2),False,7))
    assert '| 1d4 | 1 | 25%' in dice and '| 4d4 | 4 | 0.39%' in dice and '| 3d6 | 3 | 0.46%' in dice
    check('전부1의서로다른세확률',[F(1,4),F(1,4**4),F(1,6**3)],[F(1,4),F(1,256),F(1,216)])
    assert 'd100 (= d10 × 10 + d10)' in dice
    ordinary=[a*10+b for a in range(1,11) for b in range(1,11)];mapped=[100 if a==b==0 else a*10+b for a in range(10) for b in range(10)]
    check('자리정의없는두일반d10과올바른0부터9자리00매핑',(min(ordinary),max(ordinary),len(set(ordinary)),sorted(mapped)==list(range(1,101))),(11,110,100,True))
    assert 'BOD 8, PRE 6 → 한도 14개, 시작 7개' in dice and '굴림 결과 27 → 27÷5 = 6' in dice
    check('구판Pool한도시작과공급올림',(8+6,F(8+6,2),(27+4)//5),(14,F(7),6))
    pool_values=[6,5,2,6,4,5,3,1,6,5,2,4];assert '6,5,2,6,4,5,3,1,6,5,2,4' in dice and '**6 Hit**' in dice
    check('구판12Pool예의7이라고쓴후정정한실제6Hit',(len(pool_values),sum(x>=5 for x in pool_values)),(12,6))
    case=resolution[resolution.index('### 6-2-C.'):resolution.index('## 6-3.')]
    assert '3+5+2+7+6 = 23 + 4 = 27' in case and '1+2+1+3+2 = 9 + 4 = 13' in case and '누적 = 4+8+8+6+5+2+7 = 40' in case
    totals=[sum([3,5,2,7,6])+4,sum([1,2,1,3,2])+4,sum([4,8,8,6,5,2,7])+4]
    check('결과해석세예의실제합과차이',(totals,[x-25 for x in totals]),([27,13,44],[2,-12,19]))
    framework_foundation_arithmetic={'documents':4,'checks_passed':len(checks)-before_foundation,'major_sections':[8,7,11,14],'door_example_different_TNs':[15,25,25],'door_example_margins':[10,1,0,5],'legend_mean':packed(legend_mean),'legend_minimum':legend_minimum,'legend_mean_margin':packed(legend_mean-60),'stat9_nonexploding_mean':packed(nonexploding_mean),'stat9_exploding_mean':packed(exploding_mean),'six_times_d10_variance':packed(variance_single),'six_d10_variance':packed(variance_sum),'unmapped_d10_range':[min(ordinary),max(ordinary)],'pool_sample_hits':6,'resolution_example_totals':totals,'all_legacy_random_distributions_verified':False,'external_system_or_legal_claims_verified':False,'current_engine_changed':False,'old_100point_build_rewritten':False,'actual_participant_playtest':False,'scope':'4자료의지정예/단위/분포반례13검산. 폭발평균은공정독립주사위/무한최대눈재굴림 가정이며 전부1/상황/보너스를포함한전체성공확률이아니다. 기존구판엔진전체·외부게임/권리·온라인앱동작·참가자검증은포함하지않는다.'}

    before_character_combat=len(checks)
    fc_review=json.loads((here/'이전설계_통합검토.json').read_text())['framework_character_combat_review'];fc_texts={}
    for row in fc_review['snapshots']:
        path=root/row['path_relative_to_plan'];fc_texts[row['name']]=path.read_bytes().decode();files.append(path)
    stats=fc_texts['03_Stats_and_Attributes.md'];creation=fc_texts['04_Character_Creation.md'];combat=fc_texts['05_Combat_Scales.md']
    check('Framework스탯생성전투대분류',[len(re.findall(r'^## ',x,re.M)) for x in [stats,creation,combat]],[11,19,17])
    def cost_grade_rows(text,start,end):
        rows=[]
        for line in text[text.index(start):text.index(end)].splitlines():
            cells=[x.strip().replace('**','').replace(' ↑','') for x in line.split('|')[1:-1]]
            if not cells or not cells[0].isdigit():continue
            match=re.fullmatch(r'(\d+)d(\d+)',cells[1]);cost=next(int(re.match(r'(\d+)p',cell)[1]) for cell in cells if re.match(r'\d+p',cell))
            rows.append((int(cells[0]),int(match[1]),int(match[2]),cost))
        return rows
    sr=cost_grade_rows(stats,'### 3-2-A.','### 3-2-B.');cr=cost_grade_rows(creation,'### 4-3-A.','### 4-3-B.');costs={stat:cost for stat,n,sides,cost in sr};grades={stat:(n,sides) for stat,n,sides,cost in sr}
    check('스탯문서와생성문서25행Grade누적비용동일',(len(sr),sr==cr),(25,True))
    table=stats[stats.index('### 3-2-A.'):stats.index('### 3-2-B.')];printed=[]
    for line in table.splitlines():
        cells=[x.strip().replace('**','').replace(' ↑','') for x in line.split('|')[1:-1]]
        if cells and cells[0].isdigit():printed.append((F(cells[3]),int(cells[4])))
    check('25행표시비폭발평균과최대',[((F(n*(sides+1),2)),n*sides) for stat,n,sides,cost in sr],printed)
    promoted=[5,9,13,17,21];increments=[costs[x]-costs[x-1] for x in promoted]
    check('구판실제다섯승급지점비용증분',increments,[6,12,16,20,26])
    transitions=[(grades[x-1][0]*grades[x-1][1],grades[x][0]*grades[x][1],grades[x][0]) for x in promoted]
    check('승급최대초과가굴림항상초과는아닌다',(transitions,all(b>a and minimum<a for a,b,minimum in transitions)),([(16,18,3),(36,40,5),(64,70,7),(100,108,9),(144,160,8)],True))
    assert '누적 0→7 = 28p' in stats and '1~3 | 4' in stats and '10+ | 7' in stats
    caps=[min((s+2)//3+3,7) for s in range(1,26)]
    check('구판스킬삼각누적28와재능상한25값',(sum(range(1,8)),caps),(28,[4]*3+[5]*3+[6]*3+[7]*16))
    old_builds=stats[stats.index('## 3-8.'):stats.index('## 3-9.')];assert 'LCK 0 (0p)' in old_builds and '최소 스탯**: 1' in stats
    check('스탯문서네구매예의합계와영스탯상충',[sum(costs[s] for s in row) for row in [(7,7,5,6,4,3),(7,7,5,6,3,3),(9,8,2,5,1,3),(3,5,11,6,1,1),(6,6,6,6,4,3)]],[101,97,100,100,94])
    assert 'BOD 8 (6d6, Tier 2)' in stats and 'Initiative: REF 9 + SEN 10' in stats
    check('스탯시트예의191p와파생값',(sum(costs[s] for s in [8,9,7,10,6,5]),8*5,max(6*2,4),12//3,8+6,5*2,8+6,5+6),(191,40,12,4,14,10,14,11))
    assert '7 + 6 = 13 | 13 | 7 (올림)' in stats and '평균 Initiative = 약 35' in stats
    check('홀수Pool시작올림과10d6비폭발평균',((13+1)//2,10*F(7,2)),(7,F(35)))
    assert '스탯값 ÷ 4 (반올림) = Tier 근사' in stats
    check('Tier반올림근사와정확표의첫경계차이',[(s,round(F(s,4)),next(int(line.split('|')[3].replace('**','').strip()) for line in table.splitlines() if line.startswith('|') and line.split('|')[1].strip().replace('**','')==str(s))) for s in [1,5]],[(1,0,1),(5,1,2)])
    swap=creation[creation.index('### 4-8-B.'):creation.index('### 4-8-C.')];assert '기타 8p' in swap and '해킹 스킬 +3 유지 (6p)' in swap
    check('프리셋부분교체예의양쪽30p',(6+3+5+3+2+3+8,6+3+5+3+2+3+8),(30,30))
    workflow=creation[creation.index('## 4-11.'):creation.index('## 4-12.')];steps=re.findall(r'^Step (\d+) ',workflow,re.M)
    check('생성10단계표제와실제12단계',(int(re.search(r'생성 (\d+)단계',workflow)[1]),[int(x) for x in steps]),(10,list(range(1,13))))
    build_vectors=[(6,7,5,6,2,3),(8,8,2,6,1,3),(3,5,9,5,2,1),(4,5,5,5,8,3),(5,5,3,4,3,2)];totals=[sum(costs[s] for s in row) for row in build_vectors]
    examples=creation[creation.index('## 4-14.'):creation.index('## 4-15.')];assert '스탯 (52p)' in examples and '= 51p' in examples and '(1p 여유)' in examples
    check('생성다섯예스탯실제합과신참소비68여유7',(totals,totals[-1]+10+7,75-(totals[-1]+10+7)),([88,93,82,92,51],68,7))
    leader=examples[examples.index('### 4-14-D.'):examples.index('### 4-14-E.')];assert 'PRE Tier 3' in leader and 'PRE 8 = 6d6 (Tier 2 상단)' in leader
    check('사교리더PRE8실제Grade와Tier',(grades[8],2),((6,6),2))
    yaml=creation[creation.index('### 4-15-B.'):creation.index('### 4-15-C.')];assert 'stats: 91' in yaml and 'total: 105' in yaml and 'lifepath_bonus: 5' in yaml
    actual_yaml_stats=sum(costs[s] for s in [7,7,5,6,3,3]);actual_yaml_total=actual_yaml_stats+6+8
    check('생성YAML표시스탯91실제97과합의105대실제111',(actual_yaml_stats,actual_yaml_total,100+5,actual_yaml_total-(100+5)),(97,111,105,6))
    assert '최종:        65%' in creation
    check('구판BP표의몸구성감산65',100-5-10-20,65)
    a=combat[combat.index('### 5-2-D.'):combat.index('### 5-2-E.')];assert '차이: 23 - 12 = 11' in a and '차이: 15 - 23 = -8' in a
    check('실내전투예폭발전합계와차이',([sum([3,5,2,4,6])+3,sum([4,2,5])+1,sum([4,3,6])+2,sum([2,5,3,1,4,6])+2],[23-12,15-23]),([23,12,15,23],[11,-8]))
    b=combat[combat.index('### 5-3-D.'):combat.index('### 5-3-E.')];assert '차이: 24 - 13 = 11' in b and '평균 9' in b
    check('거리전투예공격방어합계와차이',([sum([6,4,3,2,5,1])+4+1-2,sum([5,3,2])+1+2,sum([3,2,5,4])+3+1-2,sum([2,5,1,4,6,3])+3],[24-13,16-24]),([24,13,16,24],[11,-8]))
    assert '1d6+1 × 2 = 2d6+2' in b and '숙련 보너스 = 해당 스킬 ÷ 2 (내림)' in combat
    check('거리전투피해표시평균9와분포차이및명시숙련누락',(2*(F(7,2)+1),4*F(35,12),2*F(35,12),2*(F(7,2)+1+4//2)),(F(9),F(35,3),F(35,6),F(13)))
    c=combat[combat.index('## 5-4.'):combat.index('## 5-5.')];assert '주 몸체: HP 400' in c and '관측 센서: HP 50' in c and '조종실: HP 100' in c and '무기 포: HP 80' in c and 'Hit 수 = 4' in c
    check('대형예독립몸부품합630과8Pool4Hit',(400+50+100+80,sum(x>=5 for x in [3,5,6,2,5,4,6,1])),(630,4))
    fat=combat[combat.index('### 5-5-C.'):combat.index('## 5-6.')];assert '10 라운드 (60÷6)' in fat and '4~6 라운드' in fat
    check('구판FatRound세시간과현재5초12라운드',(60//6,60//15,60//10,60//5),(10,4,6,12))
    assert 'HP -1 ~ -BOD' in stats and 'HP ≤ -(BOD×2)' in stats and 'HP -1 ~ -BOD' in combat
    hp_gap=[hp for hp in range(-14,0) if not (-7<=hp<=-1 or hp<=-14)]
    check('BOD7구판빈사와진사사이미정의6값',(hp_gap,len(hp_gap)),(list(range(-13,-7)),6))
    ranges=combat[combat.index('#### 거리 분류'):combat.index('### 5-3-D.')];assert '| 근접 | 0~1' in ranges and '| 근거리 | 1~5' in ranges
    check('구판거리칸구간의한칸중복',sorted(set(range(0,2))&set(range(1,6))),[1])
    framework_character_combat_arithmetic={'documents':3,'checks_passed':len(checks)-before_character_combat,'major_sections':[11,19,17],'stat_table_rows':25,'both_stat_cost_and_grade_tables_agree':sr==cr,'tier_cost_increments':increments,'creation_declared_steps':10,'creation_actual_steps':len(steps),'creation_five_example_stat_totals':totals,'creation_yaml_actual_stat_cost':actual_yaml_stats,'creation_yaml_actual_total':actual_yaml_total,'creation_yaml_approved_budget':105,'creation_yaml_over_budget':6,'novice_actual_spent':68,'novice_remaining':7,'BOD7_undefined_negative_HP_values':hp_gap,'old_range_grid_overlap':[1],'current_common_60second_rounds':12,'external_game_rules_verified':False,'all_legacy_random_distributions_verified':False,'all_specific_use_profiles_complete':False,'current_engine_changed':False,'old_100point_build_rewritten':False,'actual_participant_playtest':False,'scope':'3자료 지정표/구매예/파생/전투산술과분포반례만제한검산. 구판100p를5판빌드로수정/환산하지않으며 등급/평균만으로정사·승률/균형을증명하지않는다. 원전인물/장치/대형부품전효과·실제참가자/외부게임은별도.'}

    before_resource_growth=len(checks)
    rg_review=json.loads((here/'이전설계_통합검토.json').read_text())['framework_resource_growth_review'];rg_texts={}
    for row in rg_review['snapshots']:
        path=root/row['path_relative_to_plan'];rg_texts[row['name']]=path.read_bytes().decode();files.append(path)
    resources=rg_texts['07_Resources_Tokens.md'];tracks=rg_texts['08_Track_System.md'];growth=rg_texts['09_Growth_Progression.md']
    check('Framework자원트랙성장대분류',[len(re.findall(r'^## ',x,re.M)) for x in [resources,tracks,growth]],[12,14,17])
    ego_section=resources[resources.index('### 7-3-B.'):resources.index('### 7-3-C.')];ego_rows=[]
    for line in ego_section.splitlines():
        cells=[x.strip() for x in line.split('|')[1:-1]]
        if cells and cells[0].isdigit():ego_rows.append(tuple(int(re.search(r'\d+',x)[0]) for x in cells))
    check('구판에고열행최소4와최대기준저항',ego_rows,[(pre,max(pre*2,4),max(pre*2,4)//3) for pre in [1,2,3,4,5,6,7,10,15,20]])
    examples=resources[resources.index('## 7-9.'):resources.index('## 7-10.')];assert all(x in examples for x in ['PRE 2','PRE 5','PRE 10','PRE 17','저항 수정치: +11'])
    cases=[(pre,bod,luck) for pre,bod,luck in [(2,6,2),(5,7,3),(10,8,5),(17,12,7)]]
    check('구판4자원예의각에고저항장르운저장',[(max(pre*2,4),max(pre*2,4)//3,8+pre,luck*2,bod+pre) for pre,bod,luck in cases],[(4,1,10,4,8),(10,3,13,6,12),(20,6,18,10,18),(34,11,25,14,29)])
    storage=resources[resources.index('### 7-5-B.'):resources.index('### 7-5-C.')];assert '7 + 6 = 13 | 13 | 7 (올림)' in storage
    check('구판저장네예의시작올림',[(a+b,(a+b+1)//2) for a,b in [(4,4),(7,6),(12,10),(17,15)]],[(8,4),(13,7),(22,11),(32,16)])
    supply=resources[resources.index('### 7-5-C.'):resources.index('### 7-5-D.')];assert '결과 27 → 27÷5 = 6' in supply and '결과 14 → 14÷5 = 3' in supply
    resource_log=resources[resources.index('## 7-10.'):resources.index('## 7-11.')];assert 'amount: +3, reason: "장전 행동 (REF Grade 27 ÷ 5)"' in resource_log
    check('공급27예의6과YAML3표기사이3차이및14올림',((27+4)//5,3,(27+4)//5-3,(14+4)//5),(6,3,3,3))
    ammo=resources[resources.index('### 7-5-F.'):resources.index('### 7-5-G.')];assert 'Pool 한도 12, 세션 시작 6d6' in ammo and '현재 7d6' in ammo and '7d6만 사용 가능' in ammo
    check('구판탄창예시작6소모5공급6후7은표준10보다부족',(6-5,6-5+(28+4)//5,10-(6-5+(28+4)//5)),(1,7,3))
    assert 'session_start: 7' in resource_log and 'turn: 0, amount: +7' in resource_log and 'turn: 8, amount: -10' in resource_log
    claimed_prefix=[7,7-5,7-5+3];corrected_supply_prefix=[7,7-5,7-5+6]
    check('시작7한번으로읽은Pool로그소모10전의두조건부잔량',(claimed_prefix,corrected_supply_prefix,claimed_prefix[-1]>=10,corrected_supply_prefix[-1]>=10),([7,2,5],[7,2,8],False,False))
    assert 'current: 6' in resource_log and 'current: 10' in resource_log and '에고 회복 1d6 → 3' in resource_log
    check('자원로그명시증감만의운잔량DSR순증가와에고최대가정',(10-1-2-1,1+1+1-1-1,12-1-1+3,min(12,12-1-1+3),6-(1+1+1-1-1)),(6,1,13,12,5))
    assert '자동 크리티컬 (차이 +20 보정)' in resources
    check('차이20가산이기존실패를항상Critical로만들지는않음',[(margin,margin+20,margin+20>=20) for margin in [-35,-1,0]],[(-35,-15,False),(-1,19,False),(0,20,True)])
    threshold=tracks[tracks.index('#### 트랙 10·20 임계'):tracks.index('#### 수정치')];bounds=[]
    for line in threshold.splitlines():
        match=re.match(r'^\| \*\*(\d+)-(\d+)\*\*',line)
        if match:
            low,high=map(int,match.groups());bounds.append((low,100 if high==0 else high))
    def threshold_counts(mod):
        counts=[0]*len(bounds)
        for roll in range(1,101):
            result=max(1,min(100,roll+mod));index=next(i for i,(lo,hi) in enumerate(bounds) if lo<=result<=hi);counts[index]+=1
        return counts
    distributions={str(mod):threshold_counts(mod) for mod in [0,20,-10,10]}
    check('구판임계5범위전100눈과수정클램프분포',distributions,{'0':[20,30,25,15,10],'20':[0,30,25,15,30],'-10':[30,30,25,15,0],'10':[10,30,25,15,20]})
    failure=tracks[tracks.index('### 8-6-B.'):tracks.index('### 8-6-C.')];assert '목표 초과 10 이내' in failure and '목표 초과 10~30' in failure
    ordinary_failures=range(51,100);overlap=[roll for roll in ordinary_failures if 1<=roll-50<=10 and 10<=roll-50<=30];unassigned=[roll for roll in ordinary_failures if not (1<=roll-50<=10 or 10<=roll-50<=30)]
    check('구판목표50실패등급의60중복과81부터99공백',(overlap,unassigned),([60],list(range(81,100))))
    assert '**3/4 도달 시 징조**' in tracks and '샤이닝 7+:' in tracks
    check('구판10칸3분의4와7칸표시차이',(10*F(3,4),F(7,10)*100,20*F(3,4)),(F(15,2),F(70),F(15)))
    example=tracks[tracks.index('### 8-8-A.'):tracks.index('### 8-8-B.')];assert 'SEN 7 (5d6)' in example and '각성 스킬 4, 에고 Max 12' in example and '기대 25.5' in example
    check('샤이닝예비폭발기대25점5와폭발기대29',(5*F(7,2)+4+4,5*F(7,2)*F(6,5)+4+4),(F(51,2),F(29)))
    flow=tracks[tracks.index('### 8-8-B.'):tracks.index('## 8-9.')];assert '78-10 = 68' in flow and 'R8: 크리티컬 부위 → 7' in flow and 'R12: 운 토큰 1 → +1d6 = 10' in flow
    check('구판임계78보정68과에고명시흐름',(78-10,[12-1,12-1-1,12-1-1-3,12-1-1-3+3]),(68,[11,10,7,10]))
    assert '세션당 +2~3 (10 세션에 절반 소모)' in tracks
    check('순증가만있는10세션2부터3은10칸절반5와다름',(10*2,10*3,F(10,2)),(20,30,F(5)))
    pay=growth[growth.index('### 9-2-A.'):growth.index('### 9-2-E.')];assert '4 + 1 + 1 = 6p' in pay and '5 + 30 = 35p' in pay
    check('구판성장기본최대와명시이정표네예',([4+3,5+3,5+3,5+1],[4+1+1,5+1+1,4+10,5+30]),([7,8,8,6],[6,7,14,35]))
    wait=growth[growth.index('### 9-4-D.'):growth.index('### 9-4-E.')];assert '26p | 7' in wait and '6p | 2' in wait
    check('구판4p세션기준단일향상최소올림',[(cost+3)//4 for cost in [4,6,6,12,16,20,26]],[1,2,2,3,4,5,7])
    level=growth[growth.index('## 9-7.'):growth.index('## 9-8.')];refund=growth[growth.index('## 9-8.'):growth.index('## 9-9.')];assert '| Lv5 | 30p |' in level and '5 - 1.5 = 3.5p' in refund
    check('구판기능Lv누적30과장비포인트반액환급예',([10+5*(lv-1) for lv in range(1,6)],F(3,2),5-F(3,2)),([10,15,20,25,30],F(3,2),F(7,2)))
    replacement=growth[growth.index('### 9-10-B.'):growth.index('### 9-10-C.')];assert '팀 평균 180p → 새 PC 144p' in replacement and '150~250' in replacement and '250~400' in replacement and '400+' in replacement
    check('구판새PC세예와250400중복경계의상이한값',([180*F(4,5),300*F(3,4),500*F(7,10)],[250*F(4,5),250*F(3,4)],[400*F(3,4),400*F(7,10)]),([F(144),F(225),F(350)],[F(200),F(375,2)],[F(300),F(280)]))
    late=growth[growth.index('## 9-11.'):growth.index('## 9-12.')];assert '누적 194p' in late and '누적 131p' in late
    check('Late성장할인6와4및누적194131',(26-20,20-16,174+20,115+16),(6,4,194,131))
    pace=growth[growth.index('## 9-12.'):growth.index('## 9-13.')];assert '250~400p' in pace and '평균 세션 5~6p' in pace
    check('20부터40세션5부터6p가정의범위와40세션400필요평균',(100+20*5,100+40*6,F(400-100,40)),(200,340,F(15,2)))
    log=growth[growth.index('### 9-13-B.'):growth.index('## 9-14.')];assert '100 + 5 - 4 = 101' in log and 'total_points: 135' in log and 'total_points: 170' in log
    check('성장로그101잔량과105누적역량을구분해야함',(100+5-4,100+5,(100+5)-(100+5-4)),(101,105,4))
    framework_resource_growth_arithmetic={'documents':3,'checks_passed':len(checks)-before_resource_growth,'major_sections':[12,14,17],'ego_formula_rows':len(ego_rows),'supply_log_printed_amount':3,'supply_log_amount_from_printed_formula':6,'Pool_log_prefix_if_start_once':claimed_prefix,'Pool_log_prefix_if_supply_corrected':corrected_supply_prefix,'both_Pool_log_prefixes_cannot_pay_10':True,'assumed_zero_start_genre_log_net_change':1,'genre_start_required_for_printed_current6':5,'all_legacy_logs_are_complete_histories':False,'threshold_ranges':[list(x) for x in bounds],'threshold_modified_roll_counts':distributions,'goal50_failure_overlap_rolls':overlap,'goal50_failure_unassigned_non100_rolls':unassigned,'fourp_session_single_upgrade_ceiling':[1,2,2,3,4,5,7],'replacement_budget_250_two_values':[packed(F(200)),packed(F(375,2))],'replacement_budget_400_two_values':[packed(F(300)),packed(F(280))],'all_legacy_random_distributions_verified':False,'all_specific_use_profiles_complete':False,'external_game_rules_verified':False,'current_engine_changed':False,'old_100point_build_rewritten':False,'actual_participant_playtest':False,'scope':'3문서의지정예/표·임계100눈수정/클램프·실패구간/성장/로그조건부산술만검산. 로그의초기값/생략사건을추정하거나 현재잔량을정사로복원하지않는다. 구판100p새빌드·전체확률/균형·세션페이싱/실제앱/참가자검증과별도다.'}

    before_team_NPC_session=len(checks)
    play_review=json.loads((here/'이전설계_통합검토.json').read_text())['framework_team_NPC_session_review'];play_texts={}
    for row in play_review['snapshots']:
        path=root/row['path_relative_to_plan'];play_texts[row['name']]=path.read_bytes().decode();files.append(path)
    team=play_texts['10_Team_and_Retry.md'];npc=play_texts['11_NPC_Standard.md'];session=play_texts['12_Session_Campaign.md']
    check('Framework팀NPC세션대분류',[len(re.findall(r'^## ',x,re.M)) for x in [team,npc,session]],[12,14,14])
    assert '원조 주사위 결과 > 리더 Grade Die 평균' in team and '31.5 (주사위당 4.5)' in team
    check('원조전체평균과단일평균의서로다른기준',(7*F(9,2),F(9,2),[z>7*F(9,2) for z in [7,2,4]],[z>F(9,2) for z in [7,2,4]]),(F(63,2),F(9,2),[False,False,False],[True,False,False]))
    check('폭발d8원조전체31점5와단일4점5초과확률',(sum_threshold(1,8,32),sum_threshold(1,8,5)),(F(1,4096),F(1,2)))
    assert '리더에 +4 → 판정값 55' in team and '차이 +30 → **Critical**' in team
    leader=sum([5,7,3,2,8,4,6])+3+4;total=leader+sum([7,2,4])
    check('팀침투최대눈8폭발3리더와원조합',(leader,total,total-25,2//2,2%2,3//2,3%2),(42,55,30,1,0,1,1))
    assert '15d6/인' in team and '기본 30d6' in team
    check('집단Pool상한30과개인절반올림의15기여조건',(min(cur for cur in range(61) if (cur+1)//2>=15),30//15,[(cur+1)//2 for cur in [1,12,14,29,30]]),(29,2,[1,6,7,15,15]))
    assert '4+2+5 + 3 = 14 → Full' in team and '31 → Critical (차이 +16 → Great)' in team
    def legacy_quality(margin):
        return 'Critical' if margin>=20 else 'Great' if margin>=10 else 'Full' if margin>=5 else 'Partial' if margin>=0 else 'Fail'
    check('회상두굴림합과실제결과등급',[(sum([4,2,5])+3,14-10,legacy_quality(14-10)),(sum([5,7,2,4,6,3])+4,31-15,legacy_quality(31-15)),(42,42-25,legacy_quality(42-25))],[(14,4,'Partial'),(31,16,'Great'),(42,17,'Great')])
    check('경쟁표시값24와27의독립등급',[(24-15,legacy_quality(24-15)),(27-15,legacy_quality(27-15))],[(9,'Full'),(12,'Great')])
    assert 'PRE 4 (4d4, 평균 10) + 사교 +3' in npc and 'TN 25: 약 55%' in npc
    attitude_cases=[(4,4,3,10),(4,4,3,15),(4,6,4,15),(4,6,4,20),(5,8,5,25)]
    attitude_exploding=[sum_threshold(n,faces,tn-bonus) for n,faces,bonus,tn in attitude_cases]
    # Every case's all-initial-ones Botch lies strictly below the success threshold.
    # This makes the unlimited-explosion CDF exact for Partial+ under these five conditions.
    check('NPC다섯태도조건모두최저눈Botch가성공범위밖',[n+bonus<tn for n,faces,bonus,tn in attitude_cases],[True]*5)
    check('NPC태도지정5조건폭발합의정확통과확률',attitude_exploding,[F(241,256),F(145,256),F(829,972),F(1979,3888),F(99205,131072)])
    attitude_nonexploding=[F(sum(sum(roll)+bonus>=tn for roll in product(range(1,faces+1),repeat=n)),faces**n) for n,faces,bonus,tn in attitude_cases]
    check('NPC태도지정5조건비폭발전수대조',attitude_nonexploding,[F(241,256),F(33,128),F(545,648),F(145,432),F(11725,16384)])
    check('NPC태도제안근사70과35와55와계산값차이',[abs(pct-F(claim,100))>F(5,100) for pct,claim in zip(attitude_exploding,[70,35,70,35,55])],[True]*5)
    assert '공격 = 3d4 (BOD) + 1 (근접) = 평균 9' in npc
    check('곤봉잭비폭발공격평균8점5와방어6',(3*F(5,2)+1,2*F(5,2)+1),(F(17,2),F(6)))
    check('단위가다른공격3d4와방어2d4의Botch확률',(F(1,4**3),F(1,4**2)),(F(1,64),F(1,16)))
    assert '15d6 투입' in npc and '해킹 = 6d8 (INT) + 6 (해킹) = 평균 33' in npc
    check('제로캐스트개인Pool11로15투입부족과평균차이8',(5+6,15-(5+6),6*F(9,2)+6,33-25,legacy_quality(33-25)),(11,4,F(33),8,'Full'))
    assert '평균 43 + 1d12' in npc and '차이 18 → Great' in npc
    boss_deltas=[43+weapon-25 for weapon in range(1,13)]
    check('흑사자룡무기1d12를포함한조건부차이범위와등급',(min(boss_deltas),max(boss_deltas),[legacy_quality(x) for x in boss_deltas]),(19,30,['Great']+['Critical']*11))
    check('흑사자룡방어기본평균과두수정의합',(7*F(9,2)+5+2),F(77,2))
    npc_reaction=[roll+mod for mod in [-3,-2,-1,0,1] for roll in range(1,7)]
    check('선택NPC반응표수정후원래d6범위밖',(min(npc_reaction),max(npc_reaction),sorted(set(z for z in npc_reaction if not 1<=z<=6))),(-2,7,[-2,-1,0,7]))
    check('보스백분율4단계중복경계',[z for z in range(101) if sum(lo<=z<=hi for lo,hi in [(75,100),(50,75),(25,50),(0,25)])>1],[25,50,75])
    check('NPC최소준비목록정해진각하한의합',80+30+10+5,125)
    assert 'duration_hours: 4' in session and 'start: {min: 12' in session and 'min: 145' in session
    minutes=sum([12,28,145,25,10]);check('세션YAML단계시간합220과4시간차20',(minutes,4*60,4*60-minutes),(220,240,20))
    check('세션5단계권장시간합과휴식제외범위',(10+30+120+30+10,15+30+180+30+15),(200,270))
    assert 'tn: 15, result: 22, outcome: "Great"' in session and 'tn: 25, result: 31, outcome: "Partial"' in session
    check('세션주요굴림22와31의같은Full등급',[(22-15,legacy_quality(22-15)),(31-25,legacy_quality(31-25))],[(7,'Full'),(6,'Full')])
    assert 'milestone_reached: "에피소드 완결 (+10p 전원)"' in session and 'milestone: 0, total: 5' in session and 'milestone: 0, total: 6' in session
    check('이정표전원10과개별0의충돌및조건부총점',([4+1+0,4+2+0,4+0+10],[4+1+10,4+2+10,4+0+10]),([5,6,14],[15,16,14]))
    framework_team_NPC_session_arithmetic={'documents':3,'checks_passed':len(checks)-before_team_NPC_session,'major_sections':[12,14,14],'helper_thresholds':[packed(F(63,2)),packed(F(9,2))],'helper_success_probabilities':[packed(F(1,4096)),packed(F(1,2))],'team_leader_result':leader,'team_total_result':total,'Pool_minimum_current_for_contribution15':29,'Pool_max_contributors_if_15_each_and_total30':2,'attitude_conditions':[list(x) for x in attitude_cases],'attitude_partial_plus_exact_exploding':[packed(x) for x in attitude_exploding],'attitude_nonexploding_control':[packed(x) for x in attitude_nonexploding],'NPC_reaction_unassigned_outputs':[-2,-1,0,7],'zero_cast_Pool_cap':11,'zero_cast_requested_Pool':15,'zero_cast_shortfall':4,'boss_conditional_weapon_margins':[19,30],'session_log_minutes':minutes,'session_declared_minutes':240,'session_unitemized_minutes':20,'session_major_roll_actual_qualities':['Full','Full'],'session_printed_earned_points':[5,6,14],'session_points_if_everyone_receives_named_milestone':[15,16,14],**{k:False for k in ['all_legacy_logs_are_complete_histories','all_legacy_random_distributions_verified','all_specific_use_profiles_complete','external_game_rules_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']},'scope':'3문서지정예/평균·원조기준·Pool한도·태도5조건폭발합/비폭발전수·반응/단계경계·세션예시시간/등급/포인트만검산. 태도는개별수치와Botch가성공범위밖인조건에한정하며 NPC전체밸런스/정사수치·세션완전이력/실제참가자시험과다르다. 43+무기조건부차이는원문의평균대평균을고정해검산한것이며전체전투성공확률이아니다.'}

    before_final_framework=len(checks)
    final_review=json.loads((here/'이전설계_통합검토.json').read_text())['framework_final_reader_review'];final_texts={}
    for row in final_review['snapshots']:
        path=root/row['path_relative_to_plan'];final_texts[row['tag']]=path.read_bytes().decode();files.append(path)
    online=final_texts['13'];extension=final_texts['14'];glossary=final_texts['15'];prose=final_texts['16'];readme=final_texts['README']
    check('Framework잔여대분류',[len(re.findall(r'^## ',x,re.M)) for x in [online,extension,glossary,prose,readme]],[12,13,11,17,10])
    stat_snapshot=next(x for x in json.loads((here/'이전설계_통합검토.json').read_text())['framework_character_combat_review']['snapshots'] if x['name']=='03_Stats_and_Attributes.md');stats_text=(root/stat_snapshot['path_relative_to_plan']).read_bytes().decode()
    stat_table=stats_text[stats_text.index('### 3-2-A.'):stats_text.index('### 3-2-B.')];stat_rows={}
    for line in stat_table.splitlines():
        if not line.startswith('|'):continue
        cols=[z.strip().replace('**','') for z in line.split('|')[1:-1]]
        if cols and cols[0].isdigit():stat_rows[int(cols[0])]={'dice':re.search(r'(\d+)d(\d+)',cols[1]).group(0),'cost':int(re.search(r'\d+',cols[-1])[0])}
    online_yaml=online[online.index('### 13-4-A.'):online.index('### 13-4-B.')]
    online_stats=[7,9,6,8,5,4];expected_grades=[stat_rows[z]['dice'] for z in online_stats]
    check('구판온라인시트6Grade가Stats표와일치',expected_grades,['5d6','5d8','4d6','6d6','3d6','4d4'])
    for grade in expected_grades:assert '"'+grade+'"' in online_yaml
    assert 'HP: {current: 35, max: 35}' in online_yaml and 'storage_max: 12' in online_yaml and 'current: 6' in online_yaml
    check('온라인파생HP정신에고저항장르운Pool시작구판표',(7*5,max(5*2,4),max(5*2,4)//3,8+5,4*2,7+5,(7+5+1)//2),(35,10,3,13,8,12,6))
    assert '합계: 97p' in prose and '남은 3p로 스킬·태그 구매' in prose
    prose_stats=[7,7,5,6,3,3];prose_costs=[stat_rows[z]['cost'] for z in prose_stats];prose_total=sum(prose_costs)
    check('입문서술균형예97p는구판표와정확일치',(prose_costs,prose_total,100-prose_total),([26,26,15,20,5,5],97,3))
    check('입문균형예6Grade와Initiative비폭발평균',([stat_rows[z]['dice'] for z in prose_stats],(5+4)*F(7,2)),(['5d6','5d6','3d6','4d6','3d4','3d4'],F(63,2)))
    check('입문균형예구판파생7종',(7*5,max(3*2,4),max(3*2,4)//3,8+3,3*2,7+3,(7+3+1)//2),(35,6,2,11,6,10,5))
    assert '사격 스킬 +4' in prose and '회피 +2' in prose
    check('균형예잔량3만으로전투사격4회피2구매불가조건부',(sum(range(1,5)),sum(range(1,3)),sum(range(1,5))+sum(range(1,3)),(100-prose_total)>=sum(range(1,5))+sum(range(1,3))),(10,3,13,False))
    assert '최종 합 24' in prose and '최종 판정값 27' in prose
    check('입문폭발완료예와Partial차이2',(sum([2,3,5,6,4]),sum([2,3,5,6,4])+4,sum([2,3,5,6,4])+4+3,27-25),(20,24,27,2))
    pool_roll=[6,5,2,6,4,5,3,1,6,5];pool_hits=sum(x>=5 for x in pool_roll)
    assert 'Hit 수 = 6개' in prose and '1d10 × 6 = 6d10' in prose
    check('기관포예Pool10눈의Hit6과합43',(len(pool_roll),pool_hits,sum(pool_roll)),(10,6,43))
    single_damage=Counter({6*x:1 for x in range(1,11)});six_damage=ordinary_sum(6,10)
    check('1d10곱6과6d10피해의지지집합크기다름',(len(single_damage),len(six_damage),min(single_damage),max(single_damage),min(six_damage),max(six_damage)),(10,55,6,60,6,60))
    check('1d10곱6과6d10평균같고분산다름',(6*F(11,2),6*F(11,2),36*F(10**2-1,12),6*F(10**2-1,12)),(F(33),F(33),F(297),F(99,2)))
    assert '판정값 23' in prose and '23 - 15 = +8' in prose
    check('입문교섭폭발완료결과23과Full차이8',(sum([2,5,6,3])+4+3,23-15),(23,8))
    assert '갱 1 HP 15 → 5' in prose and '갱 1** (BOD 5, REF 5' in prose
    check('BOD5갱HP기준25와고정피해10후15',(5*5,5*5-10,15-10),(25,15,5))
    attack=prose[prose.index('### 라운드 1:'):prose.index('### 라운드 2:')]
    assert '6+4+3+2+5 = 20 + 4 + 1 - 2 = 23' in attack
    check('권총최대눈6누락Ace후최소1을더하면차이11',(sum([6,4,3,2,5])+4+1-2,(23+1)-13),(23,11))
    check('카빈응사예11과민방어19의차이',(sum([3,2,5])+3-2,sum([2,5,3,1,4])+2+2,11-19),(11,19,-8))
    assert 'Free Play (30~60분)' in prose and 'Action (60~120분)' in prose and 'Downtime (20~40분)' in prose
    check('입문5단계분범위는130부터240',(10+30+60+20+10,10+60+120+40+10),(130,240))
    assert 'HP -1 ~ -BOD' in glossary and 'HP ≤ -(BOD×2)' in glossary
    hp_gap=[hp for hp in range(-20,2) if not (hp>=1 or hp==0 or -7<=hp<=-1 or hp<=-14)]
    check('용어집BOD7음수HP기재단계공백',hp_gap,list(range(-13,-7)))
    assert '1 크레딧 = 1 KRW' in glossary and '1 오얏 = 10,000 크레딧' in glossary
    check('구판고정환율과바이트Addendum표현의수치만',(10**4,21*10**24,10**4*10**24),(10000,21000000000000000000000000,10**28))
    assert '과거' in prose and '1~2 세션 후' in prose and '- [ ] Alpha 플레이테스트 10 세션' in readme
    table_numbers=re.findall(r'^\| (\d+) \| \[',readme,re.M)
    check('README모듈표00부터15와누락16추가의서로다른계수',(list(map(int,table_numbers)),len(table_numbers)+1,len(table_numbers)+2),(list(range(16)),17,18))
    assert '/roll ?{Pool 소모량|10}d6cs5' in online and 'new Roll(`${consume}d6cs>=5`)' in online
    check('동일6눈표본의합계와정확5표시와5이상개수의차이',(sum(pool_roll),sum(x==5 for x in pool_roll),sum(x>=5 for x in pool_roll)),(43,3,6))
    assert len(final_review['tool_documentation'])==2 and final_review['tool_documentation_semantics_verified'] and not final_review['live_application_execution_verified']
    check('문서수정자확인과실제앱실행검증구분',(len(final_review['tool_documentation']),[x['live_application_execution_verified'] for x in final_review['tool_documentation']]),(2,[False,False]))
    framework_final_reader_arithmetic={'documents':5,'checks_passed':len(checks)-before_final_framework,'major_sections':[12,13,11,17,10],'online_grade_rows_checked':6,'prose_balance_costs':prose_costs,'prose_balance_total_points':prose_total,'prose_balance_remaining_points':3,'prose_same_PC_additional_shoot4_dodge2_cost':13,'prose_same_PC_history_missing_for_additional_skills':True,'Pool_sample_hits':pool_hits,'Pool_sample_face_sum':43,'damage_multiplier_support_values':10,'six_damage_dice_support_values':55,'multiplied_damage_variance':packed(F(297)),'six_damage_dice_variance':packed(F(99,2)),'gang_BOD5_formula_HP':25,'gang_HP_after_printed_damage10':15,'prose_session_minutes':[130,240],'glossary_BOD7_negative_HP_gap':hp_gap,'README_numbered_modules':16,'README_declared_module_count_with_self':17,'README_count_with_additional_16_guide':18,'tool_documentation_pages_verified':2,'live_application_execution_verified':False,**{k:False for k in ['all_legacy_logs_are_complete_histories','all_legacy_random_distributions_verified','all_specific_use_profiles_complete','external_game_rules_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']},'scope':'남은5개지정예/표·생성97p일치/별도추가학습미기재·파생/폭발/공백·배수와합분포·시간/모듈계수만검산. Roll20/Foundry공식문서는표기대조이며실제앱/봇/시스템실행검증이아니다. 구판100p빌드재작성/모든세계단위/환율·외부게임전체/정사인물수치와실제참가자시험은별도다.'}

    before_first_relationship=len(checks)
    relation_review=json.loads((here/'이전설계_통합검토.json').read_text())['first_relationship_chronology_review'];relation_texts=[]
    for row in relation_review['snapshots']:
        path=root/row['path_relative_to_plan'];relation_texts.append(path.read_bytes().decode());files.append(path)
    relationships,places,chronology,master=relation_texts
    check('1판관계장소두연대기대분류',[len(re.findall(r'^## ',x,re.M)) for x in relation_texts],[8,6,5,6])
    assert '수평 1년 = 디디 4227년 = AD 1860년' in chronology and '수평 48년 = 대사력 1년' in chronology
    check('구판가정안수평동단선형환산네시점',[(h,h+4226) for h in [1,4,34,48]],[(1,4227),(4,4230),(34,4260),(48,4274)])
    check('구판현재144와AD2003으로역산한원년및143경과',(2003-(144-1),2003-1860,144-1),(1860,143,143))
    fhi_years=[1944,1955,1963,1965];fhi_horizon_if_common=[ad-1860+1 for ad in fhi_years]
    check('구판한서력을가정하면FHI년대는수평1이후',(fhi_horizon_if_common,[h<1 for h in fhi_horizon_if_common]),([85,96,104,106],[False]*4))
    assert '검은 수평선 54년 전' in chronology
    check('1965뒤54년과구판현재2003의16년차이',(1965+54,(1965+54)-2003,(1965+54)-1860),(2019,16,159))
    assert '동쟁+15년→수평 49년+α' in chronology and '수평 19년 이전' in master
    check('동쟁34에나이15조건부출생19와이전표기49',(34-15,34+15,(34+15)-(34-15),144-(34-15)),(19,49,30,125))
    assert '사망 시 29세' in chronology and 'AD 1968~1997' in chronology
    check('크리스1968과1997차29는날짜정사입증과별개',1997-1968,29)
    check('구판대표나이역산의144빼기',[(age,144-age) for age in [17,16,22,45,27,72,14,10,5]],[(17,127),(16,128),(22,122),(45,99),(27,117),(72,72),(14,130),(10,134),(5,139)])
    types_section=master[master.index('## ■ 연대 유형 통계'):master.index('## ■ 번역·각색')]
    stated_counts=[];stated_percentages=[]
    for line in types_section.splitlines():
        cols=[x.strip() for x in line.split('|')[1:-1]]
        if len(cols)==3 and cols[0].startswith('['):stated_counts.append(int(re.search(r'\d+',cols[1])[0]));stated_percentages.append(int(re.search(r'\d+',cols[2])[0]))
    check('총람기재범주하한합129와비율합101',(stated_counts,sum(stated_counts),stated_percentages,sum(stated_percentages)),([14,12,6,11,82,4],129,[11,9,5,9,64,3],101))
    master_table=master[master.index('## ■ 전 시간축'):master.index('## ■ 비가시')];master_rows=[]
    for line in master_table.splitlines():
        cols=[x.strip() for x in line.split('|')[1:-1]]
        if len(cols)==6 and re.fullmatch(r'\[[^\]]+\]',cols[1]):master_rows.append(cols)
    master_types=Counter(row[1] for row in master_rows)
    check('총람실제표130행의유형전체수',dict(master_types),{'[추산]':6,'[확정]':13,'[범위]':7,'[현재]':100,'[미래]':3,'[한계]':1})
    check('총람실제표와요약총계의다른분모',(len(master_rows),len(master_rows)-sum(stated_counts),master_types['[현재]'],master_types['[현재]']-82),(130,1,100,18))
    summary=master[master.index('## ■ 시대별 요약'):master.index('## ■ 주요 인물')];numbered_summary=[int(x) for x in re.findall(r'^(\d+)\.',summary,re.M)]
    check('총람10줄제목과실제11항목',numbered_summary,list(range(1,12)))
    topic_by_id={row['topic']:row for row in relation_review['primary_topic_recheck']['topics']}
    assert '005  노서방' in places
    assert '신호연결사; 진;' in topic_by_id['0005']['text']
    check('원전목격10주제와위키관계3주제의별도범위',(len(topic_by_id),len(relation_review['wiki_topic_recheck']['topics'])),(10,3))
    assert '요섭 주관 장례' in chronology and '시골 청년 요섭;' in topic_by_id['0054']['text'] and '광팬이던' in topic_by_id['0054']['text']
    check('관계연대기대조새기계수치와소설전문수',(len(relation_review['new_mechanical_parameter_values']),relation_review['new_related_novels_whole_read']),(0,0))
    first_relationship_chronology_arithmetic={'documents':4,'checks_passed':len(checks)-before_first_relationship,'major_sections':[8,6,5,6],'assumed_common_AD_base':1860,'FHI_horizon_years_if_common_AD':fhi_horizon_if_common,'all_FHI_years_before_Horizon1_if_common_AD':False,'primary1965_plus54':2019,'gap_after_assumed_currentAD2003':16,'red_dragon_birth_if_battle34_and_age15':19,'red_dragon_current_age_if_constant_calendar':125,'red_dragon_dates_or_current_age_canon_verified':False,'chronology_stated_counts':stated_counts,'chronology_stated_count_sum':129,'chronology_stated_percentage_sum':101,'master_table_type_counts':dict(master_types),'master_table_rows':len(master_rows),'current_rows_in_master_table':100,'numbered_summary_rows':len(numbered_summary),'primary_topics_whole_rechecked':10,'wiki_topics_whole_rechecked':3,**{k:False for k in ['all_relationships_canon_verified','all_first_chronology_dates_canon_verified','all_related_novels_reviewed','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']},'scope':'4개문서의기재시점/계산·한AD/수평가정아래순서충돌·가정출생/나이·총람기재통계와실제표행분모/요약항목만검산. 조건부환산은FEWK세계공통정사연표/현재나이입증이아니며원전10/위키3과1판분류의출처범위를구분한다.100편동시/전체소설100의원전대조·실제참가자검증은별도다.'}

    before_first_catalog=len(checks)
    catalog_review=json.loads((here/'이전설계_통합검토.json').read_text())['first_people_places_objects_groups_catalog_review'];catalog_texts=[]
    for row in catalog_review['snapshots']:
        path=root/row['path_relative_to_plan'];catalog_texts.append(path.read_bytes().decode());files.append(path)
    people,places,objects,groups=catalog_texts
    check('1판네목록대분류43절',[len(re.findall(r'^## ',x,re.M)) for x in catalog_texts],[5,13,13,12])
    def indexed_rows(text):return re.findall(r'^\| ([A-K]\d{2,3}) \| ([^|]+) \|',text,re.M)
    person_rows=indexed_rows(people);person_bins=[sum(id.startswith(k) for id,_ in person_rows) for k in 'ABC']
    check('인물목록의번호행202는고유개인수가아님',(person_bins,len(person_rows)),([18,177,7],202))
    population=[int(x) for x in re.findall(r'^\| C\d{2} \| [^|]+ \| [^|]+ \| (\d+)만 \|',places,re.M)]
    check('구판서울인구기재5부분내부합1000만',(population,sum(population)),([300,280,250,120,50],1000))
    natural=places.split('### H-2.')[1].split('### H-3.')[0];artificial=places.split('### H-3.')[1].split('### H-4.')[0]
    natural_names=re.findall(r'^\| ([^|]+) \|',natural,re.M)[1:];artificial_names=re.findall(r'^\| ([^|]+) \|',artificial,re.M)[1:]
    def realm_name(x):return '오크계/플랫마운틴' if '오크계' in x and '플랫마운틴' in x else x.strip()
    catalog_realm_names={realm_name(x) for x in natural_names+artificial_names}
    check('장소목록의자연인공행30과한명칭겹침29',(len(natural_names),len(artificial_names),len(natural_names)+len(artificial_names),len(catalog_realm_names)),(13,17,30,29))
    object_rows=indexed_rows(objects);object_bins=[sum(id.startswith(k) for id,_ in object_rows) for k in 'ABCDEFGHIJK']
    check('사물목록11개범주179행',object_bins,[18,22,16,20,8,10,14,17,24,15,15])
    object_summary=objects.split('## M. 통계')[1];stated_object_counts=[int(x) for x in re.findall(r'^\| [^|]+ \| (\d+) \|',object_summary,re.M)]
    assert '**약 180**' in object_summary
    check('사물통계합179와약180근사는오류가아님',(stated_object_counts,sum(stated_object_counts),len(object_rows),180-sum(stated_object_counts)),(object_bins,179,179,1))
    parchment_rows=[id for id,name in object_rows if name.strip()=='양피지']
    check('양피지두번등장고유사물과행수의다른분모',parchment_rows,['I18','K01'])
    group_rows=indexed_rows(groups);company_sections=groups.split('### C-1.')[1].split('## D.')[0]
    company_parts=company_sections.split('### C-2.');existing_company=indexed_rows(company_parts[0]);new_and_other=company_parts[1].split('### C-3.');new_company=indexed_rows(new_and_other[0]);other_company=indexed_rows(new_and_other[1])
    check('기업기재15더하기8과기타10행',(len(existing_company),len(new_company),len(other_company),sum(id.startswith('C') for id,_ in group_rows)),(15,8,10,33))
    shares=[int(x) for x in re.findall(r'(?:S-Link|P-Jack|D-Port|A-Slot|I-Pin|M-Gate) (\d+)%',groups)]
    check('구판부분커넥터점유율87과미기재13',(shares,sum(shares),100-sum(shares)),([35,12,15,10,10,5],87,13))
    group_summary=groups.split('## L. 통계')[1];summary_counts=[]
    for line in group_summary.splitlines():
        cols=[x.strip() for x in line.split('|')[1:-1]]
        if len(cols)==2 and not cols[0].startswith('**'):
            nums=[int(x) for x in re.findall(r'\d+',cols[1])]
            if nums:summary_counts.append(sum(nums))
    check('집단목록170행과요약151의서로다른범주분모',(len(group_rows),summary_counts,sum(summary_counts),len(group_rows)-sum(summary_counts)),(170,[13,14,23,13,25,10,39,14],151,19))
    catalog_topics={row['topic']:row['text'] for row in catalog_review['primary_topic_recheck']['topics']}
    assert '로세아국 해군 | 넵튠' in groups and '미모국, 시크 비서관 출신' in objects and '미모대사국; 흑해전함 넵튠' in catalog_topics['0088']
    assert '이 여섯 개 구역은 실제 존재하는 지명이 아니다' in catalog_topics['0063'] and '어른들도 출입할 수' in catalog_topics['0080'] and '어떤 장비나 무기도 들어갈 수 없다' in catalog_topics['0080']
    assert '커플' in catalog_topics['0079'] and '오토바이' in catalog_topics['0079']
    first_catalog_arithmetic={'documents':4,'checks_passed':len(checks)-before_first_catalog,'major_sections':[5,13,13,12],'person_index_bins':person_bins,'person_index_rows':202,'assumed_city_population_parts_in_ten_thousands':population,'assumed_city_population_total_in_ten_thousands':1000,'natural_realm_rows':13,'artificial_realm_rows':17,'realm_rows':30,'realm_alias_normalized_names':29,'object_category_rows':object_bins,'object_rows':179,'stated_approximate_object_count':180,'parchment_rows':parchment_rows,'company_base_new_other_rows':[15,8,10],'company_rows':33,'proposed_connector_shares':shares,'proposed_connector_share_sum':87,'unreported_share_remainder':13,'group_index_rows':170,'group_summary_counts':summary_counts,'group_summary_sum':151,'group_row_summary_gap':19,'primary_topics_whole_rechecked':7,**{k:False for k in ['all_catalog_entries_individually_canon_verified','catalog_counts_are_world_unique_entities','all_related_novels_reviewed','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']},'scope':'4개 목록의 행/통계 내부 산술·약180 근사의 옳은 합·같은 양피지/오크계 중복·기업/집단/인물 분모를 검산한다. 7개 원전의 소속/스타일/이름/출입과 목록 충돌을 대조하되 모든 항목의 정사·인구/소속/고유 수/시장점유 검증은 아니다. 새 엔진 수치/100p/소설100 재작성이나 실제 참가자 검증을 포함하지 않는다.'}

    before_first_life=len(checks)
    life_review=json.loads((here/'이전설계_통합검토.json').read_text())['first_life_uncertainty_class_institutions_review'];life_texts=[]
    for row in life_review['snapshots']:
        path=root/row['path_relative_to_plan'];life_texts.append(path.read_bytes().decode());files.append(path)
    miscellaneous,unknown,class_symbols,institutions=life_texts
    check('1판생활불특정계급제도경제46절',[len(re.findall(r'^## ',x,re.M)) for x in life_texts],[15,10,10,11])
    value_section=miscellaneous.split('## C. 가치 7요소')[1].split('## D.')[0];value_rows=re.findall(r'^\| (C\d{2}) \|',value_section,re.M)
    check('구판가치7제목과여덟행혼백혼합분류',value_rows,['C01','C02','C03','C04','C05','C06','C07','C08'])
    assert '50,000+오얏 (41년 생활비)' in miscellaneous and '서민 41년치 생활비' in class_symbols
    crocodile_price_floor=50000;expense_rates=[50,100,200]
    cost_years=[F(crocodile_price_floor,monthly*12) for monthly in expense_rates]
    check('오만오얏탈것의세생활비가정별연수',cost_years,[F(250,3),F(125,3),F(125,6)])
    monthly100_months=F(crocodile_price_floor,100)
    check('월100가정500개월은41년8개월',(monthly100_months,int(monthly100_months)//12,int(monthly100_months)%12),(F(500),41,8))
    assert '50오얏 (쪽방+죽+충전)' in miscellaneous and '오얏죽 1그릇 | 2오얏' in miscellaneous
    check('구판월50총생활비와30일하루한죽가정60의10차이',(30*2,30*2-50),(60,10))
    check('구판죽하루세그릇가정180과50및100예산차',(30*3*2,30*3*2-50,30*3*2-100),(180,130,80))
    assert '서민구 최저 월세 | 50' in institutions and '와치벨 평균 월세 | 200' in institutions
    check('같은금액총생활비와월세를동시적용하면기타지출영',[budget-rent for budget,rent in zip([50,100,200],[50,100,200])],[0,0,0])
    assert '월 5오얏, 사망 시 200오얏' in miscellaneous
    check('구판보험기재지급200은보험료5의40회분',F(200,5),F(40))
    assert '오주사 1g | 105만' in institutions and '오주사 4200톤 (063) | 4,435조' in institutions
    cinnabar_grams=4200*10**6;cinnabar_unit_price=105*10**4;cinnabar_computed=cinnabar_grams*cinnabar_unit_price;cinnabar_stated=4435*10**12
    check('오주사4200톤에그램105만가정4410조와표4435조차25조',(cinnabar_grams,cinnabar_computed,F(cinnabar_computed,10**12),F(cinnabar_stated-cinnabar_computed,10**12),F(cinnabar_stated,cinnabar_grams)),(4200000000,4410000000000000,F(4410),F(25),F(22175000,21)))
    fx_section=institutions.split('### 7-2.')[1].split('### 7-3.')[0];fx_rows=[]
    for line in fx_section.splitlines():
        cols=[x.strip() for x in line.split('|')[1:-1]]
        if len(cols)==3 and re.match(r'^\d',cols[1]):fx_rows.append(cols)
    def stated_fx_bounds(label,korean=False):
        label=label.replace(',','').rstrip('+');factor=1
        if korean:
            match=re.search(r'(만|억)$',label);assert match
            factor={'만':10000,'억':100000000}[match[0]];label=label[:match.start()]
        vals=[int(x)*factor for x in label.split('-')]
        return [vals[0],vals[-1]]
    fx_agreements=[]
    for _,oyat_label,won_label in fx_rows:
        oyat_bounds=stated_fx_bounds(oyat_label);won_bounds=stated_fx_bounds(won_label,True);fx_agreements.append([x*10000 for x in oyat_bounds]==won_bounds)
    check('구판17환산행의범위와하한산술은일관',(len(fx_rows),fx_agreements),(17,[True]*17))
    assert '234억만 (= 23742190000)' in institutions
    check('234억과표기234억만곱셈해석및기재숫자의차',(234*10**8,23742190000-234*10**8,234*10**8*10**4),(23400000000,342190000,234000000000000))
    life_topics={row['topic']:row['text'] for row in life_review['primary_topic_recheck']['topics']}
    assert '회사마다 합격의 기준이 다르지만' in life_topics['0010'] and '생체순도; 100%의 노숙자' in life_topics['0011']
    assert '본래의 이름은 있지만' in life_topics['0040'] and '어른들도 출입할 수' in life_topics['0080']
    assert '플랫마운틴은 DDOGG 때문에 아이들만 접근 가능한' in institutions
    novel=life_review['related_novel_recheck'];novel_path=root/novel['path_relative_to_plan'];files.append(novel_path)
    assert novel['text']==novel_path.read_bytes().decode() and '이 편지를 누가 읽게 될지 모르겠다' in novel['text'] and '아키비스트 윤세라' in novel['text']
    first_life_uncertainty_arithmetic={'documents':4,'checks_passed':len(checks)-before_first_life,'major_sections':[15,10,10,11],'value_rows':value_rows,'value_row_count':8,'value_heading_count':7,'crocodile_assumed_price_floor':50000,'assumed_monthly_living_costs':expense_rates,'crocodile_conditional_years':[str(x) for x in cost_years],'crocodile_conditional_months_at100':500,'crocodile_conditional_year_month_at100':[41,8],'assumed_one_soup_per_day_month_cost':60,'assumed_three_soups_per_day_month_cost':180,'living_cost_rent_same_value_other_costs':[0,0,0],'proposed_insurance_monthly_premium':5,'proposed_insurance_payout':200,'payout_premium_ratio':40,'cinnabar_assumed_grams':cinnabar_grams,'cinnabar_assumed_price_per_gram':cinnabar_unit_price,'cinnabar_assumed_total_credits':cinnabar_computed,'cinnabar_stated_total_credits':cinnabar_stated,'cinnabar_total_difference_credits':cinnabar_stated-cinnabar_computed,'cinnabar_implied_quoted_price_per_gram':str(F(cinnabar_stated,cinnabar_grams)),'stated_currency_conversion_rows':17,'stated_currency_conversion_rows_agree':all(fx_agreements),'stated_234eok_credits':23400000000,'stated_numeric_value':23742190000,'numeric_gap_if_234eok':342190000,'value_if_literal_eok_times_man':234000000000000,'primary_topics_whole_rechecked':12,'related_novels_whole_rechecked':1,'new_related_novels_whole_read':0,**{k:False for k in ['all_institutions_and_laws_canon_verified','all_unnamed_stories_or_unknown_identities_verified','all_related_novels_reviewed','all_specific_use_profiles_complete','real_world_exchange_rate_current_verified','all_daily_food_requirements_or_market_prices_canon_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']},'scope':'4문서의 제목/기재행·월생활비/월세분모·기간/식사횟수/가격을가정한내부산술·보험료/지급·질량/가격과기재총액·17행환산의옳은산술·234억만의조건부단위해석을대조한다. 이값은새FEWK가격/보험/금융/생리/현실환율/법률/성장제가아니다. 원전12주제와기존관련소설1편의현재전문을대조하며새소설0/100편재작성0/실제참가자미검증을유지한다.'}

    reader_before=len(checks)
    reader=json.loads((here/'이전설계_통합검토.json').read_text())['first_encyclopedia_scene_glossary_review']
    reader_texts=[]
    for row in reader['snapshots']:
        path=root/row['path_relative_to_plan'];files.append(path);reader_texts.append(path.read_bytes().decode())
    encyclopedia,scene,glossary=reader_texts
    check('1판백과씬용어43절',[len(re.findall(r'^## ',x,re.M)) for x in reader_texts],[16,17,10])
    numbered=[int(x) for x in re.findall(r'^### (\d+)\.',glossary,re.M)]
    check('1판사전40번호중비FEWK호호레이제외39',(numbered,len(numbered)-1),(list(range(1,41)),39));assert '### 11. 호호레이(해당 없음)' in glossary
    novel=reader['related_novel_review'];path=root/novel['path_relative_to_plan'];files.append(path);nt=path.read_bytes().decode();assert nt==novel['text'] and '시급 오얏 0.3' in nt and '월급 3.6오얏' in scene and '한 달 오얏 108' in nt
    check('소설083시급03일당36월30일가정108',(F(3,10)*12,F(3,10)*12*30),(F(18,5),F(108)))
    check('씬월급36과소설월108의30배분모차',(F(108)/F(18,5),F(108)-F(18,5)),(F(30),F(522,5)))
    check('코핀300가격의일당36월108총액저축기간가정',(F(300)/F(18,5),F(300,108)),(F(250,3),F(25,9)))
    assert '보정률이 92퍼센트' in nt and '98퍼센트' in nt
    check('보정률92에서98은6퍼센트포인트상대3분의46',(98-92,F(98-92,92)),(6,F(3,46)))
    check('정식5두끼10과술3세잔9잔당3일때1은3분의1잔',(5*2,3*3,F(1,3),F(3,2)),(10,9,F(1,3),F(3,2)))
    assert '궁정구 한 달 월세' in encyclopedia and '궁정구 연간 생활' in encyclopedia
    check('월1000임대12개월은12000으로하한10000만으로불충분',(1000*12,1000*12-10000),(12000,2000))
    check('같은방10하루100삼일가정의일당비교',(F(10),F(100,3),F(100,3)-10),(F(10),F(100,3),F(70,3)))
    assert '오얏 0.5. 밥 한 끼 반' in nt and '한 개로 한 끼' in next(x['text'] for x in reader['primary_topic_recheck']['topics'] if x['topic']=='0015')
    check('원전한개한끼가정05는반끼소설한끼반과1차이',(F(1,2),F(3,2)-F(1,2)),(F(1,2),F(1)))
    assert '23시부터 11시까지' in nt and '7시. 4시간 남았어' in nt
    check('공장23시시작12시간11시종료8시간경과7시잔여4',((23+12)%24,(23+8)%24,12-8),(11,7,4))
    first_encyclopedia_scene_glossary_arithmetic={'documents':3,'checks_passed':len(checks)-reader_before,'major_sections':[16,17,10],'numbered_slots':40,'FEWK_entries_excluding_nonFEWK_placeholder':39,'daily_wage':'18/5','monthly_wage_assuming30_days':108,'scene_monthly_wage_mislabel_factor':30,'coffin300_days_at_daily36':'250/3','coffin300_months_at_monthly108':'25/9','quality_difference_percentage_points':6,'quality_relative_difference':'3/46','annual_rent_assuming1000_monthly':12000,'lower_bound10000_shortfall':2000,'room_price_terms_not_fixed':True,'half_oyat_meals_assuming_one_oyat_one_meal':'1/2','primary_topics_whole_rechecked':7,'related_novels_whole_read_in_pass':1,'all_market_prices_or_labor_conditions_canon_verified':False,'current_engine_changed':False,'old_100point_build_rewritten':False,'actual_participant_playtest':False,'scope':'구판의 기재 분모/기간/번호·직접소설083의 실제 시급/일당/월급과 각색표의 오기·퍼센트포인트/상대비율·같은 상품/월30일/전액저축 가정의 조건부 산술이다. 세계 현재 가격/근무일/회복·IO 성공률을 확정하지 않으며10000이상에12000이 포함될 수 있음을 유지한다.'}

    voice_before=len(checks)
    voice=json.loads((here/'이전설계_통합검토.json').read_text())['first_address_nuance_motif_review'];voice_texts=[]
    for row in voice['snapshots']:
        path=root/row['path_relative_to_plan'];files.append(path);voice_texts.append(path.read_bytes().decode())
    address,nuance,motif=voice_texts
    check('1판호칭뉘앙스모티프93절',[len(re.findall(r'^## ',x,re.M)) for x in voice_texts],[7,71,15])
    numbers=[int(x) for x in re.findall(r'^\*\*\[(\d+)\]',nuance,re.M)]
    check('뉘앙스83연속항목은100소설전문대조와별도',numbers,list(range(1,84)))
    story_sections=[x for x in re.split(r'^## ',nuance,flags=re.M) if re.match(r'\d{3} ',x)];story_counts=[len(re.findall(r'^\*\*\[\d+\]',x,re.M)) for x in story_sections]
    check('뉘앙스초기64편중58편한항목6편두항목',(len(story_sections),Counter(story_counts)),(64,Counter({1:58,2:6})))
    coverage={int(x[:3]) for x in story_sections};combined=nuance.split('## 067~100 주요 뉘앙스')[1].split('## 부록:')[0]
    for line in combined.splitlines():
        if not re.match(r'^\*\*\[\d+\] ',line):continue
        label=re.sub(r'^\*\*\[\d+\] ','',line).split(' — ')[0];ids=[int(x) for x in re.findall(r'\b\d{3}\b',label)]
        if '~' in label:assert len(ids)==2;coverage.update(range(ids[0],ids[1]+1))
        else:coverage.update(ids)
    absent=sorted(set(range(1,101))-coverage)
    check('뉘앙스92편번호지시와8누락은분모가다름',(len(coverage),absent),(92,[12,15,71,73,77,78,79,81]))
    def translation_rows(text,start,end):
        part=text.split(start)[1].split(end)[0];return [x for x in part.splitlines() if x.startswith('| ')][1:]
    lexicon_counts=[len(translation_rows(address,'### 5-1.','### 5-2.')),len(translation_rows(motif,'### 12-1.','### 12-2.'))]
    check('호칭28대응어모티프34대응어는별도목록',lexicon_counts,[28,34])
    assert '12초→0.4초' in address and '12초에서 0.4초로' in nuance
    check('소설의12초04초는30배기간비율이며실제성공률아님',(F(12)/F(2,5),F(12)-F(2,5)),(F(30),F(58,5)))
    novel=voice['related_novel_recheck'];path=root/novel['path_relative_to_plan'];files.append(path);assert novel['text']==path.read_bytes().decode() and '월급 3.6오얏' in nuance and '하루 오얏 3.6. 한 달 오얏 108.' in novel['text']
    first_address_nuance_motif_arithmetic={'documents':3,'checks_passed':len(checks)-voice_before,'major_sections':[7,71,15],'nuance_numbered_entries':83,'individual_story_headings':64,'individual_stories_with_one_entry':58,'individual_stories_with_two_entries':6,'story_numbers_referenced_including_grouped_ranges':92,'story_numbers_not_referenced':absent,'translation_mapping_rows':[28,34],'story12_to04_duration_ratio':30,'primary_topics_whole_rechecked':5,'related_novels_whole_rechecked':1,'new_related_novels_whole_read':0,'all_quoted_novel_passages_against_whole_novels_verified':False,'all_translation_terms_canon_verified':False,'all_related_novels_reviewed':False,'current_engine_changed':False,'old_100point_build_rewritten':False,'actual_participant_playtest':False,'scope':'문서의 절/항목/스토리 번호 지시/누락·두 번역목록 분모와 개별 소설 시간비율을 검산한다. 번호92개는92개 소설 전문 읽음/인용 대조 증거가 아니며, 해석은 전역 법칙/판정/PC감정 강제가 아니다. 소설083을 재대조해 뉘앙스의 월급3.6 오기와 기존 임금 검산을 연결한다.'}

    narrator_before=len(checks)
    narrator_review=json.loads((here/'이전설계_통합검토.json').read_text())['first_letters_narrator_translation_readme_review'];narrator_texts=[]
    for row in narrator_review['snapshots']:
        path=root/row['path_relative_to_plan'];files.append(path);narrator_texts.append(path.read_bytes().decode())
    letters,narration,translation,old_readme=narrator_texts
    check('1판서간서술번역README127절',[len(re.findall(r'^## ',x,re.M)) for x in narrator_texts],[7,10,101,9])
    letter_table=letters.split('## 1.')[1].split('## 2.')[0];letter_rows=[x.split('|')[1:-1] for x in letter_table.splitlines() if re.match(r'^\| \d+ ',x)];letter_ids=[int(x[3].strip()) for x in letter_rows if x[3].strip().isdigit()]
    check('서간22행21번호행20고유소설번호064중복',(len(letter_rows),len(letter_ids),len(set(letter_ids)),Counter(letter_ids)[64]),(22,21,20,2))
    translated_sections=[x for x in re.split(r'^## ',translation,flags=re.M) if re.match(r'\d{3} ',x)]
    check('번역안내100개연속번호는100소설전문대조와별도',[int(x[:3]) for x in translated_sections],list(range(1,101)))
    field_counts=Counter(len(re.findall(r'^\| \*\*([^*]+)\*\* \|',x,re.M)) for x in translated_sections)
    check('번역안내85표7항목후반15표2부터5항목',field_counts,Counter({7:85,2:12,5:1,4:1,3:1}))
    view_table=narration.split('### 7-1.')[1].split('## 8부.')[0];view_rows=[x for x in view_table.splitlines() if re.match(r'^\| \d{3}',x)];view_ids=set()
    for row in view_rows:
        label=row.split('|')[1].strip();ids=[int(x) for x in re.findall(r'\d{3}',label)]
        if '~' in label:view_ids.update(range(ids[0],ids[1]+1))
        else:view_ids.update(ids)
    check('시점맵86행100번호포함은08509915편묶음',(len(view_rows),sorted(view_ids)),(86,list(range(1,101))))
    fid_table=narration.split('## 3부.')[1].split('## 4부.')[0];fid_rows=[x for x in fid_table.splitlines() if re.match(r'^\| \d+ ',x)];fid_ids=[]
    for row in fid_rows:fid_ids.extend(re.findall(r'\b\d{3}\b',row.split('|')[2]))
    check('FID25위치26번호지시25고유번호065두위치',(len(fid_rows),len(fid_ids),len(set(fid_ids)),Counter(fid_ids)['065']),(25,26,25,2))
    directory=old_readme.split('## 1.')[1].split('## 2.')[0];declared_md=re.findall(r'([A-Za-z0-9가-힣_]+\.md)',directory)
    inv=json.loads((here/'이전설계_통합검토.json').read_text())['bounded_older_source_inventory'];actual_first=[entry for entry in inv['files'] if '[1판_설정집]' in unicodedata.normalize('NFC',entry['path_relative_to_plan'])]
    check('README31md와취득1판32md총람누락',(len(declared_md),len(actual_first),'03_연대기_총람.md' not in declared_md),(31,32,True))
    narrator_novels={}
    for row in narrator_review['related_novel_reviews']:
        path=root/row['path_relative_to_plan'];files.append(path);text=path.read_bytes().decode();assert text==row['text'];narrator_novels[row['name'][:3]]=text
    n24=narrator_novels['024'];n100=narrator_novels['100'];chapters=re.findall(r'^## (\d+)\.$',n24,re.M);ending=n24.split('## 7.')[1].split('**끝.**')[0]
    check('소설024일곱대화장마지막비공란과100일곱편지',(chapters,len(re.findall(r'^\*\*[^\n]*번째 편지\.\*\*$',n100,re.M)),bool(ending.strip())),([str(x) for x in range(1,8)],7,True))
    assert '아그네스는 홀로 길을 나섰다' in ending and '토닥이라니' in ending and '손톱 없이 재생되는 손' not in n24
    for row in narrator_review['current_wiki_rechecks']:files.append(root/row['path_relative_to_plan'])
    first_letters_narrator_translation_readme_arithmetic={'documents':4,'checks_passed':len(checks)-narrator_before,'major_sections':[7,10,101,9],'letter_list_rows':22,'letter_numeric_story_rows':21,'letter_unique_story_numbers':20,'translation_numbered_summaries':100,'translation_rows_with_seven_fields':85,'translation_partial_tables':15,'viewpoint_table_rows':86,'FID_locations':25,'FID_story_number_occurrences':26,'FID_unique_story_numbers':25,'readme_declared_md':31,'bounded_first_inventory_md':32,'novel024_numbered_dialogue_chapters':7,'novel024_last_chapter_nonempty':True,'novel100_letters':7,'primary_topics_whole_rechecked':6,'related_novels_whole_read_in_pass':2,'new_related_novels_whole_read':1,'previously_reviewed_related_novels_rechecked':1,'current_wiki_documents_whole_rechecked':2,'all_quoted_novel_passages_against_whole_novels_verified':False,'all_related_novels_reviewed':False,'old_self_completion_claims_are_fifth_evidence':False,'current_engine_changed':False,'old_100point_build_rewritten':False,'actual_participant_playtest':False,'scope':'범위/완료해석에영향을주는행·소설번호/묶음·표의실제필드·시점/FID분모·README구조와취득목록·직접024/기존100의서로다른7구조를대조한다.100요약/86시점행/25위치는100소설/번역전수검토증거가아니다.024마지막공란/소멸을복원하지않고기록자의정보/현지몸/장치와같은인터랙션을유지한다.'}

    chronology_review=json.loads((here/'이전설계_통합검토.json').read_text())['foundational_chronology_csv_review']
    chronology_source=chronology_review['snapshot'];chronology_path=root/chronology_source['path_relative_to_plan'];files.append(chronology_path)
    raw_chronology=chronology_path.read_bytes().decode();assert raw_chronology==chronology_source['text']
    parsed=list(csv.reader(io.StringIO(raw_chronology)));head=parsed[0];chronology_rows=parsed[1:]
    idx={name:i for i,name in enumerate(head)}
    by_year={int(row[0]):row for row in chronology_rows}
    def at(year,column):return by_year[year][idx[column]]
    before_chronology=len(checks)
    check('연대표383연도행21열연속1653부터2035',(len(chronology_rows),set(map(len,parsed)),sorted(by_year)),(383,{21},list(range(1653,2036))))
    calendar_contract={'디디':(351,2367),'수평':(144,-1859),'광제력':(141,-1862),'동쟁':(14,-1893),'대사력':(97,-1906),'(주)신성':(120,-1887)}
    calendar_results={}
    for name in calendar_contract:
        values=[(int(row[0]),int(row[idx[name]])) for row in chronology_rows if re.fullmatch(r'\d+',row[idx[name]])]
        calendar_results[name]=(len(values),{value-year for year,value in values})
    check('연대표여섯연호의실제기재행수와일정한환산차',calendar_results,{name:(count,{offset}) for name,(count,offset) in calendar_contract.items()})
    wiki_chronology={}
    for row in chronology_review['current_wiki_rechecks']:
        path=root/row['path_relative_to_plan'];files.append(path);content=path.read_bytes().decode();assert content==row['text'];wiki_chronology[row['name']]=content
    assert '광제력 1년 = 디디 4230년 = 수평 3년' in wiki_chronology['광제력.md']
    check('광제원년CSV수평4와위키수평3의한해차이',(at(1863,'디디'),at(1863,'광제력'),int(at(1863,'수평'))-3),('4230','1',1))
    assert '[[디디]]4254년, [[수평]]28년, [[광제력]]25년' in wiki_chronology['연호.md']
    check('신성창립행과기업원년카운터는서로다름',(at(1887,'FEWK'),at(1887,'디디'),at(1887,'(주)신성'),at(1888,'디디'),at(1888,'(주)신성'),int(at(1888,'디디'))-4254),('(주)신성 창립','4254','','4255','1',1))
    check('적룡화이듬해1과다른네인물출생해1',(at(1885,'적룡화'),at(1886,'적룡화'),at(1944,'마리아'),at(1968,'크리스'),at(1978,'케이티'),at(1973,'수덕')),('적룡화 출생','1','1','1','1','1'))
    original_chronology={row['topic']:row['text'] for row in chronology_review['primary_topic_recheck']['topics']}
    assert '20대 무명 헤비메탈 연주자' in original_chronology['0054'] and '기타' in original_chronology['0054']
    after_funeral=[int(row[0]) for row in chronology_rows if int(row[0])>1997 and row[idx['크리스']]]
    check('크리스카운터30의연도차29와장례뒤여섯카운터',(1997-1968,at(1997,'FEWK'),at(1997,'크리스'),at(2003,'크리스'),after_funeral),(29,'크리스의 장례식','30','36',list(range(1998,2004))))
    war_years=[int(row[0]) for row in chronology_rows if row[idx['동쟁']]]
    war_event_rows=[row for row in chronology_rows if re.fullmatch(r'동쟁\d+',row[idx['FEWK']])]
    check('동쟁14카운터는10전쟁표기와4후속사건행',(war_years,len(war_event_rows),[at(year,'FEWK') for year in range(1904,1908)]),(list(range(1894,1908)),10,['광제 망명','<사건_분할통치>','대사국 내전','<와치벨 협약>']))
    check('자료현재2003여섯값44표기행과32후속행',(tuple(at(2003,name) for name in ['FEWK','수평','광제력','대사력','(주)신성','크리스']),sum(bool(row[idx['FEWK']]) for row in chronology_rows),sum(int(row[0])>2003 for row in chronology_rows),sum(bool(row[19]) or bool(row[20]) for row in chronology_rows)),(('현재','144','141','97','116','36'),44,32,0))
    foundational_chronology_csv_arithmetic={'checks_passed':len(checks)-before_chronology,'data_rows':len(chronology_rows),'columns':len(head),'FEWK_nonempty_rows':44,'source_current_AD':2003,'source_rows_after_current':32,'Chris_funeral_year_gap':29,'Chris_funeral_counter':30,'Chris_post_funeral_counter_rows':6,'company_first_counter_DD':4255,'wiki_company_first_year_DD':4254,'war_counter_rows':14,'war_named_annual_rows':10,'calendar_numeric_rows':{name:result[0] for name,result in calendar_results.items()},'source_current_is_fifth_current':False,'all_world_calendar_dates_or_ages_fixed':False,'real_history_columns_fact_checked':False,'linked_Google_Doc_read':False,'actual_participant_playtest':False}

    outline_review=json.loads((here/'이전설계_통합검토.json').read_text())['foundational_world_bible_outline_review']
    outline_source=outline_review['snapshot'];outline_path=root/outline_source['path_relative_to_plan'];files.append(outline_path);outline_text=outline_path.read_bytes().decode();assert outline_text==outline_source['text']
    outline_lines=outline_text.splitlines();latest_outline=outline_text.split('—아래는 참고용—-')[0]
    old_outline=outline_text.split('FEWK 월드 바이블: 최종 상세 목차 설계도 (Ver. 3.0)')[1]
    def declared_budgets(pattern,part):return [int(value.replace(',','')) for value in re.findall(pattern,part,re.M)]
    outline_before=len(checks)
    latest_parts=declared_budgets(r'^(?:서문|제[1-5]부:|부록)[^\n]*총 예상 분량: ([\d,]+)자',latest_outline)
    check('Ver5기획상7부분502천자는실제집필량아님',(latest_parts,sum(latest_parts),sum(latest_parts)-500000),([7000,45000,100000,40000,110000,100000,100000],502000,2000))
    law_sections=declared_budgets(r'^\* (?:\* )?1\.\d\.[^\n]*총 ([\d,]+)자',latest_outline)
    check('Ver5법칙4묶음의기획합45천자',(law_sections,sum(law_sections)),([12000,11000,11000,11000],45000))
    geography=latest_outline.split('2.2. 지리:')[1].split('2.3. 권력의 지도:')[0]
    geo_rows=re.findall(r'^\s*\* 2\.2\.\d\.[^\n]*\(2,500자\)',geography,re.M)
    check('Ver5지리9기재행22천5백과부모25천예산',(len(geo_rows),len(geo_rows)*2500,25000-len(geo_rows)*2500),(9,22500,2500))
    power=latest_outline.split('2.3. 권력의 지도:')[1].split('2.4. 사회와 계급:')[0]
    power_rows=re.findall(r'^\s*\* 2\.3\.[1-4]\.[^\n]*\(2,500자\)',power,re.M)
    assert '18개 x 2,000자 = 36,000자' in power
    check('Ver5세력4개개요와18선정프로필46천',(len(power_rows),len(power_rows)*2500+18*2000,50000-(len(power_rows)*2500+18*2000)),(4,46000,4000))
    style=latest_outline.split('2.4. 사회와 계급:')[1].split('제3부:')[0]
    style_rows=re.findall(r'^\s*\* 2\.4\.\d\.[^\n]*\(2,500자\)',style,re.M)
    assert '25라인씩' in style
    check('Ver5스타일두개기재행5천과150라인열거계획',(len(style_rows),len(style_rows)*2500,10000-len(style_rows)*2500,6*25),(2,5000,5000,150))
    appendix=latest_outline.split('부록 (총 예상 분량:')[1];app_budgets=declared_budgets(r'^\* [ABC]\.[^\n]*총 ([\d,]+)자',appendix)
    app_budgets+=declared_budgets(r'^\s*\* \[예상 분량\]: ([\d,]+)자',appendix)
    check('Ver5부록세묶음과원문모음네예산100천',(app_budgets,sum(app_budgets)),([25000]*4,100000))
    keiti=old_outline.split('2.3.3. 사례 분석:')[1].split('2.3.4. 종교재단')[0]
    chapter_ranges=re.findall(r'소설 (\d+)~(\d+)편 수록',keiti);chapter_budgets=re.findall(r'2,500자 x 4',keiti)
    check('Ver3케이티5개번호구간50천과제목70천기획',(chapter_ranges,len(chapter_budgets),len(chapter_budgets)*2500*4,70000-len(chapter_budgets)*2500*4),([('1','10'),('11','20'),('21','30'),('31','40'),('41','50')],5,50000,20000))
    old_app=old_outline.split('부록 (Appendix):')[1]
    app_groups=declared_budgets(r'^[AB]\.[^\n]*총 ([\d,]+)자',old_app)
    check('Ver3부록A27천B28천합55천과75천기획예산',(app_groups,sum(app_groups),75000-sum(app_groups)),([27000,28000],55000,20000))
    foundational_world_bible_outline_arithmetic={'checks_passed':len(checks)-outline_before,'Ver5_part_budgets':latest_parts,'Ver5_part_sum':sum(latest_parts),'Ver5_geography_budgeted_rows':9,'Ver5_geography_allocated_chars':22500,'Ver5_selected_power_profiles_planned':18,'Ver5_power_allocated_chars':46000,'Ver5_style_features_planned_lines':150,'Ver5_appendix_part_budgets':app_budgets,'Ver3_Keiti_numbered_ranges_planned':chapter_ranges,'Ver3_Keiti_allocated_chars':50000,'Ver3_Keiti_stated_parent_budget':70000,'Ver3_appendix_AB_budget_sum':55000,'Ver3_appendix_stated_budget':75000,'source_heading_rows_are_actual_written_chapters':False,'outline_lengths_are_actual_written_lengths':False,'all_source_story_ranges_whole_read':False,'all_maps_or_project_archives_delivered':False,'fifth_engine_changed':False,'actual_participant_playtest':False}

    prose_review=json.loads((here/'이전설계_통합검토.json').read_text())['foundational_world_bible_prose_review']
    prose_source=prose_review['snapshot'];prose_path=root/prose_source['path_relative_to_plan'];files.append(prose_path);prose_text=prose_path.read_bytes().decode();assert prose_text==prose_source['text']
    prose_before=len(checks);prediction=prose_text.split('FEWK 월드 바이블 전체 원고 분량 예측')[1]
    predicted_budgets=[int(x)*10000 for x in re.findall(r'^[1-6]\. [^\r\n]*\(약 (\d+)만 자\)',prediction,re.M)]
    check('설명원고여섯기획분량합110만과실문서43175자구분',(predicted_budgets,sum(predicted_budgets),len(prose_text)),([150000,250000,150000,300000,200000,50000],1100000,43175))
    first_horizon=re.search(r'검은 수평선 사건 \(수평력 (\d+)년 / 디디 (\d+)년\)',prose_text)
    timeline=prose_text.split('3.4. FEWK 주요 사건 연표')[1].split('제4부:')[0]
    later_horizon=re.search(r'검은 수평선 사건 \(수평 (\d+)년\)',timeline)
    first_H,first_DD=map(int,first_horizon.groups());later_H=int(later_horizon[1])
    check('같은설명원고수평0과연표수평1의같은사건1년차',(first_H,first_DD,later_H,later_H-first_H),(0,4227,1,1))
    puzzle_H,puzzle_DD=map(int,re.search(r'위대한 퍼즐 \(수평 (\d+)년 / 디디 (\d+)년\)',prose_text).groups())
    check('수평0DD4227기준과퍼즐수평100DD4326의기준차',(first_DD-first_H,puzzle_DD-puzzle_H,(first_DD-first_H)-(puzzle_DD-puzzle_H)),(4227,4226,1))
    foundational_world_bible_prose_arithmetic={'checks_passed':len(checks)-prose_before,'predicted_part_budgets':predicted_budgets,'predicted_total_chars':sum(predicted_budgets),'source_actual_chars':len(prose_text),'source_horizon_labels':[first_H,later_H],'source_DD_offsets':[first_DD-first_H,puzzle_DD-puzzle_H],'estimated_lengths_are_actual_written_lengths':False,'one_world_calendar_base_fixed':False,'all_source_stories_or_maps_delivered':False,'fifth_engine_changed':False,'actual_participant_playtest':False}

    chronicle_review=json.loads((here/'이전설계_통합검토.json').read_text())['foundational_world_bible_chronicle_review']
    chronicle_source=chronicle_review['source'];chronicle_path=root/chronicle_source['path_relative_to_plan'];files.append(chronicle_path);chronicle_raw=chronicle_path.read_bytes();chronicle_text=chronicle_raw.decode()
    chronicle_part=''.join(chronicle_text.splitlines(keepends=True)[846:1066]);assert chronicle_part==chronicle_review['reviewed_part']['text']
    chronicle_cells=[x.strip() for x in chronicle_part.split('연호 변환표 (주요 사건 기준):')[1].split('[3.4.2. 상세 연표]')[0].splitlines() if x.strip()]
    assert chronicle_cells[:5]==['사건','디디(DD)','수평(Horizon Year)','광제력(光帝曆)','대사력(大使曆)'] and len(chronicle_cells)==40
    chronicle_rows=[dict(zip(['event','DD','H','G','E'],chronicle_cells[i:i+5])) for i in range(5,len(chronicle_cells),5)]
    assert chronicle_rows==chronicle_review['conversion_table_rows']
    def chronicle_number(value):return int(re.search(r'(\d+)년',value)[1])
    chronicle_at={x['event']:x for x in chronicle_rows};chronicle_before=len(checks)
    horizon0=tuple(map(int,re.search(r'검은 수평선 사건 \(수평력 (\d+)년 / 디디 (\d+)년\)',chronicle_part).groups()))
    horizon1=chronicle_number(chronicle_at['검은 수평선']['H'])
    check('확장제3부동일사건수평0와변환표1',(horizon0,horizon1,horizon1-horizon0[0]),((0,4227),1,1))
    dd_offsets=[chronicle_number(x['DD'])-chronicle_number(x['H']) for x in chronicle_rows]
    check('확장제3부7행디디수평환산4225부터4227',dd_offsets,[4227,4226,4226,4226,4225,4226,4226])
    g_offsets=[chronicle_number(x['H'])-chronicle_number(x['G']) for x in chronicle_rows if not x['G'].startswith('(')]
    check('확장제3부6행수평광제환산2부터4',g_offsets,[2,3,3,4,3,3])
    detail=chronicle_part.split('[3.4.2. 상세 연표]')[1]
    war_g=int(re.search(r'수평 40년 \(광제력 (\d+)년\)',detail)[1]);exile_g=int(re.search(r'수평 43년 \(광제력 (\d+)년\)',detail)[1])
    war_table=chronicle_number(chronicle_at['동쟁 발발']['G']);exile_table=chronicle_number(chronicle_at['광제 망명']['G'])
    check('확장제3부전쟁망명표와상세광제력각1년차',(war_table,war_g,exile_table,exile_g,war_g-war_table,exile_g-exile_table),(37,38,40,41,1,1))
    current_e=chronicle_number(chronicle_at['현재 시점']['E']);csv_current_e=int(at(2003,'대사력'))
    check('확장제3부현재대사96과CSV97의차',(current_e,csv_current_e,csv_current_e-current_e),(96,97,1))
    original92={x['topic']:x['text'] for x in chronicle_review['primary_topic_recheck']['topics']}['0092']
    assert '1965년 4월 26일' in original92 and '정확히 54년 전' in original92
    check('원본0092동일AD계산2019와동백CSV1860구분',(1965+54,int(at(1860,'수평')),(1965+54)-1860),(2019,1,159))
    foundational_world_bible_chronicle_arithmetic={'checks_passed':len(checks)-chronicle_before,'conversion_table_rows':7,'DD_H_offsets':dd_offsets,'H_G_offsets':g_offsets,'table_war_exile_G':[war_table,exile_table],'detail_war_exile_G':[war_g,exile_g],'source_current_E':current_e,'CSV_current_E':csv_current_e,'one_world_calendar_base_fixed':False,'real_history_fact_checked':False,'fifth_engine_changed':False,'actual_participant_playtest':False}

    return {'date':'2026-10-06','framework_archive_arithmetic':framework_archive_arithmetic,'second_edition_reader_arithmetic':second_edition_reader_arithmetic,'current_framework_spec_arithmetic':current_framework_spec_arithmetic,'first_character_source_arithmetic':first_character_source_arithmetic,'world_physics_byte_arithmetic':world_physics_byte_arithmetic,'world_physics_dimension_ego_arithmetic':world_physics_dimension_ego_arithmetic,'world_physics_sinki_arithmetic':world_physics_sinki_arithmetic,'world_physics_power_arithmetic':world_physics_power_arithmetic,'world_physics_causal_time_arithmetic':world_physics_causal_time_arithmetic,'world_physics_index_counts':world_physics_index_counts,'cyberpunk_pack_foundation_arithmetic':cyberpunk_pack_foundation_arithmetic,'cyberpunk_pack_catalog_arithmetic':cyberpunk_pack_catalog_arithmetic,'cyberpunk_pack_character_track_arithmetic':cyberpunk_pack_character_track_arithmetic,'cyberpunk_pack_dsr_dropout_arithmetic':cyberpunk_pack_dsr_dropout_arithmetic,'cyberpunk_pack_weapon_arithmetic':cyberpunk_pack_weapon_arithmetic,'cyberpunk_pack_NPC_arithmetic':cyberpunk_pack_NPC_arithmetic,'cyberpunk_pack_large_arithmetic':cyberpunk_pack_large_arithmetic,'cyberpunk_pack_glossary_arithmetic':cyberpunk_pack_glossary_arithmetic,'cyberpunk_pack_deck_audit_arithmetic':cyberpunk_pack_deck_audit_arithmetic,'cyberpunk_pack_world_correction_arithmetic':cyberpunk_pack_world_correction_arithmetic,'framework_foundation_arithmetic':framework_foundation_arithmetic,'framework_character_combat_arithmetic':framework_character_combat_arithmetic,'framework_resource_growth_arithmetic':framework_resource_growth_arithmetic,'framework_team_NPC_session_arithmetic':framework_team_NPC_session_arithmetic,'framework_final_reader_arithmetic':framework_final_reader_arithmetic,'first_relationship_chronology_arithmetic':first_relationship_chronology_arithmetic,'first_catalog_arithmetic':first_catalog_arithmetic,'first_life_uncertainty_arithmetic':first_life_uncertainty_arithmetic,'first_encyclopedia_scene_glossary_arithmetic':first_encyclopedia_scene_glossary_arithmetic,'first_address_nuance_motif_arithmetic':first_address_nuance_motif_arithmetic,'first_letters_narrator_translation_readme_arithmetic':first_letters_narrator_translation_readme_arithmetic,'foundational_chronology_csv_arithmetic':foundational_chronology_csv_arithmetic,'foundational_world_bible_outline_arithmetic':foundational_world_bible_outline_arithmetic,'foundational_world_bible_prose_arithmetic':foundational_world_bible_prose_arithmetic,'foundational_world_bible_chronicle_arithmetic':foundational_world_bible_chronicle_arithmetic,'scope':'구판 TN 합계≥TN·예시 산술/실제 스킬/생성 비용·성장 잔여·모두1 확률·체류 시간/명목 시나리오 분량을 제한 대조. 스킬/태그/운 토큰·모든1 자동펌블의 저TN예외·3회체인Critical자동승격·효과/피해 전체 구판 승률/호환 검증 아님. 신판 엔진으로 채택하지 않는다.','checks_passed':len(checks),'checks':checks,'old_TN_rows':rows,'source_example_recheck':source_example_recheck,'fifth_engine_changed':False,'old_complete_engine_reproduced':False,'actual_participant_playtest':False,'source_sha256':{os.path.relpath(f.resolve(),root.resolve()):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
if __name__=='__main__':
    r=run();Path(__file__).with_name('구판_판정산술_검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'checks_passed':r['checks_passed'],'TN_rows':len(r['old_TN_rows']),'fifth_engine_changed':False},ensure_ascii=False))
