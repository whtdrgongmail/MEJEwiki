from pathlib import Path
from collections import Counter
from urllib.parse import unquote,urlsplit
from copy import deepcopy
import hashlib,json,re
from 백분율_코어검증 import grade,target,contest
from 일반플레이_검증 import Body,attack,move
from 팀지원_검증 import Learner
here=Path(__file__).resolve().parent;o=here.parent;p=o.parent
profile=json.loads((here/'부록_참조규격.json').read_text());ledger=json.loads((here/'제5판_이관검수.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def run():
    checks=[]
    def check(n,a,b):assert a==b,(n,a,b);checks.append(n)
    check('same common engine',profile['engine'],'P-FEWK-0.2')
    check('no universal new resources',profile['new_universal_stats'],[])
    refs=profile['references'];check('unique33lookup IDs',(len(refs),len({e['id'] for e in refs})),(33,33))
    texts={n:(o/n).read_text() for n in {e['file'] for e in refs}|{'10_CoreRulebook.md','11_WorldLorebook.md','12_룰시트와캐릭터시트.md','13_입문시나리오.md'}}
    for e in refs:
        t=texts[e['file']];anchor='<a id="'+e['id']+'"></a>'
        heading_pattern=re.escape(anchor)+r'\n\n(?:<a id="[^"]+"></a>\n\n)*'+re.escape(e['heading'])+r'(?=\n|$)'
        check('actual heading behind anchor '+e['id'],len(re.findall(heading_pattern,t)),1)
    checked_links=0
    pending=list(texts)
    while pending:
        name=pending.pop(0);text=texts[name]
        ids=re.findall(r'<a id="([^"]+)"></a>',text)
        check('anchor uniqueness in '+name,len(ids),len(set(ids)))
        for link in re.findall(r'\[[^\]\n]*\]\(([^)]+)\)',text):
            parsed=urlsplit(link.strip('<>'))
            if parsed.scheme or not parsed.fragment.startswith('fewk-'):continue
            dest=unquote(parsed.path) or name
            if dest not in texts:
                texts[dest]=(o/dest).read_text();pending.append(dest)
            assert texts[dest].count('<a id="'+unquote(parsed.fragment)+'"></a>')==1,(name,link)
            checked_links+=1
    # 요약의 숫자를 공통 엔진의 실제 굴림과 작성 프로필로 대조한다.
    q=profile['quick_reference'];intro=json.loads((here/'입문_프로필.json').read_text())
    check('12starting skills actual allocation',sorted(q['skill_allocation']),sorted(intro['character']['allocation']))
    check('starting total440',sum(q['skill_allocation']),q['start_skill_total'])
    check('d100 range inclusive',(q['die_range'],q['printed00_value']),([1,100],100))
    t=q['sample_target'];outcomes=Counter(grade(t,n) for n in range(1,101))
    check('T70 actual success bins',outcomes,Counter({3:14,2:21,1:35,0:30}))
    check('T70 cutoff floors',(q['sample_extreme_max'],q['sample_hard_max']),(t//5,t//2))
    check('possible target clamp',(target(10,-20),target(95,20)),(1,99))
    check('situation20points',(target(50,20),target(50,-20)),(70,30))
    check('same perfect tie held',contest(50,20,50,20),0)
    check('both failed no winner',contest(50,100,70,100),0)
    learner=Learner(skills={'해킹':90});learner.grow('UNIT-01','해킹','actual learning')
    check('story growth max95',learner.skills['해킹'],q['skill_max_growth'])
    before=deepcopy(learner)
    try:learner.grow('UNIT-01','해킹','same story unit')
    except ValueError:pass
    else:raise AssertionError('duplicate growth')
    check('same person no duplicate growth',learner,before)
    body=Body();check('quick body matches actual budget',(body.hp,body.main,body.reaction,body.move),(q['body_HP_example'],q['main'],q['reaction'],q['base_move_m']))
    move(body,20,True);check('extra move spends main',(body.main,body.move),(0,0))
    victim=Body();first=attack(Body(),victim,'권총',roll=20,distance=20);second=attack(Body(),victim,'권총',roll=20,distance=20)
    check('same round two actual hits',(first,second,victim.hp,victim.charges),(('shield',0),('damage',3),9,1))
    check('powered contact damage after armor',attack(Body(),Body(),'동력 근접 도구',roll=20,distance=1),('damage',q['powered_melee_damage']-q['armor_example']))
    check('weapon values actual',(intro['weapons']['권총']['damage'],intro['weapons']['동력 근접 도구']['damage'],intro['weapons']['동력 근접 도구']['max_range_m']),(q['handgun_damage'],q['powered_melee_damage'],q['melee_range_m']))
    # 원본 일러스트 제안의 실제 표행 산술. 납품/권리/확정 수량 검증 아님.
    legacy=(p/ledger['files'][125]['source']).read_text();a=legacy.index('### Core Rulebook');b=legacy.index('### World Book');c=legacy.index('**총합 권장**')
    values=[[int(m[1]) for m in re.finditer(r'^\|.+?\|\s*(\d+)\s*\|$',s,re.M)] for s in [legacy[a:b],legacy[b:c]]]
    check('old illustration actual row totals',[sum(x) for x in values],[75,89])
    check('old illustration total mismatch',(sum(map(sum,values)),ledger['appendix_reference_conflicts']['illustration_rows']['old_summary_total']),(164,175))
    handouts=re.findall(r'\*\*(HO-S[123]-[A-Z]+) —',texts['10_CoreRulebook.md'])
    check('all five actual named handouts',handouts,profile['handouts'])
    check('handouts do not claim participant reading',profile['actual_participant_reading'],False)
    check('external conversion not validated',profile['external_system_conversions_verified'],False)
    check('no final page numbers',profile['page_numbers_final'],False)
    check('all World glossary not completed',profile['all_World_people_and_terms_verified'],False)
    topic_rules=profile['reader_topic_routes'];world=texts['11_WorldLorebook.md']
    start=world.index(topic_rules['scope_heading']);end=world.index(topic_rules['scope_end_heading'],start)
    topic_guide=world[start:end];topic_routes=topic_rules['routes']
    assert len(topic_routes)==3 and not topic_rules['all_appendix_link_meanings_verified'] and not topic_rules['actual_participant_reading']
    def topic_target_matches(entry,anchor_id):
        anchor='<a id="'+anchor_id+'"></a>'
        if world.count(anchor)!=1:return False
        fragment=world[world.index(anchor)+len(anchor):]
        heading=re.search(r'^#{2,3} [^\n]+',fragment,re.M)
        if heading is None or heading[0]!=entry['heading']:return False
        next_pattern=r'^## ' if heading[0].startswith('## ') else r'^#{2,3} '
        next_heading=re.search(next_pattern,fragment[heading.end():],re.M)
        stop=heading.end()+next_heading.start() if next_heading else len(fragment)
        return entry['required_text'] in fragment[heading.start():stop]
    for entry in topic_routes:
        check('topic route in scoped reader guide '+entry['label'],'['+entry['label']+'](#'+entry['id']+')' in topic_guide,True)
        check('topic target actual chapter and content '+entry['label'],topic_target_matches(entry,entry['id']),True)
        old=entry['previous_wrong_id']
        check('existing wrong-topic anchor rejected '+entry['label'],('<a id="'+old+'"></a>' in world,topic_target_matches(entry,old)),(True,False))
    hashes={ledger['files'][i]['source']:sha(p/ledger['files'][i]['source']) for i in profile['source_indices']}
    for i in profile['source_indices']:assert hashes[ledger['files'][i]['source']]==ledger['files'][i]['observed_sha256']
    names=['10_CoreRulebook.md','11_WorldLorebook.md','12_룰시트와캐릭터시트.md','13_입문시나리오.md','01_텀블벅_이지룰_초안.md']
    names+=['검증/'+n for n in ['부록_참조규격.json','백분율_코어검증.py','일반플레이_검증.py','입문_프로필.json','팀지원_검증.py','팀지원_프로필.json','임플란트_검증.py','임플란트_프로필.json']]
    artifacts={n:sha(o/n) for n in names};artifacts[str(Path(__file__).relative_to(o))]=sha(Path(__file__))
    return {'date':'2026-10-05','profile':profile['id'],'scope':'현재33고유참조/실제제목·fragment링크·3독자주제/도착본문과존재하는구오류거부·같은엔진의요약목표/성공/대립·숙련/성장·행동/방호/피해와구판그림표산술/5텍스트존재 대조. 실제 독자찾기/이해·시각적조판/그림납품·자료의매력/전체시나리오·전권용어/외부호환/라이선스 검증 아님.','checks_passed':len(checks),'checks':checks,'reference_entries':len(refs),'fragment_links_checked':checked_links,'quick_sample_percentile_outcomes':100,'legacy_illustration_row_totals':[75,89],'legacy_illustration_row_total':164,'legacy_illustration_summary_total':175,'handouts':5,'semantic_topic_routes_checked':len(topic_routes),'existing_wrong_topic_routes_rejected':len(topic_routes),'all_appendix_link_meanings_verified':False,'source_sha256':hashes,'artifacts_sha256':artifacts,'actual_participant_reading':False,'actual_participant_playtest':False,'full_encounter_balance_verified':False,'external_system_conversions_verified':False,'all_World_people_and_terms_verified':False,'page_numbers_final':False}
if __name__=='__main__':
 r=run();Path(__file__).with_name('부록_참조검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('profile','checks_passed','reference_entries','fragment_links_checked','handouts','actual_participant_reading')},ensure_ascii=False))
