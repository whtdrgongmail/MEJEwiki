# 현재 제5판 원고·출처·검증결과의 구조/해시 대조. 실제 참가자 검증을 대신하지 않습니다.
from pathlib import Path
import re,json,unicodedata,hashlib,subprocess,sys
from urllib.parse import unquote,urlsplit
v=Path(__file__).resolve().parent;o=v.parent;p=o.parent
local_package_only="--local-package" in sys.argv
source_hash_audit_pending_ids=[]
hash_cache={}
source_paths_revalidation_pending=set()
frozen_original_source_paths=set()
def hash_current(path):
 path=Path(path);before=path.stat();signature=(before.st_size,before.st_mtime_ns)
 key=str(path.absolute())
 if key in hash_cache and hash_cache[key][0]==signature:return hash_cache[key][1]
 digest=hashlib.sha256(path.read_bytes()).hexdigest();after=path.stat()
 assert signature==(after.st_size,after.st_mtime_ns),'file changed while read: '+key
 hash_cache[key]=(signature,digest)
 return digest

def verify_recorded_source_hash(path,expected):
 path=Path(path)
 # 로컬 모드는 현재 원고 묶음만 확인한다. 보존 본문과 원본 현재 파일도 구분한다.
 outside_package=not path.is_relative_to(o) and path not in [p/'00_최신본_기준.md',p/'01_작업계획.md']
 if str(path.absolute()) in hash_cache:
  assert hash_current(path)==expected
  return
 if local_package_only and outside_package:
  source_paths_revalidation_pending.add(str(path.relative_to(p)))
  return
 assert hash_current(path)==expected

docs=[p/'00_최신본_기준.md',p/'01_작업계획.md']+[o/x for x in ['00_제5판_설계기준.md','01_텀블벅_이지룰_초안.md','02_타롯_해킹과_지능전_초안.md','10_CoreRulebook.md','11_WorldLorebook.md','12_룰시트와캐릭터시트.md','13_입문시나리오.md','14_레디메이드_러너.md','15_표준튜터리얼_시나리오.md']]
def resolve_local(q):
 if q.exists():return q
 cur=Path(q.absolute().anchor)
 for part in q.absolute().parts[1:]:
  if part=='.':continue
  if part=='..':cur=cur.parent;continue
  if (cur/part).exists():cur=cur/part;continue
  if not cur.is_dir():return None
  matches=[x for x in cur.iterdir() if unicodedata.normalize('NFC',x.name)==unicodedata.normalize('NFC',part)]
  if len(matches)!=1:return None
  cur=matches[0]
 return cur if cur.exists() else None
def exists(q):return resolve_local(q) is not None
links=[];missing=[];fences=[];named_anchor_links=[];missing_named_anchors=[]
for q in docs:
 t=q.read_text();fences.append({'path':str(q.relative_to(p)),'balanced':sum(l.lstrip().startswith('```') for l in t.splitlines())%2==0})
 for x in re.findall(r'\[[^\]\n]*\]\(([^)]+)\)',t):
  x=x.strip('<>');s=urlsplit(x)
  if not s.scheme and s.fragment.startswith('fewk-'):
   target=resolve_local(q.parent/unquote(s.path)) if s.path else q
   named_anchor_links.append((str(q.relative_to(p)),x))
   if target is None or s.fragment not in re.findall(r'<a id="([^"]+)"',target.read_text()):missing_named_anchors.append(named_anchor_links[-1])
  if s.scheme or not s.path:continue
  links.append((str(q.relative_to(p)),x))
  if not exists(q.parent/unquote(s.path)):missing.append(links[-1])
 assert not any(x in t for x in ['固有の','replaceThis','拡張','同一人物','同目標','関連','原文','FEWKらしい']),q
assert not missing and not missing_named_anchors and all(x['balanced'] for x in fences),(missing,missing_named_anchors,fences)
for q in docs:
 assert not re.search(r'[\u3040-\u30ff]|Korean',q.read_text()),q

for name in ['백분율_v0.1_기록.json','이지룰_A_v0.10_기록.json','타롯_v0.1_기록.json','이지룰_P_v0.18_기록.json','타롯_v0.2_기록.json']:
 d=json.loads((v/'이전'/name).read_text());entries=[d] if 'text' in d else d['files']
 for entry in entries:assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
results={}
for n in ['백분율_코어검증.py','일반플레이_검증.py','스페셜_검증.py','타롯_검증.py','차원프로필_검증.py','바이트_검증.py','고유효과_검증.py','장비_검증.py','임플란트_검증.py','운송_검증.py','장면운영_검증.py','팀지원_검증.py','진행자_검증.py','NPC_검증.py','온라인_검증.py','시나리오_확장검증.py','부록_참조검증.py','몸노출_계산검증.py','시간이동_검증.py','대형시설_검증.py']:
 # Rules, profiles and verifier inputs are unchanged: validate prior results against actual hashes.
 result=json.loads((v/n.replace('.py','결과.json')).read_text());results[n]=result
 if 'artifacts_sha256' in result:
  for path,sha in result['artifacts_sha256'].items():assert hash_current((o/path))==sha
 else:assert hash_current((o/'10_CoreRulebook.md'))==result['core_sha256']
ledger=json.loads((v/'제5판_이관검수.json').read_text());assert (ledger['focused_reviews'],ledger['pending'])==(358,0)
frozen_original_source_paths={str((p/e['source']).absolute()) for e in ledger['files'] if e.get('hash_validation_mode')=='fixed_3.1_reference_snapshot'}
frozen_snapshots={e['source_id']:e for e in json.loads((o/'3.1판_참고원고_기준선.json').read_text())['pending_reference_content_preservation']['snapshots']}
historical_reference_only_ids=[]
current_reference_audit=json.loads((v/'현재_참고원고_해시검증.json').read_text())
assert (current_reference_audit['total'],current_reference_audit['read'],current_reference_audit['unread'],current_reference_audit['changed_from_baseline'],current_reference_audit['changed_from_prior_observed'])==(358,358,0,0,0)
assert current_reference_audit['full_current_worktree_revalidation_complete']
assert current_reference_audit['head_unchanged'] and current_reference_audit['git_status_unchanged'] and current_reference_audit['unstable_files']==[]
assert not current_reference_audit['content_semantic_review_inferred'] and not current_reference_audit['actual_participant_evidence']
current_rows={row['id']:row for row in current_reference_audit['files']}
assert len(current_rows)==358 and set(current_rows)=={e['id'] for e in ledger['files']}
assert sum(row['book']=='Core' for row in current_rows.values())==129 and sum(row['book']=='World' for row in current_rows.values())==229
reference_repo=p/'_ClaudeCode_Git_FEWK/FEWKbooks'
assert subprocess.check_output(['git','--no-optional-locks','-C',str(reference_repo),'rev-parse','HEAD']).decode().strip()==current_reference_audit['head_after']
assert subprocess.check_output(['git','--no-optional-locks','-C',str(reference_repo),'status','--porcelain=v1','-z']).decode()==current_reference_audit['git_status_after']
for e in ledger['files']:
 row=current_rows[e['id']]
 assert row['source']==e['source'] and row['book']==e['book']
 assert row['read_completed'] and row['stable_stat'] and row['baseline_matches'] and row['prior_observed_matches']
 assert row['stat_before']==row['stat_after'] and row['bytes']==row['stat_after']['size']
 assert row['sha256']==e['baseline_sha256']==e['observed_sha256']==e['latest_current_worktree_sha256']
 assert e['latest_current_worktree_hash_audit_id']==current_reference_audit['id'] and e['latest_current_worktree_hash_matches_baseline']
 assert hash_current(p/e['source'])==row['sha256']
for e in ledger['files']:
 if e['semantic_review']!='focused_review':continue
 if e.get('hash_validation_mode')=='fixed_3.1_reference_snapshot':
  snapshot=frozen_snapshots[e['id']];data=snapshot['text'].encode()
  assert hashlib.sha256(data).hexdigest()==snapshot['sha256']==e['reference_content_sha256']==e['baseline_sha256']
  assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==snapshot['git_blob']
  assert e['current_worktree_hash_rechecked_this_review'] is False and e['review_evidence_path']=='[5판_FEWK]/3.1판_참고원고_기준선.json'
  historical_reference_only_ids.append(e['id'])
 else:
  verify_recorded_source_hash(p/e['source'],e['observed_sha256'])
assert len(historical_reference_only_ids)==65 and historical_reference_only_ids==ledger['current_hash_audit']['previous_current_worktree_revalidation_pending_ids']
assert ledger['current_hash_audit']['current_worktree_revalidation_pending_ids']==[]
assert ledger['current_hash_audit']['latest_current_worktree_revalidation']['full_current_worktree_revalidation_complete']
assert ledger['current_hash_audit']['capture_summary_is_full_current_turn_revalidation'] is False

for entry in ledger['special_topic_sources']+ledger['story_topic_sources']+ledger['geography_topic_sources']+ledger['byte_topic_sources']+ledger['coffin_material_topic_sources']+ledger['manifest_causality_topic_sources']+ledger['sinki_effect_topic_sources']+ledger['gear_power_topic_sources']+ledger['implant_life_topic_sources']+ledger['polity_company_life_topic_sources']+ledger['history_time_story_topic_sources']+ledger['city_style_transit_topic_sources']+ledger['region_sea_topic_sources']+ledger['dimension_geography_topic_sources']+ledger['transport_topic_sources']+ledger['foundations_state_topic_sources']+ledger['resolution_team_growth_topic_sources']+ledger['GM_operations_topic_sources']+ledger['NPC_life_topic_sources']+ledger['online_operations_topic_sources']+ledger['scenario_tools_topic_sources']+ledger['local_effect_computation_topic_sources']+ledger['time_travel_topic_sources']+ledger['profession_manifest_topic_sources']+ledger['religion_economy_infrastructure_topic_sources']+ledger['runner_identity_topic_sources']+ledger['hub_mission_organization_topic_sources']+ledger['runner_life_transition_topic_sources']+ledger['realm_catalog_localization_topic_sources']+ledger['frontier_records_topic_sources']+ledger['daily_reader_topic_sources']+ledger['daily_frontier_baseline_topic_sources']+ledger['introduction_tone_dimension_topic_sources']+ledger['being_catalog_topic_sources']+ledger['factions_operations_topic_sources']+ledger['world_appendix_topic_sources']:
 if 'sha256' in entry:verify_recorded_source_hash((p/entry['path']),entry['sha256'])
for i in [2,3,5,8,18,19,21,22,25,36,62,64,67,68,71,73,74,75,0,1,4,7,10,12,14,37,38,40,41,42,43,44,33,59,286,219,222,223,224,225,227]+list(range(208,219))+list(range(199,208))+[226]+list(range(178,198))+[228,229,230,231,232,233,234,243,265,339,340,341,15,57,241,252,253,254,255,264,169,170,171,172,173,175,285,13,46,142,143,144,145,321,47,95,102,103,138,139,140,147,148,149,154,155,156,157,159,160,161,165,174,198,220,221,287]:
 e=ledger['files'][i];verify_recorded_source_hash((p/e['source']),e['observed_sha256'])
assert [results[x]['checks_passed'] for x in ['일반플레이_검증.py','스페셜_검증.py','타롯_검증.py']]==[55,78,62]
core=(o/'10_CoreRulebook.md').read_text();easy=(o/'01_텀블벅_이지룰_초안.md').read_text();tarot=(o/'02_타롯_해킹과_지능전_초안.md').read_text();story=(o/'13_입문시나리오.md').read_text()
for s in ['### B.1','### B.2','### B.3','### B.4','TAR-P-02','13_입문시나리오.md']:assert s in core
assert 'P판 입문 초안 v0.31' in easy and '[Core v0.49]' in easy
for s in ['+20퍼센트포인트','1~99','1~19','80~99','일괄 제출','주요 행동 하나씩','실제 참가자']:assert s in tarot,s
for s in ['STORY-CARD-01','원전 사건의 확정된 후속','관련 소설001','위치','COPY-CONTRACT','실제 플레이로 기입하지']:assert s in story,s
intro=json.loads((v/'입문시나리오_검토.json').read_text())
for path,sha in intro['artifacts_sha256'].items():assert hash_current((o/path))==sha
q=v/'자료_구조검증.json';d=json.loads(q.read_text());d['updated_date']='2026-10-08'
d['scope']='현재 기준/독자 원고11개 로컬 링크·펜스·해시와 P 일반55·스페셜78·타롯62·차원프로필121 검사/수학 대조. 출처358개 집중검토와 실제 참가자/전권 검수는 구분'
d['local_links_checked']=len(links);d['missing_links']=missing;d['core_shortlist']['verification']['markdown_fences']=fences
d['fifth_goal_start'].update(focused_source_reviews=358,unreviewed_sources=0,core_version='v0.49',easy_version='P v0.31',world_version='v1.00',sheet_version='v0.44',special_categories_written=4,tarot_version='TAR-P-02 v0.3',intro_version='STORY-CARD-01 v0.5')
d['current_tarot_profile']={'id':'TAR-P-02','common_engine':'P-FEWK-0.2','checks_passed':62,'whole_duel_fixed_policy_simulations':300000,'same_skill_target_and_action_budget':True,'new_persistent_person_resources':[],'actual_participant_playtest':False,'optimal_or_adaptive_sequential_strategy_proven':False,'original_PF_rules_compared':False}
d['current_easy_rules']['version']='P v0.31'
d['current_effect_contract']={'written':True,'unified_term':'인터랙션','matting_shining':'creation origin only','rhythm_filler':'NPC profession or allowed PC specialized observation','mandatory_three_slots':False,'scope':'one common interaction format plus three declared examples and metadata/content/source-copy boundaries','all_ability_and_exposure_specs_complete':False,'new_universal_stat_tracks':[],'world_topics':'causality/manifest plus Min family and Hankan record','actual_participant_playtest':False}
d['current_interaction_profiles']={'id':'FEWK-INTERACTIONS-01','checks_passed':results['고유효과_검증.py']['checks_passed'],'body_compatibility_checks_passed':26,'body_compatibility_condition_cases':672,'charge_boundary_cases':72,'output_boundary_cases':42,'actual_participant_playtest':False,'all_ability_and_exposure_specs_complete':False}
d['current_gear_profiles']={'id':'FEWK-GEAR-01','checks_passed':results['장비_검증.py']['checks_passed'],'device_boundary_cases':56,'pull_condition_cases':96,'actual_participant_playtest':False,'all_guns_and_implants_complete':False,'Cell_Byte_processor_resources_are_distinct':True}
d['current_implant_profiles']={'id':'FEWK-IMPLANT-01','checks_passed':results['임플란트_검증.py']['checks_passed'],'body_network_cases':128,'split_time_cases':20,'all_implants_and_medicine_complete':False,'actual_participant_playtest':False}
d['current_byte_profile']={'id':'EXP-BYTE-01','checks_passed':results['바이트_검증.py']['checks_passed'],'exact_standard_unit_cases':14000,'finite_declared_inventory_operations':36,'new_persistent_person_resources':[],'actual_participant_playtest':False}
dimension=results['차원프로필_검증.py']
assert (dimension['checks_passed'],dimension['exhaustive_lease_states'],dimension['coffin_entry_condition_cases'],dimension['coffin_return_state_cases'],dimension['coffin_receiver_state_cases'],dimension['coffin_operator_condition_cases'],dimension['compatible_destination_condition_cases'],dimension['two_realm_preservation_sequences'])==(121,78,32,208,5408,256,2880,169)
d['current_dimension_profiles']={'ids':['CAMP-SAE-TEST','CAMP-ORC-TEST','CAMP-COF-TEST'],'checks_passed':dimension['checks_passed'],'finite_lease_states':78,'coffin_entry_cases':32,'coffin_return_cases':208,'coffin_receiver_cases':5408,'coffin_operator_cases':256,'compatible_destination_cases':2880,'two_realm_sequences':169,'actual_receiver_and_operator_state_required':True,'actual_participant_playtest':False,'all_world_profiles_verified':False}
d['current_intro_scenario']={'id':'STORY-CARD-01','written':True,'version':'0.5','world_events_status':'new_adaptation_not_canon_sequel','related_novel001_whole_document_read':True,'related_novel001_full_setting_verified':False,'actual_participant_playtest':False}
files=docs+[o/'3.1판_참고원고_기준선.json',o/'이전자료_조달목록.json']+[v/n for n in ['백분율_코어검증.py','백분율_코어검증결과.json','일반플레이_검증.py','일반플레이_검증결과.json','입문_프로필.json','스페셜_검증.py','스페셜_검증결과.json','스페셜_프로필.json','타롯_검증.py','타롯_검증결과.json','타롯_프로필.json','입문시나리오_검토.json','제5판_이관검수.json','완료_관문.json','차원프로필.json','차원프로필_검증.py','차원프로필_검증결과.json','현재_원고상태.json','바이트_프로필.json','바이트_검증.py','바이트_검증결과.json','고유효과_프로필.json','고유효과_검증.py','고유효과_검증결과.json','장비_프로필.json','장비_검증.py','장비_검증결과.json','임플란트_프로필.json','임플란트_검증.py','임플란트_검증결과.json','운송_프로필.json','운송_검증.py','운송_검증결과.json','장면운영_프로필.json','장면운영_검증.py','장면운영_검증결과.json','팀지원_프로필.json','팀지원_검증.py','팀지원_검증결과.json','구판_판정산술_검증.py','구판_판정산술_검증결과.json','진행자_장면프로필.json','진행자_검증.py','진행자_검증결과.json','NPC_프로필.json','NPC_검증.py','NPC_검증결과.json','온라인_프로필.json','온라인_기록예시.json','온라인_검증.py','온라인_검증결과.json','시나리오_확장프로필.json','시나리오_확장검증.py','시나리오_확장검증결과.json','부록_참조규격.json','부록_참조검증.py','부록_참조검증결과.json','몸노출_계산프로필.json','몸노출_계산검증.py','몸노출_계산검증결과.json','시간이동_프로필.json','시간이동_검증.py','시간이동_검증결과.json','직업과현화_검토.json','종교경제와기반시설_검토.json','러너와템플릿_검토.json','거점임무와조직_검토.json','러너생애와전환_검토.json','계도감과현지화_검토.json','오지와기록_검토.json','일상과이지룰_검토.json','일상과오지_기준선검토.json','서문과차원개요_검토.json','존재도감_검토.json','세력과작전_검토.json','월드부록_검토.json','이전설계_통합검토.json','이전/이지룰_P_v0.18_기록.json','원고묶음_구조검증.py','현재_참고원고_해시검증.json','타롯_전략검증.py','타롯_전략검증결과.json','이전/타롯_v0.2_기록.json','대형시설_프로필.json','대형시설_검증.py','대형시설_검증결과.json']]
files += [v/n for n in ['캐릭터와시나리오북_편집.json','이전/시나리오북편성전_20261008.json','레디메이드_러너프로필.json','표준튜터리얼_프로필.json','러너와튜터리얼_검증.py','러너와튜터리얼_검증결과.json','러너와튜터리얼_대조.json','이전/러너확장전_20261008.json']]
d['updated_document_hashes']={str(f.relative_to(p)):hash_current(f) for f in files}
d['current_polity_life_review']={'world_version':'v0.11','focused_sources':12,'source_company_names':23,'source_funeral_vignettes':20,'local_embassies':10,'source_internal_conflicts_recorded':True,'all_politics_history_law_and_stories_complete':False,'actual_participant_playtest':False}
d['current_history_time_review']={'world_version':'v0.12','focused_sources':20,'source_proposals_and_conditional_analysis_separated':True,'history_date_conflicts_recorded':True,'ZADAM_count':3000000000,'ZADAM_is_refugee_count':False,'timewalk_maintains_physical_body':True,'all_history_people_and_related_novels_complete':False,'actual_participant_playtest':False}
d['current_city_style_transit_review']={'world_version':'v0.13','focused_sources':10,'related_novels_whole_document_read':['043','066'],'related_novels_full_setting_verified':False,'source_population_values':[20000,60000,50000,30000,5000],'source_population_sum':sum([20000,60000,50000,30000,5000]),'original_Luchem_city_link_disconnection_recorded':True,'novel_expansion_and_original_story_separated':True,'all_geography_people_and_related_novels_complete':False,'all_time_and_marking_profiles_complete':False,'actual_participant_playtest':False}
d['current_region_sea_review']={'world_version':'v0.14','focused_sources':11,'regions_written':8,'source_address_and_marine_life_conflicts_recorded':True,'source_jobs_and_gear_separated':True,'Catchment_headquarters_retained':True,'all_geography_people_and_related_novels_complete':False,'all_ship_time_and_marking_profiles_complete':False,'new_land_sea_rule_profiles_tested':False,'actual_participant_playtest':False}
d['current_dimension_geography_review']={'world_version':'v0.15','focused_sources':6,'cumulative_focused_sources':144,'source_internal_club_biography_and_old_Dropout_conflicts_recorded':True,'Gumi_native_life_and_runner_exit_distinguished':True,'wills_storage_category_and_self_awareness_distinguished':True,'creation_profession_and_unified_interaction_categories_preserved':True,'all_transport_time_marking_and_wills_profiles_complete':False,'all_people_and_related_novels_complete':False,'actual_participant_playtest':False}
road=results['운송_검증.py'];assert (road['checks_passed'],road['feasibility_cases'],road['movement_roll_cases'],road['repair_HP_cases'])==(93,2048,2000,40)
d['current_transport_profiles']={'id':'FEWK-ROAD-01','core_version':'v0.12','world_version':'v0.16','sheet_version':'v0.12','vehicles':['ROAD-BIKE-01','ROAD-VAN-01'],'checks_passed':road['checks_passed'],'feasibility_cases':road['feasibility_cases'],'movement_roll_cases':road['movement_roll_cases'],'repair_HP_cases':road['repair_HP_cases'],'same_percentile_action_and_body_budget':True,'movement_used_and_currently_stopped_are_distinct':True,'all_transport_ships_and_vehicle_IO_complete':False,'actual_participant_playtest':False}
scene=results['장면운영_검증.py'];assert (scene['checks_passed'],scene['start_condition_cases'],scene['split_work_cases'])==(40,16,20)
d['current_scene_operations']={'id':'FEWK-SCENE-01','core_version':'v0.13','sheet_version':'v0.13','checks_passed':40,'start_condition_cases':16,'split_work_cases':20,'new_universal_stats':[],'correction_requires_dependent_event_scope':True,'production_VTT_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False}
d['current_foundations_state_review']={'world_version':'v0.17','focused_sources':14,'cumulative_focused_sources':161,'source_Grade_preset_DSR_track_arithmetic_and_quote_conflicts_recorded':True,'source0060_quote_acknowledged_without_token_system_inheritance':True,'all_GM_online_appendix_skills_people_and_related_novels_complete':False,'actual_participant_playtest':False}
team=results['팀지원_검증.py'];assert (team['checks_passed'],team['sender_condition_cases'],team['support_target_cases'],team['growth_boundary_cases'])==(38,256,56,94)
legacy=json.loads((v/'구판_판정산술_검증결과.json').read_text());assert legacy['checks_passed']==525 and len(legacy['old_TN_rows'])==7
assert legacy['framework_archive_arithmetic']['checks_passed']==17
assert legacy['second_edition_reader_arithmetic']['checks_passed']==18
for path,expected in legacy['source_sha256'].items():verify_recorded_source_hash((p/path),expected)
assert hash_current((v/'구판_판정산술_검증.py'))==legacy['verifier_sha256']
for entry in ledger['files']:
 if entry['semantic_review']=='focused_review':verify_recorded_source_hash((p/entry['source']),entry['observed_sha256'])
d['current_team_support_growth']={'id':'FEWK-TEAM-01','core_version':'v0.14','sheet_version':'v0.14','checks_passed':38,'sender_condition_cases':256,'support_target_cases':56,'growth_boundary_cases':94,'late_delivery_preserves_previous_failure':True,'same_story_growth_credited_once_to_person':True,'mandatory_six_roles_or_contact_trust_score':False,'all_contacts_and_team_roles_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False}
d['current_resolution_team_growth_review']={'world_version':'v0.18','focused_sources':18,'cumulative_focused_sources':179,'raw_topics_whole_read':['0002','0005','0006','0007','0017','0027','0049'],'original_quotes_and_abridgement_acknowledged':True,'raw0005_choice_and_raw0027_inference_not_final_outcome':True,'legacy_arithmetic_checks':legacy['checks_passed'],'legacy_arithmetic_checks_at_original_review':11,'legacy_sum_threshold_rows':7,'legacy_critical_chain_promotion_and_whole_engine_simulated':False,'all_GM_online_appendix_skills_people_and_related_novels_complete':False,'actual_participant_playtest':False}
GM=results['진행자_검증.py'];assert (GM['checks_passed'],GM['followup_condition_cases'],GM['split_IC_time_cases'],GM['receipt_condition_cases'])==(42,160,20,4)
for path,expected in GM['source_sha256'].items():verify_recorded_source_hash((p/path),expected)
d['current_GM_operations']={'id':'FEWK-GM-01','core_version':'v0.15','world_version':'v0.18','sheet_version':'v0.15','focused_sources':14,'cumulative_focused_sources':193,'checks_passed':42,'followup_condition_cases':160,'split_IC_time_cases':20,'receipt_condition_cases':4,'operating_note_and_PC_evidence_distinguished':True,'actual_IC_time_and_body_action_required':True,'base_clue_paths_preserved_after_optional_failure':True,'source0099_quotation_abridgement_verified':True,'old_dates_names_and_ten_year_claim_not_actual_participant_evidence':True,'all_GM_online_and_information_topics_verified':False,'full_encounter_balance_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False}
NPC=results['NPC_검증.py'];assert (NPC['checks_passed'],NPC['sender_condition_cases'],NPC['access_prerequisite_cases'],NPC['single_percentile_rolls'])==(83,384,24,600)
for path,expected in NPC['source_sha256'].items():verify_recorded_source_hash(p/path,expected)
d['current_NPC_life_review']={'id':'FEWK-NPC-01','core_version':'v0.16','easy_version':'P v0.14','world_version':'v0.19','sheet_version':'v0.16','world_chapters':61,'sheet_sections':22,'focused_sources':6,'cumulative_focused_sources':199,'checks_passed':53,'templates':6,'single_percentile_rolls':600,'sender_condition_cases':384,'access_prerequisite_cases':24,'legacy_HP_sample_rows':21,'legacy_HP_outside_overview':10,'source_story_and_wiki_followup_separated':True,'source_raw_topics_whole_read':['0036','0046','0048','0053','0078','0079','0089'],'source_wiki_topics_whole_read':12,'fictional_and_real_artist_Chris_distinguished':True,'same_percentile_and_actual_body_budget':True,'new_universal_stats':[],'all_NPC_and_large_entity_profiles_complete':False,'all_people_and_related_novels_complete':False,'full_encounter_balance_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False}
online=results['온라인_검증.py'];assert (online['checks_passed'],online['parallel_registration_orders'],online['malformed_snapshot_cases'],online['digital_percentile_cases'])==(65,6,30,1800)
for path,expected in online['source_sha256'].items():verify_recorded_source_hash(p/path,expected)
d['current_online_operations']={'id':'FEWK-ONLINE-01','core_version':'v0.17','easy_version':'P v0.15','world_version':'v0.19','sheet_version':'v0.17','sheet_sections':23,'focused_sources':9,'cumulative_focused_sources':208,'checks_passed':65,'parallel_registration_orders':6,'malformed_snapshot_cases':30,'digital_percentile_cases':1800,'partial_work_seconds':120,'completion_seconds':300,'OOC_wait_seconds':604800,'original_body_and_local_body_resources_preserved':True,'contact_registration_is_not_IC_message':True,'source0018_quotation_abridgement_verified':True,'new_universal_stats':[],'production_VTT_or_bot_verified':False,'external_YAML_or_VTT_import_verified':False,'all_online_community_concurrency_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False}
scenario=results['시나리오_확장검증.py'];assert (scenario['checks_passed'],scenario['legacy_tables'],scenario['legacy_die_outcomes'],scenario['new_inspiration_die_outcomes'],scenario['split_IC_time_cases'])==(83,25,1540,200,20)
for path,expected in scenario['source_sha256'].items():verify_recorded_source_hash(p/path,expected)
d['current_scenario_tools']={'id':'FEWK-SCENARIOS-01','core_version':'v0.18','easy_version':'P v0.16','world_version':'v0.20','sheet_version':'v0.18','intro_version':'v0.3','world_chapters':61,'sheet_sections':24,'focused_sources':6,'cumulative_focused_sources':214,'checks_passed':scenario['checks_passed'],'hooks':6,'short_scenarios':3,'legacy_tables':25,'legacy_die_outcomes':1540,'nominal_minutes':[180,190,190],'legacy_NPC_raw_combinations':8000,'new_inspiration_tables':2,'new_inspiration_die_outcomes':200,'split_IC_time_cases':20,'original_main_story_prefix_verified':False,'historical_v04_main_story_prefix_verified':True,'current_main_story_editorially_updated':True,'current_intro_version':'v0.5','source_raw_topics_whole_read':['0008','0054'],'raw0101_title_only':True,'Maria_Founders_communication_preserved':True,'new_universal_stats':[],'full_encounter_balance_verified':False,'all_original_scenario_and_campaign_consequences_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
reference=results['부록_참조검증.py'];assert (reference['checks_passed'],reference['reference_entries'],reference['handouts'])==(74,33,5)
for path,expected in reference['source_sha256'].items():verify_recorded_source_hash(p/path,expected)
d['current_appendix_reference']={'id':'FEWK-REFERENCE-01','core_version':'v0.19','easy_version':'P v0.17','world_version':'v0.21','sheet_version':'v0.19','intro_version':'v0.4','world_chapters':61,'sheet_sections':24,'focused_sources':12,'cumulative_focused_sources':226,'checks_passed':63,'reference_entries':33,'fragment_links_checked':reference['fragment_links_checked'],'quick_sample_percentile_outcomes':100,'legacy_illustration_row_totals':[75,89],'legacy_illustration_row_total':164,'legacy_illustration_summary_total':175,'handouts':5,'same_common_engine_and_actual_body_preserved':True,'original_intro_story_preserved':True,'new_universal_stats':[],'all_World_people_and_terms_verified':False,'external_system_conversions_verified':False,'page_numbers_final':False,'all_illustrations_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False}
for n,expected in [('10_CoreRulebook.md','원고 v0.49 · 독자 편집 마감 2026-10-07'),('11_WorldLorebook.md','원고 v1.00 · 독자 편집 마감 2026-10-07'),('12_룰시트와캐릭터시트.md','백분율 작성 양식 v0.44'),('13_입문시나리오.md','초안 v0.5')]:assert expected in (o/n).read_text()
local=results['몸노출_계산검증.py'];assert (local['checks_passed'],local['exposure_armor_percentile_cases'],local['clinic_start_condition_cases'],local['correction_cost_time_roll_cases'],local['computation_prerequisite_cases'],local['computation_resource_cases'])==(82,400,16,48,128,48)
for path,expected in local['source_sha256'].items():verify_recorded_source_hash(p/path,expected)
assert not any(e['semantic_review']=='pending' for e in ledger['files'][:129])
d['current_local_effect_computation']={'id':'FEWK-LOCAL-EFFECTS-01','core_version':'v0.20','easy_version':'P v0.18','world_version':'v0.22','sheet_version':'v0.20','intro_version':'v0.4','world_chapters':61,'sheet_sections':25,'focused_sources':5,'cumulative_focused_sources':231,'core_files_focused':129,'core_whole_document_read_confirmed':ledger['whole_read_evidence_audit']['confirmed_by_book']['Core'],'focused_entries_requiring_whole_read_evidence_recheck':ledger['whole_read_evidence_audit']['focused_entries_requiring_whole_read_evidence_recheck'],'checks_passed':local['checks_passed'],'exposure_armor_percentile_cases':400,'clinic_start_condition_cases':16,'correction_cost_time_roll_cases':48,'computation_prerequisite_cases':128,'computation_resource_cases':48,'current_body_and_original_ego_skill_realm_bans_distinguished':True,'functional_repair_and_HP_recovery_window_distinguished':True,'actual_retry_requires_new_work_and_resources':True,'external_terminal_permission_does_not_create_local_connector':True,'memory_flare_branch_and_energy_resources_distinct':True,'new_universal_stats':[],'all_ability_exposure_injury_paradox_device_profiles_complete':False,'whole_Core_gameplay_and_all_original_quotes_verified':False,'full_encounter_balance_verified':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
d['whole_read_evidence_audit']=ledger['whole_read_evidence_audit']
d['current_early_source_recheck']={'whole_read_evidence_gap_rechecks_completed':47,'rechecked_this_pass':41,'focused_reviews':358,'pending_World_reviews':0,'Core_whole_read_and_focused':129,'World_whole_read_and_focused':229,'source_arithmetic_checks':legacy['checks_passed'],'source_examples':legacy['source_example_recheck'],'whole_semantic_review_complete':False,'all_usage_profiles_verified':False,'actual_participant_playtest':False}
temporal=results['시간이동_검증.py'];assert (temporal['checks_passed'],temporal['rail_prerequisite_cases'],temporal['walk_prerequisite_cases'],temporal['percentile_outcomes'],temporal['split_elapsed_time_cases'])==(30,32,64,100,306)
for path,expected in temporal['source_sha256'].items():verify_recorded_source_hash(p/path,expected)
d['current_time_travel']={'id':'FEWK-TIME-01','core_version':'v0.21','world_version':'v0.23','sheet_version':'v0.21','sheet_sections':26,'focused_sources':4,'cumulative_focused_sources':235,'pending_sources':123,'checks_passed':30,'rail_prerequisite_cases':32,'walk_prerequisite_cases':64,'percentile_outcomes':100,'split_elapsed_time_cases':306,'same_body_and_person_state_preserved':True,'calendar_change_is_not_state_reset':True,'timewalking_function_not_created_by_skill_alone':True,'ordinary_rail_needs_no_timewalking_ability':True,'old_user_decision_record_and_actual_original_statement_distinguished':True,'new_universal_stats':[],'all_time_physics_and_related_novels_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
profession=json.loads((v/'직업과현화_검토.json').read_text())
assert len(profession['source_ids'])==8 and len(profession['case_collection'])==10 and profession['new_mechanical_parameter_values']==[]
for entry in profession['sources']:verify_recorded_source_hash(p/entry['path'],entry['sha256'])
for i in [162,235,266,316,320,322,323,324]:assert ledger['files'][i]['semantic_review']=='focused_review' and ledger['files'][i]['whole_document_read'] is True
assert '## 75.' in (o/'11_WorldLorebook.md').read_text() and '## 78.' not in (o/'11_WorldLorebook.md').read_text()
assert '## 32.' in (o/'12_룰시트와캐릭터시트.md').read_text() and '## 33.' not in (o/'12_룰시트와캐릭터시트.md').read_text()
d['current_profession_manifest_lore']={'id':'FEWK-PROFESSION-LORE-01','core_version':'v0.22','world_version':'v0.24','sheet_version':'v0.22','world_chapters':64,'sheet_sections':27,'focused_sources':8,'cumulative_focused_sources':243,'pending_sources':115,'original_raw_topics_whole_read':12,'original_wiki_topics_whole_read':15,'directly_related_novels_whole_read':['006','043'],'case_collection_reviewed':10,'fictional_document_numbers_are_not_primary_evidence':True,'creation_origins_and_jobs_and_interactions_distinguished':True,'license_scope_and_information_truth_distinguished':True,'modern_workshops_and_rare_golden_hands_distinguished':True,'ordinary_art_support_and_extreme_last_concert_distinguished':True,'transfer_byte_exemption_not_free_storage_fabrication_permission_or_copy':True,'new_mechanical_parameter_values':[],'all_professions_religions_abilities_novels_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
institutions=json.loads((v/'종교경제와기반시설_검토.json').read_text())
assert len(institutions['source_ids'])==7 and institutions['new_mechanical_parameter_values']==[]
for e in institutions['sources']:verify_recorded_source_hash(p/e['path'],e['sha256'])
for i in [236,237,238,239,240,242,244]:assert ledger['files'][i]['semantic_review']=='focused_review' and ledger['files'][i]['whole_document_read'] is True
arithmetic=institutions['source_arithmetic_discrepancy'];assert arithmetic['computed_remaining_OYAT']==arithmetic['earned_OYAT']-arithmetic['food_OYAT']-arithmetic['commute_OYAT']==36
assert arithmetic['declared_remaining_OYAT']==34 and arithmetic['unexplained_difference_OYAT']==2 and arithmetic['additional_expense_invented'] is False
assert ledger['whole_read_evidence_audit']['confirmed_by_book']=={'Core':129,'World':229}
assert sum(e['semantic_review']=='focused_review' and e.get('whole_document_read') is True for e in ledger['files'])==358
assert sum(e['semantic_review']=='pending' for e in ledger['files'])==0
assert not institutions['actual_participant_reading'] and not institutions['actual_participant_playtest'] and not institutions['actual_async_community_test']
d['current_institutions_lore']={'id':'FEWK-INSTITUTIONS-LORE-01','core_version':'v0.23','world_version':'v0.25','sheet_version':'v0.23','world_chapters':67,'sheet_sections':28,'focused_sources':7,'cumulative_focused_sources':250,'pending_sources':108,'original_raw_topics_whole_read':11,'original_wiki_topics_whole_read':10,'older_group_list_whole_read':True,'directly_related_novels_whole_read':['007','036'],'source_arithmetic_declared_and_computed_separated':True,'fictional_report_and_definition_and_proposal_distinguished':True,'faith_and_profession_and_device_permissions_distinguished':True,'purpose_fixed_coffin_and_exploration_and_time_rail_distinguished':True,'manufacture_resources_and_transfer_and_output_rights_distinguished':True,'new_mechanical_parameter_values':[],'all_religions_prices_relations_novels_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
runner=json.loads((v/'러너와템플릿_검토.json').read_text());assert runner['source_ids']==['SRC-270','SRC-271','SRC-272','SRC-273','SRC-274','SRC-275'] and runner['new_mechanical_parameter_values']==[]
for e in runner['sources']:verify_recorded_source_hash(p/e['path'],e['sha256'])
for i in range(269,275):assert ledger['files'][i]['semantic_review']=='focused_review' and ledger['files'][i]['whole_document_read'] is True
assert runner['unread_documents_counted'] is False and runner['OOC_sheet_visibility_is_IC_knowledge'] is False and runner['class_level_is_required'] is False
assert runner['directly_related_novels_whole_read_this_pass']==[] and not runner['actual_participant_reading'] and not runner['actual_participant_playtest']
d['current_runner_identity']={'id':'FEWK-RUNNER-IDENTITY-01','core_version':'v0.24','world_version':'v0.26','sheet_version':'v0.24','world_chapters':68,'sheet_sections':29,'focused_sources':6,'cumulative_focused_sources':256,'pending_sources':102,'original_raw_topics_whole_read':7,'original_wiki_topics_whole_read':25,'directly_related_novels_whole_read_this_pass':[],'unread_documents_counted':False,'job_and_role_and_social_style_distinguished':True,'class_level_is_required':False,'runner_currency_is_global_reputation_stat':False,'OOC_sheet_visibility_is_IC_knowledge':False,'new_mechanical_parameter_values':[],'all_runner_economy_jobs_gangs_novels_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
hubs=json.loads((v/'거점임무와조직_검토.json').read_text());assert hubs['source_ids']==['SRC-'+str(i) for i in range(276,286)]
for entry in hubs['sources']:verify_recorded_source_hash(p/entry['path'],entry['sha256'])
for i in range(275,285):assert ledger['files'][i]['semantic_review']=='focused_review' and ledger['files'][i]['whole_document_read'] is True
assert len(hubs['original_raw_topics_whole_read'])==14 and len(hubs['original_wiki_topic_indices_whole_read'])==19
assert hubs['directly_related_novels_whole_read_this_pass']==['002'] and hubs['new_mechanical_parameter_values']==[] and hubs['new_universal_stats']==[]
assert hubs['Red_Monkeys_has_branches'] is False and hubs['Sohwa_original_farm_and_cafe_link_confirmed'] is True and hubs['Sohwa_vs_Soha_spelling_resolved'] is False
assert hubs['Chris_gas_promotion_death_supported'] is True and hubs['Chris_gas_promotion_debut_supported'] is False and hubs['Tirori_20years_first_observation_supported'] is True
ar=hubs['novel_arithmetic_discrepancy'];assert ar['earned_OYAT']-ar['interest_OYAT']==ar['available_principal_reduction_OYAT']==30 and ar['additional_expenses_invented'] is False
assert not hubs['unread_documents_counted'] and not hubs['mandatory_job_slots_added'] and not hubs['physical_runner_label_creates_cross_body_damage']
assert not hubs['actual_participant_reading'] and not hubs['actual_participant_playtest'] and not hubs['actual_async_community_test']
d['current_hub_missions']={'id':hubs['id'],'core_version':'v0.25','world_version':'v0.27','sheet_version':'v0.25','world_chapters':70,'sheet_sections':30,'focused_sources':10,'cumulative_focused_sources':266,'pending_sources':92,'original_raw_topics_whole_read':14,'original_wiki_topics_whole_read':19,'previous_S07_decisions_preserved':True,'directly_related_novels_whole_read_this_pass':['002'],'source_original_and_later_story_distinguished':True,'farm_and_cafe_original_link_confirmed':True,'one_local_combat_and_interaction_engine':True,'new_mechanical_parameter_values':[],'mandatory_job_slots_added':False,'physical_runner_label_creates_cross_body_damage':False,'source_arithmetic_discrepancy_recorded':True,'all_runner_hubs_jobs_groups_novels_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
life=json.loads((v/'러너생애와전환_검토.json').read_text());assert life['source_ids']==['SRC-'+str(i) for i in range(289,295)]
for entry in life['sources']:verify_recorded_source_hash(p/entry['path'],entry['sha256'])
for i in range(288,294):assert ledger['files'][i]['semantic_review']=='focused_review' and ledger['files'][i]['whole_document_read'] is True
assert life['Pei_failed_guardian_and_successful_runner_distinguished'] is True and life['Pei_exact_career_dates_and_32years_confirmed'] is False
assert life['new_mechanical_parameter_values']==[] and life['new_universal_stats']==[] and not life['new_mandatory_job_slots']
assert not life['actual_participant_reading'] and not life['actual_participant_playtest'] and not life['actual_async_community_test']
d['current_runner_life']={'id':life['id'],'core_version':'v0.25','world_version':'v0.28','sheet_version':'v0.25','world_chapters':71,'sheet_sections':30,'focused_sources':6,'cumulative_focused_sources':272,'pending_sources':86,'original_raw_topics_whole_read_this_pass':4,'directly_related_novels_whole_read_this_pass':[],'career_and_profession_and_learning_distinguished':True,'Pei_failed_guardian_and_successful_runner_distinguished':True,'dropout_means_only_named_realm_reentry_ban':True,'new_mechanical_parameter_values':[],'all_career_jobs_funerals_world_law_novels_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
catalog=json.loads((v/'계도감과현지화_검토.json').read_text());assert catalog['source_ids']==['SRC-295','SRC-297','SRC-298','SRC-299','SRC-300','SRC-301','SRC-302','SRC-303']
for entry in catalog['sources']:verify_recorded_source_hash(p/entry['path'],entry['sha256'])
for i in [294,296,297,298,299,300,301,302]:assert ledger['files'][i]['semantic_review']=='focused_review' and ledger['files'][i]['whole_document_read'] is True
assert ledger['files'][302]['semantic_review']=='focused_review' and catalog['pending_read_not_counted']==[] and catalog['read_delay_resolved'] is True
assert len(catalog['original_raw_topics_whole_read_this_pass'])==9 and len(catalog['original_wiki_topic_indices_whole_read_this_pass'])==8
assert catalog['new_mechanical_parameter_values']==[] and catalog['new_universal_stats']==[] and catalog['Heropone_is_emergency_transport_service'] is False and catalog['Heropone_is_DDOGG_childhood_powder'] is True
assert not catalog['unread_documents_counted'] and not catalog['actual_participant_reading'] and not catalog['actual_participant_playtest'] and not catalog['actual_async_community_test']
d['current_realm_catalog']={'id':catalog['id'],'core_version':'v0.25','world_version':'v0.29','sheet_version':'v0.25','world_chapters':72,'sheet_sections':30,'focused_sources':8,'cumulative_focused_sources':280,'pending_sources':78,'original_raw_topics_whole_read_this_pass':9,'original_wiki_topics_whole_read_this_pass':8,'directly_related_novels_whole_read_this_pass':[],'same_local_combat_and_interaction_engine':True,'pioneer_IO_family_and_actual_body_and_price_distinguished':True,'Heropone_is_emergency_transport_service':False,'source_unverified_global_card_values_not_imported':True,'new_mechanical_parameter_values':[],'all_realm_catalog_original_physics_novels_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
frontier=json.loads((v/'오지와기록_검토.json').read_text())
assert frontier['source_ids']==['SRC-'+str(i) for i in [304,305,306,307,308,309,314,315,316,319,320]]
for entry in frontier['sources']:verify_recorded_source_hash(p/entry['path'],entry['sha256'])
for i in [303,304,305,306,307,308,313,314,315,318,319]:assert ledger['files'][i]['semantic_review']=='focused_review' and ledger['files'][i]['whole_document_read'] is True
assert len(frontier['original_raw_topics_whole_read_this_pass'])==7 and len(frontier['original_wiki_topic_indices_whole_read_this_pass'])==15
assert frontier['pending_read_not_counted']==['SRC-310','SRC-311','SRC-312','SRC-313']
for i in range(309,313):assert ledger['files'][i]['semantic_review']=='focused_review' and ledger['files'][i]['hash_validation_mode']=='fixed_3.1_reference_snapshot'
assert frontier['new_mechanical_parameter_values']==[] and frontier['new_universal_stats']==[]
assert not frontier['Jemin_originally_wealthy'] and not frontier['Jemin_sealed_coffin_sale_is_confirmed_transaction'] and not frontier['recorder_Sara_signature_proves_omniscient_world_institution']
assert not frontier['unread_documents_counted'] and not frontier['actual_participant_reading'] and not frontier['actual_participant_playtest'] and not frontier['actual_async_community_test']
d['current_frontier_records']={'id':frontier['id'],'core_version':'v0.25','world_version':'v0.30','sheet_version':'v0.25','world_chapters':74,'sheet_sections':30,'focused_sources':11,'cumulative_focused_sources':291,'pending_sources':67,'original_raw_topics_whole_read_this_pass':7,'original_wiki_topics_whole_read_this_pass':15,'directly_related_novels_whole_read_this_pass':[],'pending_read_not_counted':frontier['pending_read_not_counted'],'optional_frontier_proposals_preserved':frontier['optional_frontier_proposals_preserved'],'recorder_optional_NPC_role_preserved':True,'same_local_combat_and_interaction_engine':True,'new_mechanical_parameter_values':[],'whole_semantic_review_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
baseline_preservation=json.loads((o/'3.1판_참고원고_기준선.json').read_text())['pending_reference_content_preservation']
assert baseline_preservation['baseline_matched_count']==len(baseline_preservation['snapshots'])==65
assert baseline_preservation['whole_document_reads_this_step']==baseline_preservation['semantic_reviews_completed_this_step']==0
assert baseline_preservation['current_worktree_revalidation_pending'] is True
baseline_entries={e['id']:e for e in ledger['files']}
for snapshot in baseline_preservation['snapshots']:
 data=snapshot['text'].encode();assert hashlib.sha256(data).hexdigest()==snapshot['sha256']==baseline_entries[snapshot['source_id']]['baseline_sha256']
 assert len(data)==snapshot['bytes'] and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==snapshot['git_blob']
 assert snapshot['current_worktree_read_this_turn'] is False and snapshot['whole_document_read_this_step'] is False and snapshot['semantic_review']=='pending'
assert [e['source_id'] for e in baseline_preservation['cached_text_not_matching_baseline']]==['SRC-354']
d['pending_baseline_content_preservation']={'baseline_matched_count':65,'whole_document_reads_this_step':0,'semantic_reviews_completed_this_step':0,'current_worktree_revalidation_pending':True,'cached_text_not_matching_baseline':['SRC-354']}
daily=json.loads((v/'일상과이지룰_검토.json').read_text())
assert daily['source_ids']==['SRC-249']
for entry in daily['sources']:verify_recorded_source_hash(p/entry['path'],entry['sha256'])
assert ledger['files'][248]['semantic_review']=='focused_review' and ledger['files'][248]['whole_document_read'] is True
assert len(daily['original_raw_topics_whole_read_this_pass'])==3 and len(daily['original_wiki_topic_indices_whole_read_this_pass'])==12
assert daily['easy_original_chars']==13662 and daily['versions']['easy']=='P v0.19' and daily['easy_current_chars']==7916
assert len(easy)<daily['easy_original_chars']  # 현재 예시 보강 후에도 이전 상세안보다 짧다.
assert not daily['easy_rules_changed'] and daily['unified_interaction_placed_in_creation'] and daily['new_mechanical_parameter_values']==[]
assert not daily['unread_documents_counted'] and not daily['actual_participant_reading'] and not daily['actual_participant_playtest'] and not daily['actual_async_community_test']
d['current_daily_reader']={'id':daily['id'],'core_version':'v0.25','easy_version':'P v0.19','world_version':'v0.31','sheet_version':'v0.25','world_chapters':74,'sheet_sections':30,'focused_sources':1,'cumulative_focused_sources':292,'pending_sources':66,'original_raw_topics_whole_read_this_pass':3,'original_wiki_topics_whole_read_this_pass':12,'easy_original_chars':daily['easy_original_chars'],'easy_current_chars':daily['easy_current_chars'],'easy_rules_changed':False,'unified_interaction_placed_in_creation':True,'new_mechanical_parameter_values':[],'whole_semantic_review_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
daily_frontier=json.loads((v/'일상과오지_기준선검토.json').read_text())
expected_ids=['SRC-'+str(i+1) for i in [245,246,247,249,250,251]+list(range(256,264))+[267,268]+list(range(309,313))]
assert daily_frontier['source_ids']==expected_ids and set(expected_ids).issubset(historical_reference_only_ids)
for source in daily_frontier['sources']:verify_recorded_source_hash(p/source['path'],source['sha256'])
for record in daily_frontier['reference_snapshots_reviewed']:
 assert record['whole_document_read'] is True and record['current_worktree_hash_rechecked_this_review'] is False
 assert record['text_sha256']==record['baseline_sha256']==frozen_snapshots[record['source_id']]['sha256']
assert len(daily_frontier['original_raw_topics_whole_read_this_pass'])==9 and len(daily_frontier['original_wiki_topic_indices_whole_read_this_pass'])==16
assert daily_frontier['memorial_flower_is_manufactured_by_Grie'] and not daily_frontier['memorial_flower_is_exclusive_wild_origin_in_flower_garden'] and not daily_frontier['Flower_Garden_DC12_three_failures_is_core_rule']
assert daily_frontier['Worry_Doll_original_idle_power_unneeded_and_expensive'] and not daily_frontier['wills_are_all_self_reduced_monks'] and not daily_frontier['Yoseob_is_religion_branch']
assert daily_frontier['fur_coat_example_credits']//daily_frontier['reference_credits_per_OYAT']==daily_frontier['computed_fur_coat_example_OYAT']==30000
assert daily_frontier['new_mechanical_parameter_values']==[] and daily_frontier['new_universal_stats']==[] and not daily_frontier['unread_documents_counted']
assert not daily_frontier['actual_participant_reading'] and not daily_frontier['actual_participant_playtest'] and not daily_frontier['actual_async_community_test']
d['current_daily_frontier_baseline']={'id':daily_frontier['id'],'core_version':'v0.25','easy_version':'P v0.19','world_version':'v0.32','sheet_version':'v0.25','world_chapters':74,'sheet_sections':30,'focused_sources':20,'cumulative_focused_sources':312,'pending_sources':46,'original_raw_topics_whole_read_this_pass':9,'original_wiki_topics_whole_read_this_pass':16,'current_worktree_hash_revalidation_pending_ids':daily_frontier['current_worktree_revalidation_pending_ids'],'fixed_reference_baseline_content_verified':True,'same_local_combat_and_interaction_engine':True,'new_mechanical_parameter_values':[],'whole_semantic_review_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
d['source_hash_validation_scope']={'focused_content_reviews':358,'original_source_paths_rehashed_in_current_audit':358,'fixed_reference_snapshot_content_validated':65,'current_worktree_hash_revalidation_pending_ids':[],'full_current_worktree_revalidation_complete':True,'current_reference_audit_record':'현재_참고원고_해시검증.json','historical_reference_only_review_ids':historical_reference_only_ids,'other_source_hash_audit_pending_ids':source_hash_audit_pending_ids,'audit_mode':'local_package' if local_package_only else 'package_and_available_original_sources','source_paths_current_hash_revalidation_pending':sorted(source_paths_revalidation_pending)}
d['current_local_package_verification']={'docs':len(docs),'links':len(links),'missing':missing,'package_artifacts_hashed':len(files),'fixed_reference_snapshots_verified':65,'whole_semantic_review_complete':False,'full_original_source_hash_audit_completed':True,'full_other_older_source_hash_audit_completed':False,'other_source_hash_audit_pending_ids':source_hash_audit_pending_ids,'source_checks_are_separate':True}
intro_dimensions=json.loads((v/'서문과차원개요_검토.json').read_text())
intro_ids=['SRC-130','SRC-131','SRC-132','SRC-133','SRC-135','SRC-136','SRC-138','SRC-142','SRC-147','SRC-159','SRC-164','SRC-167','SRC-168','SRC-169','SRC-177','SRC-178']
assert intro_dimensions['source_ids']==intro_ids and set(intro_ids+expected_ids).issubset(historical_reference_only_ids)
for source in intro_dimensions['sources']:verify_recorded_source_hash(p/source['path'],source['sha256'])
for record in intro_dimensions['reference_snapshots_reviewed']:
 assert record['whole_document_read'] and not record['current_worktree_hash_rechecked_this_review']
 assert record['text_sha256']==record['baseline_sha256']==frozen_snapshots[record['source_id']]['sha256']
assert len(intro_dimensions['original_raw_topics_whole_read_this_pass'])==9 and len(intro_dimensions['original_wiki_topic_indices_whole_read_this_pass'])==14
assert len(intro_dimensions['primary_topic_snapshots'])==23
for topic in intro_dimensions['primary_topic_snapshots']:
 assert hashlib.sha256(topic['text'].encode()).hexdigest()==topic['text_sha256'] and topic['whole_topic_read'] and not topic['current_source_file_rehashed']
assert intro_dimensions['raw_cache_line_endings']['original_capture_hash_matches'] and not intro_dimensions['raw_cache_line_endings']['current_source_file_rehashed']
assert intro_dimensions['legacy_claimed_exact_layer_count']==7 and intro_dimensions['legacy_layer_table_data_rows']==9 and not intro_dimensions['legacy_upper_second_layer_is_confirmed_original_fact']
assert intro_dimensions['physical_density_standard_bytes_per_gram']//intro_dimensions['lower_first_density_standard_bytes_per_gram']==10000 and intro_dimensions['physical_60kg_standard_za']==60000
assert intro_dimensions['reader_paths']==3 and intro_dimensions['original_Orc_city_economy_specialists_and_low_reward_preserved'] and not intro_dimensions['Orc_is_universal_high_reward_uncharted_first_entry']
assert intro_dimensions['new_mechanical_parameter_values']==[] and intro_dimensions['new_universal_stats']==[] and not intro_dimensions['universal_BP_or_matting_shining_paradox_tracks_added']
assert not intro_dimensions['unread_documents_counted'] and not intro_dimensions['actual_participant_reading'] and not intro_dimensions['actual_participant_playtest'] and not intro_dimensions['actual_async_community_test']
world_text=(o/'11_WorldLorebook.md').read_text()
assert '<a id="fewk-reading-paths"></a>' in world_text and '<a id="fewk-tone"></a>' in world_text
assert '차원의 성격·밀도·지원은 각각 확인한다' in world_text and '개척을 준비하는 팀' in world_text
# 현재 실제 앵커 참조를 확인한다. 원본 해시의 별도 대기는 유지한다.
for document in docs:
 for href in re.findall(r'\[[^\]\n]*\]\(([^)]+)\)',document.read_text()):
  target=urlsplit(href.strip('<>'))
  if target.scheme or not target.fragment.startswith('fewk-'):continue
  path=document.parent/unquote(target.path) if target.path else document
  assert exists(path) and '<a id="'+target.fragment+'"></a>' in path.read_text(),(document,href)
d['current_introduction_dimensions']={'id':intro_dimensions['id'],'world_version':'v0.33','design_version':'v0.51','focused_sources':16,'cumulative_focused_sources':328,'pending_sources':30,'original_raw_topics_whole_read_this_pass':9,'original_wiki_topics_whole_read_this_pass':14,'cumulative_reference_snapshots_reviewed':36,'current_worktree_hash_revalidation_pending_ids':[sid for sid in historical_reference_only_ids if sid in intro_ids+expected_ids],'reader_paths':3,'same_local_combat_and_interaction_engine':True,'new_mechanical_parameter_values':[],'whole_semantic_review_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
d['source_hash_validation_scope']['source_paths_current_hash_revalidation_pending']=sorted(source_paths_revalidation_pending)
npc_acquisition=ledger['files'][353]['current_acquisition_snapshot']
assert hashlib.sha256(npc_acquisition['text'].encode()).hexdigest()==npc_acquisition['sha256']==ledger['files'][353]['baseline_sha256']
assert len(npc_acquisition['text'].encode())==npc_acquisition['bytes']==5227 and npc_acquisition['current_source_file_read_and_hashed_at_capture']
assert ledger['files'][353]['semantic_review']=='focused_review' and not npc_acquisition['whole_document_semantically_reviewed'] and not npc_acquisition['counted_as_focused_review']
d['reference_source_acquisition']={'source_id':'SRC-354','date':'2026-10-05','bytes':5227,'baseline_hash_matches':True,'current_source_file_hashed_at_capture':True,'counted_as_focused_review_at_capture':False,'whole_document_reviewed_in_later_appendix_pass':True}
being_catalog=json.loads((v/'존재도감_검토.json').read_text())
being_ids=['SRC-'+str(i) for i in range(326,336)]
assert being_catalog['source_ids']==being_ids and set(historical_reference_only_ids)==set(intro_ids+expected_ids+being_ids+['SRC-'+str(i) for i in [336,337,338,339]+list(range(343,352))]+['SRC-'+str(i) for i in [352,353,355,356,357,358]])
for source in being_catalog['sources']:verify_recorded_source_hash(p/source['path'],source['sha256'])
for record in being_catalog['reference_snapshots_reviewed']:
 assert record['whole_document_read'] and not record['current_worktree_hash_rechecked_this_review']
 assert record['text_sha256']==record['baseline_sha256']==frozen_snapshots[record['source_id']]['sha256']
assert len(being_catalog['original_raw_topics_whole_read_this_pass'])==13 and len(being_catalog['original_wiki_topic_indices_whole_read_this_pass'])==15 and len(being_catalog['primary_topic_snapshots'])==28
for topic in being_catalog['primary_topic_snapshots']:
 assert hashlib.sha256(topic['text'].encode()).hexdigest()==topic['text_sha256'] and topic['whole_topic_read'] and not topic['current_source_file_rehashed']
assert not being_catalog['legacy_monster_bundle_is_common_rule'] and not being_catalog['all_mekgaebi_have_five_official_ranks'] and not being_catalog['mimyung_has_automatic_random_forms_equipment_and_concentration_threshold']
assert json.loads((v/'스페셜_프로필.json').read_text())['modes']=={'settled':0,'walker':1,'runner':2,'flyer':3}
assert '현지 정착·워커·러너·플라이어' in core and '정착한 이민자가 네이티브로 다시 태어난' in world_text
assert being_catalog['native_and_settled_residence_reconciliation']['birth_definition_preserved']
assert being_catalog['DDI_is_zodiac_divine_beast_concept'] and not being_catalog['DDI_is_Dimensional_Density_Inheritor'] and being_catalog['native_is_born_citizen_of_its_realm']
assert being_catalog['DDOGG_future_five_moons_description_preserved'] and not being_catalog['DDOGG_has_universal_invulnerability_or_forced_feelings'] and being_catalog['Seleen_is_original0033_human_character_not_universal_DDOGG']
assert being_catalog['Yakcha_is_Gabo_sinki_divine_beast_product_and_cheaper_than_Worry_Doll'] and not being_catalog['Yakcha_30m_four_hour_rule_is_universal'] and not being_catalog['all_ready_made_30_are_Kim']
assert being_catalog['Crocodile_three_forms_and_energy_air_supply_are_confirmed_original0083'] and being_catalog['Beast794_character_details_are_marked_optional_proposals']
assert being_catalog['new_mechanical_parameter_values']==[] and being_catalog['new_universal_stats']==[] and not being_catalog['unread_documents_counted']
assert not being_catalog['actual_participant_reading'] and not being_catalog['actual_participant_playtest'] and not being_catalog['actual_async_community_test']
assert '<a id="fewk-being-catalog"></a>' in world_text and '## 75. 존재의 도감' in world_text
measure=being_catalog['wiki551_measurement_difference'];assert measure['reported_extra_za']//measure['reported_za_per_gram']==measure['computed_extra_grams']==21 and not measure['current_rule_values_changed']
d['current_being_catalog']={'id':being_catalog['id'],'world_version':'v0.34','design_version':'v0.52','world_chapters':75,'sheet_sections':30,'focused_sources':10,'cumulative_focused_sources':338,'pending_sources':20,'original_raw_topics_whole_read_this_pass':13,'original_wiki_topics_whole_read_this_pass':15,'cumulative_reference_snapshots_reviewed':46,'same_local_combat_and_interaction_engine':True,'new_mechanical_parameter_values':[],'whole_semantic_review_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
d['source_hash_validation_scope']['source_paths_current_hash_revalidation_pending']=sorted(source_paths_revalidation_pending)
factions=json.loads((v/'세력과작전_검토.json').read_text())
assert factions['source_ids']==['SRC-'+str(i) for i in [336,337,338,339]+list(range(343,352))]
for source in factions['sources']:verify_recorded_source_hash(p/source['path'],source['sha256'])
for record in factions['reference_snapshots_reviewed']:
 assert record['whole_document_read'] and not record['current_worktree_hash_rechecked_this_review']
 snapshot=frozen_snapshots[record['source_id']];data=snapshot['text'].encode()
 assert hashlib.sha256(data).hexdigest()==record['text_sha256']==record['baseline_sha256']
 assert len(data)==record['bytes'] and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==record['git_blob']
assert len(factions['original_raw_topics_whole_read_this_pass'])==11 and len(factions['original_wiki_topic_indices_whole_read_this_pass'])==40
assert len(factions['primary_topic_snapshots'])==51 and factions['original_raw_topics_title_only']==['0102']
for topic in factions['primary_topic_snapshots']:
 assert hashlib.sha256(topic['text'].encode()).hexdigest()==topic['text_sha256'] and topic['whole_topic_read'] and not topic['current_source_file_rehashed']
assert factions['ten_states_count']==10 and factions['overlapping_top_two_three_six_not_added'] and factions['longsa_is_repair_profession']
assert factions['Gonghwa_hotel_body_maintenance_cause_and_current_resident_guild_preserved'] and factions['Amy_Heart_detail_from_wiki_NFT0102_and_current_occupation_preserved']
assert not factions['five_universal_official_guilds_claimed'] and not factions['runner_D_to_S_grade_and_wage_table_is_common_rule']
assert not factions['Amy_Heart_is_confirmed_dead_in_recent_exploration'] and not factions['Amy_Heart_victims_confirmed_high_intelligence_civilisation']
assert factions['first_Shindan_and_later_Jin_Shindan_conflict_distinguished'] and factions['fictional_speeches_and_optional_campaign_proposals_preserved']
assert factions['new_mechanical_parameter_values']==[] and factions['new_universal_stats']==[] and not factions['unread_documents_counted']
assert not factions['actual_participant_reading'] and not factions['actual_participant_playtest'] and not factions['actual_async_community_test']
assert '<a id="fewk-factions"></a>' in world_text and '## 76. 세력과 작전' in world_text and '호텔의 남아 있는 영수증' in world_text
d['current_factions_operations']={'id':factions['id'],'world_version':'v0.35','design_version':'v0.53','world_chapters':76,'sheet_sections':30,'focused_sources':13,'cumulative_focused_sources':351,'pending_sources':7,'original_raw_topics_whole_read_this_pass':11,'original_wiki_topics_whole_read_this_pass':40,'cumulative_reference_snapshots_reviewed':59,'same_local_combat_and_interaction_engine':True,'new_mechanical_parameter_values':[],'whole_semantic_review_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
d['source_hash_validation_scope']['source_paths_current_hash_revalidation_pending']=sorted(source_paths_revalidation_pending)
world_appendix=json.loads((v/'월드부록_검토.json').read_text())
assert world_appendix['source_ids']==['SRC-'+str(i) for i in range(352,359)]
for source in world_appendix['sources']:verify_recorded_source_hash(p/source['path'],source['sha256'])
for record in world_appendix['reference_snapshots_reviewed']:
 assert record['whole_document_read'] and not record['current_worktree_hash_rechecked_this_review']
 snapshot=frozen_snapshots[record['source_id']];data=snapshot['text'].encode()
 assert hashlib.sha256(data).hexdigest()==record['text_sha256']==record['baseline_sha256']
 assert len(data)==record['bytes'] and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==record['git_blob']
acquired=world_appendix['acquired_reference_snapshots_reviewed'];assert len(acquired)==1 and acquired[0]['source_id']=='SRC-354'
assert acquired[0]['whole_document_read'] and acquired[0]['text_sha256']==npc_acquisition['sha256'] and acquired[0]['bytes']==5227
assert len(world_appendix['original_raw_topics_whole_read_this_pass'])==8 and len(world_appendix['original_wiki_topic_indices_whole_read_this_pass'])==23
for topic in world_appendix['primary_topic_snapshots']:
 assert hashlib.sha256(topic['text'].encode()).hexdigest()==topic['text_sha256'] and topic['whole_topic_read'] and not topic['current_source_file_rehashed']
assert len(world_appendix['primary_topic_snapshots'])==31
assert len(re.findall(r'^\| \*\*',npc_acquisition['text'],re.M))==27
assert len(re.findall(r'^\| (?!수평|---)',frozen_snapshots['SRC-353']['text'],re.M))==16
assert len(re.findall(r'^\*\*',frozen_snapshots['SRC-355']['text'],re.M))==93
assert len(world_appendix['world_glossary'])==94 and len(world_appendix['world_people_index'])==27
for record in world_appendix['world_glossary']+world_appendix['world_people_index']:
 document,anchor=record['href'].split('#');assert '<a id="'+anchor+'"></a>' in (o/document).read_text()
for ch in range(1,78):assert '<a id="fewk-world-'+f'{ch:02}'+'"></a>' in world_text
assert world_appendix['dropout_means_named_realm_reentry_ban'] and world_appendix['birth_origin_profession_interaction_residence_mode_distinguished']
assert world_appendix['Ballae_original0013_and_wiki_future_and_expanded_story_distinguished']
assert not world_appendix['old_price_or_Grade_or_A2_Neuro_is_common_rule'] and not world_appendix['NPC27_is_official_simultaneous_population']
assert not world_appendix['Jin_original0005_contains_completed_release_of_Cheongho'] and not world_appendix['Shining_means_only_sinki_branch']
assert not world_appendix['maps_delivered_or_page_numbers_final'] and not world_appendix['FWOL2_1_legal_publication_claim_verified']
assert not world_appendix['actual_participant_reading'] and not world_appendix['actual_participant_playtest'] and not world_appendix['actual_async_community_test']
assert world_appendix['new_mechanical_parameter_values']==[] and world_appendix['new_universal_stats']==[] and not world_appendix['unread_documents_counted']
assert '<a id="fewk-world-reference"></a>' in world_text and '## 77. 찾아보기' in world_text and '<a id="fewk-core-reference"></a>' in core
d['current_world_appendix']={'id':world_appendix['id'],'core_version':'v0.27','world_version':'v0.36','sheet_version':'v0.27','design_version':'v0.54','world_chapters':77,'focused_sources':7,'cumulative_focused_sources':358,'pending_reference_documents':0,'whole_semantic_review_complete':False,'world_glossary_groups':94,'world_people_index_entries':27,'world_chapter_anchors':77,'frozen_reference_snapshots_reviewed':65,'recently_acquired_reference_snapshot_reviewed':1,'new_mechanical_parameter_values':[],'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
d['source_hash_validation_scope']['source_paths_current_hash_revalidation_pending']=sorted(source_paths_revalidation_pending)
procurement=json.loads((o/'이전자료_조달목록.json').read_text())
legacy_coherence=json.loads((v/'이전설계_통합검토.json').read_text())
assert len(legacy_coherence['source_snapshots'])==23
for source in legacy_coherence['source_snapshots']:
 data=source['text'].encode();assert len(data)==source['bytes'] and hashlib.sha256(data).hexdigest()==source['sha256']
 assert source['whole_document_read'] and source['current_source_file_read_and_hashed_this_pass']
 recorded=next(e for e in procurement['files'] if e['name']==source['name'])
 assert recorded['sha256']==source['sha256'] and recorded['whole_document_read'] and recorded['baseline_hash_matches']
 assert recorded['review_evidence']=='검증/이전설계_통합검토.json'
ar=legacy_coherence['old_arithmetic'];assert (ar['field_professor_actual'],ar['field_professor_corrected_option1'],ar['generalist_actual'])==(33,30,30)
assert legacy_coherence['new_mechanical_parameter_values']==[] and not legacy_coherence['old_100point_build_rewritten']
assert legacy_coherence['whole_older_procurement_semantic_review_complete'] and not legacy_coherence['actual_participant_playtest']
d['current_legacy_coherence']={'id':legacy_coherence['id'],'whole_older_documents_read_this_pass':2,'cumulative_whole_documents_in_report':23,'new_mechanical_parameter_values':[],'all_older_sources_complete':False,'actual_participant_playtest':False}
assert len(legacy_coherence['primary_topic_snapshots'])==32
for topic in legacy_coherence['primary_topic_snapshots']:
 assert hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256'] and topic['whole_topic_read']
for source in legacy_coherence['original_sources']:verify_recorded_source_hash(p/source['path'],source['sha256'])
assert (ar['shin_warrior_actual'],ar['Katie_purchase_actual'],ar['Katie_total_actual'],ar['Katie_remove_kit_total'],ar['Katie_reduce_background_total'])==(29,34,101,99,100)
assert (ar['new_book_actual_count'],ar['new_book_actual_pages'],ar['candidate_rows'],ar['candidate_unique_original_topics'])==(11,3191,30,22)
assert len(legacy_coherence['procurement_entries_still_marked_semantic_pending'])==0
assert legacy_coherence['previous_major_decision_reviews_are_all_whole_document_reviews']
assert legacy_coherence['new_campaign_openings']==['다음 날의 반지'] and not legacy_coherence['new_opening_is_original0030_ending']
assert '#### 다음 날의 반지 — 새 캠페인 도입' in world_text
assert len(legacy_coherence['quote_fidelity_checks'])==23
raw_topics={entry['topic']:entry['text'] for entry in legacy_coherence['primary_topic_snapshots']}
older_texts={entry['name']:entry['text'] for entry in legacy_coherence['source_snapshots']}
normalize_quote=lambda text:re.sub(r'\s+','',text.replace(';',''))
for check in legacy_coherence['quote_fidelity_checks']:
 source=re.split(r'\s{2,}'+check['topic']+r'\s{2,}',raw_topics[check['topic']],maxsplit=1)[1]
 source=re.split(r'연관\s*:',source,maxsplit=1)[0].strip().strip('"').strip()
 section=next(section for title,section in re.findall(r'^## (.*?)\n(.*?)(?=^## |\Z)',older_texts[check['document']],re.M|re.S) if '#'+check['topic'] in title)
 quote=re.search(r'```\n(.*?)\n```',section,re.S)[1]
 assert normalize_quote(source)==normalize_quote(quote)
 assert hashlib.sha256(normalize_quote(quote).encode()).hexdigest()==check['normalized_text_sha256']
 for target in [check['core_destination'],check['world_destination']]:
  filename,anchor=target.split('#');assert '<a id="'+anchor+'"></a>' in (o/filename).read_text()
catalog_check=legacy_coherence['catalog_review']
assert (catalog_check['rows'],catalog_check['unique_topic_codes'],catalog_check['corrected_objects'],catalog_check['corrected_unclassified'])==(105,105,18,0)
assert not catalog_check['all_105_primary_bodies_whole_read'] and not catalog_check['archived_catalog_modified']
assert '### 발췌 속 이름을 현재 인물과 행동에 연결하기' in world_text
novel=legacy_coherence['related_novel_review']
assert novel['whole_document_read'] and len(novel['text'].encode())==novel['bytes']
assert hashlib.sha256(novel['text'].encode()).hexdigest()==novel['sha256']
verify_recorded_source_hash(p/novel['path_relative_to_plan'],novel['sha256'])
assert len(novel['wiki_topic_snapshots'])==4
for topic in novel['wiki_topic_snapshots']:assert hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256'] and topic['whole_topic_read']
assert not novel['all_related_novels_reviewed'] and not novel['novel_rewritten'] and not novel['actual_participant_reading']
assert len(legacy_coherence['procurement_whole_document_reviews_pending'])==0
pending_procurement={entry['name'] for entry in procurement['files'] if not entry.get('whole_document_read')}
assert pending_procurement==set(legacy_coherence['procurement_whole_document_reviews_pending'])
assert len(ar['v1_3_review_preset_formulae'])==9
for name,values in ar['v1_3_review_preset_formulae'].items():assert sum(values)==ar['v1_3_review_preset_sums'][name]==30
assert (ar['v1_3_review_previous_G5_claim'],ar['earlier_v1_2_review_G5_formula_actual'],ar['quick_start_proposed_pages'])==(29,33,46)
assert (ar['update_plan_pilot_topics'],ar['update_plan_listed_directory_files'],ar['S07_layer_table_rows'],ar['S07_log_layer_count'])==(7,40,9,8)
assert '**선택 캠페인 — 구판의 추가 기업:**' in world_text
assert (ar['candidate_numbered_rows'],ar['candidate_active_systems'],ar['candidate_deleted_slots'])==(12,11,1)
assert ar['candidate_ADnD_reached_AC']==ar['candidate_ADnD_THAC0']-ar['candidate_ADnD_total_attack']==5
assert ar['candidate_ADnD_target_AC']>=ar['candidate_ADnD_reached_AC']
assert sum(ar['v1_3_Katie_stat_components'])==ar['v1_3_Katie_stats']==37
assert sum(ar['v1_3_Katie_purchase_components'])==ar['v1_3_Katie_purchase']==33
assert ar['v1_3_Katie_total']==ar['v1_3_Katie_stats']+30+ar['v1_3_Katie_purchase']==100
assert ar['v1_3_G6_guideline_total']==ar['v1_3_G6_guideline_stats']+ar['v1_3_G6_guideline_free']==70
assert (ar['v1_3_G0_from_all_ones_required'],ar['v1_3_G0_listed_stats'])==(24,16)
corrections=legacy_coherence['external_candidate_corrections']
assert len(corrections['references'])==10 and all(e['official_primary_source'] for e in corrections['references'])
assert not corrections['all_requested_systems_fully_reviewed'] and not corrections['arbitrary_star_ratings_are_empirical_scores']
assert corrections['RED_official_counterexample']=={'BODY':3,'WILL':8,'HP':40,'candidate_BODY_times_5':15}
design_text=(o/'00_제5판_설계기준.md').read_text()
assert '## 이전 후보군의 비교 근거 정정 — 제5판에 가져올 절차' in design_text
for ref in corrections['references']:assert ref['url'] in design_text and not ref['external_full_rulebook_review_complete']
r_attribution=legacy_coherence['arithmetic_source_attribution']
assert len(ar['v1_2_decision_preset_formulae'])==8
assert {k:sum(a) for k,a in ar['v1_2_decision_preset_formulae'].items()}==ar['v1_2_decision_preset_sums']
assert all(a==30 for a in ar['v1_2_decision_preset_sums'].values())
assert sum(ar['v1_2_decision_Katie_stat_components'])==37
assert sum(ar['v1_2_decision_Katie_purchase_components'])==33
assert ar['v1_2_decision_Katie_total']==37+30+33==100
assert sum(ar['v1_2_campaign_reward_components'])==ar['v1_2_campaign_reward_total']==34
assert (ar['v1_2_environment_label_grades'],ar['v1_2_environment_table_rows'],ar['v1_2_resistance_formula_example'])==(5,6,105)
assert r_attribution['previous_ambiguous_v1_2_G5_key_corrected'] and not r_attribution['original_archival_documents_rewritten']
assert len(legacy_coherence['v1_2_todo_current_mapping'])==10
assert '## 초기 결정에서 현재 분류로 — 무엇을 계승하는가' in design_text
assert len(procurement['files'])==23
assert {e['name'] for e in procurement['files']}=={e['name'] for e in legacy_coherence['source_snapshots']}
assert all(e['whole_document_read'] and e['baseline_hash_matches'] for e in procurement['files'])
assert sum(ar['v1_1_shin_warrior_components'])==29
assert sum(ar['v1_1_Katie_stat_components'])==37 and sum(ar['v1_1_Katie_preset_components'])==30
assert sum(ar['v1_1_Katie_printed_purchase_components'])==33
assert sum(ar['v1_1_Katie_price_corrected_purchase_components'])==34
assert ar['v1_1_Katie_printed_total']==37+30+33==100
assert ar['v1_1_Katie_price_corrected_total']==37+30+34==101
assert ar['v1_1_Katie_purchased_LCK_tokens']==2*ar['v1_1_Katie_purchased_LCK']==6
assert ar['v1_1_Katie_printed_LCK_tokens']==2*ar['v1_1_Katie_printed_LCK']==4
for points,oyat in [(ar['v1_1_crow_example_points'],ar['v1_1_crow_example_oyat']),(ar['v1_1_carbine_example_points'],ar['v1_1_carbine_example_oyat'])]:
 assert oyat/points<ar['v1_1_oyat_conversion_stated_min_per_point']
assert '## 조달 목록23개 전문 대조 완료와 남은 범위' in design_text
marking_sources=legacy_coherence['marking_source_preparation']
assert {e['topic'] for e in marking_sources['topics']}=={'0065','0068','0074'}
for topic in marking_sources['topics']:
 assert topic['whole_topic_read'] and hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256']
assert marking_sources['original_source_sha256']==legacy_coherence['original_sources'][0]['sha256']
assert not marking_sources['usable_marking_profiles_complete'] and not marking_sources['all_marking_functions_are_skill_percentage_bonuses']
assert not marking_sources['current_original_file_rehashed_this_pass'] and not marking_sources['actual_participant_playtest']
marking=json.loads((v/'고유효과_프로필.json').read_text())['marking']
assert marking['id']=='FEWK-MARK-01' and not marking['all_original_marking_functions_complete']
assert not marking['all_markings_are_percentage_bonuses'] and marking['additional_person_stats']==[]
assert marking['boost']['skill']=='운동' and marking['travel']['movement_type']=='same_body_transfer'
assert marking['summon']['target_actual_acceptance_required'] and not marking['summon']['target_main_actions_reset']
assert marking['seal']['ordinary_melee_defense'] and marking['seal']['damage_on_success']==0
assert '<a id="fewk-marking"></a>' in core and '## 31. 도안의 제작' in (o/'12_룰시트와캐릭터시트.md').read_text()
d['current_marking_profiles']={'id':marking['id'],'profiles':4,'core':'v0.28','world':'v0.40','sheet':'v0.28','sheet_sections':31,'checks_passed':results['고유효과_검증.py']['marking_checks_passed'],'boundary_cases':results['고유효과_검증.py']['marking_boundary_cases'],'all_marking_functions_complete':False,'actual_participant_playtest':False}
vessel_sources=legacy_coherence['vessel_source_review']
assert {e['topic'] for e in vessel_sources['topics']}=={'0088','0052','0061','0067'}
for e in vessel_sources['topics']:
 assert e['whole_topic_read'] and hashlib.sha256(e['text'].encode()).hexdigest()==e['sha256']
assert vessel_sources['original_source_sha256']==legacy_coherence['original_sources'][0]['sha256']
assert (vessel_sources['neptune_engine_count'],vessel_sources['Warpeace_airship_count'],vessel_sources['Warpeace_shindan_count'])==(6,1,2)
assert not vessel_sources['house_storage_is_free_person_gateway'] and not vessel_sources['physical_hull_and_black_protection_are_same']
assert not vessel_sources['current_original_file_rehashed_this_pass'] and not vessel_sources['actual_participant_playtest']
vessels=json.loads((v/'운송_프로필.json').read_text())['vessels']
assert vessels['id']=='FEWK-VESSEL-01' and len(vessels['models'])==2 and vessels['new_universal_stats']==[]
assert vessels['drive']['one_craft_move_per_round'] and vessels['drive']['passengers_deck_movement_kept']
assert not vessels['protection']['blocks_P_L_or_collision'] and not vessels['actual_participant_playtest']
assert '<a id="fewk-vessel"></a>' in core and '<a id="fewk-vessel-sheet"></a>' in (o/'12_룰시트와캐릭터시트.md').read_text()
assert (road['vessel_checks_passed'],road['vessel_total_boundary_cases'])==(54,1328)
assert not road['all_ships_aircraft_and_vehicle_IO_complete'] and not road['vessel_actual_participant_playtest']
d['current_vessel_profiles']={'id':vessels['id'],'models':2,'core':'v0.48','world':'v0.99','sheet':'v0.44','sheet_sections':32,'checks_passed':road['vessel_checks_passed'],'boundary_cases':road['vessel_total_boundary_cases'],'all_ships_aircraft_and_vehicle_IO_complete':False,'actual_participant_playtest':False}

archive_review=legacy_coherence['older_framework_archive_review']
assert archive_review['whole_documents_read']==archive_review['folder_documents_in_this_scope']==4
assert archive_review['whole_archive_four_document_review_complete'] and not archive_review['all_older_unique_sources_reviewed']
assert not archive_review['current_engine_changed'] and not archive_review['actual_external_expert_or_participant_evidence']
additional_procurement=json.loads((o/'이전자료_조달목록.json').read_text())['additional_older_unique_files']
framework_procurement=[e for e in additional_procurement if e['id'].startswith('LEG-ARCH-')]
assert len(framework_procurement)==4 and all(e['whole_document_read'] for e in framework_procurement)
for e in archive_review['snapshots']:
 assert e['whole_document_read'] and hashlib.sha256(e['text'].encode()).hexdigest()==e['sha256']
 assert e['migration_decisions']
 assert any(row['name']==e['name'] and row['sha256']==e['sha256'] for row in additional_procurement)
status_review=json.loads((v/'현재_원고상태.json').read_text())
assert status_review['semantic_review_of_all_git_changes_completed']
changes=status_review['current_changed_files_semantic_review']
assert changes['head']==status_review['head']=='da9ef735022517779fcbd3865e43efaa98e0094d'
assert changes['complete_patch_read'] and hashlib.sha256(changes['patch'].encode()).hexdigest()==changes['patch_sha256']
assert (changes['tracked_files_reviewed'],changes['link_only_files'],changes['semantic_or_tool_files'],changes['changed_reference_manuscript_hashes_checked'])==(50,39,11,49)
assert len(changes['entries'])==50 and len(status_review['status_entries'])==50
assert not changes['all_358_current_file_hashes_rechecked'] and not changes['fifth_content_published'] and not changes['actual_participant_playtest']
for item in changes['entries']:
 assert item['complete_patch_read'] and item['fifth_migration_decision']
 assert hash_current(p/status_review['repo_relative']/item['path'])==item['sha256']
 if item['source_id']:
  assert item['reference_hash_matches']
  assert any(e['id']==item['source_id'] and e['observed_sha256']==item['sha256'] for e in ledger['files'])
assert changes['converter_boundary_verification']['checks_passed']==4
assert not changes['converter_boundary_verification']['real_358_file_export_performed']
script_entry=next(e for e in changes['entries'] if e['path']=='scripts/convert.py')
assert script_entry['sha256']==changes['converter_boundary_verification']['script_sha256']
d['current_older_framework_archive_review']={'date':'2026-10-06','whole_documents':4,'limited_arithmetic_checks':17,'old_issue_count':50,'actual_external_expert_evidence':False,'all_older_unique_sources_reviewed':False,'actual_participant_playtest':False}
d['current_git_change_review']={'date':'2026-10-06','head':changes['head'],'files':50,'link_only':39,'semantic_or_tool':11,'current_reference_hashes_checked':49,'converter_boundary_checks':4,'all_358_current_hashes_checked':False,'fifth_content_published':False}
second_review=legacy_coherence['second_edition_reader_review']
assert (second_review['acquired_documents'],second_review['whole_documents_read'],len(second_review['whole_document_reviews_pending']))==(9,9,0)
assert second_review['all_second_edition_documents_reviewed'] and not second_review['all_older_unique_sources_reviewed']
assert not second_review['current_engine_changed'] and not second_review['actual_participant_reading']
second_procurement=[e for e in additional_procurement if e['id'].startswith('LEG-SECOND-')]
assert len(second_procurement)==9 and sum(e['whole_document_read'] for e in second_procurement)==9
assert {e['name'] for e in second_procurement if not e['whole_document_read']}==set(second_review['whole_document_reviews_pending'])
for e in second_review['snapshots']:
 assert e['whole_document_read'] and len(e['text'].encode())==e['bytes'] and hashlib.sha256(e['text'].encode()).hexdigest()==e['sha256']
 assert e['migration_decisions']['adopt'] and e['migration_decisions']['correct']
 assert any(row['name']==e['name'] and row['sha256']==e['sha256'] and row['whole_document_read'] for row in second_procurement)
nav=world_text.split('| 읽고 싶은 내용 | 본문 위치 |',1)[1].split('<a id="fewk-world-01">',1)[0]
navrows=[line for line in nav.splitlines() if line.startswith('| ')];coverage=[]
assert len(navrows)==27
for row in navrows:
 match=re.search(r'(\d+)(?:~(\d+))?장',row);assert match,row
 low=int(match[1]);high=int(match[2] or match[1]);coverage+=list(range(low,high+1))
 assert '#fewk-world-'+str(low).zfill(2) in row
assert coverage==list(range(1,78))
assert '### 이름과 행동을 나누어 기록하기' in world_text and '원본0006 「샤이닝」을 요약한 도입' in world_text
for qdoc in docs:
 ids=re.findall(r'<a id="([^"]+)"',qdoc.read_text());assert len(ids)==len(set(ids)),qdoc
arith=second_review['arithmetic']
assert arith['mass_70kg_za']==70*1000 and arith['mass_70kg_yang']==70*1000/10000
assert arith['outline_sections']==sum([3,7,8,5,8,3]) and arith['outline_proposed_pages']==160
assert arith['anthology_lines']==2190 and arith['manifest_independent_interval_total_range_percent']==[94,106]
d['current_second_edition_reader_review']={'date':'2026-10-06','acquired_documents':9,'whole_documents':9,'whole_reviews_pending':0,'limited_arithmetic_checks':18,'world_version':'v0.43','navigation_rows':27,'navigation_chapter_coverage':77,'all_older_unique_sources_reviewed':False,'actual_participant_reading':False}
primary_noene=second_review['noene_and_mechatronics_primary_recheck']
assert primary_noene['current_file_hash_matches_existing_reference'] and not primary_noene['whole_file_semantically_reviewed']
for e in primary_noene['ranges']:
 assert len(e['text'].split('\n'))==e['end']-e['start']+1
 assert hashlib.sha256(e['text'].encode()).hexdigest()==e['text_sha256']
verify_recorded_source_hash(o/primary_noene['path_relative_to_fifth'],primary_noene['sha256'])
assert arith['handover_density_0_to_6']==[10**24//10000**i for i in range(7)]
assert (arith['Codex_forward_rows'],arith['Codex_reverse_rows'],arith['Codex_total_rows'])==(35,10,45)
codex_text=next(e['text'] for e in second_review['snapshots'] if e['name']=='Volume1_World_Codex_목차.md')
forward=codex_text.split('### 4-1. 서사(V1)',1)[1].split('### 4-2.',1)[0]
reverse=codex_text.split('### 4-2. 수치(V2)',1)[1].split('### 4-3.',1)[0]
assert len([line for line in forward.splitlines() if line.startswith('| §')])==arith['Codex_forward_rows']
assert len([line for line in reverse.splitlines() if line.startswith('| §')])==arith['Codex_reverse_rows']
assert '<a id="fewk-noene"></a>' in world_text and '<a id="fewk-cafe-stranger"></a>' in world_text
assert '### 선택 도입 — 카페의 이방인' in world_text
assert '현지의 시계가 얼마나 흐르는지와 존재 유지 자원이 얼마나 빨리 소모되는지는 서로 다른 조건' in world_text
editorial_snapshot=next(e for e in second_review['snapshots'] if e['name']=='편집규칙.md')
assert editorial_snapshot['whole_document_read'] and len(editorial_snapshot['text'].splitlines())==2137
page_section=editorial_snapshot['text'].split('### 12-1.',1)[1].split('### 12-2.',1)[0]
page_rows=[]
for line in page_section.splitlines():
 match=re.match(r'\| ([^|]+) \| (\d+) \| (\d+) \|$',line)
 if match:page_rows.append({'name':match[1],'A4':int(match[2]),'B5':int(match[3])})
assert page_rows==second_review['editorial_arithmetic']['page_rows'] and len(page_rows)==23
assert not second_review['editorial_arithmetic']['actual_render_or_publication_pages_verified']
assert not second_review['editorial_current_implementation']['actual_participant_playtest']
assert not second_review['editorial_current_implementation']['actual_async_community_test']
assert '<a id="fewk-reading-example"></a>' in core
sheet_text=(o/'12_룰시트와캐릭터시트.md').read_text()
assert '<a id="fewk-reading-example-sheet"></a>' in sheet_text
assert '<a id="fewk-online-sheet"></a>' in sheet_text
assert '예시 v12' in sheet_text and '예시 확정 상태: v13' in sheet_text
assert '가상 플레이 대본' in core and '작성 예' in sheet_text
assert '35<62≤70' in core and '최종 목표70 / 좋은35 / 탁월14' in sheet_text
current_framework=legacy_coherence['current_framework_spec_review']
assert current_framework['whole_documents_read']==3 and len(current_framework['snapshots'])==3
assert not current_framework['all_older_unique_sources_reviewed'] and not current_framework['current_engine_changed'] and not current_framework['actual_participant_playtest']
for entry in current_framework['snapshots']:
 data=entry['text'].encode()
 assert entry['whole_document_read'] and len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
 verify_recorded_source_hash(o/entry['path_relative_to_fifth'],entry['sha256'])
inventory=legacy_coherence['bounded_older_source_inventory']
assert len(inventory['families'])==4 and len(inventory['files'])==90
assert inventory['whole_documents_reviewed_this_pass']==3 and inventory['semantic_review_pending_in_this_inventory_pass']==87
assert not inventory['other_directory_inventory_complete'] and not inventory['all_older_unique_sources_reviewed']
assert sum(e['whole_document_reviewed_this_pass'] for e in inventory['files'])==3
for entry in inventory['files']:
 assert entry['text_acquired'] and (p/entry['path_relative_to_plan']).stat().st_size==entry['bytes']
 verify_recorded_source_hash(p/entry['path_relative_to_plan'],entry['sha256'])
assert legacy['current_framework_spec_arithmetic']['documents']==3 and legacy['current_framework_spec_arithmetic']['checks_passed']==12
assert legacy['current_framework_spec_arithmetic']['minimum_stat_cost_for_old_six_stat_mean_6_to_8']==120
assert not legacy['current_framework_spec_arithmetic']['old_100point_build_rewritten']
d['current_framework_spec_review']={'documents_whole_read':3,'arithmetic_checks':12,'current_engine_changed':False,'actual_participant_playtest':False}
d['bounded_older_source_inventory']={'families':4,'files_acquired_and_hashed':90,'cumulative_whole_documents_reviewed':90,'cumulative_semantic_pending':0,'initial_framework_review_documents':3,'latest_first_character_review_documents':4,'all_older_unique_sources_reviewed':False}
first_character=legacy_coherence['first_edition_character_review']
assert first_character['whole_documents_read']==4 and len(first_character['snapshots'])==4
assert len(first_character['related_novels_reviewed'])==3 and not first_character['all_related_novels_reviewed']
assert not first_character['all_older_unique_sources_reviewed'] and not first_character['current_engine_changed']
assert not first_character['actual_participant_reading'] and not first_character['actual_participant_playtest'] and not first_character['actual_async_community_test']
assert first_character['new_mechanical_parameter_values']==[] and first_character['versions']['World']=='0.44'
for entry in first_character['snapshots']:
 data=entry['text'].encode()
 assert entry['whole_document_read'] and len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
 verify_recorded_source_hash(o/entry['path_relative_to_fifth'],entry['sha256'])
 assert any(row['name']==entry['name'] and row['sha256']==entry['sha256'] and row['whole_document_read'] for row in additional_procurement)
for entry in first_character['related_novels_reviewed']:
 data=entry['text'].encode()
 assert entry['whole_document_read'] and len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
 assert not entry['novel_rewritten'] and not entry['full_setting_verified'] and not entry['actual_participant_reading']
 verify_recorded_source_hash(p/entry['path_relative_to_plan'],entry['sha256'])
for key,count in [('primary_topic_recheck',9),('wiki_topic_recheck',8)]:
 record=first_character[key]
 assert len(record['topics'])==count
 path=p/record['source_path_relative_to_plan'];sha=record.get('sha256',record.get('source_sha256'))
 verify_recorded_source_hash(path,sha)
 current_text=path.read_text()
 for entry in record['topics']:
  assert entry['whole_topic_read'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
  assert entry['text'] in current_text
assert inventory['cumulative_whole_documents_reviewed']==90 and inventory['cumulative_semantic_pending_in_bounded_inventory']==0
assert sum(e['whole_document_reviewed_cumulatively'] for e in inventory['files'])==90
assert legacy['first_character_source_arithmetic']['checks_passed']==2 and not legacy['first_character_source_arithmetic']['current_engine_changed']
world=(o/'11_WorldLorebook.md').read_text()
for phrase in ['숙자의 선택과 관련 소설의 다른 장면','왕조의 전언과 오늘의 망명자','기타를 물려받는 사람과 다시 불리는 이름','관련 소설065에서 가져오는 네 사람의 이유','하트의 여왕 — 돌아갈 몸을 잃은 뒤의 삶','2대 크리스·레드몽키즈의 리더','카일 블랙의 마이크 테스트 발언','인간처럼 고지능 존재나 문명이 없었다고 명시']:
 assert phrase in world,phrase
d['current_first_edition_character_review']={'World':'v0.44','Design':'v0.68','character_documents_whole_reviewed':4,'primary_whole_topics':9,'wiki_whole_topics':8,'related_novels_whole_reviewed':['012','064','065'],'limited_arithmetic_checks':2,'current_engine_changed':False,'all_related_novels_reviewed':False,'all_older_unique_sources_reviewed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
d['current_editorial_reader_example']={'easy_current_chars':len(easy),'historical_easy_P019_chars':daily['easy_current_chars'],'Core':'v0.48','Easy':'P v0.31','Sheet':'v0.44','World':'v0.99','scene':'CAFE-READ','skill':50,'situation':20,'target':70,'good':35,'exceptional':14,'roll':62,'IC_seconds':5,'source_state_example_version':12,'accepted_example_version':13,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False,'print_layout_delivered':False}
profession_review=legacy_coherence['first_edition_profession_review']
assert profession_review['whole_documents_read']==len(profession_review['snapshots'])==3
assert not profession_review['all_related_novels_reviewed'] and not profession_review['all_older_unique_sources_reviewed'] and not profession_review['current_engine_changed']
assert profession_review['new_mechanical_parameter_values']==[]
assert not profession_review['actual_participant_reading'] and not profession_review['actual_participant_playtest'] and not profession_review['actual_async_community_test']
assert profession_review['versions']['World']=='v0.45' and profession_review['versions']['Design']=='v0.70'
for snapshot in profession_review['snapshots']:
 data=snapshot['text'].encode()
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256']
 assert snapshot['migration_decisions']
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
assert {row['id'] for row in profession_review['related_novels_reviewed']}=={'049','050'}
for novel in profession_review['related_novels_reviewed']:
 data=novel['text'].encode()
 assert novel['whole_document_read'] and len(data)==novel['bytes'] and hashlib.sha256(data).hexdigest()==novel['sha256']
 assert hash_current(p/novel['path_relative_to_plan'])==novel['sha256']
for source,count in [(profession_review['primary_topic_recheck'],8),(profession_review['wiki_topic_recheck'],6)]:
 assert len(source['topics'])==count
 assert hash_current(p/source['source_path_relative_to_plan'])==source['source_sha256']
 source_text=(p/source['source_path_relative_to_plan']).read_text()
 for topic in source['topics']:
  assert topic['whole_topic_read'] and hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256'] and topic['text'] in source_text
world_text=(o/'11_WorldLorebook.md').read_text()
for required in ['직업과 실제 기능','운영자 자료의 읽기','솔라 — 유지하는 사람과 곁에 남는 사람','내일의 수리를 함께 정하기','자발적 절제나 죄책감은 낮은 에고나 BP의 결과가 아닙니다']:
 assert required in world_text,required
assert len(additional_procurement)==117 and all(e['whole_document_read'] for e in additional_procurement)
d['current_first_edition_profession_review']={'World':'v0.45','Design':'v0.70','whole_documents_reviewed':3,'primary_whole_topics':8,'wiki_whole_topics':6,'related_novels_whole_reviewed':['049','050'],'bounded_cumulative_whole_reviews':10,'bounded_cumulative_pending':80,'current_engine_changed':False,'all_related_novels_reviewed':False,'all_older_unique_sources_reviewed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
physics=legacy_coherence['world_physics_byte_review']
assert physics['whole_documents_read']==len(physics['snapshots'])==3
assert (physics['physics_family_documents_reviewed'],physics['physics_family_documents_pending'])==(3,13)
assert physics['versions']['World']=='v0.46' and physics['versions']['Design']=='v0.72'
assert physics['new_mechanical_parameter_values']==[]
for flag in ['all_world_physics_documents_reviewed','all_older_unique_sources_reviewed','current_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not physics[flag]
for snapshot in physics['snapshots']:
 data=snapshot['text'].encode()
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
for key,count in [('primary_topic_recheck',4),('wiki_topic_recheck',8)]:
 source=physics[key]
 assert len(source['topics'])==count and hash_current(p/source['source_path_relative_to_plan'])==source['source_sha256']
 source_text=(p/source['source_path_relative_to_plan']).read_text()
 for topic in source['topics']:
  assert topic['whole_topic_read'] and hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256'] and topic['text'] in source_text
physics_math=legacy['world_physics_byte_arithmetic']
assert (physics_math['documents'],physics_math['checks_passed'],physics_math['actual_value_categories'])==(3,17,8)
assert physics_math['mass_70kg_yang']['numerator']==7 and physics_math['mass_70kg_yang']['denominator']==1
assert (physics_math['initial_subject_20jaa_times30'],physics_math['wiki_subject_21jaa_times30'])==(600,630)
assert not physics_math['current_engine_changed'] and not physics_math['actual_participant_playtest']
assert '### 기록의 단위와 살아 있는 주체' in world_text
assert '혼백과 생명의 식별은 출처와 기술 모델의 차이를 함께 확인합니다.' in world_text
d['current_world_physics_byte_review']={'World':'v0.46','Design':'v0.72','whole_documents_reviewed':3,'primary_whole_topics':4,'wiki_whole_topics':8,'limited_arithmetic_checks':17,'physics_family_pending':13,'bounded_cumulative_whole_reviews':13,'bounded_cumulative_pending':77,'current_engine_changed':False,'all_older_unique_sources_reviewed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
dimension_ego=legacy_coherence['world_physics_dimension_ego_review']
assert dimension_ego['whole_documents_read']==len(dimension_ego['snapshots'])==2
assert (dimension_ego['physics_family_cumulative_documents_reviewed'],dimension_ego['physics_family_documents_pending'])==(5,11)
assert dimension_ego['versions']['World']=='v0.47' and dimension_ego['versions']['Design']=='v0.73'
assert dimension_ego['new_mechanical_parameter_values']==[]
for flag in ['all_world_physics_documents_reviewed','all_older_unique_sources_reviewed','current_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not dimension_ego[flag]
for snapshot in dimension_ego['snapshots']:
 data=snapshot['text'].encode()
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
for key,count in [('primary_topic_recheck',3),('wiki_topic_recheck',11)]:
 source=dimension_ego[key]
 assert len(source['topics'])==count and hash_current(p/source['source_path_relative_to_plan'])==source['source_sha256']
 source_text=(p/source['source_path_relative_to_plan']).read_text()
 for topic in source['topics']:
  assert topic['whole_topic_read'] and hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256'] and topic['text'] in source_text
math=legacy['world_physics_dimension_ego_arithmetic']
assert (math['documents'],math['checks_passed'])==(2,20)
assert math['five_day_ego_loss']['numerator']==5 and math['thirty_minute_fraction_used']['denominator']==5
assert math['ego8_consistent_remaining_hours']['numerator']==96 and math['ego8_consistent_remaining_hours']['denominator']==5
assert (math['ego8_consistent_six_hour_loss']['numerator'],math['ego8_consistent_six_hour_loss']['denominator'])==(5,2)
assert math['ego8_unscaled_six_hour_loss']['numerator']==2 and math['BP30_actual_old_band']==['Broken','-3','-10','-15']
assert not math['current_engine_changed'] and not math['actual_participant_playtest']
for phrase in ['### 남아 있는 힘과 돌아갈 시간','### 낮은 밀도에서도 집은 실제 집이다','### 사람 안의 세계와 천체의 신화','2.5를 써5.5가 남습니다.','참가자는 자기 확인의 표현과 다음 행동을 고릅니다.']:
 assert phrase in world_text,phrase
d['current_world_physics_dimension_ego_review']={'World':'v0.47','Design':'v0.73','whole_documents_reviewed':2,'primary_whole_topics':3,'wiki_whole_topics':11,'limited_arithmetic_checks':20,'physics_family_cumulative_whole_reviews':5,'physics_family_pending':11,'bounded_cumulative_whole_reviews':15,'bounded_cumulative_pending':75,'current_engine_changed':False,'all_older_unique_sources_reviewed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
black_noene=legacy_coherence['world_physics_black_noene_review']
assert black_noene['whole_documents_read']==len(black_noene['snapshots'])==2
assert (black_noene['physics_family_cumulative_documents_reviewed'],black_noene['physics_family_documents_pending'])==(7,9)
assert black_noene['versions']['World']=='v0.48' and black_noene['versions']['Design']=='v0.74'
assert black_noene['new_mechanical_parameter_values']==[]
for flag in ['all_world_physics_documents_reviewed','all_older_unique_sources_reviewed','current_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not black_noene[flag]
for snapshot in black_noene['snapshots']:
 data=snapshot['text'].encode()
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
for key,count in [('primary_topic_recheck',5),('wiki_topic_recheck',11)]:
 source=black_noene[key]
 assert len(source['topics'])==count and hash_current(p/source['source_path_relative_to_plan'])==source['source_sha256']
 source_text=(p/source['source_path_relative_to_plan']).read_text()
 for topic in source['topics']:
  assert topic['whole_topic_read'] and hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256'] and topic['text'] in source_text
primary_topics=black_noene['primary_topic_recheck']['topics']
assert black_noene['primary_topics_with_body_reviewed']==sum(t['body_available'] for t in primary_topics)==4
assert black_noene['primary_heading_only_topics']==[t['topic'] for t in primary_topics if t['heading_only']]==['0102']
heading=next(t for t in primary_topics if t['topic']=='0102')
assert not heading['body_available'] and len(heading['text'].splitlines())==1 and len(heading['text'])==66
raw_source=(p/black_noene['primary_topic_recheck']['source_path_relative_to_plan']).read_text()
raw_headers=list(re.finditer(r'(?m)^(?:\ufeff)?"?FEWK;\s*(\d{4})',raw_source))
heading_occurrences=[]
for i,h in enumerate(raw_headers):
 if h.group(1)=='0102':heading_occurrences.append(raw_source[h.start():raw_headers[i+1].start() if i+1<len(raw_headers) else len(raw_source)])
assert heading_occurrences==[heading['text'],heading['text']]
for phrase in ['### 뇌네와 접속 도구, 해킹을 함께 읽기','### 같은 흑공을 서로 다른 일에 쓰는 사람들','전임 탐사자의 지도','교육용 흑공샘플','개인별 발현 차이','파워셀의 보존 안정성이 모든 샘플의 접촉 안전성을 보증하지는 않습니다.']:
 assert phrase in world_text,phrase
d['current_world_physics_black_noene_review']={'World':'v0.48','Design':'v0.74','whole_documents_reviewed':2,'primary_topics_with_body_reviewed':4,'primary_heading_only_topics':['0102'],'wiki_whole_topics':11,'new_arithmetic_checks_added':0,'physics_family_cumulative_whole_reviews':7,'physics_family_pending':9,'bounded_cumulative_whole_reviews':17,'bounded_cumulative_pending':73,'current_engine_changed':False,'all_older_unique_sources_reviewed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
sinki=legacy_coherence['world_physics_sinki_review']
assert sinki['whole_documents_read']==len(sinki['snapshots'])==1
assert (sinki['physics_family_cumulative_documents_reviewed'],sinki['physics_family_documents_pending'])==(8,8)
assert sinki['versions']['World']=='v0.49' and sinki['versions']['Design']=='v0.75'
assert sinki['new_mechanical_parameter_values']==[]
for flag in ['all_world_physics_documents_reviewed','all_older_unique_sources_reviewed','current_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not sinki[flag]
for snapshot in sinki['snapshots']:
 data=snapshot['text'].encode()
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert len(snapshot['text'].splitlines())==872
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
for key,count in [('primary_topic_recheck',4),('wiki_topic_recheck',7)]:
 source=sinki[key]
 assert len(source['topics'])==count and hash_current(p/source['source_path_relative_to_plan'])==source['source_sha256']
 source_text=(p/source['source_path_relative_to_plan']).read_text()
 for topic in source['topics']:
  assert topic['whole_topic_read'] and hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256'] and topic['text'] in source_text
assert sinki['primary_topics_with_body_reviewed']==4
math=legacy['world_physics_sinki_arithmetic']
assert (math['documents'],math['wiki_unit_topics'],math['checks_passed'])==(1,1,8)
assert math['million_times_subject_bytes']==21*10**30 and math['subject21jaa_bytes']==21*10**24
assert (math['million_times_subject_yang']['numerator'],math['million_times_subject_yang']['denominator'])==(2100,1)
assert math['unadjusted_to_printed_21yang_ratio']['numerator']==100 and math['comparison_10000cell_kcal']==10000 and math['comparison_10000cell_OYAT']['numerator']==10
for flag in ['post_LCC_21yang_verified','real_nutrition_or_soul_measurement_verified','current_engine_changed','actual_participant_playtest']:
 assert not math[flag]
for phrase in ['### 신기를 사용하는 행동도 한 목록에 적기','### 유대와 공급이 함께 만드는 행동','신기와 매개는 가능한 기능과 실제 공급을','유대는 약속과 함께 겪은 사건으로 표현합니다.','오얏10개','초심자의 저장량에도 개인차가 있습니다.']:
 assert phrase in world_text,phrase
d['current_world_physics_sinki_review']={'World':'v0.49','Design':'v0.75','whole_documents_reviewed':1,'whole_source_lines':872,'primary_whole_topics':4,'wiki_whole_topics':7,'limited_arithmetic_checks':8,'physics_family_cumulative_whole_reviews':8,'physics_family_pending':8,'bounded_cumulative_whole_reviews':18,'bounded_cumulative_pending':72,'current_engine_changed':False,'all_older_unique_sources_reviewed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
power_artificial=legacy_coherence['world_physics_power_artificial_review']
assert power_artificial['whole_documents_read']==len(power_artificial['snapshots'])==2
assert (power_artificial['physics_family_cumulative_documents_reviewed'],power_artificial['physics_family_documents_pending'])==(10,6)
assert power_artificial['versions']['World']=='v0.50' and power_artificial['versions']['Design']=='v0.76'
assert power_artificial['new_mechanical_parameter_values']==[]
for flag in ['all_world_physics_documents_reviewed','all_older_unique_sources_reviewed','current_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not power_artificial[flag]
for snapshot in power_artificial['snapshots']:
 data=snapshot['text'].encode()
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert len(snapshot['text'].splitlines())==({'08_':893,'10_':506}[snapshot['name'][:3]])
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
for key,count in [('primary_topic_recheck',5),('wiki_topic_recheck',15)]:
 source=power_artificial[key]
 assert len(source['topics'])==count and hash_current(p/source['source_path_relative_to_plan'])==source['source_sha256']
 source_text=(p/source['source_path_relative_to_plan']).read_text()
 for topic in source['topics']:
  assert topic['whole_topic_read'] and hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256'] and topic['text'] in source_text
assert power_artificial['primary_topics_with_body_reviewed']==5
math=legacy['world_physics_power_arithmetic']
assert (math['documents'],math['wiki_unit_topics'],math['checks_passed'])==(2,1,8)
assert (math['old_Dolchip_actual_spec_rows'],math['old_Dolchip_printed_spec_count'])==(7,6)
assert math['wiki_canister_solution_kg']['numerator']==20 and math['wiki_drum_solution_kg']['numerator']==200 and math['old_canister_mass_mismatch_ratio']['numerator']==10
assert [x['numerator'] for x in math['old_C_cell_consumption_price_range_OYAT']]==[9,12]
assert not math['current_engine_changed'] and not math['actual_participant_playtest']
for phrase in ['### 다이브의 세 비유를 지금의 IO에 연결하기','### 동력 관로와 정보 접근은 다른 일이다','그릇 | 주체를 보낸 뒤 물질계에 남는 몸','진흙 | 목적지에서 주체를 담을 몸의 구성','흑공그리드','흑공정제용액이 흐르는 관로','크기·무게와 충전량에 큰 상관이 없다고','와치엔진으로 발전한 계보']:
 assert phrase in world_text,phrase
d['current_world_physics_power_artificial_review']={'World':'v0.50','Design':'v0.76','whole_documents_reviewed':2,'whole_source_lines':[893,506],'primary_whole_topics':5,'wiki_whole_topics':15,'limited_arithmetic_checks':8,'physics_family_cumulative_whole_reviews':10,'physics_family_pending':6,'bounded_cumulative_whole_reviews':20,'bounded_cumulative_pending':70,'current_engine_changed':False,'all_older_unique_sources_reviewed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
causal_time=legacy_coherence['world_physics_causal_time_review']
assert causal_time['whole_documents_read']==len(causal_time['snapshots'])==3
assert (causal_time['physics_family_cumulative_documents_reviewed'],causal_time['physics_family_documents_pending'])==(13,3)
assert causal_time['versions']['World']=='v0.51' and causal_time['versions']['Design']=='v0.77'
assert causal_time['new_mechanical_parameter_values']==[]
for flag in ['all_world_physics_documents_reviewed','all_older_unique_sources_reviewed','current_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not causal_time[flag]
for snapshot in causal_time['snapshots']:
 data=snapshot['text'].encode()
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert len(snapshot['text'].splitlines())==({'06_':503,'09_':504,'12_':470}[snapshot['name'][:3]])
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
for key,count in [('primary_topic_recheck',5),('wiki_topic_recheck',15)]:
 source=causal_time[key]
 assert len(source['topics'])==count and hash_current(p/source['source_path_relative_to_plan'])==source['source_sha256']
 source_text=(p/source['source_path_relative_to_plan']).read_text()
 for topic in source['topics']:
  assert topic['whole_topic_read'] and hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256'] and topic['text'] in source_text
assert causal_time['primary_topics_with_body_reviewed']==5
math=legacy['world_physics_causal_time_arithmetic']
assert (math['documents'],math['checks_passed'])==(3,8)
assert math['printed_adult_jaa']['numerator']==7000 and math['old_Mokgaebi_table_widths']==[20,20,20,20,15,5]
assert [(x['numerator'],x['denominator']) for x in math['old_cost_range_to_printed_mass_ratio']]==[(600,7),(900,7)]
assert [(x['numerator'],x['denominator']) for x in math['old_cost_range_to_corrected_70kg_ratio']]==[(60,7),(90,7)]
assert (math['old_Consumption_table_fraction']['numerator'],math['old_Consumption_table_fraction']['denominator'])==(1,20)
assert not math['current_engine_changed'] and not math['actual_participant_playtest']
for phrase in ['### 관측과 설명, 실제 보정의 범위','### 다른 때를 다녀온 사람의 생활','신규 도입 — 남겨 둔 약속','바이트 장부·트랜잭션·엔트로피','그 질서를 설명하려는 모델','서술 속 회상도 그 사람이 이미 겪은 일과 준비를 보여 주며']:
 assert phrase in world_text,phrase
d['current_world_physics_causal_time_review']={'World':'v0.51','Design':'v0.77','whole_documents_reviewed':3,'whole_source_lines':[503,504,470],'primary_whole_topics':5,'wiki_whole_topics':15,'limited_arithmetic_checks':8,'physics_family_cumulative_whole_reviews':13,'physics_family_pending':3,'bounded_cumulative_whole_reviews':23,'bounded_cumulative_pending':67,'current_engine_changed':False,'all_older_unique_sources_reviewed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
index_audit=legacy_coherence['world_physics_index_audit_review']
assert index_audit['whole_documents_read']==len(index_audit['snapshots'])==3
assert (index_audit['physics_family_cumulative_documents_reviewed'],index_audit['physics_family_documents_pending'])==(16,0)
assert index_audit['versions']['World']=='v0.52' and index_audit['versions']['Design']=='v0.78'
assert index_audit['new_mechanical_parameter_values']==[] and index_audit['all_world_physics_documents_reviewed']
for flag in ['all_older_unique_sources_reviewed','current_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not index_audit[flag]
for key in ['new_primary_topics_whole_read','new_wiki_topics_whole_read','new_related_novels_whole_read']:
 assert index_audit[key]==0
for snapshot in index_audit['snapshots']:
 data=snapshot['text'].encode()
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert len(snapshot['text'].splitlines())=={'11_용어_색인.md':538,'README.md':296,'_Consistency_Check.md':461}[snapshot['name']]
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
family=index_audit['physics_family_sources']
assert len(family)==len({e['path_relative_to_plan'] for e in family})==16
for entry in family:
 source=p/entry['path_relative_to_plan']
 assert source.stat().st_size==entry['bytes'] and hash_current(source)==entry['sha256'] and entry['whole_document_read']
 record=legacy_coherence[entry['whole_review_evidence']]
 assert any(e['sha256']==entry['sha256'] and e['path_relative_to_plan']==entry['path_relative_to_plan'] and e['whole_document_read'] for e in record['snapshots'])
physics_inventory=[e for e in inventory['files'] if 'World Physics' in e['path_relative_to_plan']]
assert len(physics_inventory)==16 and all(e['whole_document_reviewed_cumulatively'] for e in physics_inventory)
assert {e['path_relative_to_plan'] for e in family}=={e['path_relative_to_plan'] for e in physics_inventory}
assert len(index_audit['legacy_code_map'])==len({e['code'] for e in index_audit['legacy_code_map']})==102
for entry in index_audit['legacy_code_map']:
 assert entry['current_world_anchor'] in world_text and entry['migration_decision'] and entry['current_role']
 assert not entry['legacy_number_imported_to_current_engine']
 assert hash_current(p/entry['body_source_path_relative_to_plan'])==entry['body_source_sha256']
 record=legacy_coherence[entry['prior_whole_document_evidence']]
 assert any(e['sha256']==entry['body_source_sha256'] and entry['code'] in e['text'] and e['whole_document_read'] for e in record['snapshots'])
metrics=index_audit['metrics']
assert (metrics['directory_markdown_files'],metrics['index_base_law_rows'],metrics['index_addendum_law_rows'],metrics['index_unique_codes'])==(16,99,3,102)
assert (metrics['report_file_table_rows'],metrics['readme_file_table_rows'],metrics['report_citation_rows'],metrics['report_inherited_citation_rows'],metrics['report_new_citation_rows'])==(15,14,17,16,1)
assert (metrics['external_analogy_rows'],metrics['report_label_rows'],metrics['report_label_unique_codes'],metrics['literal_TN_matching_lines_in_01_to_10'])==(19,19,22,3)
assert metrics['readme_still_allocates_PHYS_A']
counts=legacy['world_physics_index_counts']
assert counts['checks_passed']==18 and counts['index_code_mappings']==102 and counts['metrics']==metrics
assert not counts['current_engine_changed'] and not counts['actual_participant_playtest']
for phrase in ['### 이름에서 실제 행동까지 찾기','### 익숙한 비유를 사용할 때','별도의 리듬필러 능력치나 장치용 판정 엔진을 만들 필요는 없습니다','드랍아웃은 지정 차원에 다시 들어갈 수 없는 상태','같은 기능을 얻는 경로는 여러 가지입니다']:
 assert phrase in world_text,phrase
d['current_world_physics_index_audit_review']={'World':'v0.52','Design':'v0.78','whole_documents_reviewed':3,'whole_source_lines':[538,296,461],'physics_family_cumulative_whole_reviews':16,'physics_family_pending':0,'legacy_index_codes_mapped':102,'source_count_checks':18,'bounded_cumulative_whole_reviews':26,'bounded_cumulative_pending':64,'all_world_physics_documents_reviewed':True,'all_older_unique_sources_reviewed':False,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
pack_review=legacy_coherence['cyberpunk_pack_foundations_review']
assert pack_review['whole_documents_read']==len(pack_review['snapshots'])==4
assert (pack_review['pack_family_cumulative_documents_reviewed'],pack_review['pack_family_documents_pending'])==(4,17)
assert pack_review['versions']['World']=='v0.53' and pack_review['versions']['Design']=='v0.79'
assert pack_review['new_mechanical_parameter_values']==[] and pack_review['new_related_novels_whole_read']==0
for flag in ['all_cyberpunk_pack_documents_reviewed','all_older_unique_sources_reviewed','all_specific_use_profiles_complete','current_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not pack_review[flag]
for snapshot in pack_review['snapshots']:
 data=snapshot['text'].encode()
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert len(snapshot['text'].splitlines())=={'00_Pack_Overview.md':203,'_Pack_Spec.md':791,'02_BP_Body_Purity.md':395,'_v0.3_Review_Report.md':229}[snapshot['name']]
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
for key,count in [('primary_topic_recheck',4),('wiki_topic_recheck',6)]:
 source=pack_review[key]
 assert len(source['topics'])==count and hash_current(p/source['source_path_relative_to_plan'])==source['source_sha256']
 assert not source['whole_document_read']
 source_text=(p/source['source_path_relative_to_plan']).read_bytes().decode()
 for topic in source['topics']:
  assert topic['whole_topic_read'] and hashlib.sha256(topic['text'].encode()).hexdigest()==topic['sha256'] and topic['text'] in source_text
pack_inventory=[e for e in inventory['files'] if 'Cyberpunk Pack' in e['path_relative_to_plan']]
assert len(pack_inventory)==21 and sum(e['whole_document_reviewed_cumulatively'] for e in pack_inventory)==21
assert {e['path_relative_to_plan'] for e in pack_review['snapshots']} <= {e['path_relative_to_plan'] for e in pack_inventory if e['whole_document_reviewed_cumulatively']}
catalog=pack_review['spec_catalog_map']
assert len(catalog)==len({(e['legacy_group'],e['legacy_name']) for e in catalog})==39
spec=next(e['text'] for e in pack_review['snapshots'] if e['name']=='_Pack_Spec.md')
for entry in catalog:
 assert entry['legacy_name'] in spec and entry['migration_decision'] and entry['current_world_anchor'] in world_text
 assert entry['acquisition_origin_preserved']
 for flag in ['old_three_slot_or_level_cost_imported','detailed_catalog_whole_read_this_pass','complete_current_use_profile_verified_by_this_pass']:
  assert not entry[flag]
bp=next(e['text'] for e in pack_review['snapshots'] if e['name']=='02_BP_Body_Purity.md')
assert '하얀 여우' in bp and 'Pack 창작' not in bp
metrics=pack_review['metrics']
assert (metrics['actual_pack_documents'],metrics['declared_pack_files'],metrics['spec_file_tree_entries'],metrics['catalog_total'])==(21,18,19,39)
assert metrics['spec_catalog_counts']=={'능력':15,'기술':12,'기능':12}
math=legacy['cyberpunk_pack_foundation_arithmetic']
assert (math['documents'],math['checks_passed'])==(4,18)
assert math['spec_catalog_counts']==metrics['spec_catalog_counts'] and math['reported_critical_split']==[12,10,2]
assert (math['level5_formula_difference'],math['level1_table_starting_BP'],math['two_implants_table_starting_BP'],math['printed_hacker_change_total'])==(5,95,85,82)
assert math['old_d100_fumble_band_widths']==[1,2,5,10,20]
assert not math['current_engine_changed'] and not math['actual_participant_playtest']
for phrase in ['### 몸을 바꿔도 이어지는 것, 그 몸에 남는 것','### 두 장의 입학 안내 — 새 캠페인 도입','그 인물의 참가자가 정합니다','그 제도가 참조하는 몸·조직 자산과 기준 시점']:
 assert phrase in world_text,phrase
d['current_cyberpunk_pack_foundations_review']={'World':'v0.53','Design':'v0.79','whole_documents_reviewed':4,'whole_source_lines':[203,791,395,229],'primary_whole_topics':4,'wiki_whole_topics':6,'limited_arithmetic_checks':18,'pack_family_cumulative_whole_reviews':4,'pack_family_pending':17,'spec_catalog_summaries_mapped':39,'detailed_catalog_whole_review_complete':False,'bounded_cumulative_whole_reviews':30,'bounded_cumulative_pending':60,'all_older_unique_sources_reviewed':False,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
catalog_review=legacy_coherence['cyberpunk_pack_interaction_catalog_review']
assert catalog_review['whole_documents_read']==len(catalog_review['snapshots'])==3
assert (catalog_review['pack_family_cumulative_documents_reviewed'],catalog_review['pack_family_documents_pending'],catalog_review['catalog_entries_whole_read_and_mapped'])==(7,14,39)
assert catalog_review['versions']['World']=='v0.54' and catalog_review['versions']['Design']=='v0.80'
assert catalog_review['new_mechanical_parameter_values']==[]
for name in ['new_primary_topics_whole_read','new_wiki_topics_whole_read','new_related_novels_whole_read']:
 assert catalog_review[name]==0
for flag in ['all_cyberpunk_pack_documents_reviewed','all_older_unique_sources_reviewed','all_specific_use_profiles_complete','current_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not catalog_review[flag]
detail_sources={}
for snapshot in catalog_review['snapshots']:
 data=snapshot['text'].encode();detail_sources[snapshot['name']]=snapshot['text']
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert snapshot['lines']==len(snapshot['text'].splitlines())=={'05_Interactions_Powers.md':1167,'06_Interactions_Skills.md':831,'07_Interactions_Functions.md':789}[snapshot['name']]
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
expected_paths={e['path_relative_to_plan'] for e in pack_review['snapshots']+catalog_review['snapshots']+legacy_coherence['cyberpunk_pack_character_tracks_review']['snapshots']+legacy_coherence['cyberpunk_pack_dsr_dropout_review']['snapshots']+legacy_coherence['cyberpunk_pack_weapon_review']['snapshots']+legacy_coherence['cyberpunk_pack_NPC_review']['snapshots']+legacy_coherence['cyberpunk_pack_large_entity_review']['snapshots']+legacy_coherence['cyberpunk_pack_glossary_review']['snapshots']+legacy_coherence['cyberpunk_pack_deck_audit_review']['snapshots']+legacy_coherence['cyberpunk_pack_world_correction_review']['snapshots']}
assert expected_paths=={e['path_relative_to_plan'] for e in pack_inventory if e['whole_document_reviewed_cumulatively']}
detailed=catalog_review['detailed_catalog_map'];assert len(detailed)==len({(e['legacy_group'],e['legacy_name']) for e in detailed})==39
for entry in detailed:
 source=detail_sources[entry['source_name']];m=re.search(r'(?m)^## '+re.escape(entry['source_section'])+r'\. .*$',source);assert m
 end=re.search(r'(?m)^## \d+-\d+\.',source[m.end():]);stop=m.end()+end.start() if end else len(source);section=source[m.start():stop]
 assert section.splitlines()[0]==entry['source_section_heading'] and entry['legacy_name'] in section.splitlines()[0]
 assert hashlib.sha256(section.encode()).hexdigest()==entry['source_section_sha256']
 assert entry['detailed_migration_decision'] and entry['current_world_anchor'] in world_text and entry['detailed_catalog_whole_read_this_pass'] and entry['acquisition_origin_preserved']
 assert not entry['complete_current_use_profile_verified_by_this_pass'] and not entry['old_three_slot_or_level_cost_imported']
for ref in catalog_review['prior_source_topic_references']:
 record=legacy_coherence[ref['record']][ref['topic_group']];topic=next(e for e in record['topics'] if e['topic']==ref['topic'])
 assert ref['prior_whole_topic_review_reused'] and not ref['new_whole_topic_read_this_pass'] and topic['whole_topic_read'] and topic['sha256']==ref['sha256']
 assert record['source_sha256']==ref['source_sha256']==hash_current(p/record['source_path_relative_to_plan'])
for ref in catalog_review['focused_framework_excerpts']:
 path=p/ref['path_relative_to_plan'];assert hash_current(path)==ref['sha256'] and ref['excerpt'] in path.read_bytes().decode() and not ref['whole_document_read_this_pass']
math=legacy['cyberpunk_pack_catalog_arithmetic'];assert (math['documents'],math['checks_passed'],math['detailed_entries'],math['same_three_dice_outcomes'])==(3,26,39,216)
assert (math['actual_shooting_margin'],math['remaining_example_HP'],math['BP55_actual_legacy_matting_modifier'],math['level3_removal_net_BP'],math['level3_point_refund'],math['shield_level5_table_dice'])==(11,19,-5,6,10,6)
assert not math['current_engine_changed'] and not math['actual_participant_playtest']
for phrase in ['### 같은 감지, 서로 다른 수단','### 기록을 지키고 연락을 이어가기','소급','위치를 아는 것만으로 벽이 사라지지는 않습니다','뇌네는 차원 주파수 동기화의 속칭','인물이 몇 시까지 답을 주기로 했는가']:
 if phrase!='소급':assert phrase in world_text,phrase
d['current_cyberpunk_pack_interaction_catalog_review']={'World':'v0.54','Design':'v0.80','whole_documents_reviewed':3,'whole_source_lines':[1167,831,789],'detailed_entries_whole_read_and_mapped':39,'prior_whole_topic_reviews_reused':3,'new_primary_whole_topics':0,'new_wiki_whole_topics':0,'new_related_novels_whole_read':0,'limited_arithmetic_checks':26,'pack_family_cumulative_whole_reviews':7,'pack_family_pending':14,'all_specific_use_profiles_complete':False,'bounded_cumulative_whole_reviews':33,'bounded_cumulative_pending':57,'all_older_unique_sources_reviewed':False,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
character_tracks=legacy_coherence['cyberpunk_pack_character_tracks_review']
assert character_tracks['whole_documents_read']==len(character_tracks['snapshots'])==3
assert (character_tracks['pack_family_cumulative_documents_reviewed'],character_tracks['pack_family_documents_pending'])==(10,11)
assert character_tracks['versions']['World']=='v0.55' and character_tracks['versions']['Design']=='v0.81'
assert character_tracks['new_mechanical_parameter_values']==[] and character_tracks['new_related_novels_whole_read']==0
for flag in ['all_cyberpunk_pack_documents_reviewed','all_older_unique_sources_reviewed','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not character_tracks[flag]
character_sources={}
for snapshot in character_tracks['snapshots']:
 data=snapshot['text'].encode();character_sources[snapshot['name']]=snapshot['text']
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert snapshot['lines']==len(snapshot['text'].splitlines())=={'03_Runner_Tags.md':815,'04_Presets.md':1037,'08_Tracks_Shining_Matting.md':993}[snapshot['name']]
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
def character_section(text,heading):
 a=text.index(heading);start_end=text.find('\n',a)
 end=re.search(r'(?m)^#{2,3} \d+-\d+(?:-\d+)?\.',text[start_end:]);stop=start_end+end.start() if end else len(text)
 return text[a:stop]
tags=character_tracks['tag_migration_map'];presets=character_tracks['preset_migration_map']
assert len(tags)==len({(e['legacy_group'],e['legacy_name']) for e in tags})==30
assert tuple(sum(e['legacy_group']==name for e in tags) for name in ['유형','성격','배경'])==(10,10,10)
assert len(presets)==9 and [e['legacy_id'] for e in presets]==[f'G-{n}' for n in range(9)]
for entries,name in [(tags,'03_Runner_Tags.md'),(presets,'04_Presets.md')]:
 for entry in entries:
  section=character_section(character_sources[name],entry['source_heading'])
  assert hashlib.sha256(section.encode()).hexdigest()==entry['source_section_sha256'] and entry['migration_decision'] and entry['whole_section_read']
  assert entry['current_world_anchor'] in world_text
  if name.startswith('03'):assert not entry['fixed_trait_bonus_or_cost_imported']
  else:assert not entry['old_100point_build_rewritten'] and not entry['old_package_numeric_profile_imported']
assert len(character_tracks['legacy_trauma_names'])==8
for name in character_tracks['legacy_trauma_names']:assert name in character_sources['08_Tracks_Shining_Matting.md']
math=legacy['cyberpunk_pack_character_track_arithmetic']
assert (math['documents'],math['checks_passed'],math['tags_total'],math['trauma_catalog_items'],math['actual_d100_result_tables'])==(3,22,30,8,3)
assert math['package_totals']==[30]*9 and math['original_stat_cost_totals']==[68,70,68,72,77,68,68,66,66]
assert math['G0_stat_table_PRE_SEN']==[3,4] and math['G0_correct_legacy_derived_values']==[6,11,9] and math['G0_printed_derived_values']==[4,10,8]
assert (math['G3_adjusted_stat_total'],math['G4_adjusted_stat_total'],math['G8_net_resistance_modifier'],math['G1_replacement_total'],math['shining_log62_actual_band'])==(68,69,10,31,4)
assert not math['G6_BP_tag_requirement_met'] and not math['current_engine_changed'] and not math['old_100point_build_rewritten'] and not math['actual_participant_playtest']
for phrase in ['### 직능을 고를 때 — 같은 일을 서로 다른 사람으로 하기','#### 첫 의뢰를 앞둔 카페 — 새 도입','### 경험과 현재 상태를 따로 이어 쓰기','밤의 공방을 계속 운영하려는 사람','플라잉은 본능이나 행운의 등급이 아닙니다','같은 악몽·감정·말투나 평생 고칠 수 없는 상태를 부과하지 않습니다']:
 assert phrase in world_text,phrase
d['current_cyberpunk_pack_character_tracks_review']={'World':'v0.55','Design':'v0.81','whole_documents_reviewed':3,'whole_source_lines':[815,1037,993],'tags_whole_read_and_mapped':30,'preset_concepts_whole_read_and_mapped':9,'legacy_trauma_motifs_reviewed':8,'new_related_novels_whole_read':0,'limited_arithmetic_checks':22,'pack_family_cumulative_whole_reviews':10,'pack_family_pending':11,'all_specific_use_profiles_complete':False,'bounded_cumulative_whole_reviews':36,'bounded_cumulative_pending':54,'all_older_unique_sources_reviewed':False,'old_100point_build_rewritten':False,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
dsr_dropout=legacy_coherence['cyberpunk_pack_dsr_dropout_review']
assert dsr_dropout['whole_documents_read']==len(dsr_dropout['snapshots'])==2
assert dsr_dropout['source_lines']==[818,833]
assert (dsr_dropout['pack_family_cumulative_documents_reviewed'],dsr_dropout['pack_family_documents_pending'])==(12,9)
assert dsr_dropout['versions']=={'World':'v0.56','Design':'v0.82','Core':'v0.31','Sheet':'v0.31','Easy':'P v0.21','Tarot':'v0.3'}
assert dsr_dropout['new_mechanical_parameter_values']==[] and dsr_dropout['new_related_novels_whole_read']==0
assert dsr_dropout['trial_detonation_preconditions_checked']
for flag in ['all_cyberpunk_pack_documents_reviewed','all_older_unique_sources_reviewed','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','new_campaign_scene_is_canon_sequel','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not dsr_dropout[flag]
dsr_sources={}
for snapshot in dsr_dropout['snapshots']:
 data=snapshot['text'].encode();dsr_sources[snapshot['name']]=snapshot['text']
 assert snapshot['whole_document_read'] and len(data)==snapshot['bytes'] and len(snapshot['text'])==snapshot['chars']
 assert len(snapshot['text'].splitlines())==snapshot['lines'] and hashlib.sha256(data).hexdigest()==snapshot['sha256']
 assert hash_current(p/snapshot['path_relative_to_plan'])==snapshot['sha256'] and snapshot['migration_decisions']
 assert any(e['name']==snapshot['name'] and e['sha256']==snapshot['sha256'] and e['whole_document_read'] for e in additional_procurement)
mapping=dsr_dropout['section_migration_map'];assert len(mapping)==22 and len({(e['source_name'],e['source_heading']) for e in mapping})==22
for entry in mapping:
 text=dsr_sources[entry['source_name']];a=text.index(entry['source_heading']);end=re.search(r'(?m)^## \d+-\d+\.',text[a+len(entry['source_heading']):]);b=a+len(entry['source_heading'])+end.start() if end else len(text)
 assert hashlib.sha256(text[a:b].encode()).hexdigest()==entry['source_section_sha256']
 assert entry['whole_section_read'] and entry['migration_decision'] and entry['current_anchor'] in core+(o/'12_룰시트와캐릭터시트.md').read_text()
ref=dsr_dropout['prior_sources_reused']['framework_grade_9'];assert hash_current(p/ref['path_relative_to_plan'])==ref['sha256']
assert ref['whole_read_from_previous_review'] and ref['focused_text'] in (p/ref['path_relative_to_plan']).read_text()
ar=legacy['cyberpunk_pack_dsr_dropout_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['logged_DSR_net'],ar['special_gear_qualified_DSR_net'],ar['inferred_unwritten_opening_d6_pool'])==(2,21,0,1,9)
assert (ar['sample_A_HP_after_damage'],ar['sample_A_ego_after_loss'],ar['sample_B_actual_d10067_band'],ar['sample_B_declared_paradox_after_losses'],ar['sample_B_printed_paradox'])==(-14,5,4,7,8)
assert ar['legacy_stat9_grade']=='5d8' and ar['BOD7_omitted_HP_values']==list(range(-13,-7))
assert ar['ambiguous_26_damage_has_expanded_reading'] and ar['own_numeric_d100_threshold_rows']==0 and not ar['current_engine_changed'] and not ar['actual_participant_playtest']
special=results['스페셜_검증.py'];assert special['checks_passed']==78 and special['dropout_campaign_checks']==11
for phrase in ['### 닫힌 문 바깥의 약속 — 새 드랍아웃 시나리오 도입','주민은 공방에 남아 계속 일하려 하고','진입 금지가 소유권을 저절로 옮기지는 않습니다','다른 참가자의 장면을 일괄 종료하지 않습니다']:
 assert phrase in world_text,phrase
sheet=(o/'12_룰시트와캐릭터시트.md').read_text()
for phrase in ['fewk-dropout-sheet','#### 채워진 예 — 남긴 공구와 부상한 본체','HP9 유지','현지 보관 몸`B-D2`·HP7','공학70 공유','다른 시나리오의 무조건 결행까지 금지하는 보편 규칙은 아닙니다']:
 assert phrase in sheet,phrase
assert '현지 결행자는 행동 가능한 활성 몸으로 해당 단말에 접근해야 합니다' in core
assert re.search(r'<a id="fewk-realm-catalog"></a>\s*<a id="fewk-world-72"></a>\s*## 72\.',world_text)
d['current_special_profiles'].update(checks_passed=78,dropout_campaign_checks=11,all_world_profiles_verified=False,actual_participant_playtest=False)
d['current_cyberpunk_pack_dsr_dropout_review']={'World':'v0.56','Design':'v0.82','Core':'v0.31','Easy':'P v0.21','Sheet':'v0.31','whole_documents_reviewed':2,'whole_source_lines':[818,833],'major_sections_mapped':22,'limited_arithmetic_checks':21,'new_local_dropout_boundary_checks':11,'pack_family_cumulative_whole_reviews':12,'pack_family_pending':9,'bounded_cumulative_whole_reviews':38,'bounded_cumulative_pending':52,'new_related_novels_whole_read':0,'all_specific_use_profiles_complete':False,'all_older_unique_sources_reviewed':False,'current_engine_changed':False,'old_100point_build_rewritten':False,'new_scene_is_canon_sequel':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
weapon_review=legacy_coherence['cyberpunk_pack_weapon_review']
assert weapon_review['whole_documents_read']==len(weapon_review['snapshots'])==1
assert (weapon_review['pack_family_cumulative_documents_reviewed'],weapon_review['pack_family_documents_pending'])==(13,8)
assert weapon_review['versions']=={'Core':'v0.32','World':'v0.57','Sheet':'v0.32','Easy':'P v0.22','Design':'v0.83','Tarot':'v0.3'}
for flag in ['all_cyberpunk_pack_documents_reviewed','all_older_unique_sources_reviewed','all_specific_use_profiles_complete','all_weapon_catalog_primary_provenance_verified','current_engine_changed','new_model_is_original_named_product','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not weapon_review[flag]
source=weapon_review['snapshots'][0];weapon=source['text'];data=weapon.encode()
assert source['name']=='11_Weapons_Equipment.md' and source['whole_document_read']
assert (len(data),len(weapon),len(weapon.splitlines()))==(65428,40925,1086)
assert source['bytes']==len(data) and source['chars']==len(weapon) and source['lines']==1086
assert hashlib.sha256(data).hexdigest()==source['sha256']==hash_current(p/source['path_relative_to_plan'])
assert any(e['name']==source['name'] and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
catalog=weapon_review['catalog_rows'];assert len(catalog)==weapon_review['main_table_rows']==100
assert weapon_review['standalone_crocodile_items']==1 and weapon_review['declared_prior_v02_inventory']==110
assert weapon_review['catalog_counts']==dict(zip('ABCDEFGHI',[26,12,15,7,5,6,15,9,5]))
for entry in catalog:
 assert entry['source_row'] in weapon and hashlib.sha256(entry['source_row'].encode()).hexdigest()==entry['source_row_sha256']
 assert entry['actual_columns']==len(entry['fields']) and entry['row_complete']==(entry['actual_columns']==entry['expected_columns'])
 assert entry['migration_decision'] and not entry['all_primary_claims_confirmed'] and not entry['current_detailed_numeric_profile_complete']
bad=[e for e in catalog if not e['row_complete']];assert len(bad)==1 and bad[0]['legacy_name']=='전투 활 (신기 강화)' and bad[0]['actual_columns']==7 and bad[0]['expected_columns']==8
major=weapon_review['major_section_mapping'];assert len(major)==18
heads=list(re.finditer(r'(?m)^## .*$',weapon));assert [m.group() for m in heads]==[e['source_heading'] for e in major]
for i,entry in enumerate(major):
 section=weapon[heads[i].start():heads[i+1].start() if i+1<len(heads) else len(weapon)]
 assert hashlib.sha256(section.encode()).hexdigest()==entry['source_section_sha256'] and entry['whole_section_read'] and entry['migration_scope']
 assert all(anchor in core for anchor in entry['current_anchors'])
assert [e['topic'] for e in weapon_review['primary_topics_reused']]==['0077','0083']
for entry in weapon_review['primary_topics_reused']:
 raw_path=p/entry['path_relative_to_plan'];assert hash_current(raw_path)==entry['container_sha256']
 lines=raw_path.read_text().splitlines();assert '\n'.join(lines[entry['line_start']-1:entry['line_end']])==entry['text']
 assert entry['whole_topic_read'] and entry['previous_topic_review_reused'] and not entry['whole_container_read']
ar=legacy['cyberpunk_pack_weapon_arithmetic'];assert (ar['documents'],ar['checks_passed'],ar['major_headings'],ar['duplicated_11_15_headings'],ar['main_catalog_table_rows'],ar['with_standalone_crocodile'])==(1,23,18,2,100,101)
assert ar['malformed_battle_bow_columns']==[7,8] and ar['external_deck_variants_by_type']==[3,3,3,3]
assert ar['weapon_set_lower_bounds']==[420,400,1150,900,1700,2500,2500,50000]
assert ar['damage_multiplier_interpretations_not_same_distribution'] and not ar['own_core_damage_multipliers_adopted'] and not ar['current_engine_changed'] and not ar['actual_participant_playtest']
gear=results['장비_검증.py'];assert (gear['checks_passed'],gear['v_suppression_checks'],gear['v_suppression_boundary_cases'])==(106,17,4608)
assert gear['v_model']=='V-SUPPRESS-01' and not gear['all_V_guns_verified'] and not gear['all_guns_and_implants_complete'] and not gear['actual_participant_playtest']
profile=json.loads((v/'장비_프로필.json').read_text());vg=profile['vgun']
assert (vg['id'],vg['classification'],vg['damage_type'],vg['capacity'],vg['ammo_per_action'],vg['main_actions'],vg['hp_damage'])==('V-SUPPRESS-01','V','P',6,3,1,0)
assert vg['actual_physical_projectiles'] and vg['ammo_unit']=='one_physical_projectile_and_one_use_power_package' and not vg['forced_emotion_or_Ego_damage'] and not vg['direct_physical_original_damage'] and not vg['all_V_guns_share_this_effect']
for phrase in ['#### 선택 모델 — 소리열 억제 단말 V-SUPPRESS-01','물질 탄두와 발사용 동력1회분이 묶인 복합 소모품','여러 공격자가 억제했다면 각 압박의 종료를 확인하되 불리 수치는 누적하지 않습니다']:
 assert phrase in core,phrase
assert '### 억제 사격을 기록하기 — V-SUPPRESS-01 작성 예' in (o/'12_룰시트와캐릭터시트.md').read_text()
for phrase in ['### 총을 고를 때는 이름보다 사용할 행동을 확인하기','새 장면 — 공방 앞의 대치','외장 장비로 만들었다는 이유만으로 원전 뉴로덱의 생체 의존성이 사라지지는 않습니다']:
 assert phrase in world_text,phrase
d['current_gear_profiles'].update(v_model='V-SUPPRESS-01',v_suppression_checks=17,v_suppression_boundary_cases=4608,all_V_guns_verified=False)
d['current_cyberpunk_pack_weapon_review']={'Core':'v0.32','World':'v0.57','Sheet':'v0.32','Easy':'P v0.22','Design':'v0.83','whole_documents_reviewed':1,'whole_source_lines':1086,'main_catalog_table_rows_mapped':100,'standalone_crocodile_items':1,'major_sections_mapped':18,'limited_arithmetic_checks':23,'V_suppression_checks':17,'V_suppression_boundary_cases':4608,'new_related_novels_whole_read':0,'pack_family_cumulative_whole_reviews':13,'pack_family_pending':8,'bounded_cumulative_whole_reviews':39,'bounded_cumulative_pending':51,'all_specific_use_profiles_complete':False,'all_older_unique_sources_reviewed':False,'all_weapon_catalog_primary_provenance_verified':False,'all_V_guns_verified':False,'current_engine_changed':False,'new_model_is_original_named_product':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
npc_review=legacy_coherence['cyberpunk_pack_NPC_review']
assert (npc_review['whole_documents_read'],npc_review['NPC_blocks_mapped'],npc_review['sample_NPC_blocks'],npc_review['original_name_based_blocks'],npc_review['new_named_adaptations'])==(1,17,13,4,3)
assert (npc_review['pack_family_cumulative_documents_reviewed'],npc_review['pack_family_documents_pending'])==(14,7)
assert npc_review['versions']=={'Core':'v0.33','World':'v0.58','Sheet':'v0.33','Easy':'P v0.23','Design':'v0.84','Tarot':'v0.3'}
for flag in ['all_NPC_canonical_facts_verified','all_specific_use_profiles_complete','all_older_unique_sources_reviewed','all_cyberpunk_pack_documents_reviewed','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not npc_review[flag]
assert npc_review['new_related_novels_whole_read']==0
source=npc_review['snapshots'][0];data=source['text'].encode()
assert source['name']=='12_NPC_Catalog.md' and source['whole_document_read'] and len(data)==source['bytes']==65863
assert len(source['text'])==source['chars']==39279 and len(source['text'].splitlines())==source['lines']==1558
assert hashlib.sha256(data).hexdigest()==source['sha256']
verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
assert any(e['name']==source['name'] and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
heads=list(re.finditer(r'^### (12-[1-5]-[B-Z])\. (.*)$',source['text'],re.M));cards=npc_review['NPC_block_mapping']
assert len(heads)==len(cards)==len({e['section'] for e in cards})==17
for match,entry in zip(heads,cards):
 nxt=re.search(r'^#{2,3} ',source['text'][match.end():],re.M);end=match.end()+nxt.start() if nxt else len(source['text'])
 assert entry['section']==match[1] and entry['text']==source['text'][match.start():end]
 assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['decision']
 assert not entry['current_numeric_conversion_complete'] and not entry['all_claimed_original_facts_verified']
assert sum(e['status']=='Pack 창작 샘플' for e in cards)==13
assert len(npc_review['major_section_mapping'])==len(re.findall(r'^## ',source['text'],re.M))==8
primary=npc_review['primary_topics_reused'];verify_recorded_source_hash(p/primary['path'],primary['sha256'])
assert not primary['whole_container_read'] and set(primary['topics'])=={'0001','0006','0052','0053','0054','0089'}
raw_lines=(p/primary['path']).read_text().splitlines()
for entry in primary['topics'].values():
 assert entry['whole_topic_read'] and entry['previous_topic_review_reused']
 assert '\n'.join(raw_lines[entry['start_line']-1:entry['end_line']])==entry['text']
 assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
assert '팬이던' in primary['topics']['0054']['text'] and '기타를 선물 받고' in primary['topics']['0054']['text']
assert all(name in primary['topics']['0089']['text'] for name in ['크리스','케이티','수덕'])
assert '현화;' in primary['topics']['0001']['text'] and '천군; 신원;' in primary['topics']['0052']['text']
ar=legacy['cyberpunk_pack_NPC_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['NPC_blocks'],ar['derived_value_cells_checked'],ar['initiative_means_checked'],ar['grade_map_cells_checked'])==(1,17,17,102,17,102)
assert ar['grade_differences']==[['12-5-D','BOD',9,'6d6','5d8'],['12-5-E','LCK',13,'8d10','7d10']]
assert len(ar['outside_declared_stat_range'])==19 and ar['source_critical_guarantee_counterexamples']==[-8,-7]
assert not ar['legacy_number_derivation_is_current_adoption'] and not ar['current_engine_changed'] and not ar['actual_participant_playtest']
assert (NPC['checks_passed'],NPC['named_sample_checks'],NPC['named_sample_sender_cases'],NPC['named_sample_percentile_rolls'])==(83,30,192,700)
assert not NPC['all_17_legacy_NPC_numeric_profiles_complete'] and not NPC['full_encounter_balance_verified']
named=json.loads((v/'NPC_프로필.json').read_text())
assert [(x['id'],x['base_template']) for x in named['named_samples']]==[('NP-HAN-01','N01'),('NP-WHITE-01','N04'),('NP-BIPA-01','N05')]
assert len(named['templates'])==6 and named['new_universal_stats']==[]
for entry in named['named_samples']:
 assert entry['status'].startswith('NEW') and not entry['automatic_PC_relationship'] and not entry['automatic_access_to_other_sources']
 assert all(item['skill'] is None or item['skill'] in named['templates'][0]['skills'] for item in entry['interactions'])
assert not named['named_sample_rules']['all_17_legacy_NPC_numeric_profiles_complete'] and not named['named_sample_rules']['canonical_people_numeric_profiles_added']
for phrase in ['### 이름을 붙여 쓰는 구판 창작 소재 세 사람','NP-HAN-01','NP-WHITE-01','NP-BIPA-01','실제 상태 하나']:
 assert phrase in core,phrase
for phrase in ['### 구판의 이름을 다시 만나는 방법','### 원전 인물은 이름과 사건의 시점을 함께 보기','### 새 도입 — 장부를 돌려주는 저녁','케이티와 크리스는0089에서 실제로 함께 일하므로']:
 assert phrase in world_text,phrase
assert '### 채운 구판 창작 재구성 — 산복도로 한 씨' in (o/'12_룰시트와캐릭터시트.md').read_text()
d['current_cyberpunk_pack_NPC_review']={'Core':'v0.33','World':'v0.58','Sheet':'v0.33','Easy':'P v0.23','Design':'v0.84','whole_documents_reviewed':1,'whole_source_lines':1558,'NPC_blocks_mapped':17,'sample_blocks':13,'original_name_based_blocks':4,'primary_whole_topics_reused':6,'new_named_samples_using_existing_cards':3,'limited_legacy_arithmetic_checks':17,'new_NPC_checks':30,'named_sender_cases':192,'named_percentile_rolls':700,'pack_family_cumulative_whole_reviews':14,'pack_family_pending':7,'bounded_cumulative_whole_reviews':40,'bounded_cumulative_pending':50,'all_specific_use_profiles_complete':False,'all_older_unique_sources_reviewed':False,'all_NPC_canonical_facts_verified':False,'new_related_novels_whole_read':0,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
large_review=legacy_coherence['cyberpunk_pack_large_entity_review']
assert (large_review['whole_documents_read'],large_review['entity_blocks_mapped'],large_review['four_divine_beast_blocks'],large_review['major_sections'])==(1,11,4,10)
assert (large_review['pack_family_cumulative_documents_reviewed'],large_review['pack_family_documents_pending'])==(15,6)
assert large_review['versions']=={'Core':'v0.34','World':'v0.59','Sheet':'v0.34','Easy':'P v0.24','Design':'v0.85','Tarot':'v0.3'}
assert large_review['new_facility_model']=='PLANT-STOP-01' and large_review['new_related_novels_whole_read']==0
for flag in ['all_11_entity_numeric_profiles_complete','all_entity_primary_provenance_verified','all_specific_use_profiles_complete','all_older_unique_sources_reviewed','all_cyberpunk_pack_documents_reviewed','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:
 assert not large_review[flag]
source=large_review['snapshots'][0];data=source['text'].encode()
assert source['name']=='13_Scale_C_Entities.md' and source['whole_document_read'] and len(data)==source['bytes']==50857
assert len(source['text'])==source['chars']==28957 and len(source['text'].splitlines())==source['lines']==1122
assert hashlib.sha256(data).hexdigest()==source['sha256']
verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
assert any(e['name']==source['name'] and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
heads=list(re.finditer(r'^### (13-[2-6]-[A-Z])\. (.*)$',source['text'],re.M));cards=large_review['entity_block_mapping']
assert len(heads)==len(cards)==len({e['section'] for e in cards})==11
for match,entry in zip(heads,cards):
 nxt=re.search(r'^#{2,3} ',source['text'][match.end():],re.M);end=match.end()+nxt.start() if nxt else len(source['text'])
 assert entry['section']==match[1] and entry['text']==source['text'][match.start():end]
 assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['decision']
 assert not entry['current_individual_numeric_profile_complete'] and not entry['all_claimed_original_facts_verified']
assert len(re.findall(r'^## ',source['text'],re.M))==10
primary=large_review['primary_topics_reused'];verify_recorded_source_hash(p/primary['path'],primary['sha256'])
assert not primary['whole_container_read'] and set(primary['topics'])=={'0005','0008','0046','0057'}
raw_lines=(p/primary['path']).read_text().splitlines()
for entry in primary['topics'].values():
 assert entry['whole_topic_read'] and entry['previous_topic_review_reused']
 assert '\n'.join(raw_lines[entry['start_line']-1:entry['end_line']])==entry['text']
 assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
wiki=large_review['wiki_topics_reused'];verify_recorded_source_hash(p/wiki['path'],wiki['sha256'])
assert not wiki['whole_container_read'] and {e['topic'] for e in wiki['topics']}=={'산악보행트럭.txt','흑공말통.txt','신수.txt'}
wiki_text=(p/wiki['path']).read_text();wiki_heads=list(re.finditer(r'^--- %[^\n]+? ---\n(?:\n)?',wiki_text,re.M))
wiki_parts={unquote(m[0].split('--- ')[1].split(' ---')[0]):wiki_text[m.end():wiki_heads[i+1].start() if i+1<len(wiki_heads) else len(wiki_text)] for i,m in enumerate(wiki_heads)}
for entry in wiki['topics']:
 assert entry['whole_topic_read'] and entry['previous_topic_review_reused']
 assert wiki_parts[entry['topic']]==entry['text'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
ar=legacy['cyberpunk_pack_large_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['entity_blocks'],ar['major_sections'],ar['clock_rows'],ar['clock_diagram_mismatches'])==(1,17,11,10,17,14)
assert list(ar['part_HP_sums'].values())==[1230,1060,950,890,1170,200,1550]
assert ar['white_form_part_sums']==[150,860,450] and ar['plant_conflicting_deadline_seconds_at_60s_round']==[300,600]
assert ar['old_A_rounds_at_6s_and_current_5s']==[60,50] and ar['minimum_old_breath_damage_on_current_guard']==[20,19,0]
for flag in ['part_sums_are_current_whole_body_HP','current_engine_changed','legacy_damage_values_adopted','actual_participant_playtest']:assert not ar[flag]
facility=results['대형시설_검증.py']
assert (facility['checks_passed'],facility['command_boundary_cases'],facility['common_attack_boundary_cases'],facility['percentile_cases'])==(38,12288,6912,900)
assert facility['actual_IC_deadline_is_not_success_clock'] and facility['new_universal_stats']==[]
for flag in ['all_large_entity_profiles_complete','all_black_material_or_facility_effects_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not facility[flag]
profile=json.loads((v/'대형시설_프로필.json').read_text())
assert profile['model']=='PLANT-STOP-01' and profile['engine']=='P-FEWK-0.2' and profile['status'].startswith('NEW')
assert profile['parts']=={'tank':{'max_hp':12,'armor':1},'console':{'max_hp':6,'armor':0},'cooling_a':{'max_hp':8,'armor':0},'cooling_b':{'max_hp':8,'armor':0}}
assert not profile['parts_sum_is_hull_HP'] and not profile['part_hit_automatically_damages_operators_or_base'] and not profile['automatic_attack']
assert profile['overheat']['seconds_to_leak']==60 and profile['overheat']['deadline_is_fixed_once_started'] and not profile['overheat']['OOC_wait_advances_IC_seconds']
assert (profile['shutdown']['skill'],profile['shutdown']['main_actions'],profile['shutdown']['actual_work_seconds'])==('공학',1,5)
assert not profile['shutdown']['restores_HP_or_contents_or_power'] and not profile['shutdown']['repairs_or_reverses_leak']
assert profile['new_universal_stats']==[] and not profile['all_large_entity_profiles_complete'] and not profile['actual_participant_playtest']
assert '### 큰 시설의 한 기능을 멈추기 — PLANT-STOP-01' in core
for phrase in ['큰 존재와 재해 앞에서 무엇을 지킬 것인가','최후의 연주자들 — 재해를 둘러싼 FEWK의 예술과 의무','새 도입 — 작업장을 멈춘 뒤 돌아갈 곳','fewk-large-facility']:assert phrase in world_text
assert '채운 대형 시설 — 작동과 기한을 같은 기록으로' in (o/'12_룰시트와캐릭터시트.md').read_text()
d['current_cyberpunk_pack_large_entity_review']={'Core':'v0.34','World':'v0.59','Sheet':'v0.34','Easy':'P v0.24','Design':'v0.85','whole_documents_reviewed':1,'whole_source_lines':1122,'entity_blocks_mapped':11,'primary_whole_topics_reused':4,'wiki_whole_topics_reused':3,'limited_legacy_arithmetic_checks':17,'new_facility_model':'PLANT-STOP-01','facility_checks':38,'command_boundary_cases':12288,'common_attack_boundary_cases':6912,'percentile_cases':900,'pack_family_cumulative_whole_reviews':15,'pack_family_pending':6,'bounded_cumulative_whole_reviews':41,'bounded_cumulative_pending':49,'all_11_entity_numeric_profiles_complete':False,'all_entity_primary_provenance_verified':False,'all_specific_use_profiles_complete':False,'all_older_unique_sources_reviewed':False,'new_related_novels_whole_read':0,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
glossary_review=legacy_coherence['cyberpunk_pack_glossary_review']
assert (glossary_review['whole_documents_read'],glossary_review['term_heading_entries_mapped'],glossary_review['major_sections_by_file'])==(2,259,[11,9])
assert glossary_review['term_entries_by_area']==[42,49,64,81,23]
assert (glossary_review['pack_family_cumulative_documents_reviewed'],glossary_review['pack_family_documents_pending'])==(17,4)
assert glossary_review['versions']=={'Core':'v0.35','World':'v0.60','Sheet':'v0.35','Easy':'P v0.25','Design':'v0.86','Tarot':'v0.3'}
assert glossary_review['new_mechanical_parameter_values']==[] and glossary_review['new_related_novels_whole_read']==glossary_review['new_primary_topics_whole_read']==0
for flag in ['all_term_primary_provenance_verified','all_specific_use_profiles_complete','all_older_unique_sources_reviewed','all_cyberpunk_pack_documents_reviewed','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not glossary_review[flag]
source_by_name={s['name']:s for s in glossary_review['snapshots']}
assert set(source_by_name)=={'14_Pack_Glossary.md','README.md'}
for name,shape in [('14_Pack_Glossary.md',(72672,42557,1344)),('README.md',(10892,7358,261))]:
 source=source_by_name[name];data=source['text'].encode()
 assert source['whole_document_read'] and (len(data),len(source['text']),len(source['text'].splitlines()))==shape
 assert source['bytes']==shape[0] and source['chars']==shape[1] and source['lines']==shape[2]
 assert hashlib.sha256(data).hexdigest()==source['sha256'] and source['migration_decisions']
 verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
 assert any(e['name']==name and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
source=source_by_name['14_Pack_Glossary.md'];text=source['text'];heads=[];fence=False;offset=0;area='';terms=[]
for line in text.splitlines(keepends=True):
 if line.lstrip().startswith('```'):fence=not fence
 if not fence:
  if line.startswith('## '):area=line[3:].strip()
  if re.match(r'^#{2,3} ',line):
   heads.append({'start':offset,'title':line.split(' ',1)[1].strip(),'area':area,'level':len(line.split(' ')[0])})
 offset+=len(line)
for i,h in enumerate(heads):
 if h['level']==3 and re.match(r'14-[1-5]\.',h['area']):terms.append((h,heads[i+1]['start'] if i+1<len(heads) else len(text)))
assert len(terms)==len(glossary_review['term_block_mapping'])==259
for i,((h,end),entry) in enumerate(zip(terms,glossary_review['term_block_mapping']),1):
 assert entry['index']==i and entry['title']==h['title'] and entry['area']==h['area']
 assert (entry['start_char'],entry['end_char'])==(h['start'],end) and entry['text']==text[h['start']:end]
 assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['decision'] and entry['role']
 assert not entry['all_claimed_original_facts_verified'] and not entry['current_individual_numeric_profile_complete']
assert len(glossary_review['major_section_mapping'])==20
for entry in glossary_review['major_section_mapping']:
 source=source_by_name[entry['source_name']]['text'];assert entry['text'] in source and entry['text'].startswith('## '+entry['title']+'\n')
 assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['decision']
primary_topics=[]
for record in glossary_review['primary_topic_reviews_reused']:
 verify_recorded_source_hash(p/record['path'],record['sha256']);current=(p/record['path']).read_bytes().decode().replace('\r\n','\n')
 assert not record['whole_container_read']
 for entry in record['topics']:
  assert entry['whole_topic_read'] and entry['previous_topic_review_reused'] and entry['text'].replace('\r\n','\n') in current
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'];primary_topics.append(entry['topic'])
assert set(primary_topics)=={'0042','0045','0056','0031','0072','0011'} and len(primary_topics)==6
wiki=glossary_review['wiki_topics_reused'];verify_recorded_source_hash(p/wiki['path'],wiki['sha256']);current=(p/wiki['path']).read_bytes().decode()
assert not wiki['whole_container_read'] and {e['topic'] for e in wiki['topics']}=={'상위_차원계.txt','낮은_차원계.txt','축적계.txt','네이티브.txt'}
for entry in wiki['topics']:
 assert entry['whole_topic_read'] and entry['previous_topic_review_reused'] and entry['text'] in current
 assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
ar=legacy['cyberpunk_pack_glossary_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['term_heading_entries'],ar['actual_H3_outside_fences'],ar['cross_reference_rows'])==(2,14,259,277,31)
assert ar['term_entries_by_area']==[42,49,64,81,23] and ar['major_sections']==[11,9]
assert (ar['approximate_distribution_values_sum'],ar['approximate_declared_total'])==(193,190)
assert ar['layer_printed_unit_exponents']==[24,20,16,12,4,0,28] and ar['lower_adjacent_density_ratios']==[10000,10000,10000,100000000,10000]
assert (ar['README_file_table_rows'],ar['current_pack_files'],ar['README_declared_files'],ar['README_checked_Critical_rows'],ar['old_review_count_sum'],ar['README_actual_playtest_count'])==(19,21,18,12,63,0)
assert ar['planned_alpha_beta']==[10,30]
for flag in ['all_term_headings_are_distinct_canonical_terms','code_and_credit_are_same_unit_proven','current_engine_changed','legacy_currency_conversion_adopted','all_source_canonical_facts_verified','actual_participant_playtest']:assert not ar[flag]
for phrase in ['fewk-term-roles','### 이름을 읽고 실제 행동을 고르기','전조 감지','IC/ICE','암호 잠금']:assert phrase in core
for phrase in ['fewk-word-roles','### 비슷한 이름을 다른 삶과 행동으로 읽기','초기 원본0042','원본0045','21자','냥 표기']:assert phrase in world_text
sheet=(o/'12_룰시트와캐릭터시트.md').read_text()
for phrase in ['fewk-term-sheet','### 채운 용어 구분 — 감지한 뒤 약속하기','관찰50','P-WORD-1','B-WORD-0','반복 성장 트랙 없음']:assert phrase in sheet
assert '보안 장애를 IC/ICE라 부르는 캠페인' in easy
d['current_cyberpunk_pack_glossary_review']={'Core':'v0.35','World':'v0.60','Sheet':'v0.35','Easy':'P v0.25','Design':'v0.86','whole_documents_reviewed':2,'whole_source_lines':[1344,261],'term_heading_entries_mapped':259,'term_entries_by_area':[42,49,64,81,23],'cross_reference_rows':31,'limited_legacy_arithmetic_checks':14,'primary_whole_topics_reused':6,'wiki_whole_topics_reused':4,'pack_family_cumulative_whole_reviews':17,'pack_family_pending':4,'bounded_cumulative_whole_reviews':43,'bounded_cumulative_pending':47,'all_term_primary_provenance_verified':False,'all_specific_use_profiles_complete':False,'all_older_unique_sources_reviewed':False,'new_related_novels_whole_read':0,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
deck_review=legacy_coherence['cyberpunk_pack_deck_audit_review']
assert (deck_review['whole_documents_read'],len(deck_review['major_section_mapping']),deck_review['major_sections_by_file'])==(2,27,[12,15])
assert (deck_review['pack_family_cumulative_documents_reviewed'],deck_review['pack_family_documents_pending'])==(19,2)
assert deck_review['versions']=={'Core':'v0.35','World':'v0.61','Sheet':'v0.35','Easy':'P v0.25','Design':'v0.87','Tarot':'v0.3'}
assert deck_review['new_mechanical_parameter_values']==[] and deck_review['new_related_novels_whole_read']==deck_review['new_primary_topics_whole_read']==0
assert (deck_review['reader_topic_routes_corrected'],deck_review['existing_wrong_topic_routes_rejected'])==(3,3)
for flag in ['all_audit_completion_claims_verified','all_specific_use_profiles_complete','all_older_unique_sources_reviewed','all_cyberpunk_pack_documents_reviewed','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','all_appendix_link_meanings_verified','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not deck_review[flag]
source_by_name={unicodedata.normalize('NFC',s['name']):s for s in deck_review['snapshots']}
assert set(source_by_name)=={'사이버덱 정리용 정보누적 처리 대기문서.md','_Consistency_Check_Pack_v0.1.md'}
for name,shape in [('사이버덱 정리용 정보누적 처리 대기문서.md',(23373,13430,407)),('_Consistency_Check_Pack_v0.1.md',(40334,26434,706))]:
 source=source_by_name[name];data=source['text'].encode()
 assert source['whole_document_read'] and (len(data),len(source['text']),len(source['text'].splitlines()))==shape
 assert (source['bytes'],source['chars'],source['lines'])==shape and source['migration_decisions']
 assert hashlib.sha256(data).hexdigest()==source['sha256'];verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
 assert any(e['name']==source['name'] and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
 rows=[entry for entry in deck_review['major_section_mapping'] if entry['source_name']==source['name']]
 assert len(rows)==(12 if name.startswith('사이버덱') else 15)
 offsets=list(re.finditer(r'^## [^\n]+',source['text'],re.M));assert len(offsets)==len(rows)
 for i,(heading,entry) in enumerate(zip(offsets,rows)):
  end=offsets[i+1].start() if i+1<len(offsets) else len(source['text'])
  assert entry['title']==heading[0][3:] and entry['text']==source['text'][heading.start():end]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['decision']
primary_topics=[]
for record in deck_review['primary_topic_reviews_reused']:
 verify_recorded_source_hash(p/record['path'],record['sha256']);current=(p/record['path']).read_bytes().decode().replace('\r\n','\n')
 assert not record['whole_container_read']
 for entry in record['topics']:
  assert entry['whole_topic_read'] and entry['previous_topic_review_reused'] and entry['text'].replace('\r\n','\n') in current
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'];primary_topics.append(entry['topic'])
assert set(primary_topics)=={'0056','0031'} and len(primary_topics)==2
wiki_topics=[]
for record in deck_review['wiki_topic_reviews_reused']:
 verify_recorded_source_hash(p/record['path'],record['sha256']);current=(p/record['path']).read_bytes().decode()
 assert not record['whole_container_read']
 for entry in record['topics']:
  assert entry['whole_topic_read'] and entry['previous_topic_review_reused'] and entry['text'] in current
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'];wiki_topics.append(entry['topic'])
assert set(wiki_topics)=={'상위_차원계.txt','뇌네.txt','축적계.txt','%EB%82%AE%EC%9D%80_%EB%B0%94%EC%9D%B4%ED%8A%B8_%EA%B5%AC%EC%84%B1.txt'} and len(wiki_topics)==4
ar=legacy['cyberpunk_pack_deck_audit_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['major_sections'])==(2,12,[12,15])
assert (ar['completion_checkboxes_checked'],ar['completion_checkboxes_pending'],ar['explicit_pending_rows'])==(2,1,5)
assert ar['concept_inventory_counts']==[16,9,5] and (ar['TODO_concept_rows'],ar['byte_density_repeated_rows'])==(18,2)
assert ar['printed_density_exponents']==[24,20,16,12,4,0,28] and ar['jo_to_man_printed_density_ratio']==100000000
assert ar['initial_audit_scope_rows']==17 and ar['initial_read_modes']=={'whole':9,'partial':6,'skipped':1,'missing':1}
assert (ar['initial_issue_count'],ar['appendix_C_changed_count'],ar['appendix_D_remaining_count'],ar['appendix_E_claimed_count'])==(20,10,10,63)
assert ar['illustrative_mass_grams']==60000 and ar['illustrative_body_to_one_high_gram_byte_ratio']['decimal']==6.0
for flag in ['illustrative_mass_is_source_canonical_profile','illustrative_ratio_is_travel_permission','all_audit_completion_claims_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']:assert not ar[flag]
assert (reference['semantic_topic_routes_checked'],reference['existing_wrong_topic_routes_rejected'])==(3,3) and not reference['all_appendix_link_meanings_verified']
for phrase in ['### 실제 세계를 보고, 실제 대상에 접속하기','보정 기록을 빌리는 저녁','[직업](#fewk-world-62)','[뇌네](#fewk-noene)','[축적계](#fewk-world-74)']:assert phrase in world_text
assert world_text.count('<a id="fewk-noene"></a>')==1
d['current_cyberpunk_pack_deck_audit_review']={'Core':'v0.35','World':'v0.61','Sheet':'v0.35','Easy':'P v0.25','Design':'v0.87','whole_documents_reviewed':2,'whole_source_lines':[407,706],'major_sections_mapped':27,'limited_legacy_arithmetic_checks':12,'primary_whole_topics_reused':2,'wiki_whole_topics_reused':4,'corrected_reader_topic_routes':3,'reference_checks':72,'pack_family_cumulative_whole_reviews':19,'pack_family_pending':2,'bounded_cumulative_whole_reviews':45,'bounded_cumulative_pending':45,'all_audit_completion_claims_verified':False,'all_appendix_link_meanings_verified':False,'all_specific_use_profiles_complete':False,'all_older_unique_sources_reviewed':False,'new_related_novels_whole_read':0,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
wc_review=legacy_coherence['cyberpunk_pack_world_correction_review']
assert (wc_review['whole_documents_read'],len(wc_review['major_section_mapping']),wc_review['major_sections_by_file'])==(2,27,[18,9])
assert (wc_review['pack_family_cumulative_documents_reviewed'],wc_review['pack_family_documents_pending'])==(21,0) and wc_review['all_cyberpunk_pack_documents_reviewed']
assert wc_review['versions']=={'Core':'v0.35','World':'v0.62','Sheet':'v0.35','Easy':'P v0.25','Design':'v0.88','Tarot':'v0.3'}
assert wc_review['new_mechanical_parameter_values']==[] and wc_review['new_related_novels_whole_read']==wc_review['new_primary_topics_whole_read']==0
assert (wc_review['correction_detailed_issue_blocks'],wc_review['correction_label_rows'],wc_review['declared_correction_codes'])==(39,17,63)
for flag in ['all_63_reported_items_are_distinct_actual_errors','all_original_facts_verified','all_audit_completion_claims_verified','all_specific_use_profiles_complete','all_older_unique_sources_reviewed','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not wc_review[flag]
source_by_name={unicodedata.normalize('NFC',s['name']):s for s in wc_review['snapshots']}
assert set(source_by_name)=={'01_World_Background.md','사이버팩수정리스트1.md'}
for name,shape in [('01_World_Background.md',(63181,35406,989)),('사이버팩수정리스트1.md',(48710,28762,613))]:
 source=source_by_name[name];data=source['text'].encode()
 assert source['whole_document_read'] and (len(data),len(source['text']),len(source['text'].splitlines()))==shape
 assert (source['bytes'],source['chars'],source['lines'])==shape and source['migration_decisions']
 assert hashlib.sha256(data).hexdigest()==source['sha256'];verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
 assert any(e['name']==source['name'] and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
 rows=[entry for entry in wc_review['major_section_mapping'] if entry['source_name']==source['name']]
 assert len(rows)==(18 if name.startswith('01_') else 9)
 offsets=list(re.finditer(r'^## [^\n]+',source['text'],re.M));assert len(offsets)==len(rows)
 for i,(heading,entry) in enumerate(zip(offsets,rows)):
  end=offsets[i+1].start() if i+1<len(offsets) else len(source['text'])
  assert entry['title']==heading[0][3:] and entry['text']==source['text'][heading.start():end]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['decision']
correction=source_by_name['사이버팩수정리스트1.md']['text'];heads3=list(re.finditer(r'^### ([^\n]+)',correction,re.M));expected=[]
for i,h in enumerate(heads3):
 match=re.match(r'((?:C|M|m)-\d+(?:~\d+)?)\.',h[1])
 if match:expected.append((match[1],h[1],correction[h.start():heads3[i+1].start() if i+1<len(heads3) else len(correction)]))
assert len(expected)==len(wc_review['correction_issue_block_mapping'])==39
for (code,title,text),entry in zip(expected,wc_review['correction_issue_block_mapping']):
 assert (entry['code'],entry['title'],entry['text'])==(code,title,text) and entry['decision']
 assert hashlib.sha256(text.encode()).hexdigest()==entry['sha256'] and not entry['all_claimed_original_facts_verified'] and not entry['current_individual_numeric_profile_complete']
label_block=correction[correction.index('## 5.'):correction.index('## 6.')];label_rows=[line for line in label_block.splitlines() if line.startswith('| L-')]
assert len(label_rows)==len(wc_review['correction_label_row_mapping'])==17
for line,entry in zip(label_rows,wc_review['correction_label_row_mapping']):
 assert entry['text']==line and entry['code']==line.split('|')[1].strip() and entry['reported_already_labeled_pass']==('✓ 합격' in line) and entry['decision']
 assert hashlib.sha256(line.encode()).hexdigest()==entry['sha256']
assert [e['code'] for e in wc_review['correction_label_row_mapping'] if e['reported_already_labeled_pass']]==['L-12','L-13']
primary_topics=[]
for record in wc_review['primary_topic_reviews_reused']:
 verify_recorded_source_hash(p/record['path'],record['sha256']);current=(p/record['path']).read_bytes().decode().replace('\r\n','\n')
 assert not record['whole_container_read']
 for entry in record['topics']:
  assert entry['whole_topic_read'] and entry['previous_topic_review_reused'] and entry['text'].replace('\r\n','\n') in current
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'];primary_topics.append(entry['topic'])
assert set(primary_topics)=={'0001','0005','0006','0008','0022','0023','0046'} and len(primary_topics)==7
wiki=wc_review['wiki_topic_recheck'];verify_recorded_source_hash(p/wiki['source_path_relative_to_plan'],wiki['source_sha256']);current=(p/wiki['source_path_relative_to_plan']).read_bytes().decode()
assert not wiki['whole_container_read'] and len(wiki['topics'])==8
assert {e['decoded_topic'].lower() for e in wiki['topics']}=={'사건_대신단출.txt','사건_진신단출.txt','스타일지구.txt','연호.txt','민.txt','케이티.txt','대령대사국.txt','ddogg.txt'}
for entry in wiki['topics']:
 assert entry['whole_topic_read'] and entry['text'] in current and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
ar=legacy['cyberpunk_pack_world_correction_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['major_sections'])==(2,16,[18,9])
assert ar['declared_correction_class_counts']==[12,23,11,17] and ar['declared_correction_code_total']==63
assert (ar['detailed_issue_heading_count'],ar['detailed_issue_heading_counts'],ar['expanded_C_M_m_codes'],ar['label_rows'])==(39,[12,16,11],46,17)
assert ar['already_passing_label_rows']==['L-12','L-13'] and ar['label_rows_other_than_already_passing']==15
assert (ar['main_layer_rows'],ar['appendix_declared_layers'],ar['appendix_actual_density_rows'])==(7,8,9) and ar['appendix_printed_density_exponents']==[32,28,24,20,16,12,8,4,0]
assert [x['decimal'] for x in ar['old_Ego10_limits_minutes']]==[144000,14400,1440,150,15]
assert [x['decimal'] for x in ar['old_weapon_price_ratios']]==[1.5,1.5,4,10] and ar['old_insurance_monthly_price_ratio']['decimal']==100
assert ar['nominal_report_sample']==250 and [x['decimal'] for x in ar['nominal_report_shares']]==[68,18.4,13.6]
for flag in ['same_insurance_product_proven','all_63_reported_codes_are_distinct_actual_errors','all_audit_completion_claims_verified','all_nominal_sample_items_revalidated','canonical_current_year_fixed','legacy_price_layer_or_track_parameters_adopted','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']:assert not ar[flag]
for phrase in ['### 같은 사건, 다른 삶의 이유','| 원본0006의 민과 가족','| 원본0001의 케이티','| 원본0005의 진','| 대신단출 |','**대신단출·진신단출·국소 신단출은 발생 맥락이 다릅니다.**']:assert phrase in world_text
assert '이 첫 본문은 검증하지 않은 재난 통계를' not in world_text
assert all(e['whole_document_reviewed_cumulatively'] for e in pack_inventory)
d['current_cyberpunk_pack_world_correction_review']={'Core':'v0.35','World':'v0.62','Sheet':'v0.35','Easy':'P v0.25','Design':'v0.88','whole_documents_reviewed':2,'whole_source_lines':[989,613],'major_sections_mapped':27,'detailed_correction_issue_blocks':39,'correction_label_rows':17,'limited_legacy_arithmetic_checks':16,'primary_whole_topics_reused':7,'wiki_whole_topics':8,'pack_family_cumulative_whole_reviews':21,'pack_family_pending':0,'bounded_cumulative_whole_reviews':47,'bounded_cumulative_pending':43,'registered_cyberpunk_pack_whole_review_complete':True,'all_63_reported_codes_are_distinct_actual_errors':False,'all_original_facts_verified':False,'all_specific_use_profiles_complete':False,'all_older_unique_sources_reviewed':False,'new_related_novels_whole_read':0,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
fw_review=legacy_coherence['framework_foundation_review']
assert (fw_review['whole_documents_read'],len(fw_review['major_section_mapping']),fw_review['major_sections_by_file'])==(4,40,[8,7,11,14])
assert (fw_review['framework_family_cumulative_whole_reviews'],fw_review['framework_family_pending'])==(7,14)
assert fw_review['versions']=={'Core':'v0.36','World':'v0.62','Sheet':'v0.35','Easy':'P v0.26','Design':'v0.89','Tarot':'v0.3'} and fw_review['new_mechanical_parameter_values']==[]
for flag in ['external_system_stat_counts_verified','external_licensing_or_legal_clearance_verified','online_plugin_or_macros_executed','fixed_three_aces_required_by_source','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','all_older_unique_sources_reviewed','all_specific_use_profiles_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not fw_review[flag]
assert fw_review['new_related_novels_whole_read']==0
source_by_name={s['name']:s for s in fw_review['snapshots']}
assert set(source_by_name)=={'00_Overview.md','01_Core_Principles.md','02_Dice_System.md','06_Resolution_System.md'}
shapes={'00_Overview.md':(12908,8167,302,8),'01_Core_Principles.md':(18255,11516,541,7),'02_Dice_System.md':(14814,9879,508,11),'06_Resolution_System.md':(13150,8648,496,14)}
for name,(byte_count,char_count,line_count,section_count) in shapes.items():
 source=source_by_name[name];data=source['text'].encode()
 assert source['whole_document_read'] and (len(data),len(source['text']),len(source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (source['bytes'],source['chars'],source['lines'])==(byte_count,char_count,line_count) and len(source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==source['sha256'];verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
 assert any(e['name']==name and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
 rows=[entry for entry in fw_review['major_section_mapping'] if entry['source_name']==name];offsets=list(re.finditer(r'^## [^\n]+',source['text'],re.M));assert len(rows)==len(offsets)==section_count
 for i,(heading,entry) in enumerate(zip(offsets,rows)):
  end=offsets[i+1].start() if i+1<len(offsets) else len(source['text'])
  assert entry['title']==heading[0][3:] and entry['text']==source['text'][heading.start():end] and entry['decision']==source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==source['text'][:heading.start()].count('\n')+1
framework_inventory=[e for e in inventory['files'] if 'Framework Core' in e['path_relative_to_plan']]
assert len(framework_inventory)==21 and sum(e['whole_document_reviewed_cumulatively'] for e in framework_inventory)==21
for source in fw_review['snapshots']:
 row=next(e for e in framework_inventory if e['path_relative_to_plan']==source['path_relative_to_plan'])
 assert row['whole_document_reviewed_cumulatively'] and row['sha256']==source['sha256']
ar=legacy['framework_foundation_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['major_sections'])==(4,13,[8,7,11,14])
assert ar['door_example_different_TNs']==[15,25,25] and ar['door_example_margins']==[10,1,0,5]
assert ar['legend_mean']['decimal']==85 and ar['legend_minimum']==19 and ar['legend_mean_margin']['decimal']==25
assert ar['six_times_d10_variance']['decimal']==297 and ar['six_d10_variance']['decimal']==49.5
assert ar['unmapped_d10_range']==[11,110] and ar['pool_sample_hits']==6 and ar['resolution_example_totals']==[27,13,44]
for flag in ['all_legacy_random_distributions_verified','external_system_or_legal_claims_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']:assert not ar[flag]
core_text=(o/'10_CoreRulebook.md').read_text();easy_text=(o/'01_텀블벅_이지룰_초안.md').read_text()
for phrase in ['#### 설명의 상세도와 판정값','같은 목표·방법·현재 몸/장비·상황이면 같은 판정값과 결과 규약','어느 작성 방식에서도 목표50','같은 굴림62는 같은 실패','새로운 조건의 시도','별도 ‘가능성 확인’']:assert phrase in core_text
assert '짧은 선언·상세한 전술 설명·커뮤 게시물도 같은 몸/장비·방법·상황에서는 같은 목표값과 결과 규약' in easy_text
d['current_framework_foundation_review']={'Core':'v0.36','World':'v0.62','Sheet':'v0.35','Easy':'P v0.26','Design':'v0.89','whole_documents_reviewed':4,'whole_source_lines':[302,541,508,496],'major_sections_mapped':40,'limited_legacy_arithmetic_checks':13,'framework_family_cumulative_whole_reviews':7,'framework_family_pending':14,'bounded_cumulative_whole_reviews':51,'bounded_cumulative_pending':39,'same_facts_same_resolution_clarified':True,'current_engine_changed':False,'all_older_unique_sources_reviewed':False,'all_specific_use_profiles_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
fc_review=legacy_coherence['framework_character_combat_review']
assert (fc_review['whole_documents_read'],len(fc_review['major_section_mapping']),fc_review['major_sections_by_file'])==(3,47,[11,19,17])
assert (fc_review['framework_family_cumulative_whole_reviews'],fc_review['framework_family_pending'],fc_review['bounded_cumulative_whole_reviews'],fc_review['bounded_cumulative_pending'])==(10,11,54,36)
assert fc_review['versions']=={'Core':'v0.37','World':'v0.62','Sheet':'v0.35','Easy':'P v0.27','Design':'v0.90','Tarot':'v0.3'} and fc_review['new_mechanical_parameter_values']==[]
for flag in ['external_game_rules_verified','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','all_older_unique_sources_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not fc_review[flag]
assert fc_review['new_related_novels_whole_read']==0
source_by_name={s['name']:s for s in fc_review['snapshots']}
shapes={'03_Stats_and_Attributes.md':(13555,9976,525,11),'04_Character_Creation.md':(33777,22947,1035,19),'05_Combat_Scales.md':(18244,11867,649,17)}
assert set(source_by_name)==set(shapes)
for name,(byte_count,char_count,line_count,section_count) in shapes.items():
 source=source_by_name[name];data=source['text'].encode()
 assert source['whole_document_read'] and (len(data),len(source['text']),len(source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (source['bytes'],source['chars'],source['lines'])==(byte_count,char_count,line_count) and len(source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==source['sha256'];verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
 assert any(e['name']==name and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
 rows=[entry for entry in fc_review['major_section_mapping'] if entry['source_name']==name];offsets=list(re.finditer(r'^## [^\n]+',source['text'],re.M));assert len(rows)==len(offsets)==section_count
 for i,(heading,entry) in enumerate(zip(offsets,rows)):
  end=offsets[i+1].start() if i+1<len(offsets) else len(source['text'])
  assert entry['title']==heading[0][3:] and entry['text']==source['text'][heading.start():end] and entry['decision']==source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==source['text'][:heading.start()].count('\n')+1
  assert entry['decision']
 row=next(e for e in framework_inventory if e['path_relative_to_plan']==source['path_relative_to_plan'])
 assert row['whole_document_reviewed_cumulatively'] and row['sha256']==source['sha256']
ar=legacy['framework_character_combat_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['major_sections'],ar['stat_table_rows'])==(3,23,[11,19,17],25) and ar['both_stat_cost_and_grade_tables_agree']
assert ar['tier_cost_increments']==[6,12,16,20,26] and (ar['creation_declared_steps'],ar['creation_actual_steps'])==(10,12)
assert ar['creation_five_example_stat_totals']==[88,93,82,92,51] and (ar['creation_yaml_actual_stat_cost'],ar['creation_yaml_actual_total'],ar['creation_yaml_approved_budget'],ar['creation_yaml_over_budget'])==(97,111,105,6)
assert (ar['novice_actual_spent'],ar['novice_remaining'])==(68,7) and ar['BOD7_undefined_negative_HP_values']==list(range(-13,-7))
assert ar['old_range_grid_overlap']==[1] and ar['current_common_60second_rounds']==12
for flag in ['external_game_rules_verified','all_legacy_random_distributions_verified','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']:assert not ar[flag]
core_text=(o/'10_CoreRulebook.md').read_text();easy_text=(o/'01_텀블벅_이지룰_초안.md').read_text()
for phrase in ['#### 지도를 바꿔도 거리와 시간이 이어집니다','입문 몸의10m 이동은1m 지도에서10칸,5m 지도에서2칸','같은 현지 시각','60초는5초 라운드12번','큰 칸']:
 if phrase=='큰 칸':assert phrase in easy_text
 else:assert phrase in core_text
assert '같은 몸의 이동량·사거리·5초 라운드와 행동 예산' in easy_text
d['current_framework_character_combat_review']={'Core':'v0.37','World':'v0.62','Sheet':'v0.35','Easy':'P v0.27','Design':'v0.90','whole_documents_reviewed':3,'whole_source_lines':[525,1035,649],'major_sections_mapped':47,'limited_legacy_arithmetic_checks':23,'framework_family_cumulative_whole_reviews':10,'framework_family_pending':11,'bounded_cumulative_whole_reviews':54,'bounded_cumulative_pending':36,'same_actual_distance_and_time_across_maps':True,'current_engine_changed':False,'old_100point_build_rewritten':False,'all_older_unique_sources_reviewed':False,'all_specific_use_profiles_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
rg_review=legacy_coherence['framework_resource_growth_review']
assert (rg_review['whole_documents_read'],len(rg_review['major_section_mapping']),rg_review['major_sections_by_file'])==(3,43,[12,14,17])
assert (rg_review['framework_family_cumulative_whole_reviews'],rg_review['framework_family_pending'],rg_review['bounded_cumulative_whole_reviews'],rg_review['bounded_cumulative_pending'])==(13,8,57,33)
assert rg_review['versions']=={'Core':'v0.38','World':'v0.62','Sheet':'v0.35','Easy':'P v0.28','Design':'v0.91','Tarot':'v0.3'} and rg_review['new_mechanical_parameter_values']==[]
for flag in ['external_game_rules_verified','all_legacy_logs_are_complete_histories','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','all_older_unique_sources_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not rg_review[flag]
assert rg_review['new_related_novels_whole_read']==0
source_by_name={s['name']:s for s in rg_review['snapshots']}
shapes={'07_Resources_Tokens.md':(19917,12582,656,12),'08_Track_System.md':(21524,13579,636,14),'09_Growth_Progression.md':(22105,14716,744,17)}
assert set(source_by_name)==set(shapes)
for name,(byte_count,char_count,line_count,section_count) in shapes.items():
 source=source_by_name[name];data=source['text'].encode()
 assert source['whole_document_read'] and (len(data),len(source['text']),len(source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (source['bytes'],source['chars'],source['lines'])==(byte_count,char_count,line_count) and len(source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==source['sha256'];verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
 assert any(e['name']==name and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
 rows=[entry for entry in rg_review['major_section_mapping'] if entry['source_name']==name];offsets=list(re.finditer(r'^## [^\n]+',source['text'],re.M));assert len(rows)==len(offsets)==section_count
 for i,(heading,entry) in enumerate(zip(offsets,rows)):
  end=offsets[i+1].start() if i+1<len(offsets) else len(source['text'])
  assert entry['title']==heading[0][3:] and entry['text']==source['text'][heading.start():end] and entry['decision']==source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==source['text'][:heading.start()].count('\n')+1 and entry['decision']
 row=next(e for e in framework_inventory if e['path_relative_to_plan']==source['path_relative_to_plan'])
 assert row['whole_document_reviewed_cumulatively'] and row['sha256']==source['sha256']
ar=legacy['framework_resource_growth_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['major_sections'],ar['ego_formula_rows'])==(3,22,[12,14,17],10)
assert (ar['supply_log_printed_amount'],ar['supply_log_amount_from_printed_formula'])==(3,6)
assert ar['Pool_log_prefix_if_start_once']==[7,2,5] and ar['Pool_log_prefix_if_supply_corrected']==[7,2,8] and ar['both_Pool_log_prefixes_cannot_pay_10']
assert ar['genre_start_required_for_printed_current6']==5 and ar['assumed_zero_start_genre_log_net_change']==1
assert ar['threshold_ranges']==[[1,20],[21,50],[51,75],[76,90],[91,100]]
assert ar['threshold_modified_roll_counts']=={'0':[20,30,25,15,10],'20':[0,30,25,15,30],'-10':[30,30,25,15,0],'10':[10,30,25,15,20]}
assert ar['goal50_failure_overlap_rolls']==[60] and ar['goal50_failure_unassigned_non100_rolls']==list(range(81,100))
assert ar['fourp_session_single_upgrade_ceiling']==[1,2,2,3,4,5,7]
assert [x['decimal'] for x in ar['replacement_budget_250_two_values']]==[200,187.5] and [x['decimal'] for x in ar['replacement_budget_400_two_values']]==[300,280]
for flag in ['all_legacy_logs_are_complete_histories','all_legacy_random_distributions_verified','all_specific_use_profiles_complete','external_game_rules_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']:assert not ar[flag]
core_text=(o/'10_CoreRulebook.md').read_text();easy_text=(o/'01_텀블벅_이지룰_초안.md').read_text()
for phrase in ['#### 한 이야기 끝에 여러 변화를 정리하기','| 배운 숙련 |','| 새 인터랙션/전문 범위 |','| 장치 교체/몸 정비 |','| 일자리·관계·약속 |','| 휴식/존재 유지 |','공방에서 배운 해킹50→55와 새 단말의 인계','빠진 비용이나 관계를 추측해 채우지 않습니다']:assert phrase in core_text
assert '모임 종료는 탄약·HP·존재 유지의 초기화가 아닙니다' in easy_text
d['current_framework_resource_growth_review']={'Core':'v0.38','World':'v0.62','Sheet':'v0.35','Easy':'P v0.28','Design':'v0.91','whole_documents_reviewed':3,'whole_source_lines':[656,636,744],'major_sections_mapped':43,'limited_legacy_arithmetic_checks':22,'framework_family_cumulative_whole_reviews':13,'framework_family_pending':8,'bounded_cumulative_whole_reviews':57,'bounded_cumulative_pending':33,'independent_skill_function_gear_relation_and_residence_changes':True,'current_engine_changed':False,'old_100point_build_rewritten':False,'all_legacy_logs_are_complete_histories':False,'all_older_unique_sources_reviewed':False,'all_specific_use_profiles_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
play_review=legacy_coherence['framework_team_NPC_session_review']
assert (play_review['whole_documents_read'],len(play_review['major_section_mapping']),play_review['major_sections_by_file'])==(3,40,[12,14,14])
assert (play_review['framework_family_cumulative_whole_reviews'],play_review['framework_family_pending'],play_review['bounded_cumulative_whole_reviews'],play_review['bounded_cumulative_pending'])==(16,5,60,30)
assert play_review['versions']=={'Core':'v0.39','World':'v0.62','Sheet':'v0.35','Easy':'P v0.29','Design':'v0.92','Tarot':'v0.3'} and play_review['new_mechanical_parameter_values']==[]
for flag in ['external_game_rules_verified','all_legacy_logs_are_complete_histories','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','all_older_unique_sources_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not play_review[flag]
assert play_review['new_related_novels_whole_read']==0
source_by_name={s['name']:s for s in play_review['snapshots']}
shapes={'10_Team_and_Retry.md':(23898,14814,756,12),'11_NPC_Standard.md':(22151,14691,809,14),'12_Session_Campaign.md':(22716,13988,599,14)}
assert set(source_by_name)==set(shapes)
for name,(byte_count,char_count,line_count,section_count) in shapes.items():
 source=source_by_name[name];data=source['text'].encode()
 assert source['whole_document_read'] and (len(data),len(source['text']),len(source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (source['bytes'],source['chars'],source['lines'])==(byte_count,char_count,line_count) and len(source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==source['sha256'];verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
 assert any(e['name']==name and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
 rows=[entry for entry in play_review['major_section_mapping'] if entry['source_name']==name];offsets=list(re.finditer(r'^## [^\n]+',source['text'],re.M));assert len(rows)==len(offsets)==section_count
 for i,(heading,entry) in enumerate(zip(offsets,rows)):
  end=offsets[i+1].start() if i+1<len(offsets) else len(source['text'])
  assert entry['title']==heading[0][3:] and entry['text']==source['text'][heading.start():end] and entry['decision']==source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==source['text'][:heading.start()].count('\n')+1 and entry['decision']
 row=next(e for e in framework_inventory if e['path_relative_to_plan']==source['path_relative_to_plan'])
 assert row['whole_document_reviewed_cumulatively'] and row['sha256']==source['sha256']
ar=legacy['framework_team_NPC_session_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['major_sections'])==(3,23,[12,14,14])
assert [x['decimal'] for x in ar['helper_thresholds']]==[31.5,4.5] and [x['decimal'] for x in ar['helper_success_probabilities']]==[1/4096,0.5]
assert (ar['team_leader_result'],ar['team_total_result'],ar['Pool_minimum_current_for_contribution15'],ar['Pool_max_contributors_if_15_each_and_total30'])==(42,55,29,2)
assert ar['attitude_conditions']==[[4,4,3,10],[4,4,3,15],[4,6,4,15],[4,6,4,20],[5,8,5,25]]
assert [(x['numerator'],x['denominator']) for x in ar['attitude_partial_plus_exact_exploding']]==[(241,256),(145,256),(829,972),(1979,3888),(99205,131072)]
assert ar['NPC_reaction_unassigned_outputs']==[-2,-1,0,7]
assert (ar['zero_cast_Pool_cap'],ar['zero_cast_requested_Pool'],ar['zero_cast_shortfall'])==(11,15,4) and ar['boss_conditional_weapon_margins']==[19,30]
assert (ar['session_log_minutes'],ar['session_declared_minutes'],ar['session_unitemized_minutes'])==(220,240,20) and ar['session_major_roll_actual_qualities']==['Full','Full']
assert ar['session_printed_earned_points']==[5,6,14] and ar['session_points_if_everyone_receives_named_milestone']==[15,16,14]
for flag in ['all_legacy_logs_are_complete_histories','all_legacy_random_distributions_verified','all_specific_use_profiles_complete','external_game_rules_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']:assert not ar[flag]
core_text=(o/'10_CoreRulebook.md').read_text();easy_text=(o/'01_텀블벅_이지룰_초안.md').read_text()
for phrase in ['#### 부탁한 일과 실제로 맡은 일','| 부탁했고 답을 기다림 |','| 거절하거나 다른 조건을 제시함 |','| 제공할 정보/물건에 합의함 |','| 실제로 전달하거나 작업을 시작함 |','한 씨가 자기 영수증REC-HAN-01을 보내기로 동의했다면','단골 명단은 그 합의의 대상이 아니고']:assert phrase in core_text
assert '대화에서는 부탁·합의·실제 실행을 구분해 남깁니다' in easy_text
d['current_framework_team_NPC_session_review']={'Core':'v0.39','World':'v0.62','Sheet':'v0.35','Easy':'P v0.29','Design':'v0.92','whole_documents_reviewed':3,'whole_source_lines':[756,809,599],'major_sections_mapped':40,'limited_legacy_arithmetic_checks':23,'framework_family_cumulative_whole_reviews':16,'framework_family_pending':5,'bounded_cumulative_whole_reviews':60,'bounded_cumulative_pending':30,'request_agreement_and_execution_separated':True,'current_engine_changed':False,'old_100point_build_rewritten':False,'all_legacy_logs_are_complete_histories':False,'all_older_unique_sources_reviewed':False,'all_specific_use_profiles_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
final_framework=legacy_coherence['framework_final_reader_review']
assert (final_framework['whole_documents_read'],len(final_framework['major_section_mapping']),final_framework['major_sections_by_file'])==(5,63,[12,13,11,17,10])
assert (final_framework['framework_family_cumulative_whole_reviews'],final_framework['framework_family_pending'],final_framework['bounded_cumulative_whole_reviews'],final_framework['bounded_cumulative_pending'])==(21,0,65,25) and final_framework['framework_registered_family_complete']
assert final_framework['versions']=={'Core':'v0.40','World':'v0.62','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.93','Tarot':'v0.3'} and final_framework['new_mechanical_parameter_values']==[]
for flag in ['live_application_execution_verified','external_game_rules_verified','all_legacy_logs_are_complete_histories','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','all_older_unique_sources_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not final_framework[flag]
assert final_framework['new_related_novels_whole_read']==0 and final_framework['tool_documentation_semantics_verified']
tool_docs=final_framework['tool_documentation'];assert len(tool_docs)==2
assert [doc['url'] for doc in tool_docs]==['https://help.roll20.net/hc/en-us/articles/360037773133-Dice-Reference','https://foundryvtt.com/article/dice-modifiers/']
assert all(doc['checked_date']=='2026-10-06' and doc['scope'] and not doc['live_application_execution_verified'] for doc in tool_docs)
source_by_tag={s['tag']:s for s in final_framework['snapshots']}
shapes={'13':(14082,9854,502,12),'14':(12016,7742,439,13),'15':(18426,12599,590,11),'16':(22975,13851,698,17),'README':(10009,7066,288,10)}
assert set(source_by_tag)==set(shapes)
for tag,(byte_count,char_count,line_count,section_count) in shapes.items():
 source=source_by_tag[tag];data=source['text'].encode();name=source['name']
 assert source['whole_document_read'] and (len(data),len(source['text']),len(source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (source['bytes'],source['chars'],source['lines'])==(byte_count,char_count,line_count) and len(source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==source['sha256'];verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
 assert any(e['name']==name and e['sha256']==source['sha256'] and e['whole_document_read'] for e in additional_procurement)
 rows=[entry for entry in final_framework['major_section_mapping'] if entry['source_name']==name];offsets=list(re.finditer(r'^## [^\n]+',source['text'],re.M));assert len(rows)==len(offsets)==section_count
 for i,(heading,entry) in enumerate(zip(offsets,rows)):
  end=offsets[i+1].start() if i+1<len(offsets) else len(source['text'])
  assert entry['title']==heading[0][3:] and entry['text']==source['text'][heading.start():end] and entry['decision']==source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==source['text'][:heading.start()].count('\n')+1 and entry['decision']
 row=next(e for e in framework_inventory if e['path_relative_to_plan']==source['path_relative_to_plan'])
 assert row['whole_document_reviewed_cumulatively'] and row['sha256']==source['sha256']
ar=legacy['framework_final_reader_arithmetic']
assert (ar['documents'],ar['checks_passed'],ar['major_sections'],ar['online_grade_rows_checked'])==(5,21,[12,13,11,17,10],6)
assert ar['prose_balance_costs']==[26,26,15,20,5,5] and (ar['prose_balance_total_points'],ar['prose_balance_remaining_points'],ar['prose_same_PC_additional_shoot4_dodge2_cost'])==(97,3,13) and ar['prose_same_PC_history_missing_for_additional_skills']
assert (ar['Pool_sample_hits'],ar['Pool_sample_face_sum'],ar['damage_multiplier_support_values'],ar['six_damage_dice_support_values'])==(6,43,10,55)
assert (ar['multiplied_damage_variance']['decimal'],ar['six_damage_dice_variance']['decimal'])==(297,49.5)
assert (ar['gang_BOD5_formula_HP'],ar['gang_HP_after_printed_damage10'])==(25,15)
assert ar['prose_session_minutes']==[130,240] and ar['glossary_BOD7_negative_HP_gap']==list(range(-13,-7))
assert (ar['README_numbered_modules'],ar['README_declared_module_count_with_self'],ar['README_count_with_additional_16_guide'])==(16,17,18)
assert ar['tool_documentation_pages_verified']==2
for flag in ['live_application_execution_verified','all_legacy_logs_are_complete_histories','all_legacy_random_distributions_verified','all_specific_use_profiles_complete','external_game_rules_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']:assert not ar[flag]
core_text=(o/'10_CoreRulebook.md').read_text();easy_text=(o/'01_텀블벅_이지룰_초안.md').read_text()
for phrase in ['#### 새 차원 룰시트를 함께 사용할 때','| 차원ID·룰시트/규격 버전·세계 출처 |','| IO계통·반입/반출·신체 이전·보관 |','| 인물·공통 숙련·성공 수준·대립/성장 |','환경 차이만으로 모든 공격을 본체 피해나 별도 정신 전투로 바꾸지 않습니다','90의절반45이하이므로 좋은 성공입니다']:assert phrase in core_text
assert '어려운 성공' not in core_text and '새 차원에서는 룰시트의 판본·환경·지원 몸/장비·IO와 보관 조건을 확인합니다' in easy_text
d['current_framework_final_reader_review']={'Core':'v0.40','World':'v0.62','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.93','whole_documents_reviewed':5,'whole_source_lines':[502,439,590,698,288],'major_sections_mapped':63,'limited_legacy_arithmetic_checks':21,'framework_family_cumulative_whole_reviews':21,'framework_family_pending':0,'framework_registered_family_complete':True,'bounded_cumulative_whole_reviews':65,'bounded_cumulative_pending':25,'same_engine_and_state_across_dimension_rulesheets':True,'success_level_terms_unified':True,'tool_documentation_pages_verified':2,'live_application_execution_verified':False,'current_engine_changed':False,'old_100point_build_rewritten':False,'all_legacy_logs_are_complete_histories':False,'all_older_unique_sources_reviewed':False,'all_specific_use_profiles_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
relation_review=legacy_coherence['first_relationship_chronology_review']
assert (relation_review['whole_documents_read'],len(relation_review['major_section_mapping']),relation_review['major_sections_by_file'])==(4,25,[8,6,5,6])
assert (relation_review['first_family_cumulative_whole_reviews'],relation_review['first_family_pending'],relation_review['bounded_cumulative_whole_reviews'],relation_review['bounded_cumulative_pending'])==(11,21,69,21)
assert relation_review['versions']=={'Core':'v0.40','World':'v0.63','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.94','Tarot':'v0.3'} and relation_review['new_mechanical_parameter_values']==[]
for flag in ['all_older_unique_sources_reviewed','all_related_novels_reviewed','all_first_chronology_dates_canon_verified','all_relationships_canon_verified','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not relation_review[flag]
assert relation_review['new_related_novels_whole_read']==0 and relation_review['new_primary_review_totals_not_inferred']
rel_shapes={'01_인물관계도.md':(12239,6293,321,8),'02_인물별_사건별_장소관계도.md':(12364,6423,366,6),'03_연대기.md':(14992,8311,328,5),'03_연대기_총람.md':(18120,10472,225,6)}
assert {s['name'] for s in relation_review['snapshots']}==set(rel_shapes)
for rel_source in relation_review['snapshots']:
 name=rel_source['name'];byte_count,char_count,line_count,section_count=rel_shapes[name];data=rel_source['text'].encode()
 assert rel_source['whole_document_read'] and (len(data),len(rel_source['text']),len(rel_source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (rel_source['bytes'],rel_source['chars'],rel_source['lines'])==(byte_count,char_count,line_count) and len(rel_source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==rel_source['sha256'];verify_recorded_source_hash(p/rel_source['path_relative_to_plan'],rel_source['sha256'])
 assert any(e['name']==name and e['sha256']==rel_source['sha256'] and e['whole_document_read'] for e in additional_procurement)
 rel_rows=[entry for entry in relation_review['major_section_mapping'] if entry['source_name']==name];rel_offsets=list(re.finditer(r'^## [^\n]+',rel_source['text'],re.M));assert len(rel_rows)==len(rel_offsets)==section_count
 for i,(heading,entry) in enumerate(zip(rel_offsets,rel_rows)):
  end=rel_offsets[i+1].start() if i+1<len(rel_offsets) else len(rel_source['text'])
  assert entry['title']==heading[0][3:] and entry['text']==rel_source['text'][heading.start():end] and entry['decision']==rel_source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==rel_source['text'][:heading.start()].count('\n')+1 and entry['decision']
 rel_row=next(e for e in inventory['files'] if e['path_relative_to_plan']==rel_source['path_relative_to_plan'])
 assert rel_row['whole_document_reviewed_cumulatively'] and rel_row['sha256']==rel_source['sha256']
rel_first_inventory=[e for e in inventory['files'] if '1판_설정집' in unicodedata.normalize('NFC',e['path_relative_to_plan'])]
assert len(rel_first_inventory)==32 and sum(e['whole_document_reviewed_cumulatively'] for e in rel_first_inventory)==32
rel_primary=relation_review['primary_topic_recheck'];verify_recorded_source_hash(p/rel_primary['source_path_relative_to_plan'],rel_primary['sha256']);rel_raw=(p/rel_primary['source_path_relative_to_plan']).read_text();rel_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',rel_raw))
assert not rel_primary['whole_container_read'] and relation_review['primary_topics_whole_rechecked']==len(rel_primary['topics'])==10
assert [e['topic'] for e in rel_primary['topics']]==['0001','0005','0006','0036','0046','0053','0054','0092','0096','0099']
for entry in rel_primary['topics']:
 head=next(x for x in rel_heads if x[1]==entry['topic']);i=rel_heads.index(head);text=rel_raw[head.start():rel_heads[i+1].start() if i+1<len(rel_heads) else len(rel_raw)].strip()
 assert entry['whole_topic_read'] and text==entry['text'] and len(text)==entry['chars'] and hashlib.sha256(text.encode()).hexdigest()==entry['sha256']
rel_wiki=relation_review['wiki_topic_recheck'];verify_recorded_source_hash(p/rel_wiki['source_path_relative_to_plan'],rel_wiki['source_sha256']);rel_wiki_text=(p/rel_wiki['source_path_relative_to_plan']).read_text()
assert not rel_wiki['whole_container_read'] and relation_review['wiki_topics_whole_rechecked']==len(rel_wiki['topics'])==3
for entry in rel_wiki['topics']:assert entry['whole_topic_read'] and entry['text'] in rel_wiki_text and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256']
rel_ar=legacy['first_relationship_chronology_arithmetic']
assert (rel_ar['documents'],rel_ar['checks_passed'],rel_ar['major_sections'])==(4,14,[8,6,5,6])
assert rel_ar['assumed_common_AD_base']==1860 and rel_ar['FHI_horizon_years_if_common_AD']==[85,96,104,106] and not rel_ar['all_FHI_years_before_Horizon1_if_common_AD']
assert (rel_ar['primary1965_plus54'],rel_ar['gap_after_assumed_currentAD2003'],rel_ar['red_dragon_birth_if_battle34_and_age15'],rel_ar['red_dragon_current_age_if_constant_calendar'])==(2019,16,19,125) and not rel_ar['red_dragon_dates_or_current_age_canon_verified']
assert rel_ar['chronology_stated_counts']==[14,12,6,11,82,4] and (rel_ar['chronology_stated_count_sum'],rel_ar['chronology_stated_percentage_sum'])==(129,101)
assert rel_ar['master_table_type_counts']=={'[추산]':6,'[확정]':13,'[범위]':7,'[현재]':100,'[미래]':3,'[한계]':1}
assert (rel_ar['master_table_rows'],rel_ar['current_rows_in_master_table'],rel_ar['numbered_summary_rows'],rel_ar['primary_topics_whole_rechecked'],rel_ar['wiki_topics_whole_rechecked'])==(130,100,11,10,3)
for flag in ['all_relationships_canon_verified','all_first_chronology_dates_canon_verified','all_related_novels_reviewed','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']:assert not rel_ar[flag]
rel_world=(o/'11_WorldLorebook.md').read_text();rel_plan=(p/'01_작업계획.md').read_text()
for phrase in ['### 이름과 관계를 시간표에 놓을 때','| 민과 소이 |','| 크리스·마리아·요섭 |','| 가보·가야·루드 |','| 적룡화 숙자 |','원본0054에서 팬인 요섭은 추모장을 찾아와 기타를 받고','신규 활용 제안']:assert phrase in rel_world
rel_current_plan=next(line for line in rel_plan.splitlines() if line.startswith('**현재 진행:**'))
assert '독자 편집/내용 대조' in rel_current_plan and '현재 파일/해시' in rel_current_plan
assert '현재 완료 범위 — 2026-10-07 사용자 정정' in rel_plan and '독자편집_대조.json' in rel_plan
d['current_first_relationship_chronology_review']={'Core':'v0.40','World':'v0.63','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.94','whole_documents_reviewed':4,'whole_source_lines':[321,366,328,225],'major_sections_mapped':25,'limited_legacy_arithmetic_checks':14,'primary_topics_whole_rechecked':10,'wiki_topics_whole_rechecked':3,'first_family_cumulative_whole_reviews':11,'first_family_pending':21,'bounded_cumulative_whole_reviews':69,'bounded_cumulative_pending':21,'relationships_names_and_observed_times_separated':True,'current_plan_header_refreshed':True,'current_engine_changed':False,'old_100point_build_rewritten':False,'all_related_novels_reviewed':False,'all_older_unique_sources_reviewed':False,'all_relationships_canon_verified':False,'all_first_chronology_dates_canon_verified':False,'all_specific_use_profiles_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
catalog_review=legacy_coherence['first_people_places_objects_groups_catalog_review']
assert (catalog_review['whole_documents_read'],len(catalog_review['major_section_mapping']),catalog_review['major_sections_by_file'])==(4,43,[5,13,13,12])
assert (catalog_review['first_family_cumulative_whole_reviews'],catalog_review['first_family_pending'],catalog_review['bounded_cumulative_whole_reviews'],catalog_review['bounded_cumulative_pending'])==(15,17,73,17)
assert catalog_review['versions']=={'Core':'v0.40','World':'v0.64','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.95','Tarot':'v0.3'} and catalog_review['new_mechanical_parameter_values']==[]
for flag in ['all_older_unique_sources_reviewed','all_related_novels_reviewed','all_catalog_entries_individually_canon_verified','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not catalog_review[flag]
assert catalog_review['new_related_novels_whole_read']==0 and catalog_review['new_primary_review_totals_not_inferred']
catalog_shapes={'04_전체인물리스트.md':(17600,10096,291,5),'05_전체장소리스트.md':(12039,6918,282,13),'06_전체사물리스트.md':(13392,7982,282,13),'07_전체집단리스트.md':(13699,7942,310,12)}
assert {entry['name'] for entry in catalog_review['snapshots']}==set(catalog_shapes)
for catalog_source in catalog_review['snapshots']:
 byte_count,char_count,line_count,section_count=catalog_shapes[catalog_source['name']];data=catalog_source['text'].encode()
 assert catalog_source['whole_document_read'] and (len(data),len(catalog_source['text']),len(catalog_source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (catalog_source['bytes'],catalog_source['chars'],catalog_source['lines'])==(byte_count,char_count,line_count) and len(catalog_source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==catalog_source['sha256'];verify_recorded_source_hash(p/catalog_source['path_relative_to_plan'],catalog_source['sha256'])
 assert any(entry['name']==catalog_source['name'] and entry['sha256']==catalog_source['sha256'] and entry['whole_document_read'] for entry in additional_procurement)
 catalog_rows=[entry for entry in catalog_review['major_section_mapping'] if entry['source_name']==catalog_source['name']];catalog_heads=list(re.finditer(r'^## [^\n]+',catalog_source['text'],re.M));assert len(catalog_rows)==len(catalog_heads)==section_count
 for i,(head,entry) in enumerate(zip(catalog_heads,catalog_rows)):
  end=catalog_heads[i+1].start() if i+1<len(catalog_heads) else len(catalog_source['text'])
  assert entry['title']==head[0][3:] and entry['text']==catalog_source['text'][head.start():end] and entry['decision']==catalog_source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==catalog_source['text'][:head.start()].count('\n')+1 and entry['decision']
 catalog_inventory=next(entry for entry in inventory['files'] if entry['path_relative_to_plan']==catalog_source['path_relative_to_plan'])
 assert catalog_inventory['whole_document_reviewed_cumulatively'] and catalog_inventory['sha256']==catalog_source['sha256']
catalog_primary=catalog_review['primary_topic_recheck'];verify_recorded_source_hash(p/catalog_primary['source_path_relative_to_plan'],catalog_primary['sha256']);catalog_raw=(p/catalog_primary['source_path_relative_to_plan']).read_text();catalog_raw_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',catalog_raw))
assert not catalog_primary['whole_container_read'] and catalog_review['primary_topics_whole_rechecked']==len(catalog_primary['topics'])==7
assert [entry['topic'] for entry in catalog_primary['topics']]==['0005','0011','0062','0063','0079','0080','0088']
for entry in catalog_primary['topics']:
 head=next(x for x in catalog_raw_heads if x[1]==entry['topic']);i=catalog_raw_heads.index(head);text=catalog_raw[head.start():catalog_raw_heads[i+1].start() if i+1<len(catalog_raw_heads) else len(catalog_raw)].strip()
 assert entry['whole_topic_read'] and entry['text']==text and len(text)==entry['chars'] and hashlib.sha256(text.encode()).hexdigest()==entry['sha256']
catalog_ar=legacy['first_catalog_arithmetic']
assert (catalog_ar['documents'],catalog_ar['checks_passed'],catalog_ar['major_sections'],catalog_ar['primary_topics_whole_rechecked'])==(4,10,[5,13,13,12],7)
assert catalog_ar['person_index_bins']==[18,177,7] and catalog_ar['person_index_rows']==202
assert catalog_ar['assumed_city_population_parts_in_ten_thousands']==[300,280,250,120,50] and catalog_ar['assumed_city_population_total_in_ten_thousands']==1000
assert (catalog_ar['natural_realm_rows'],catalog_ar['artificial_realm_rows'],catalog_ar['realm_rows'],catalog_ar['realm_alias_normalized_names'])==(13,17,30,29)
assert catalog_ar['object_category_rows']==[18,22,16,20,8,10,14,17,24,15,15] and (catalog_ar['object_rows'],catalog_ar['stated_approximate_object_count'])==(179,180) and catalog_ar['parchment_rows']==['I18','K01']
assert catalog_ar['company_base_new_other_rows']==[15,8,10] and catalog_ar['company_rows']==33 and catalog_ar['proposed_connector_shares']==[35,12,15,10,10,5] and (catalog_ar['proposed_connector_share_sum'],catalog_ar['unreported_share_remainder'])==(87,13)
assert catalog_ar['group_summary_counts']==[13,14,23,13,25,10,39,14] and (catalog_ar['group_index_rows'],catalog_ar['group_summary_sum'],catalog_ar['group_row_summary_gap'])==(170,151,19)
for flag in ['all_catalog_entries_individually_canon_verified','catalog_counts_are_world_unique_entities','all_related_novels_reviewed','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']:assert not catalog_ar[flag]
catalog_world=(o/'11_WorldLorebook.md').read_text();catalog_section=catalog_world.split('### 한 이름이 가리키는 사람·물건·소속')[1].split('### 지도에서 찾을 것')[0]
for phrase in ['| 옐부르스 |','| 넵튠·시크 |','| 오크계·플랫마운틴·브로 |','| 요섭·크리스·워피스 |','미모대사국 흑해전함','사람과의 관계·탈것의 기능','이름을 이어받은 사연','배운 스킬과 사용할 인터랙션']:assert phrase in catalog_section
for target in ['#fewk-world-57','#fewk-world-69','#fewk-world-52','#fewk-world-17','#fewk-world-72','#fewk-world-60','#fewk-world-64']:assert target in catalog_section
catalog_basis_line=next(line for line in (p/'00_최신본_기준.md').read_text().splitlines() if line.startswith('**현재 집필 버전:**'))
assert 'Core0.49·이지룰P0.31·World1.00·시트0.44/32절·타롯0.3·입문0.5' in catalog_basis_line and '취득 구판90개는 누적90개 전문 대조/0개 대기' in catalog_basis_line
d['current_first_people_places_objects_groups_catalog_review']={'Core':'v0.40','World':'v0.64','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.95','whole_documents_reviewed':4,'whole_source_lines':[291,282,282,310],'major_sections_mapped':43,'limited_legacy_arithmetic_checks':10,'primary_topics_whole_rechecked':7,'first_family_cumulative_whole_reviews':15,'first_family_pending':17,'bounded_cumulative_whole_reviews':73,'bounded_cumulative_pending':17,'names_people_objects_affiliation_separated':True,'catalog_occurrences_are_not_unique_entities':True,'all_catalog_entries_individually_canon_verified':False,'new_mechanical_parameter_values':[],'current_engine_changed':False,'all_related_novels_reviewed':False,'all_older_unique_sources_reviewed':False,'all_specific_use_profiles_complete':False,'old_100point_build_rewritten':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
life_review=legacy_coherence['first_life_uncertainty_class_institutions_review']
assert (life_review['whole_documents_read'],len(life_review['major_section_mapping']),life_review['major_sections_by_file'])==(4,46,[15,10,10,11])
assert (life_review['first_family_cumulative_whole_reviews'],life_review['first_family_pending'],life_review['bounded_cumulative_whole_reviews'],life_review['bounded_cumulative_pending'])==(19,13,77,13)
assert life_review['versions']=={'Core':'v0.40','World':'v0.65','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.96','Tarot':'v0.3'} and life_review['new_mechanical_parameter_values']==[]
for flag in ['all_older_unique_sources_reviewed','all_related_novels_reviewed','all_institutions_and_laws_canon_verified','all_specific_use_profiles_complete','all_unnamed_stories_or_unknown_identities_verified','current_engine_changed','old_100point_build_rewritten','old_DSR_LCK_Grade_or_six_abilities_restored','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not life_review[flag]
assert life_review['new_related_novels_whole_read']==0 and life_review['new_primary_review_totals_not_inferred'] and life_review['related_novels_whole_rechecked']==1
life_shapes={'08_전체기타리스트.md':(12682,7084,386,15),'09_전체불특정리스트.md':(11636,6098,247,10),'10_사물_계급상징_사전.md':(13546,7106,312,10),'11_제도_경제용어_관계도.md':(16035,8529,421,11)}
assert {entry['name'] for entry in life_review['snapshots']}==set(life_shapes)
for life_source in life_review['snapshots']:
 byte_count,char_count,line_count,section_count=life_shapes[life_source['name']];data=life_source['text'].encode()
 assert life_source['whole_document_read'] and (len(data),len(life_source['text']),len(life_source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (life_source['bytes'],life_source['chars'],life_source['lines'])==(byte_count,char_count,line_count) and len(life_source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==life_source['sha256'];verify_recorded_source_hash(p/life_source['path_relative_to_plan'],life_source['sha256'])
 assert any(entry['name']==life_source['name'] and entry['sha256']==life_source['sha256'] and entry['whole_document_read'] for entry in additional_procurement)
 life_rows=[entry for entry in life_review['major_section_mapping'] if entry['source_name']==life_source['name']];life_heads=list(re.finditer(r'^## [^\n]+',life_source['text'],re.M));assert len(life_rows)==len(life_heads)==section_count
 for i,(head,entry) in enumerate(zip(life_heads,life_rows)):
  end=life_heads[i+1].start() if i+1<len(life_heads) else len(life_source['text'])
  assert entry['title']==head[0][3:] and entry['text']==life_source['text'][head.start():end] and entry['decision']==life_source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==life_source['text'][:head.start()].count('\n')+1 and entry['decision']
 life_inventory=next(entry for entry in inventory['files'] if entry['path_relative_to_plan']==life_source['path_relative_to_plan'])
 assert life_inventory['whole_document_reviewed_cumulatively'] and life_inventory['sha256']==life_source['sha256']
life_primary=life_review['primary_topic_recheck'];verify_recorded_source_hash(p/life_primary['source_path_relative_to_plan'],life_primary['sha256']);life_raw=(p/life_primary['source_path_relative_to_plan']).read_text();life_raw_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',life_raw))
assert not life_primary['whole_container_read'] and life_review['primary_topics_whole_rechecked']==len(life_primary['topics'])==12
assert [entry['topic'] for entry in life_primary['topics']]==['0001','0010','0011','0015','0016','0030','0040','0045','0049','0076','0080','0082']
for entry in life_primary['topics']:
 head=next(x for x in life_raw_heads if x[1]==entry['topic']);i=life_raw_heads.index(head);text=life_raw[head.start():life_raw_heads[i+1].start() if i+1<len(life_raw_heads) else len(life_raw)].strip()
 assert entry['whole_topic_read'] and entry['text']==text and len(text)==entry['chars'] and hashlib.sha256(text.encode()).hexdigest()==entry['sha256']
life_novel=life_review['related_novel_recheck'];verify_recorded_source_hash(p/life_novel['path_relative_to_plan'],life_novel['sha256']);assert (life_novel['bytes'],life_novel['chars'],life_novel['lines'])==(14330,6378,186) and life_novel['text']==(p/life_novel['path_relative_to_plan']).read_bytes().decode()
assert life_novel['whole_document_read'] and life_novel['previously_reviewed_document_rechecked'] and not life_novel['novel_rewritten'] and len(life_novel['decisions'])==3
assert '이 편지를 누가 읽게 될지 모르겠다' in life_novel['text'] and '아키비스트 윤세라' in life_novel['text'] and '지문: 없음.' in life_novel['text']
life_ar=legacy['first_life_uncertainty_arithmetic']
assert (life_ar['documents'],life_ar['checks_passed'],life_ar['major_sections'],life_ar['primary_topics_whole_rechecked'],life_ar['related_novels_whole_rechecked'],life_ar['new_related_novels_whole_read'])==(4,11,[15,10,10,11],12,1,0)
assert life_ar['value_rows']==['C01','C02','C03','C04','C05','C06','C07','C08'] and (life_ar['value_heading_count'],life_ar['value_row_count'])==(7,8)
assert life_ar['assumed_monthly_living_costs']==[50,100,200] and life_ar['crocodile_conditional_years']==['250/3','125/3','125/6'] and life_ar['crocodile_conditional_months_at100']==500 and life_ar['crocodile_conditional_year_month_at100']==[41,8]
assert (life_ar['assumed_one_soup_per_day_month_cost'],life_ar['assumed_three_soups_per_day_month_cost'],life_ar['living_cost_rent_same_value_other_costs'])==(60,180,[0,0,0])
assert (life_ar['proposed_insurance_monthly_premium'],life_ar['proposed_insurance_payout'],life_ar['payout_premium_ratio'])==(5,200,40)
assert (life_ar['cinnabar_assumed_grams'],life_ar['cinnabar_assumed_price_per_gram'],life_ar['cinnabar_assumed_total_credits'],life_ar['cinnabar_stated_total_credits'],life_ar['cinnabar_total_difference_credits'],life_ar['cinnabar_implied_quoted_price_per_gram'])==(4200000000,1050000,4410000000000000,4435000000000000,25000000000000,'22175000/21')
assert life_ar['stated_currency_conversion_rows']==17 and life_ar['stated_currency_conversion_rows_agree']
assert (life_ar['stated_234eok_credits'],life_ar['stated_numeric_value'],life_ar['numeric_gap_if_234eok'],life_ar['value_if_literal_eok_times_man'])==(23400000000,23742190000,342190000,234000000000000)
for flag in ['all_institutions_and_laws_canon_verified','all_unnamed_stories_or_unknown_identities_verified','all_related_novels_reviewed','all_specific_use_profiles_complete','real_world_exchange_rate_current_verified','all_daily_food_requirements_or_market_prices_canon_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_playtest']:assert not life_ar[flag]
life_world=(o/'11_WorldLorebook.md').read_text();life_scene=life_world.split('### 함께 사는 약속과 쓰는 물건')[1].split('<a id="fewk-world-68">')[0];life_unknown=life_world.split('### 모르는 이름과 알고 있는 생활')[1].split('### 큰 존재와 재해 앞에서')[0]
for phrase in ['| 공동 지출과 각자의 보수 |','| 함께 쓰는 방과 장치 |','| 선물·기념품·남겨진 기록 |','새 거주 장면 — 기타를 돌려줄 날','그 지급수단을 받지 않습니다','다른 악기로 공연하고 기타를 먼저 돌려줄지','오늘은 식사만 같이 하고 공연을 미뤄도','배운 스킬은 그 인물의 이력']:assert phrase in life_scene
# 적용 지위의 반복 문장은 독자 본문 대신 말미 주석에 보존한다.
assert '신규 캠페인 제안' in life_world.split('<a id="fewk-editorial-source-notes"></a>',1)[1]
for phrase in ['| 이름을 밝히지 않은 작업자 |','| 출처를 다 알지 못하는 기록 |','| 다른 이름으로 돌아온 사람 |','본래 이름이 있지만 인식의 위험 때문에 안전한 통칭','기록자는 윤세라','각색 모티프를 읽는 안내']:assert phrase in life_unknown
d['current_first_life_uncertainty_class_institutions_review']={'Core':'v0.40','World':'v0.65','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.96','whole_documents_reviewed':4,'whole_source_lines':[386,247,312,421],'major_sections_mapped':46,'limited_legacy_arithmetic_checks':11,'primary_topics_whole_rechecked':12,'related_novels_whole_rechecked':1,'new_related_novels_whole_read':0,'first_family_cumulative_whole_reviews':19,'first_family_pending':13,'bounded_cumulative_whole_reviews':77,'bounded_cumulative_pending':13,'shared_life_contracts_and_unrevealed_names_separated':True,'new_cafe_guitar_scene_is_campaign_proposal':True,'all_institutions_and_laws_canon_verified':False,'all_unnamed_stories_or_unknown_identities_verified':False,'current_engine_changed':False,'all_related_novels_reviewed':False,'all_older_unique_sources_reviewed':False,'all_specific_use_profiles_complete':False,'old_100point_build_rewritten':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
reader_review=legacy_coherence['first_encyclopedia_scene_glossary_review']
assert (reader_review['whole_documents_read'],len(reader_review['major_section_mapping']),reader_review['major_sections_by_file'])==(3,43,[16,17,10])
assert (reader_review['first_family_cumulative_whole_reviews'],reader_review['first_family_pending'],reader_review['bounded_cumulative_whole_reviews'],reader_review['bounded_cumulative_pending'])==(22,10,80,10)
assert reader_review['versions']=={'Core':'v0.40','World':'v0.66','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.97','Tarot':'v0.3'} and reader_review['new_mechanical_parameter_values']==[]
for flag in ['all_older_unique_sources_reviewed','all_related_novels_reviewed','all_glossary_entries_individually_canon_verified','all_market_prices_or_labor_conditions_canon_verified','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not reader_review[flag]
reader_shapes={'12_FEWK세계관백과.md':(15039,7799,556,16),'13_씬_세트_구성도.md':(15981,8303,547,17),'14_FEWK용어사전.md':(15034,8608,508,10)}
assert {x['name'] for x in reader_review['snapshots']}==set(reader_shapes)
for reader_source in reader_review['snapshots']:
 byte_count,char_count,line_count,section_count=reader_shapes[reader_source['name']];data=reader_source['text'].encode()
 assert reader_source['whole_document_read'] and (len(data),len(reader_source['text']),len(reader_source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (reader_source['bytes'],reader_source['chars'],reader_source['lines'])==(byte_count,char_count,line_count) and len(reader_source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==reader_source['sha256'];verify_recorded_source_hash(p/reader_source['path_relative_to_plan'],reader_source['sha256'])
 assert any(x['name']==reader_source['name'] and x['sha256']==reader_source['sha256'] and x['whole_document_read'] for x in additional_procurement)
 reader_rows=[x for x in reader_review['major_section_mapping'] if x['source_name']==reader_source['name']];reader_heads=list(re.finditer(r'^## [^\n]+',reader_source['text'],re.M));assert len(reader_rows)==len(reader_heads)==section_count
 for i,(head,entry) in enumerate(zip(reader_heads,reader_rows)):
  end=reader_heads[i+1].start() if i+1<len(reader_heads) else len(reader_source['text'])
  assert entry['title']==head[0][3:] and entry['text']==reader_source['text'][head.start():end] and entry['decision']==reader_source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==reader_source['text'][:head.start()].count('\n')+1 and entry['decision']
 reader_inventory=next(x for x in inventory['files'] if x['path_relative_to_plan']==reader_source['path_relative_to_plan']);assert reader_inventory['whole_document_reviewed_cumulatively'] and reader_inventory['sha256']==reader_source['sha256']
reader_primary=reader_review['primary_topic_recheck'];verify_recorded_source_hash(p/reader_primary['source_path_relative_to_plan'],reader_primary['sha256']);reader_raw=(p/reader_primary['source_path_relative_to_plan']).read_text();reader_raw_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',reader_raw))
assert not reader_primary['whole_container_read'] and reader_review['primary_topics_whole_rechecked']==len(reader_primary['topics'])==7
assert [x['topic'] for x in reader_primary['topics']]==['0001','0006','0015','0032','0063','0065','0076']
for entry in reader_primary['topics']:
 head=next(x for x in reader_raw_heads if x[1]==entry['topic']);i=reader_raw_heads.index(head);text=reader_raw[head.start():reader_raw_heads[i+1].start() if i+1<len(reader_raw_heads) else len(reader_raw)].strip()
 assert entry['whole_topic_read'] and entry['text']==text and len(text)==entry['chars'] and hashlib.sha256(text.encode()).hexdigest()==entry['sha256']
reader_novel=reader_review['related_novel_review'];verify_recorded_source_hash(p/reader_novel['path_relative_to_plan'],reader_novel['sha256']);assert reader_novel['text']==(p/reader_novel['path_relative_to_plan']).read_bytes().decode()
assert (len(reader_novel['text'].encode()),len(reader_novel['text']),len(reader_novel['text'].splitlines()))==(reader_novel['bytes'],reader_novel['chars'],reader_novel['lines'])
assert reader_novel['whole_document_read'] and not reader_novel['novel_rewritten'] and len(reader_novel['decisions'])==3 and reader_review['related_novels_whole_read_in_pass']==1
reader_ar=legacy['first_encyclopedia_scene_glossary_arithmetic'];assert (reader_ar['documents'],reader_ar['checks_passed'],reader_ar['major_sections'])==(3,11,[16,17,10])
assert (reader_ar['numbered_slots'],reader_ar['FEWK_entries_excluding_nonFEWK_placeholder'],reader_ar['monthly_wage_assuming30_days'],reader_ar['scene_monthly_wage_mislabel_factor'],reader_ar['quality_difference_percentage_points'])==(40,39,108,30,6)
assert reader_ar['quality_relative_difference']=='3/46' and not reader_ar['all_market_prices_or_labor_conditions_canon_verified'] and not reader_ar['current_engine_changed']
reader_world=(o/'11_WorldLorebook.md').read_text().split('### 감각을 행동 가능한 장면으로')[1].split('<a id="fewk-world-07">')[0]
assert '재생사 케이티는 트랜스에 들지 않고도' in reader_world and 'AI 안내를 받는 복도' in reader_world and '브로커가 같은 현장에 있는 것은 아니다' in reader_world
assert '**인터랙션 목록**' in reader_world and '**스킬의 같은 백분율**' in reader_world and '다음 교대에 돌려줄 도구' in reader_world and '**신규 캠페인 제안**' in life_world.split('<a id="fewk-editorial-source-notes"></a>',1)[1]
d['current_first_encyclopedia_scene_glossary_review']={'Core':'v0.40','World':'v0.66','Design':'v0.97','whole_documents_reviewed':3,'major_sections_mapped':43,'limited_legacy_arithmetic_checks':11,'primary_topics_whole_rechecked':7,'related_novels_whole_read_in_pass':1,'bounded_cumulative_whole_reviews':80,'bounded_cumulative_pending':10,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
voice_review=legacy_coherence['first_address_nuance_motif_review']
assert (voice_review['whole_documents_read'],len(voice_review['major_section_mapping']),voice_review['major_sections_by_file'])==(3,93,[7,71,15])
assert (voice_review['first_family_cumulative_whole_reviews'],voice_review['first_family_pending'],voice_review['bounded_cumulative_whole_reviews'],voice_review['bounded_cumulative_pending'])==(25,7,83,7)
assert voice_review['versions']=={'Core':'v0.40','World':'v0.67','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.98','Tarot':'v0.3'} and voice_review['new_mechanical_parameter_values']==[]
for flag in ['all_older_unique_sources_reviewed','all_related_novels_reviewed','all_quoted_novel_passages_against_whole_novels_verified','all_translation_terms_canon_verified','all_motif_interpretations_are_world_laws','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not voice_review[flag]
voice_shapes={'15_경칭_어조_번역가이드.md':(13556,7458,408,7),'16_뉘앙스리스트.md':(22843,11857,845,71),'17_반복모티프_추적표.md':(13364,7863,455,15)}
assert {x['name'] for x in voice_review['snapshots']}==set(voice_shapes)
for voice_source in voice_review['snapshots']:
 byte_count,char_count,line_count,section_count=voice_shapes[voice_source['name']];data=voice_source['text'].encode()
 assert voice_source['whole_document_read'] and (len(data),len(voice_source['text']),len(voice_source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (voice_source['bytes'],voice_source['chars'],voice_source['lines'])==(byte_count,char_count,line_count) and len(voice_source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==voice_source['sha256'];verify_recorded_source_hash(p/voice_source['path_relative_to_plan'],voice_source['sha256'])
 assert any(x['name']==voice_source['name'] and x['sha256']==voice_source['sha256'] and x['whole_document_read'] for x in additional_procurement)
 voice_rows=[x for x in voice_review['major_section_mapping'] if x['source_name']==voice_source['name']];voice_heads=list(re.finditer(r'^## [^\n]+',voice_source['text'],re.M));assert len(voice_rows)==len(voice_heads)==section_count
 for i,(head,entry) in enumerate(zip(voice_heads,voice_rows)):
  end=voice_heads[i+1].start() if i+1<len(voice_heads) else len(voice_source['text'])
  assert entry['title']==head[0][3:] and entry['text']==voice_source['text'][head.start():end] and entry['decision']==voice_source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==voice_source['text'][:head.start()].count('\n')+1 and entry['decision']
 voice_inventory=next(x for x in inventory['files'] if x['path_relative_to_plan']==voice_source['path_relative_to_plan']);assert voice_inventory['whole_document_reviewed_cumulatively'] and voice_inventory['sha256']==voice_source['sha256']
voice_primary=voice_review['primary_topic_recheck'];verify_recorded_source_hash(p/voice_primary['source_path_relative_to_plan'],voice_primary['sha256']);voice_raw=(p/voice_primary['source_path_relative_to_plan']).read_text();voice_raw_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',voice_raw))
assert not voice_primary['whole_container_read'] and voice_review['primary_topics_whole_rechecked']==len(voice_primary['topics'])==5
assert [x['topic'] for x in voice_primary['topics']]==['0001','0030','0040','0054','0063']
for entry in voice_primary['topics']:
 head=next(x for x in voice_raw_heads if x[1]==entry['topic']);i=voice_raw_heads.index(head);text=voice_raw[head.start():voice_raw_heads[i+1].start() if i+1<len(voice_raw_heads) else len(voice_raw)].strip()
 assert entry['whole_topic_read'] and entry['text']==text and len(text)==entry['chars'] and hashlib.sha256(text.encode()).hexdigest()==entry['sha256']
voice_novel=voice_review['related_novel_recheck'];verify_recorded_source_hash(p/voice_novel['path_relative_to_plan'],voice_novel['sha256']);assert voice_novel['text']==(p/voice_novel['path_relative_to_plan']).read_bytes().decode()
assert (voice_novel['bytes'],voice_novel['chars'],voice_novel['lines'])==(14349,6357,165)
assert voice_novel['whole_document_read'] and voice_novel['previously_reviewed_document_rechecked'] and not voice_novel['novel_rewritten'] and len(voice_novel['decisions'])==3
assert voice_review['related_novels_whole_rechecked']==1 and voice_review['new_related_novels_whole_read']==0
voice_ar=legacy['first_address_nuance_motif_arithmetic'];assert (voice_ar['documents'],voice_ar['checks_passed'],voice_ar['major_sections'])==(3,6,[7,71,15])
assert (voice_ar['nuance_numbered_entries'],voice_ar['individual_story_headings'],voice_ar['individual_stories_with_one_entry'],voice_ar['individual_stories_with_two_entries'],voice_ar['story_numbers_referenced_including_grouped_ranges'])==(83,64,58,6,92)
assert voice_ar['story_numbers_not_referenced']==[12,15,71,73,77,78,79,81] and voice_ar['translation_mapping_rows']==[28,34] and voice_ar['story12_to04_duration_ratio']==30
assert not voice_ar['all_quoted_novel_passages_against_whole_novels_verified'] and not voice_ar['all_translation_terms_canon_verified'] and not voice_ar['current_engine_changed']
voice_world=(o/'11_WorldLorebook.md').read_text().split('### 서로를 부르는 말과 남겨진 흔적')[1].split('**새 거점 장면 — 한 곡과 한 통의 인계:**')[0]
assert '당사자가 원하는 부름' in voice_world and '운영자의 직책과 실제 보관/인계 권한' in voice_world and '상대의 답을 듣는다' in voice_world
assert '장례 집전 사제로 바꾸는 근거가 아닙니다' in voice_world and '‘협조’와 ‘설득’' in voice_world and '공연을 같이 준비하는 결말도 열려 있습니다' in voice_world
d['current_first_address_nuance_motif_review']={'Core':'v0.40','World':'v0.67','Design':'v0.98','whole_documents_reviewed':3,'major_sections_mapped':93,'limited_legacy_arithmetic_checks':6,'primary_topics_whole_rechecked':5,'related_novels_whole_rechecked':1,'new_related_novels_whole_read':0,'bounded_cumulative_whole_reviews':83,'bounded_cumulative_pending':7,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
narrator_review=legacy_coherence['first_letters_narrator_translation_readme_review']
assert (narrator_review['whole_documents_read'],len(narrator_review['major_section_mapping']),narrator_review['major_sections_by_file'])==(4,127,[7,10,101,9])
assert (narrator_review['first_family_cumulative_whole_reviews'],narrator_review['first_family_pending'],narrator_review['bounded_cumulative_whole_reviews'],narrator_review['bounded_cumulative_pending'])==(29,3,87,3)
assert narrator_review['versions']=={'Core':'v0.40','World':'v0.68','Sheet':'v0.35','Easy':'P v0.30','Design':'v0.99','Tarot':'v0.3'} and narrator_review['new_mechanical_parameter_values']==[]
for flag in ['all_older_unique_sources_reviewed','all_related_novels_reviewed','all_quoted_novel_passages_against_whole_novels_verified','all_current_wiki_entries_canon_verified','old_self_completion_claims_are_fifth_evidence','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not narrator_review[flag]
narrator_shapes={'18_서간체_모음집.md':(13521,7068,463,7),'19_서술자_가이드.md':(15393,8412,456,10),'20_스토리별_번역가이드.md':(44717,25323,1364,101),'README.md':(11229,6139,295,9)}
assert {x['name'] for x in narrator_review['snapshots']}==set(narrator_shapes)
for narrator_source in narrator_review['snapshots']:
 byte_count,char_count,line_count,section_count=narrator_shapes[narrator_source['name']];data=narrator_source['text'].encode()
 assert narrator_source['whole_document_read'] and (len(data),len(narrator_source['text']),len(narrator_source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (narrator_source['bytes'],narrator_source['chars'],narrator_source['lines'])==(byte_count,char_count,line_count) and len(narrator_source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==narrator_source['sha256'];verify_recorded_source_hash(p/narrator_source['path_relative_to_plan'],narrator_source['sha256'])
 assert any(x['name']==narrator_source['name'] and x['sha256']==narrator_source['sha256'] and x['whole_document_read'] for x in additional_procurement)
 narrator_rows=[x for x in narrator_review['major_section_mapping'] if x['source_name']==narrator_source['name']];narrator_heads=list(re.finditer(r'^## [^\n]+',narrator_source['text'],re.M));assert len(narrator_rows)==len(narrator_heads)==section_count
 for i,(head,entry) in enumerate(zip(narrator_heads,narrator_rows)):
  end=narrator_heads[i+1].start() if i+1<len(narrator_heads) else len(narrator_source['text'])
  assert entry['title']==head[0][3:] and entry['text']==narrator_source['text'][head.start():end] and entry['decision']==narrator_source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==narrator_source['text'][:head.start()].count('\n')+1 and entry['decision']
 narrator_inventory=next(x for x in inventory['files'] if x['path_relative_to_plan']==narrator_source['path_relative_to_plan']);assert narrator_inventory['whole_document_reviewed_cumulatively'] and narrator_inventory['sha256']==narrator_source['sha256']
narrator_primary=narrator_review['primary_topic_recheck'];verify_recorded_source_hash(p/narrator_primary['source_path_relative_to_plan'],narrator_primary['sha256']);narrator_raw=(p/narrator_primary['source_path_relative_to_plan']).read_text();narrator_raw_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',narrator_raw))
assert not narrator_primary['whole_container_read'] and narrator_review['primary_topics_whole_rechecked']==len(narrator_primary['topics'])==6
assert [x['topic'] for x in narrator_primary['topics']]==['0001','0022','0040','0054','0060','0098']
for entry in narrator_primary['topics']:
 head=next(x for x in narrator_raw_heads if x[1]==entry['topic']);i=narrator_raw_heads.index(head);text=narrator_raw[head.start():narrator_raw_heads[i+1].start() if i+1<len(narrator_raw_heads) else len(narrator_raw)].strip()
 assert entry['whole_topic_read'] and entry['text']==text and len(text)==entry['chars'] and hashlib.sha256(text.encode()).hexdigest()==entry['sha256']
narrator_header=narrator_review['header_only_primary_0102'];head=next(x for x in narrator_raw_heads if x[1]=='0102');i=narrator_raw_heads.index(head);text=narrator_raw[head.start():narrator_raw_heads[i+1].start()].strip()
assert narrator_header['text']==text and '\n' not in text and hashlib.sha256(text.encode()).hexdigest()==narrator_header['sha256'] and not narrator_header['narrative_body_available_in_first_extract'] and narrator_header['not_counted_as_substantive_topic_review']
assert len(narrator_review['related_novel_reviews'])==2 and (narrator_review['related_novels_whole_read_in_pass'],narrator_review['new_related_novels_whole_read'],narrator_review['previously_reviewed_related_novels_rechecked'])==(2,1,1)
for entry in narrator_review['related_novel_reviews']:
 verify_recorded_source_hash(p/entry['path_relative_to_plan'],entry['sha256']);assert entry['text']==(p/entry['path_relative_to_plan']).read_bytes().decode() and entry['whole_document_read'] and not entry['novel_rewritten']
 assert (len(entry['text'].encode()),len(entry['text']),len(entry['text'].splitlines()))==(entry['bytes'],entry['chars'],entry['lines'])
 assert (entry['bytes'],entry['chars'],entry['lines'])==((18380,7822,217) if entry['name'].startswith('024') else (14330,6378,186))
 assert entry['previously_reviewed_document_rechecked']==entry['name'].startswith('100') and entry['decisions']
assert len(narrator_review['current_wiki_rechecks'])==narrator_review['current_wiki_documents_whole_rechecked']==2
for entry in narrator_review['current_wiki_rechecks']:
 verify_recorded_source_hash(p/entry['path_relative_to_plan'],entry['sha256']);assert entry['text']==(p/entry['path_relative_to_plan']).read_bytes().decode() and entry['whole_document_read'] and len(entry['text'].encode())==entry['bytes'] and entry['decisions']
narrator_ar=legacy['first_letters_narrator_translation_readme_arithmetic'];assert (narrator_ar['documents'],narrator_ar['checks_passed'],narrator_ar['major_sections'])==(4,8,[7,10,101,9])
assert (narrator_ar['letter_list_rows'],narrator_ar['letter_numeric_story_rows'],narrator_ar['letter_unique_story_numbers'],narrator_ar['translation_numbered_summaries'],narrator_ar['translation_rows_with_seven_fields'],narrator_ar['translation_partial_tables'],narrator_ar['viewpoint_table_rows'])==(22,21,20,100,85,15,86)
assert (narrator_ar['FID_locations'],narrator_ar['FID_story_number_occurrences'],narrator_ar['FID_unique_story_numbers'],narrator_ar['readme_declared_md'],narrator_ar['bounded_first_inventory_md'])==(25,26,25,31,32)
assert narrator_ar['novel024_numbered_dialogue_chapters']==narrator_ar['novel100_letters']==7 and narrator_ar['novel024_last_chapter_nonempty'] and not narrator_ar['all_quoted_novel_passages_against_whole_novels_verified'] and not narrator_ar['old_self_completion_claims_are_fifth_evidence']
d['current_first_letters_narrator_translation_readme_review']={'Core':'v0.40','World':'v0.68','Design':'v0.99','whole_documents_reviewed':4,'major_sections_mapped':127,'limited_legacy_arithmetic_checks':8,'primary_topics_whole_rechecked':6,'related_novels_whole_read_in_pass':2,'new_related_novels_whole_read':1,'previously_reviewed_related_novels_rechecked':1,'current_wiki_documents_whole_rechecked':2,'bounded_cumulative_whole_reviews':87,'bounded_cumulative_pending':3,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
tarot_strategy=json.loads((v/'타롯_전략검증결과.json').read_text())
assert (tarot_strategy['checks_passed'],tarot_strategy['full_deck_fixed_hand_cases'],tarot_strategy['fixed_order_policy_cases'],tarot_strategy['reactive_policy_cases'])==(32,120,90,30)
assert tarot_strategy['independent_physical_ID_hand_enumerations']==3003 and tarot_strategy['information_states_evaluated']==2077615
assert tarot_strategy['positive_adaptive_gain_cases']==4 and tarot_strategy['fixed_policy_zero_gain_cases']==90
assert len(tarot_strategy['cases'])==120
for path,sha in tarot_strategy['artifacts_sha256'].items():assert hash_current(o/path)==sha
assert tarot_strategy['claims']['exact_best_response_in_declared_fixtures'] and tarot_strategy['claims']['adaptive_sequential_strategy_tested']
for flag in ['all_possible_PC_hands_tested','global_optimal_strategy_proven','mutual_optimal_or_Nash_strategy_proven','new_rules_or_persistent_resources_added','actual_participant_reading','actual_participant_playtest','actual_async_community_test','paradise_fleet_original_rules_compared','enough_card_selection_depth_for_release']:
 assert not tarot_strategy['claims'][flag]
tarot_profile=json.loads((v/'타롯_프로필.json').read_text())
assert tarot_profile['version']=='0.3' and tarot_profile['npc_public_score_policy']['id']=='median_chase'
assert tarot_profile['sequential_information_contract']['NPC_policy_locked_before_PC_submissions']
assert not tarot_profile['npc_public_score_policy']['current_PC_submission_access'] and not tarot_profile['npc_public_score_policy']['hidden_PC_hand_access']
for phrase in ['순차 NPC의 공개 반응 규약','선택 전략 대조에서 확인한 점','2117/783020','승리1·동률0·패배-1','이번 PC 제출이나 PC의 비공개 손패를 보고 선택하지 않습니다']:
 assert phrase in tarot,phrase
d['current_tarot_profile'].update(version='0.3',adaptive_sequential_strategy_tested=True,exact_declared_fixture_best_responses_verified=True,full_deck_fixed_hand_strategy_cases=120,fixed_order_zero_gain_cases=90,reactive_cases_with_positive_gain=4,global_optimal_or_mutual_equilibrium_proven=False,actual_participant_playtest=False)
d['current_tarot_strategy']={'id':tarot_strategy['id'],'checks_passed':32,'declared_fixed_hand_policy_cases':120,'information_states_evaluated':2077615,'independent_actual_card_ID_combinations':3003,'original_percentile_and_action_rules_changed':False,'all_PC_hands_or_mutual_optimal_strategies_proven':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# 관련 소설083의 현재 원본과 전문/작가 노트/용어집, 원전 우선 정정 범위를 확인한다.
novel083_review=legacy_coherence['mobius_night_shift_related_novel_review']
assert novel083_review['versions']=={'Core':'v0.44','World':'v0.82','Sheet':'v0.39','Design':'v1.16'}
novel083=novel083_review['novel'];verify_recorded_source_hash(p/novel083['path_relative_to_plan'],novel083['sha256'])
novel083_raw=(p/novel083['path_relative_to_plan']).read_bytes()
assert len(novel083_raw)==novel083['bytes'] and novel083_raw.decode()==novel083['text']
assert hashlib.sha256(novel083['text'].encode()).hexdigest()==novel083['text_sha256']
assert len(novel083['text'].splitlines())==novel083['lines']==165 and novel083['whole_document_read'] and novel083['story_author_notes_and_glossary_read']
assert all(x['reviewed'] for x in novel083['blocks']) and novel083['blocks'][-1]['lines']==[155,165]
assert novel083_review['new_related_novels_whole_read']==1 and novel083_review['new_primary_topics_whole_read']==0
for source,pattern,id_field in [(novel083_review['primary_source'],r'(?m)^\ufeff?"?FEWK; (\d{4})k','id'),(novel083_review['wiki_source'],r'(?m)^--- (.+?) ---\s*$','title')]:
 verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256'])
 actual=(p/source['path_relative_to_plan']).read_text();headers=list(re.finditer(pattern,actual))
 for entry in source['topics']:
  keys=[m[1] if id_field=='id' else unicodedata.normalize('NFC',unquote(m[1])).removesuffix('.txt') for m in headers]
  i=keys.index(entry[id_field]);expected=actual[headers[i].start():headers[i+1].start() if i+1<len(headers) else len(actual)]
  assert entry['text']==expected and entry['whole_topic_rechecked'] and hashlib.sha256(expected.encode()).hexdigest()==entry['text_sha256']
assert [e['id'] for e in novel083_review['primary_source']['topics']]==['0015','0043','0056','0066']
assert len(novel083_review['wiki_source']['topics'])==9 and len(novel083_review['issues'])==11
from decimal import Decimal
N083=Decimal
novel083_values=[N083('0.3')*12,N083('3.6')*30,N083('3.6')-N083('0.5'),N083('3.1')+N083('0.5'),N083('98')-N083('92'),N083('108')<N083('300'),N083('0.5')/N083('1'),N083('0.5')/N083('1')!=N083('1.5')]
assert len(novel083_values)==len(novel083_review['arithmetic_examples'])==novel083_review['arithmetic_examples_checked']==8
for observed,entry in zip(novel083_values,novel083_review['arithmetic_examples']):
 expected=entry['expected']
 assert observed==(N083(expected) if isinstance(expected,str) else expected),entry['id']
for flag in ['current_engine_changed','novel_source_rewritten','all_related_novels_reviewed','all_coffin_manufacturing_profiles_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test','Crocodile_three_forms_answer_inferred']:assert not novel083_review[flag],flag
assert novel083_review['new_mechanical_parameter_values']==[] and novel083_review['implemented_world_chapters']==[20,22,34,36]
for phrase in ['그릇은 돌아올 본체','야간조의 손','마지막 네 시간의 선택','코핀 제조 사업과 공정을 확정 원전','제작/정비 전문 → 내벽 각인·검수 인터랙션','반 끼 상당']:assert phrase in world,phrase
assert all(f'## {chapter}.' in world for chapter in novel083_review['implemented_world_chapters'])
d['current_mobius_night_shift_related_novel_review']={'World':'v0.82','Design':'v1.16','new_whole_related_novels_read':1,'story_notes_and_glossary_read':True,'original_topics_rechecked':4,'wiki_topics_rechecked':9,'source_arithmetic_examples_checked':8,'all_related_novels_reviewed':False,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# 두 관련 소설의 본문/작가 설명/용어집과 실제 출처를 대조한다.
noene_family=legacy_coherence['noene_family_related_novels_review']
assert noene_family['versions']=={'Core':'v0.44','World':'v0.83','Sheet':'v0.39','Design':'v1.17'}
assert len(noene_family['novels'])==noene_family['new_related_novels_whole_read']==2
assert [e['number'] for e in noene_family['novels']]==['021','092']
for entry in noene_family['novels']:
 path=p/entry['path_relative_to_plan'];verify_recorded_source_hash(path,entry['sha256']);raw=path.read_bytes()
 assert len(raw)==entry['bytes'] and raw.decode()==entry['text'] and hashlib.sha256(entry['text'].encode()).hexdigest()==entry['text_sha256']
 assert len(entry['text'].splitlines())==entry['lines'] and entry['whole_document_read'] and entry['story_author_notes_and_glossary_read']
assert [e['lines'] for e in noene_family['novels']]==[193,251]
for source,pattern,id_field in [(noene_family['primary_source'],r'(?m)^\ufeff?"?FEWK; (\d{4})k','id'),(noene_family['wiki_source'],r'(?m)^--- (.+?) ---\s*$','title')]:
 verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256']);actual=(p/source['path_relative_to_plan']).read_text();headers=list(re.finditer(pattern,actual))
 for entry in source['topics']:
  keys=[m[1] if id_field=='id' else unicodedata.normalize('NFC',unquote(m[1])).removesuffix('.txt') for m in headers]
  i=keys.index(entry[id_field]);expected=actual[headers[i].start():headers[i+1].start() if i+1<len(headers) else len(actual)]
  assert entry['text']==expected and entry['whole_topic_rechecked'] and hashlib.sha256(expected.encode()).hexdigest()==entry['text_sha256']
assert [e['id'] for e in noene_family['primary_source']['topics']]==['0018','0031','0085','0095']
assert len(noene_family['wiki_source']['topics'])==9 and len(noene_family['issues'])==19 and noene_family['new_primary_topics_whole_read']==0
noene_family_math=[Decimal('72')/24,Decimal('3')*15,Decimal('6')+1,Decimal('2')+3+5+6+1,Decimal('17')+1,Decimal('300')/5,Decimal('60')/4,Decimal('42')+15,Decimal('300')/3,Decimal('1')+1+3+1]
assert len(noene_family_math)==len(noene_family['limited_arithmetic_examples'])==noene_family['limited_arithmetic_examples_checked']==10
for observed,entry in zip(noene_family_math,noene_family['limited_arithmetic_examples']):assert observed==Decimal(entry['expected']),entry['id']
for flag in ['current_engine_changed','novel_sources_rewritten','all_related_novels_reviewed','all_noene_and_world_implant_profiles_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not noene_family[flag],flag
assert noene_family['new_mechanical_parameter_values']==[] and noene_family['implemented_world_chapters']==[20,22,65]
assert len(noene_family['remaining_story_specific_scope'])==4
for phrase in ['돌아온 사람과 그 사람을 돕는 기술자','내 세계를 가진 사람, 함께 살고 싶은 사람','PRE×2 에고','파란 가루와 소설의 휴대식 단발 이동기','어느 물건이 압수됐으며','새 정비소의 첫 약속']:
 assert phrase in world,phrase
intro_family=json.loads((v/'입문시나리오_검토.json').read_text())['world_noene_family_regression']
assert intro_family['World']=='v0.83' and intro_family['related_novels_whole_read']==['021','092'] and intro_family['same_profession_interaction_skill_and_body'] and intro_family['real_memory_and_chosen_relationship_distinguished']
assert not intro_family['all_related_novels_reviewed'] and not intro_family['actual_participant_reading'] and not intro_family['actual_participant_playtest']
d['current_noene_family_related_novels_review']={'World':'v0.83','Design':'v1.17','new_whole_related_novels_read':2,'story_notes_and_glossary_read':True,'original_topics_rechecked':4,'wiki_topics_rechecked':9,'limited_arithmetic_examples_checked':10,'remaining_story_specific_scopes':4,'current_engine_changed':False,'all_related_novels_reviewed':False,'all_noene_and_world_implant_profiles_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# 관련 소설094와 원본 공화 호텔의 서로 다른 몸/사건을 구분하여 대조한다.
ghost_cafe=legacy_coherence['ghost_cafe_related_novel_review']
assert ghost_cafe['versions']=={'Core':'v0.44','World':'v0.84','Sheet':'v0.39','Design':'v1.18'}
assert ghost_cafe['new_related_novels_whole_read']==1 and ghost_cafe['new_primary_topics_whole_read']==0
ghost_novel=ghost_cafe['novel'];verify_recorded_source_hash(p/ghost_novel['path_relative_to_plan'],ghost_novel['sha256'])
ghost_raw=(p/ghost_novel['path_relative_to_plan']).read_bytes()
assert len(ghost_raw)==ghost_novel['bytes'] and ghost_raw.decode()==ghost_novel['text']
assert hashlib.sha256(ghost_novel['text'].encode()).hexdigest()==ghost_novel['text_sha256']
assert len(ghost_novel['text'].splitlines())==ghost_novel['lines']==343 and ghost_novel['whole_document_read'] and ghost_novel['story_author_notes_and_glossary_read']
for source,pattern,id_field in [(ghost_cafe['primary_source'],r'(?m)^\ufeff?"?FEWK; (\d{4})k','id'),(ghost_cafe['wiki_source'],r'(?m)^--- (.+?) ---\s*$','title')]:
 verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256']);actual=(p/source['path_relative_to_plan']).read_text();headers=list(re.finditer(pattern,actual))
 for entry in source['topics']:
  keys=[m[1] if id_field=='id' else unicodedata.normalize('NFC',unquote(m[1])).removesuffix('.txt') for m in headers]
  i=keys.index(entry[id_field]);expected=actual[headers[i].start():headers[i+1].start() if i+1<len(headers) else len(actual)]
  assert entry['text']==expected and entry['whole_topic_rechecked'] and hashlib.sha256(expected.encode()).hexdigest()==entry['text_sha256']
assert [e['id'] for e in ghost_cafe['primary_source']['topics']]==['0056','0073','0084'] and len(ghost_cafe['wiki_source']['topics'])==4
assert len(ghost_cafe['issues'])==14 and len(ghost_cafe['remaining_story_specific_scope'])==4
GHOST_D=Decimal
ghost_math=[GHOST_D('100')-3,GHOST_D('97')-8,GHOST_D('89')+8,GHOST_D('96')+1,GHOST_D('97')+1,GHOST_D('97')+1+1,GHOST_D('100')*(1-GHOST_D('0.9')),GHOST_D('1')/10,GHOST_D('120000')/100,GHOST_D('89')*3]
assert len(ghost_math)==len(ghost_cafe['limited_arithmetic_examples'])==ghost_cafe['limited_arithmetic_examples_checked']==10
for observed,entry in zip(ghost_math,ghost_cafe['limited_arithmetic_examples']):assert observed==GHOST_D(entry['expected']),entry['id']
assert all('condition' in ghost_cafe['limited_arithmetic_examples'][i] for i in [6,8,9])
for flag in ['current_engine_changed','novel_source_rewritten','all_related_novels_reviewed','all_ghost_and_coffin_use_profiles_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not ghost_cafe[flag],flag
assert ghost_cafe['new_mechanical_parameter_values']==[] and ghost_cafe['implemented_world_chapters']==[22,59,69,76]
for phrase in ['사일런트 카페 — 잡을 수 없는 손과 계속하는 일','소설094의 추가·변경','코핀 고장만으로 모두 같은 유령','첫 한 기의 사흘과 총89기의 두 달','오늘의 물잔과 맡긴 거울','은아가 다음 임무를 제안한 말과97명 모두가 동의했다는 기록']:
 assert phrase in world,phrase
assert '사이버 유령' in ghost_novel['text'] and '그들의 육체는 손상과 감염, 부패' in next(e['text'] for e in ghost_cafe['primary_source']['topics'] if e['id']=='0084')
ghost_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_ghost_cafe_regression']
assert ghost_intro['World']=='v0.84' and ghost_intro['novel094_whole_read'] and ghost_intro['primary0084_and_novel_adaptation_distinguished'] and ghost_intro['same_profession_interaction_skill_body_and_residence']
assert not ghost_intro['appearance_repair_is_body_healing_or_resurrection'] and not ghost_intro['all_related_novels_reviewed'] and not ghost_intro['actual_participant_reading'] and not ghost_intro['actual_participant_playtest']
d['current_ghost_cafe_related_novel_review']={'World':'v0.84','Design':'v1.18','new_whole_related_novels_read':1,'story_notes_and_glossary_read':True,'original_topics_rechecked':3,'wiki_topics_rechecked':4,'limited_arithmetic_examples_checked':10,'remaining_story_specific_scopes':4,'current_engine_changed':False,'all_related_novels_reviewed':False,'all_ghost_and_coffin_use_profiles_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# 현재 본체 수신과 실제 지원자 상태를 연결한 제한된 코핀 구현.
coffin_review=legacy_coherence['coffin_receiver_support_review']
assert coffin_review['versions']=={'Core':'v0.45','Sheet':'v0.40','World':'v0.84','Design':'v1.19'}
assert coffin_review['profile']=='CAMP-COF-TEST' and coffin_review['new_primary_topics_whole_read_count']==coffin_review['new_related_novels_whole_read_count']==0
coffin_source=coffin_review['primary_source'];verify_recorded_source_hash(p/coffin_source['path_relative_to_plan'],coffin_source['sha256'])
coffin_raw=(p/coffin_source['path_relative_to_plan']).read_text();coffin_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',coffin_raw))
assert [e['id'] for e in coffin_source['topics']]==['0056','0072']
for entry in coffin_source['topics']:
 i=next(i for i,m in enumerate(coffin_heads) if m[1]==entry['id'])
 expected=coffin_raw[coffin_heads[i].start():coffin_heads[i+1].start()]
 assert entry['text']==expected and entry['whole_topic_rechecked'] and hashlib.sha256(expected.encode()).hexdigest()==entry['text_sha256']
coffin_profile=json.loads((v/'차원프로필.json').read_text())['profiles']['CAMP-COF-TEST']
assert coffin_profile['base_alive'] and coffin_profile['route_online'] and coffin_profile['receiver_enabled']
assert not coffin_profile['base_hp0_is_automatic_death'] and not coffin_profile['dead_base_can_receive'] and not coffin_profile['dead_base_automatically_destroys_local']
assert coffin_profile['support_operator']['person_id']!=coffin_profile['person_id'] and coffin_profile['support_operator']['main_remaining']==coffin_profile['support_action_main']==1
assert dimension['base_alive_distinct_from_HP0'] and dimension['actual_receiver_and_operator_state_required'] and not dimension['local_action_scheduler_implemented']
assert not dimension['actual_participant_playtest'] and not dimension['all_world_profiles_verified']
for phrase in ['귀환 수신과 구조 지원 — 살아 있는 본체로 돌아오기','귀환은 치료가 아니며','현재 본체가 있는 곳','별도 인물P-SUP-C','거주 장면: 돌아올 장치가 꺼졌다','현지 몸을 자동 파괴하거나 드랍아웃·유령 상태로 바꾸지 않습니다']:
 assert phrase in core,phrase
sheet_now=(o/'12_룰시트와캐릭터시트.md').read_text()
for phrase in ['본체는 살아 있으나HP0','본체 사망/소실 확인','현지 몸HP0 / 지원자 부재·행동 소진','수신 복구 완료']:assert phrase in sheet_now,phrase
for flag in ['new_state_fields_are_universal_character_stats','all_coffin_and_immigration_profiles_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not coffin_review[flag],flag
coffin_intro=json.loads((v/'입문시나리오_검토.json').read_text())['core_coffin_receiver_regression']
assert (coffin_intro['Core'],coffin_intro['Sheet'])==('0.45','0.40') and coffin_intro['existing_scenario_events_unchanged'] and not coffin_intro['actual_participant_playtest']
d['current_coffin_receiver_support_review']={'Core':'v0.45','Sheet':'v0.40','World':'v0.84','Design':'v1.19','checks_passed':105,'receiver_state_cases':5408,'operator_condition_cases':256,'base_alive_distinct_from_HP0':True,'actual_receiver_and_operator_state_required':True,'all_coffin_and_immigration_profiles_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# 영상/인물/몸과 현재 입문 문서의 증명 범위를 실제 출처와 대조한다.
identity_review=legacy_coherence['intro_identity_evidence_review']
assert identity_review['versions']=={'Core':'v0.45','Sheet':'v0.40','World':'v0.85','Intro':'v0.5','Design':'v1.20'}
assert identity_review['new_primary_topics_whole_read_count']==identity_review['new_related_novels_whole_read_count']==0 and identity_review['previously_reviewed_related_novels_whole_rechecked']==1
identity_novel=identity_review['novel'];verify_recorded_source_hash(p/identity_novel['path_relative_to_plan'],identity_novel['sha256'])
assert (p/identity_novel['path_relative_to_plan']).read_text()==identity_novel['text'] and hashlib.sha256(identity_novel['text'].encode()).hexdigest()==identity_novel['text_sha256']
assert len(identity_novel['text'].splitlines())==identity_novel['lines']==116 and identity_novel['whole_document_rechecked'] and identity_novel['story_notes_and_glossary_read']
for source,pattern,id_field in [(identity_review['primary_source'],r'(?m)^\ufeff?"?FEWK; (\d{4})k','id'),(identity_review['wiki_source'],r'(?m)^--- (.+?) ---\s*$','title')]:
 verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256']);actual=(p/source['path_relative_to_plan']).read_text();heads=list(re.finditer(pattern,actual))
 keys=[m[1] if id_field=='id' else unicodedata.normalize('NFC',unquote(m[1])).removesuffix('.txt') for m in heads]
 for entry in source['topics']:
  i=keys.index(entry[id_field]);expected=actual[heads[i].start():heads[i+1].start() if i+1<len(heads) else len(actual)]
  assert entry['text']==expected and entry['whole_topic_rechecked'] and hashlib.sha256(expected.encode()).hexdigest()==entry['text_sha256']
assert [e['id'] for e in identity_review['primary_source']['topics']]==['0001','0002','0034','0043','0068','0089'] and len(identity_review['wiki_source']['topics'])==11
assert len(identity_review['issues'])==15 and len(identity_review['remaining_story_specific_scope'])==4
assert identity_review['handouts']==['STATEMENT-K-01','COPY-VISIT-01','COPY-RECEIPT-01','COPY-CONTRACT-01']
for name in identity_review['handouts']:assert name in story,name
for phrase in ['진행자의 준비 — 얼굴·몸·기록을 같은 사람으로 단정하지 않기','바로 건네줄 기록 — 읽은 사실과 다음 질문','물질계 첫 회동에서는B0','실명·몸ID·계약 당사자 식별 정보는 가려져','“아직017이 누구인지 모른다”','새 자료를 찾는 데 필요한 접근·동의·시간']:assert phrase in story,phrase
for phrase in ['영상 속 나 — 얼굴의 닮음과 같은 몸의 기록','돈의 보편 명칭이 아닙니다','다섯 대륙','얼굴이 누구인지 다 밝히기 전에도 증언을 안전하게 맡기고']:assert phrase in world,phrase
assert identity_review['scenario_tools_appendix_unchanged'] and identity_review['new_mechanical_parameter_values']==[]
for flag in ['original_sources_rewritten','novel_source_rewritten','current_engine_changed','all_related_novels_reviewed','novel001_full_setting_verified','original_card_content_canon_fixed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not identity_review[flag],flag
assert scenario['historical_v04_main_story_prefix_verified'] and scenario['current_main_story_editorially_updated'] and scenario['historical_scenario_tools_appendix_unchanged'] and scenario['current_scenario_tools_editorially_reviewed'] and not scenario['scenario_tools_appendix_unchanged'] and not scenario['original_main_story_prefix_verified']
identity_intro=json.loads((v/'입문시나리오_검토.json').read_text())
assert identity_intro['version']=='0.5' and identity_intro['identity_evidence_review']['issues_reviewed']==15 and not identity_intro['identity_evidence_review']['identity_canon_answer_fixed']
d['current_intro_identity_evidence_review']={'World':'v0.85','Intro':'v0.5','Design':'v1.20','previous_related_novel_whole_rechecked':1,'new_whole_related_novels_read':0,'primary_topics_rechecked':6,'wiki_topics_rechecked':11,'issues_reviewed':15,'handouts_written':4,'scenario_tools_appendix_unchanged':True,'original_card_content_canon_fixed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# 독자 경로/시트32절/현재 실행 표의 구조를 현재 원고에서 확인한다.
navigation=legacy_coherence['reader_navigation_status_review']
assert navigation['versions']=={'Core':'v0.46','World':'v0.86','Sheet':'v0.41','Intro':'v0.5','Design':'v1.21'}
assert navigation['current_plan_execution_rows_refreshed']==11 and navigation['sheet_sections_preserved']==navigation['sheet_section_named_anchors_added']==32
sheet_reader=(o/'12_룰시트와캐릭터시트.md').read_text()
sheet_section_numbers=[int(x) for x in re.findall(r'(?m)^## (\d+)\.',sheet_reader)]
assert sheet_section_numbers==list(range(1,33))
assert re.findall(r'<a id="fewk-sheet-(\d{2})"',sheet_reader)==[f'{i:02d}' for i in range(1,33)]
assert all(f'](#fewk-sheet-{i:02d})' in sheet_reader.split('## 1.',1)[0] for i in range(1,33))
assert '세계관 고유 확장 몸/장비는 후속 집필입니다.' not in sheet_reader
execution=rel_plan.split('## 실행 순서와 완료 조건',1)[1].split('## 일반 플레이와 스페셜의 보강',1)[0]
# 1.21의 11행 실행 표는 당시 기록이다. 1.37부터 현재 실행은 기존 P0~P7 한 표로 통합한다.
assert not any(re.match(r'^\| \d+ \| ',l) for l in execution.splitlines())
priority_section=rel_plan.split('## 이번 진행 목표와 다음 작업 예정',1)[1].split('P0~P3의 첫 결과를',1)[0]
priority_rows=[l.split('|') for l in priority_section.splitlines() if re.match(r'^\| P\d \| ',l)]
assert [c[1].strip() for c in priority_rows]==[f'P{i}' for i in range(8)]
assert all(len(c)==6 and all(cell.strip() for cell in c[1:5]) for c in priority_rows)
assert navigation['new_primary_topics_whole_read_count']==navigation['new_related_novels_whole_read_count']==0 and navigation['new_mechanical_parameter_values']==[]
for flag in ['mechanics_changed','all_book_editorial_review_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not navigation[flag],flag
d['current_reader_navigation_status_review']={'Core':'v0.46','World':'v0.86','Sheet':'v0.41','Design':'v1.21','sheet_sections':32,'direct_section_anchors':32,'execution_rows_refreshed':11,'mechanics_changed':False,'all_book_editorial_review_complete':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# 같은 IO의 실제 두 대상/몸/개인 첫 방문/지원 슬롯과 공유 자원을 확인한다.
compatible_review=legacy_coherence['compatible_io_two_realm_review']
assert compatible_review['versions']=={'Core':'v0.47','World':'v0.87','Sheet':'v0.42','Design':'v1.22'}
assert compatible_review['profile']=='CAMP-COF-TEST' and compatible_review['new_formal_pioneer_types']==[]
assert compatible_review['new_primary_topics_whole_read_count']==compatible_review['new_related_novels_whole_read_count']==0
for source,pattern,id_field in [(compatible_review['primary_source'],r'(?m)^\ufeff?"?FEWK; (\d{4})k','id'),(compatible_review['wiki_source'],r'(?m)^--- (.+?) ---\s*$','title')]:
 verify_recorded_source_hash(p/source['path_relative_to_plan'],source['sha256']);actual=(p/source['path_relative_to_plan']).read_text();heads=list(re.finditer(pattern,actual))
 keys=[m[1] if id_field=='id' else unicodedata.normalize('NFC',unquote(m[1])).removesuffix('.txt') for m in heads]
 for entry in source['topics']:
  i=keys.index(entry[id_field]);expected=actual[heads[i].start():heads[i+1].start() if i+1<len(heads) else len(actual)]
  assert entry['text']==expected and entry['whole_topic_rechecked'] and hashlib.sha256(expected.encode()).hexdigest()==entry['text_sha256']
assert [e['id'] for e in compatible_review['primary_source']['topics']]==['0043','0056']
assert [e['title'] for e in compatible_review['wiki_source']['topics']]==['러닝','파이오니아','파이오니아와_차원_개척']
destinations=coffin_profile['compatible_destinations'];prepared_two=coffin_profile['two_realm_prepared_case']
assert set(destinations)=={'TEST-COF','TEST-COF-B'} and compatible_review['new_trial_realms']==['TEST-COF','TEST-COF-B']
assert all(e['io']==coffin_profile['io'] and all(e[k] for k in ('charted','compatible','brain_updated','permission')) for e in destinations.values())
assert destinations['TEST-COF']['local_body_id']=='B-C1' and destinations['TEST-COF-B']['local_body_id']=='B-C2'
assert destinations['TEST-COF']['initial_local_body']==coffin_profile['initial_local_body']
assert destinations['TEST-COF-B']['initial_local_body']=={'hp':12,'ammo':0,'shield':1,'treated_since_full_recovery':False}
assert (coffin_profile['construction_batches'],coffin_profile['first_entry_ampoules'],coffin_profile['stored_body_slot_count'])==(2,1,1)
assert (prepared_two['construction_batches'],prepared_two['first_entry_ampoules'],prepared_two['stored_body_slot_count'])==(4,2,2)
assert prepared_two['route']==['TEST-COF','TEST-COF-B','TEST-COF','TEST-COF-B'] and prepared_two['additional_capacity_explicitly_prepared']
assert prepared_two['personal_first_visit_is_per_realm'] and prepared_two['dropout_ban_is_person_and_named_realm'] and not prepared_two['gear_automatically_transferred']
assert (dimension['checks_passed'],dimension['compatible_destination_condition_cases'],dimension['two_realm_preservation_sequences'])==(121,2880,169)
for flag in ['all_io_lineages_verified','all_world_profiles_verified','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not compatible_review[flag],flag
for phrase in ['호환 IO로 두 곳을 오가기','구성4회분·최초진입 앰플2개','이 인물에게는 다른 차원의 첫 방문','한 슬롯에B-C1을 남긴 채B-C2','같은 인물·본체·구성분/앰플의 최신 상태 버전']:assert phrase in core,phrase
assert '같은 접속 방식으로 두 곳에서 살아가기' in world
assert '같은 IO, 두 차원 기록 — CAMP-COF-TEST 확장 예' in sheet_reader and '0 / 0 | 두 차원' in sheet_reader
assert json.loads((v/'입문시나리오_검토.json').read_text())['compatible_io_regression']['scenario_events_unchanged']
d['current_compatible_io_two_realm_review']={'Core':'v0.47','World':'v0.87','Sheet':'v0.42','Design':'v1.22','checks_passed':121,'actual_destination_condition_cases':2880,'two_realm_preservation_sequences':169,'shared_person_and_base':True,'separate_local_bodies_and_first_visit_history':True,'supported_storage_capacity_required':True,'named_realm_ban_only':True,'all_io_lineages_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# 한 인물의 학습/숙련과 현재 몸/매개의 실제 기능 조건을 대조한다.
interaction_review=legacy_coherence['interaction_body_compatibility_review']
assert interaction_review['versions']=={'Core':'v0.48','World':'v0.88','Sheet':'v0.43','Design':'v1.23'}
assert interaction_review['new_primary_topics_whole_read_count']==interaction_review['new_related_novels_whole_read_count']==0
interaction_source=interaction_review['primary_source'];verify_recorded_source_hash(p/interaction_source['path_relative_to_plan'],interaction_source['sha256'])
interaction_raw=(p/interaction_source['path_relative_to_plan']).read_text();interaction_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',interaction_raw))
assert [e['id'] for e in interaction_source['topics']]==['0023','0037','0067']
for entry in interaction_source['topics']:
 i=next(i for i,h in enumerate(interaction_heads) if h[1]==entry['id']);actual=interaction_raw[interaction_heads[i].start():interaction_heads[i+1].start()]
 assert entry['text']==actual and entry['whole_topic_rechecked'] and hashlib.sha256(actual.encode()).hexdigest()==entry['text_sha256']
interaction_results=results['고유효과_검증.py']
assert (interaction_results['checks_passed'],interaction_results['body_compatibility_checks_passed'],interaction_results['body_compatibility_condition_cases'],interaction_results['charge_boundary_cases'],interaction_results['output_boundary_cases'])==(94,26,672,72,42)
assert interaction_review['checks_passed']==94 and interaction_review['existing_checks_retained']==68 and interaction_review['new_body_compatibility_checks']==26 and interaction_review['body_compatibility_condition_cases']==672
interaction_case=json.loads((v/'고유효과_프로필.json').read_text())['body_compatibility_case']
assert interaction_case['person_id']=='P-U1' and interaction_case['io']=='IO-COF-TEST' and set(interaction_case['bodies'])=={'B-U1','B-U2'}
assert len(interaction_case['person']['skills'])==interaction_review['initial_skill_count']==12 and sum(interaction_case['person']['skills'].values())==interaction_review['initial_skill_total']==440
assert sorted(interaction_case['person']['skills'].values())==[10]*3+[30]*4+[50]*3+[70]*2
assert interaction_case['person']['learned']==interaction_review['existing_functions']==['BIO-RHYTHM-TEST','SINDAN-LINK-TEST','SIN-STORAGE-TEST']
assert interaction_case['bodies']['B-U1']['supported']==interaction_case['person']['learned'] and interaction_case['bodies']['B-U2']['supported']==['SINDAN-LINK-TEST']
assert (interaction_case['bodies']['B-U1']['storage_capacity'],interaction_case['bodies']['B-U1']['stored_energy'],interaction_case['bodies']['B-U2']['storage_capacity'],interaction_case['bodies']['B-U2']['stored_energy'])==(2,1,0,0)
assert interaction_case['output_target']=={'id':'LAMP-U1','realm':'TEST-COF','seconds':0,'capacity_seconds':3600,'compatible':True,'contact_body':'B-U1'}
assert interaction_case['person']['main']==1 and all('main' not in body for body in interaction_case['bodies'].values()) and interaction_review['same_person_main_budget_preserved_across_body_change']
assert interaction_case['body_entry_and_storage_prepared_separately'] and not interaction_case['same_io_grants_all_features'] and not interaction_case['return_route_is_output_power_source'] and not interaction_case['legal_restrictions_are_physical_disable_switch']
assert interaction_review['uses_existing_profile_time_and_output_values'] and interaction_review['new_universal_stats']==interaction_review['new_mechanical_parameter_values']==[]
for flag in ['all_io_lineages_verified','all_formation_results_or_implants_covered','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not interaction_review[flag],flag
for phrase in ['몸을 바꾼 뒤 인터랙션을 읽는 순서','법으로 금지된 기능과 물리적으로 작동하지 않는 기능','신규 작성 예 — P-U1의 두 작업 몸','관찰/공학70','귀환 경로가 끊겼어도 이 몸의 독립 저장분']:assert phrase in core,phrase
assert '같은 솜씨를 다른 몸에서 쓰기' in world and '같은 ‘신사’라는 직업군이나 높은 공학 숙련만으로' in world
assert 'P-U1 — 같은 목록, 현재 몸에서 가능한 기능' in sheet_reader and 'B-U2에서 같은 출력 선언' in sheet_reader
assert json.loads((v/'입문시나리오_검토.json').read_text())['interaction_body_regression']['scenario_events_unchanged']
d['current_interaction_body_compatibility_review']={'Core':'v0.48','World':'v0.88','Sheet':'v0.43','Design':'v1.23','checks_passed':94,'existing_checks_retained':68,'new_body_compatibility_checks':26,'body_compatibility_condition_cases':672,'one_person_skill_total':440,'same_io_does_not_grant_all_body_features':True,'independent_output_survives_broken_return_route':True,'all_formation_results_or_implants_covered':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# 현재 독자 원고가 번호로 참조하는 관련 소설의 전문 근거/해시를 대조한다.
novel_corpus=legacy_coherence['current_numbered_related_novel_corpus_review']
assert novel_corpus['versions']=={'Core':'v0.48','World':'v0.89','Sheet':'v0.43','Design':'v1.24'}
expected_novels=['001','002','006','007','012','021','024','036','043','049','050','064','065','066','083','092','094','100']
assert novel_corpus['numbers']==expected_novels and [r['number'] for r in novel_corpus['rows']]==expected_novels
assert novel_corpus['extraction_documents']==['10_CoreRulebook.md','11_WorldLorebook.md','13_입문시나리오.md']
# 출처 번호만 간소화한 현재 표와 편집 전 원문 표를 각각 확인한다.
novel_old_table='\n'.join(l for l in novel_corpus['reader_table_text'].splitlines() if l.startswith('|'))
novel_current_table=re.sub(r'원본(?:Core)?\d{4}(?:/\d{4})*의 ', '',novel_old_table)
world_body,world_editorial_notes=world.split('<a id="fewk-editorial-source-notes"></a>',1)
assert world_body.count(novel_current_table)==1 and world_editorial_notes.count(novel_old_table)==1
without_new_table=world
for index_paragraph in novel_corpus['reader_table_text'].strip().split('\n\n'):
 normalized_index_paragraph=re.sub(r'원본(?:Core)?\d{4}(?:/\d{4})*의 ', '',index_paragraph)
 without_new_table=without_new_table.replace(normalized_index_paragraph,'').replace(index_paragraph,'')
found_novels=sorted(set(re.findall(r'소설\s*(\d{3})',(core+'\n'+without_new_table+'\n'+story).replace('**',''))))
assert found_novels==expected_novels # the new index cannot create its own coverage
assert novel_corpus['historical_whole_read_evidence_count']==novel_corpus['current_novel_hashes_checked']==18
for entry in novel_corpus['rows']:
 evidence_pointer=entry['historical_whole_read_evidence'];record=json.loads((v/evidence_pointer['file']).read_text())
 for key in evidence_pointer['pointer']:record=record[key]
 assert record[evidence_pointer['flag']] is True
 assert record.get('path_relative_to_plan',record.get('path'))==entry['path_relative_to_plan'] and record['sha256']==entry['sha256']
 verify_recorded_source_hash(p/entry['path_relative_to_plan'],entry['sha256'])
 assert (p/entry['path_relative_to_plan']).stat().st_size==entry['bytes'] and entry['current_source_hash_checked']
 assert not entry['whole_novel_newly_read_this_pass'] and not entry['whole_setting_verified']
 actual_chapters=[]
 world_body,world_notes=without_new_table.split('<a id="fewk-editorial-source-notes"></a>',1)
 for section in re.finditer(r'(?ms)^## (\d+)\..*?(?=^## |\Z)',world_body):
  if entry['number'] in re.findall(r'소설\s*(\d{3})',section[0].replace('**','')):actual_chapters.append(int(section[1]))
 for section in re.finditer(r'(?ms)^### (\d+)\..*?의 대조 근거\n.*?(?=^### |\Z)',world_notes):
  if entry['number'] in re.findall(r'소설\s*(\d{3})',section[0].replace('**','')):actual_chapters.append(int(section[1]))
 assert sorted(set(actual_chapters))==entry['current_world_chapters'],(entry['number'],sorted(set(actual_chapters)),entry['current_world_chapters'])
assert novel_corpus['new_related_novels_whole_read_this_pass']==0 and novel_corpus['previously_reviewed_novels_whole_rechecked_this_pass']==['002']
assert novel_corpus['all_current_numbered_references_have_whole_read_evidence']
for flag in ['all_current_numbered_novel_settings_verified','all_quoted_passages_semantically_verified','all_related_novels_or_series100_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not novel_corpus[flag],flag
debt=legacy_coherence['debt_story_related_novel_review'];assert debt['versions']=={'World':'v0.89','Design':'v1.24'}
debt_novel=debt['novel'];verify_recorded_source_hash(p/debt_novel['path_relative_to_plan'],debt_novel['sha256'])
assert (p/debt_novel['path_relative_to_plan']).read_text()==debt_novel['text'] and hashlib.sha256(debt_novel['text'].encode()).hexdigest()==debt_novel['text_sha256']
assert len(debt_novel['text'].splitlines())==debt_novel['lines']==156 and debt_novel['whole_document_rechecked'] and debt_novel['story_notes_and_glossary_read']
assert len(debt['issues'])==10 and len(debt['remaining_story_specific_scope'])==4 and debt['new_primary_topics_whole_read_count']==debt['new_related_novels_whole_read_count']==0
debt_primary=debt['primary_source'];verify_recorded_source_hash(p/debt_primary['path_relative_to_plan'],debt_primary['sha256'])
debt_raw=(p/debt_primary['path_relative_to_plan']).read_text();debt_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',debt_raw))
assert [e['id'] for e in debt_primary['topics']]==['0004','0010','0015','0025','0028','0072','0073','0093']
for entry in debt_primary['topics']:
 i=next(i for i,h in enumerate(debt_heads) if h[1]==entry['id']);actual=debt_raw[debt_heads[i].start():debt_heads[i+1].start()]
 assert entry['text']==actual and entry['whole_topic_rechecked'] and hashlib.sha256(actual.encode()).hexdigest()==entry['text_sha256']
debt_math=[Decimal(50)+250,Decimal(50)+250-300,Decimal(400)-250,Decimal(400)+50-80,Decimal(80)-50]
assert len(debt['limited_source_arithmetic_examples'])==len(debt_math)==5
for value,entry in zip(debt_math,debt['limited_source_arithmetic_examples']):assert value==Decimal(entry['expected'])
for phrase in ['갚은 금액과 돌아오지 않은 것은 다른 문제다','이전400·추가50·지급80·잔액370오얏','DEBT-STATEMENT-01','COLLATERAL-RECEIPT-01','소설003/004/015의 전문을 읽었다는 근거로 바꾸지 않습니다','숫자가 맞는 영수증을 얻은 것과 담보 대응물을 돌려받은 것']:
 assert phrase in world,phrase
for flag in ['new_scene_is_original_Sohwa_Chiko_or_Dowon_sequel','original_novel_rewritten','current_engine_changed','whole_novel_setting_verified','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not debt[flag],flag
assert debt['new_mechanical_parameter_values']==[]
assert debt['Native_label_includes_material_born_resolves_label_only_conflict'] and not debt['Native_label_proves_artificial_realm_birth']
assert '네이티브는 물질계에서 태어난 존재도 포함' in world and '별도 현지 몸/귀환 경로를 만들지 않습니다' in world
assert json.loads((v/'입문시나리오_검토.json').read_text())['debt_story_and_corpus_regression']['scenario_events_unchanged']
d['current_numbered_related_novel_corpus_review']={'World':'v0.89','Design':'v1.24','current_numbered_novels':18,'historical_whole_read_evidence_count':18,'current_novel_hashes_verified':18,'new_whole_novels_read':0,'all_current_numbered_novel_settings_verified':False,'all_related_novels_or_series100_reviewed':False,'actual_participant_reading':False,'actual_participant_playtest':False}
d['current_debt_story_related_novel_review']={'World':'v0.89','Design':'v1.24','whole_novel002_rechecked':True,'primary_topics_rechecked':8,'issues_reviewed':10,'limited_arithmetic_examples_checked':5,'original_novel_rewritten':False,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False}
# 공식 공개 외부 자료의 실제 취득본/쪽 범위와 현재 선택 근거. 원서 전권/참가자 시험이 아니다.
external_public=legacy_coherence['external_public_handout_review']
assert external_public['versions']=={'Design':'v1.25','Core':'v0.48','World':'v0.89','Sheet':'v0.43'}
assert external_public['selected_engine']=='P-FEWK 백분율'
assert len(external_public['sources'])==2 and len(external_public['comparative_findings'])==7
external_pages={}
for entry,expected_pages,read_pages in zip(external_public['sources'],[4,8],[[1,2,3,4],[1,2,3,4,7,8]]):
 pdf=p/entry['pdf_path_relative_to_plan'];txt=p/entry['text_path_relative_to_plan']
 verify_recorded_source_hash(pdf,entry['sha256']);verify_recorded_source_hash(txt,entry['text_sha256'])
 assert pdf.read_bytes().startswith(b'%PDF') and entry['official_primary_source']
 extracted=subprocess.run(['pdftotext','-layout',str(pdf),'-'],capture_output=True,text=True,check=True).stdout
 assert extracted==txt.read_text(),'public PDF extraction differs from stored text'
 pages=[page for page in extracted.split('\f') if page.strip()]
 assert len(pages)==entry['pdf_pages']==expected_pages and entry['read_pdf_pages']==read_pages and entry['selected_pages_whole_read']
 assert entry['whole_file_read']==(len(read_pages)==len(pages)) and not entry['external_full_rulebook_review_complete']
 external_pages[entry['id']]=[' '.join(page.split()) for page in pages]
 assert entry['url'] in design_text and entry['author_link_url']=='https://ardensludere.itch.io/'
for page,phrase in [(1,'Les PJ choisissent de le'),(1,'agir sous pression'),(2,'Produire du matériel'),(2,'Investigation'),(3,'opération'),(4,'déconnectes')]:
 # 단락/장식 머리글의 글자 분리는 원문 그대로 보존한다.
 if phrase=='Produire du matériel':phrase='matériel'
 assert phrase in external_pages['SPRAWL-VF-MOVES'][page-1],(page,phrase)
for page,phrase in [(1,'fiction'),(2,'12h00'),(3,'Corporations'),(4,'Menaces'),(7,'Trace +3'),(7,'algorithmes létaux'),(8,'connexions externes'),(8,'alimentation de secours')]:
 assert phrase in external_pages['SPRAWL-VF-MC'][page-1],(page,phrase)
assert (external_public['moves_pages_read'],external_public['MC_pages_read'],external_public['MC_pages_not_read'],external_public['playbook_pages_acquired_but_not_reviewed'])==(4,6,[5,6],20)
assert external_public['Double_Cross_scope']=={'basic_introduction_whole_page_read':True,'basic_detailed_rules_verified':False,'immersive_sheet_is_basic_rules':False}
assert external_public['Paradise_Fleet_scope']=={'official_store_preview_announced_pages':36,'viewer_HTML_reached':True,'preview_body_pages_read':0,'detailed_card_rules_verified':False}
for flag in ['current_engine_changed','all_requested_external_systems_fully_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not external_public[flag]
assert external_public['new_mechanical_parameter_values']==[]
for phrase in ['현재 선택과 비교 결과 — 백분율 엔진에 무엇을 남겼는가','스프롤 공개 자료 대조','거절에 추가 굴림/성장 손실을 붙이지 않음','단말 접속과 실제 차원 몸/코핀 귀환','미리보기 본문을 판독하지 못했습니다']:
 assert phrase in design_text,phrase
d['current_external_public_handout_review']={'Design':'v1.25','public_source_PDF_hashes_verified':2,'stored_extractions_reproduced_from_actual_PDFs':2,'moves_pages_read':4,'MC_pages_read':6,'comparative_findings':7,'Paradise_Fleet_preview_body_pages_read':0,'current_engine_changed':False,'all_requested_external_systems_fully_reviewed':False,'actual_participant_playtest':False}
d['source_review_scope']='공식 공개 전투 설명·FAQ·GURPS Lite·BRP2025 Quickstart 해당 단락과 Sprawl 공개 프랑스어v1.1 행동4쪽/MC지정6쪽·DX3기본판 공식소개. 시판 코어 전권/최신 정오표 전수/PF카드본문 검토 아님'
# 시작 양식의 실제 수치/참조와 준비된 참가자 시험을 대조한다. 참가자 결과를 생성하지 않는다.
trial_prep=json.loads((v/'입문시나리오_검토.json').read_text())['reader_start_and_human_trial_preparation']
assert trial_prep['versions']=={'Design':'v1.26','Core':'v0.48','World':'v0.89','Sheet':'v0.44','Easy':'P v0.31','Intro':'v0.5','Tarot':'v0.3'}
for name,sha in trial_prep['artifacts_sha256'].items():assert hash_current(o/name)==sha
assert trial_prep['sheet_numbered_sections_preserved']==32 and trial_prep['start_sheet_is_same_person_body_primary_record']
start_sheet=sheet_reader.split('<a id="fewk-first-scene-sheet"></a>',1)[1].split('<a id="fewk-sheets"></a>',1)[0]
human_trials=sheet_reader.split('<a id="fewk-human-trials"></a>',1)[1].split('<a id="fewk-sheet-22"></a>',1)[0]
start_preset_rows=[line for line in start_sheet.splitlines() if re.match(r'^\| (격투|사격|운동|은밀|관찰|조사|해킹|공학|의학|교섭|생활|지식) \|',line)]
intro_profile=json.loads((v/'입문_프로필.json').read_text())
assert len(start_preset_rows)==12 and trial_prep['skill_names']==intro_profile['character']['skills']
assert trial_prep['preset_names']==list(intro_profile['character']['presets'])
start_preset_totals=[]
for i,line in enumerate(start_preset_rows):
 cells=[cell.strip() for cell in line.split('|')[1:-1]]
 assert cells[0]==intro_profile['character']['skills'][i]
 assert [int(value) for value in cells[1:]]==[values[i] for values in intro_profile['character']['presets'].values()]
for values in intro_profile['character']['presets'].values():
 assert sorted(values)==sorted(intro_profile['character']['allocation']) and sum(values)==440
 start_preset_totals.append(sum(values))
import runpy
percentile_rules=runpy.run_path(str(v/'백분율_코어검증.py'))
answer=trial_prep['reading_numeric_answer'];actual_target=percentile_rules['target'](answer['prepared'],answer['situation'])
assert actual_target==answer['target']==50 and (actual_target//2,actual_target//5)==(answer['good_limit'],answer['exceptional_limit'])==(25,10)
assert percentile_rules['grade'](actual_target,answer['roll'])==2 and answer['level']=='좋은 성공'
assert trial_prep['independent_reading_tasks']==['R1','R2','R3','R4','R5']
assert all(f'| {task} |' in human_trials for task in trial_prep['independent_reading_tasks'])
assert trial_prep['human_trial_modes']==['R','P','A','T'] and all(f'#### {mode}.' in human_trials for mode in trial_prep['human_trial_modes'])
assert human_trials.count('<details>')==human_trials.count('</details>')==1
for phrase in ['같은 인물/몸ID의 원본 기록','Core의 일반 지급 예와 입문 시나리오의 계약 지급','몸을 바꿨다고 행동을 새로 받지 않습니다']:
 assert phrase in start_sheet,phrase
for phrase in ['첫 답과 해설 후 고친 답','별도 시험ID의 전투 연습','실제 게시/답변 시각','별도 비교 장면','미확보','수정한 원고 위치·버전']:
 assert phrase in human_trials,phrase
assert '12_룰시트와캐릭터시트.md#fewk-first-scene-sheet' in easy
assert trial_prep['unplayed_routes_not_counted'] and trial_prep['actual_vs_rehearsed_async_distinguished'] and trial_prep['tarot_percentile_comparison_is_separate_scene'] and trial_prep['core_intro_story_events_unchanged']
assert trial_prep['participant_evidence_received']==[] and trial_prep['new_mechanical_parameter_values']==[]
for flag in ['all_reader_and_playtest_issues_resolved','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not trial_prep[flag]
d['current_reader_start_and_human_trial_preparation']={'Sheet':'v0.44','Easy':'P v0.31','Design':'v1.26','numbered_sheet_sections':32,'preset_skill_cells_checked':36,'preset_totals':start_preset_totals,'reading_tasks':5,'numeric_reading_answer_checked_against_common_engine':True,'human_trial_modes':['R','P','A','T'],'current_core_and_intro_events_unchanged':True,'actual_evidence_received':0,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# Uploaded source directory: actual file/hash coverage and two newly read source texts.
upload_inventory=legacy_coherence['uploaded_settings_inventory']
upload_review=legacy_coherence['uploaded_author_note_and_outline_review']
upload_rows=upload_inventory['files'];upload_paths={row['path_relative_to_plan'] for row in upload_rows}
upload_directory=(p/upload_rows[0]['path_relative_to_plan']).parent
assert upload_paths=={str(path.relative_to(p)) for path in upload_directory.iterdir() if path.is_file()}
upload_seen={};upload_status_by_hash={}
for row in upload_rows:
 path=p/row['path_relative_to_plan'];verify_recorded_source_hash(path,row['sha256'])
 raw=path.read_bytes();assert (len(raw),len(raw.decode('utf-8-sig').splitlines()))==(row['bytes'],row['lines'])
 assert row['content_acquired_and_hashed'] and row['duplicate_of_upload_path']==upload_seen.get(row['sha256'])
 upload_seen.setdefault(row['sha256'],row['path_relative_to_plan'])
 upload_status_by_hash.setdefault(row['sha256'],row['semantic_status'])
 assert row['whole_document_read_evidence']==(row['semantic_status'] in ['reused_whole_document','new_whole_document'])
assert len(upload_rows)==14 and len(upload_seen)==12 and sum(row['duplicate_of_upload_path'] is not None for row in upload_rows)==2
assert sum(status=='reused_whole_document' for status in upload_status_by_hash.values())==4
assert sum(status=='new_whole_document' for status in upload_status_by_hash.values())==4
assert sum(status=='selected_topics_only' for status in upload_status_by_hash.values())==1
assert sum(status=='scope_and_semantic_review_pending' for status in upload_status_by_hash.values())==3
upload_sources=upload_review['snapshots'];assert len(upload_sources)==upload_review['whole_documents_read']==upload_review['new_distinct_whole_documents_read']==2
assert upload_review['versions']=={'World':'v0.90','Design':'v1.27','Core':'v0.48','Sheet':'v0.44','Easy':'P v0.31','Intro':'v0.5','Tarot':'v0.3'}
for source in upload_sources:
 path=p/source['path_relative_to_plan'];verify_recorded_source_hash(path,source['sha256']);text=path.read_text(encoding='utf-8-sig')
 assert source['text']==text and hashlib.sha256(text.encode()).hexdigest()==source['normalized_text_sha256']
 assert (len(text),len(text.splitlines()))==(source['chars'],source['lines'])
 assert source['whole_document_read'] and source['semantic_review_complete']
 assert any(entry['sha256']==source['sha256'] and entry['whole_document_read'] for entry in additional_procurement)
assert [source['lines'] for source in upload_sources]==[54,102]
assert len(upload_review['issues'])==10 and {row['id'] for row in upload_review['issues']}=={f'UP-N{i:02d}' for i in range(1,11)}
for row in upload_review['issues']:
 a,b=row['lines'];assert 1<=a<=b<=54 and row['decision']
outline_numbers=[int(match[1]) for match in re.finditer(r'(?m)^(\d+)\. ',upload_sources[1]['text'])]
assert outline_numbers==[row['source_top_section'] for row in upload_review['outline_mapping']]==list(range(1,12))
for row in upload_review['outline_mapping']:
 for destination in row['destinations']:
  name,anchor=destination.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text()),destination
assert '사람 중심으로 돌아갑니다' in upload_sources[0]['text'] and '오늘 먹을 오얏' in upload_sources[0]['text']
assert '프라임 스탯' in upload_sources[1]['text']
for phrase in ['거대한 비밀 곁에서 오늘을 이어가기','장면이 끝나도 사람의 관계와 실제 몸·물건·기록은 이어집니다','사람을 따라 읽는 시간','기본 주사위를d6으로 바꾸거나','원래 장면의 죽음·지출을 취소하거나']:
 assert phrase in world,phrase
assert upload_review['additional_registered_whole_documents']==114 and len(additional_procurement)==117 and upload_review['new_mechanical_parameter_values']==[]
for flag in ['current_engine_changed','linked_remote_documents_reviewed','whole_upload_inventory_semantically_complete','all_older_unique_sources_reviewed','all_related_novels_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not upload_review[flag]
upload_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_uploaded_author_note_regression']
assert upload_intro['World']=='v0.90' and upload_intro['world_sha256']==legacy_coherence['uploaded_keyword_table_review']['input_world_sha256_before']
assert upload_intro['same_scene_actions_and_intro_events'] and upload_intro['same_percentile_engine'] and upload_intro['short_scenes_do_not_reset_person_body_records'] and upload_intro['human_dice_is_not_d6_engine_or_auto_undo']
d['current_uploaded_author_note_and_outline_review']={'World':'v0.90','Design':'v1.27','uploaded_file_hashes_verified':14,'distinct_upload_contents':12,'new_whole_documents_read':2,'new_whole_source_lines':[54,102],'issues_reviewed':10,'outline_top_sections_mapped':11,'uploaded_scope_and_semantic_pending_distinct_contents':6,'additional_registered_whole_documents':114,'current_engine_changed':False,'all_uploaded_unique_contents_semantically_reviewed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# Keyword source: prefix coverage is separate from whole-file parsing and hashing.
import csv,io,collections
keyword_review=legacy_coherence['uploaded_keyword_table_review'];keyword_source=keyword_review['source']
keyword_path=p/keyword_source['path_relative_to_plan'];verify_recorded_source_hash(keyword_path,keyword_source['sha256'])
keyword_raw=keyword_path.read_bytes();keyword_text=keyword_raw.decode('utf-8-sig')
assert (len(keyword_raw),len(keyword_text),len(keyword_text.splitlines()))==(keyword_source['bytes'],keyword_source['chars'],keyword_source['physical_lines'])==(173915,82098,996)
keyword_reader=csv.reader(io.StringIO(keyword_text));keyword_rows=[];keyword_physical=[];keyword_last=0
for row in keyword_reader:
 keyword_rows.append(row);keyword_physical.append([keyword_last+1,keyword_reader.line_num]);keyword_last=keyword_reader.line_num
assert keyword_rows[0]==keyword_source['header'] and len(keyword_rows)-1==keyword_source['logical_data_rows']==984 and set(map(len,keyword_rows))=={12}
assert (keyword_review['reviewed_prefix_data_rows'],keyword_review['remaining_data_rows'])==(250,734)
assert keyword_review['reviewed_prefix_physical_line_end']==keyword_physical[250][1] and len(keyword_review['rows'])==250
keyword_terms=collections.defaultdict(list)
for i,row in enumerate(keyword_review['rows'],1):
 assert row['data_row']==i and row['values']==keyword_rows[i] and row['physical_lines']==keyword_physical[i]
 assert row['all_12_cells_read'] and row['disposition'] and not row['all_individual_facts_canon_verified']
 keyword_terms[keyword_rows[i][0]].append(i)
assert {key:ns for key,ns in keyword_terms.items() if len(ns)>1}==keyword_review['prefix_same_spelling_groups']=={'각성':[42,43,44],'대사관':[183,184],'리버힐':[246,247]}
assert len(keyword_review['focused_issues'])==18 and {row['id'] for row in keyword_review['focused_issues']}=={f'K{i:02d}' for i in range(1,19)}
for row in keyword_review['focused_issues']:
 assert row['decision'] and all(1<=n<=250 for n in row['data_rows'])
 for dest in row['destinations']:
  name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text()),dest
for row in keyword_review['rows']:
 assert row['focused_issue_ids']==[issue['id'] for issue in keyword_review['focused_issues'] if row['data_row'] in issue['data_rows']]
assert keyword_rows[158][0]=='네이티브' and '완전한 죽음' in keyword_rows[158][1]
assert keyword_rows[216][0]=='드랍아웃' and keyword_rows[216][1]=='코마 참고'
assert '\x08' in keyword_rows[208][8] and keyword_rows[51][5]=='Code 59' and keyword_rows[126][5]=='Code 46'
assert '.nation' in keyword_rows[123][6] and keyword_rows[123][8]=='.domain'
keyword_primary=keyword_review['primary_source_rechecks'];verify_recorded_source_hash(p/keyword_primary['path_relative_to_plan'],keyword_primary['sha256'])
keyword_primary_text=(p/keyword_primary['path_relative_to_plan']).read_text();keyword_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',keyword_primary_text))
assert [row['topic'] for row in keyword_primary['topics']]==['0006','0007','0029','0049','0058','0064','0072','0079']
for row in keyword_primary['topics']:
 i=next(i for i,h in enumerate(keyword_heads) if h[1]==row['topic']);body=keyword_primary_text[keyword_heads[i].start():keyword_heads[i+1].start()]
 assert row['text']==body and hashlib.sha256(body.encode()).hexdigest()==row['text_sha256'] and row['whole_topic_rechecked'] and not row['new_whole_topic_counted']
assert keyword_review['prefix_all_cells_read'] and keyword_review['new_whole_documents']==0 and keyword_primary['new_whole_documents']==0 and keyword_review['additional_registered_whole_documents']==114
assert not keyword_source['whole_document_read'] and not keyword_source['whole_document_semantic_review_complete']
for flag in ['foreign_language_translation_quality_verified','all_AD_originals_obtained_or_read','remote_links_read','current_engine_changed','all_prefix_individual_facts_canon_verified','all_uploaded_unique_contents_semantically_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not keyword_review[flag]
assert keyword_review['new_mechanical_parameter_values']==[]
keyword_guide=world.split('<a id="fewk-keyword-reading"></a>',1)[1].split('### 지도에서 찾을 것',1)[0]
assert len(re.findall(r'^\| (?!찾은 말)(.+?) \|',keyword_guide,re.M))==24
assert '그 칸이 곧 배운 스킬이라는 뜻은 아닙니다' in keyword_guide and '984자료행의 모든12칸' in keyword_guide and '연결된AD 원문' in keyword_guide
assert '지정 차원 재진입이 막히는 드랍아웃은 혼수·사망과 구분' in keyword_guide and '두 장소의 차원 귀속·좌표와 통행을 확정하지 않습니다' in keyword_guide
assert '55장의 마리아/클럽 전기' not in world and '[60장의 마리아/클럽 전기](#fewk-world-60)' in world
assert '\x08' not in world
keyword_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_keyword_prefix_regression']
assert keyword_intro['World']=='v0.91' and keyword_intro['world_sha256']==legacy_coherence['uploaded_keyword_table_middle_review']['input_world_sha256_before'] and keyword_intro['same_scene_actions_and_intro_events'] and keyword_intro['same_percentile_engine'] and not keyword_intro['whole_keyword_table_reviewed']
d['current_uploaded_keyword_table_review']={'World':'v0.91','Design':'v1.28','total_source_data_rows':984,'reviewed_prefix_data_rows':250,'remaining_data_rows':734,'all_cells_in_reviewed_prefix':3000,'prefix_duplicate_spelling_groups':3,'focused_issues':18,'primary_topics_rechecked':8,'reader_distinctions':8,'new_whole_documents':0,'additional_registered_whole_documents':114,'whole_document_reviewed':False,'current_engine_changed':False,'foreign_language_translation_quality_verified':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# Second CSV pass retains the first pass and checks contiguous cumulative coverage.
keyword_middle=legacy_coherence['uploaded_keyword_table_middle_review']
assert keyword_middle['source']==keyword_source and keyword_middle['previous_pass_record']=='uploaded_keyword_table_review'
assert keyword_middle['data_row_range']==[251,500] and len(keyword_middle['rows'])==250
assert keyword_middle['versions']=={'World':'v0.92','Design':'v1.29','Core':'v0.48','Sheet':'v0.44','Easy':'P v0.31','Intro':'v0.5','Tarot':'v0.3'}
for i,row in enumerate(keyword_middle['rows'],251):
 assert row['data_row']==i and row['values']==keyword_rows[i] and row['physical_lines']==keyword_physical[i]
 assert row['all_12_cells_read'] and row['disposition'] and not row['all_individual_facts_canon_verified']
 assert row['focused_issue_ids']==[issue['id'] for issue in keyword_middle['focused_issues'] if i in issue['data_rows']]
assert len(keyword_middle['focused_issues'])==18 and {row['id'] for row in keyword_middle['focused_issues']}=={f'K{i:02d}' for i in range(19,37)}
for row in keyword_middle['focused_issues']:
 assert row['decision'] and all(251<=n<=500 for n in row['data_rows'])
 for dest in row['destinations']:
  name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text()),dest
keyword_cumulative=keyword_review['rows']+keyword_middle['rows']
assert [row['data_row'] for row in keyword_cumulative]==list(range(1,501))
assert (keyword_middle['cumulative_reviewed_prefix_data_rows'],keyword_middle['remaining_data_rows'],keyword_middle['cumulative_focused_issues'])==(500,484,36)
assert len(keyword_review['focused_issues'])+len(keyword_middle['focused_issues'])==36
keyword_cumulative_terms=collections.defaultdict(list)
for row in keyword_cumulative:keyword_cumulative_terms[row['values'][0]].append(row['data_row'])
assert {k:ns for k,ns in keyword_cumulative_terms.items() if len(ns)>1}==keyword_middle['cumulative_same_spelling_groups']
assert keyword_middle['pass_all_cells_read'] and keyword_middle['new_mechanical_parameter_values']==[] and keyword_middle['new_whole_documents']==0 and keyword_middle['additional_registered_whole_documents']==114
for flag in ['foreign_language_translation_quality_verified','all_AD_originals_obtained_or_read','remote_links_read','current_engine_changed','all_individual_facts_canon_verified','all_uploaded_unique_contents_semantically_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not keyword_middle[flag]
middle_primary=keyword_middle['primary_source_rechecks'];assert middle_primary['sha256']==keyword_primary['sha256'] and middle_primary['path_relative_to_plan']==keyword_primary['path_relative_to_plan'] and middle_primary['new_whole_documents']==0
assert [row['topic'] for row in middle_primary['topics']]==['0035','0041','0043','0056','0065','0066','0077','0083']
for row in middle_primary['topics']:
 i=next(i for i,h in enumerate(keyword_heads) if h[1]==row['topic']);body=keyword_primary_text[keyword_heads[i].start():keyword_heads[i+1].start()]
 assert row['text']==body and hashlib.sha256(body.encode()).hexdigest()==row['text_sha256'] and row['whole_topic_rechecked'] and not row['new_whole_topic_counted']
from fractions import Fraction
fraction_note=keyword_middle['fraction_note_check'];assert fraction_note['source_data_row']==463 and keyword_rows[463][0]=='숫자세기'
assert '모(毛) = 1/10000' in keyword_rows[463][1] and '사(絲) = 0.0001' in keyword_rows[463][1] and '홀(忽) = 0.00001' in keyword_rows[463][1]
assert Fraction(fraction_note['source_mo'])==Fraction(fraction_note['source_sa'])
expected=Fraction(fraction_note['source_mo']);fraction_corrections_checked=0
for name in ['sa','hol']:
 expected/=10;corrected=fraction_note['sequential_tenth_after_mo'][name]
 assert Fraction(corrected['numerator'],corrected['denominator'])==Fraction(corrected['decimal'])==expected
 fraction_corrections_checked+=1
assert not fraction_note['source_rewritten'] and not fraction_note['new_rule_parameters']
assert keyword_rows[464][0]==keyword_rows[465][0]=='쉘터' and keyword_rows[464][3]=='AD' and keyword_rows[464][5]=='AD 77' and keyword_rows[465][5]=='Core 56'
assert '석유 플랜트' in keyword_rows[464][1] and '다이버 코핀' in keyword_rows[465][1]
assert 'Vite' in keyword_rows[325][6] and '컴퓨터 바이트' in keyword_rows[325][6]
assert '교환되는 개념' in keyword_rows[470][1] and '생체순도' in keyword_rows[412][1]
assert '원본0056의 쉘터는 코핀과 방호 옵션' in world and 'AD77 ‘쉘터’는 북부 해협' in world
assert '새 거주 장면 — 기다리는 사람에게 남길 말' in world and '바이트라는 말과 단위표 읽기' in world
assert '사는1/100000=0.00001, 홀은1/1000000=0.000001' in world
middle_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_keyword_middle_regression']
assert (middle_intro['World'],middle_intro['Design'],middle_intro['reviewed_prefix_data_rows'],middle_intro['remaining_data_rows'],middle_intro['cumulative_issues'],middle_intro['reader_distinctions'])==('v0.92','v1.29',500,484,36,16)
assert middle_intro['world_sha256']==legacy_coherence['uploaded_keyword_table_full_review']['input_world_sha256_before'] and middle_intro['same_scene_actions_and_intro_events'] and middle_intro['same_percentile_engine'] and not middle_intro['whole_keyword_table_reviewed']
keyword_upload=next(row for row in upload_rows if row['path_relative_to_plan']==keyword_source['path_relative_to_plan'])
assert keyword_upload['semantic_status']=='new_whole_document' and keyword_upload['whole_document_read_evidence']
assert (keyword_upload['current_partial_review']['reviewed_data_rows'],keyword_upload['current_partial_review']['remaining_data_rows'])==(984,0)
d['current_uploaded_keyword_table_review']={'World':'v0.92','Design':'v1.29','pass_records':['uploaded_keyword_table_review','uploaded_keyword_table_middle_review'],'total_source_data_rows':984,'reviewed_prefix_data_rows':500,'remaining_data_rows':484,'all_cells_in_reviewed_prefix':6000,'prefix_duplicate_spelling_groups':len(keyword_middle['cumulative_same_spelling_groups']),'focused_issues':36,'primary_topics_rechecked_by_pass':[8,8],'reader_distinctions':16,'fraction_corrections_checked':fraction_corrections_checked,'new_whole_documents':0,'additional_registered_whole_documents':114,'whole_document_reviewed':False,'current_engine_changed':False,'foreign_language_translation_quality_verified':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# Whole keyword table: all 984 rows have reading and current-use decisions, not all canon/translation claims.
keyword_full=legacy_coherence['uploaded_keyword_table_full_review'];keyword_full_source=keyword_full['source']
assert {k:value for k,value in keyword_full_source.items() if k not in ['whole_document_read','whole_document_semantic_review_complete']}=={k:value for k,value in keyword_source.items() if k not in ['whole_document_read','whole_document_semantic_review_complete']}
assert keyword_full_source['whole_document_read'] and keyword_full_source['whole_document_semantic_review_complete']
assert keyword_full['previous_pass_records']==['uploaded_keyword_table_review','uploaded_keyword_table_middle_review']
assert keyword_full['data_row_range']==[501,984] and len(keyword_full['rows'])==484
assert keyword_full['versions']=={'World':'v0.93','Design':'v1.30','Core':'v0.48','Sheet':'v0.44','Easy':'P v0.31','Intro':'v0.5','Tarot':'v0.3'}
for i,row in enumerate(keyword_full['rows'],501):
 assert row['data_row']==i and row['values']==keyword_rows[i] and row['physical_lines']==keyword_physical[i]
 assert row['all_12_cells_read'] and row['disposition'] and not row['all_individual_facts_canon_verified']
 assert row['focused_issue_ids']==[issue['id'] for issue in keyword_full['focused_issues'] if i in issue['data_rows']]
assert len(keyword_full['focused_issues'])==24 and {row['id'] for row in keyword_full['focused_issues']}=={f'K{i:02d}' for i in range(37,61)}
for row in keyword_full['focused_issues']:
 assert row['decision'] and all(501<=n<=984 for n in row['data_rows'])
 for dest in row['destinations']:
  name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text()),dest
keyword_complete_rows=keyword_cumulative+keyword_full['rows']
assert [row['data_row'] for row in keyword_complete_rows]==list(range(1,985))
assert (keyword_full['cumulative_reviewed_data_rows'],keyword_full['remaining_data_rows'],keyword_full['cumulative_all_cells_read'],keyword_full['cumulative_focused_issues'])==(984,0,11808,60)
assert sum(len(review['focused_issues']) for review in [keyword_review,keyword_middle,keyword_full])==60
keyword_full_terms=collections.defaultdict(list)
for row in keyword_complete_rows:keyword_full_terms[row['values'][0]].append(row['data_row'])
assert {k:ns for k,ns in keyword_full_terms.items() if len(ns)>1}==keyword_full['cumulative_same_spelling_groups']
assert keyword_full['pass_all_cells_read'] and keyword_full['table_whole_document_first_pass_complete'] and keyword_full['new_whole_documents']==1 and keyword_full['additional_registered_whole_documents']==115 and len(additional_procurement)==117
assert keyword_full['new_mechanical_parameter_values']==[]
for flag in ['source_file_rewritten','foreign_language_translation_quality_verified','all_AD_originals_obtained_or_read','remote_links_read','current_engine_changed','all_individual_facts_canon_verified','all_uploaded_unique_contents_semantically_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not keyword_full[flag]
full_primary=keyword_full['primary_source_rechecks'];assert full_primary['sha256']==keyword_primary['sha256'] and full_primary['path_relative_to_plan']==keyword_primary['path_relative_to_plan'] and full_primary['new_whole_documents']==0
assert [row['topic'] for row in full_primary['topics']]==['0031','0044','0060','0067','0072','0073','0085','0087','0095','0098','0100']
for row in full_primary['topics']:
 i=next(i for i,h in enumerate(keyword_heads) if h[1]==row['topic']);body=keyword_primary_text[keyword_heads[i].start():keyword_heads[i+1].start()]
 assert row['text']==body and hashlib.sha256(body.encode()).hexdigest()==row['text_sha256'] and row['whole_topic_rechecked'] and not row['new_whole_topic_counted']
full_primary_by_topic={row['topic']:row['text'] for row in full_primary['topics']}
assert keyword_rows[707][0]=='재민' and '드랍아웃하고 만다' in keyword_rows[707][1] and '직접 그를 드랍아웃' in full_primary_by_topic['0095']
assert '일반적으로 다이브를 한 번 할때마다 600배' in keyword_rows[670][1] and '본체로 이중 다이브' in full_primary_by_topic['0044'] and '600배' in full_primary_by_topic['0044']
assert '모든 행동은 에고를 소진' in keyword_rows[572][1] and '그 즉시 드랍아웃' in keyword_rows[575][1]
assert '모든 플라이어;가 다 의지체;는 아니지만' in full_primary_by_topic['0044']
assert '모든 것을 둔 채 연결된 존재를 조종만 하는 아바타' in full_primary_by_topic['0072']
assert '물질계;를 포함한 계;에서 태어난 사람' in full_primary_by_topic['0072']
assert '웅와' in keyword_rows[640][0] and '여성형' in keyword_rows[640][1] and '남성 키와로 남와, 웅와' in keyword_rows[841][1]
assert keyword_rows[509][5]=='Crore 67' and keyword_rows[814][5]=='Code 73' and keyword_rows[819][5]=='Code 27'
assert keyword_rows[826][1]=='파이 참고' and keyword_rows[867][1]=='코코 참고' and keyword_rows[840][1]=='클리에989 참고'
assert keyword_rows[746][0]==keyword_rows[747][0]=='줄' and keyword_rows[746][5]=='AD 21' and keyword_rows[747][5]=='AD 59'
assert '누가 이동했는지' in world and '원격 조종 아바타' in world and '자의식을 가진 의지체' in world
assert '원본0095에서 드랍아웃을 시킨 사람은 재민, 당한 사람은 맥도웰' in keyword_guide
assert '두 연결을 유지하는 일과 다른 자아를 만드는 일' in world and '한 번 더 들어갈 때마다 무조건600배' in world
full_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_keyword_full_regression']
assert (full_intro['World'],full_intro['Design'],full_intro['reviewed_data_rows'],full_intro['remaining_data_rows'],full_intro['cumulative_issues'],full_intro['reader_distinctions'])==('v0.93','v1.30',984,0,60,24)
assert full_intro['world_sha256']==legacy_coherence['uploaded_core_basic_reuse_review']['input_world_sha256_before'] and full_intro['same_scene_actions_and_intro_events'] and full_intro['same_percentile_engine'] and full_intro['whole_keyword_table_reviewed']
assert not full_intro['foreign_language_translation_quality_verified'] and not full_intro['all_individual_facts_canon_verified']
assert any(row['id']=='LEG-UPLOAD-03' and row['sha256']==keyword_source['sha256'] and row['source_relative_to_plan']==keyword_source['path_relative_to_plan'] and row['whole_document_read'] for row in additional_procurement)
assert upload_inventory['new_whole_distinct_contents']==4 and upload_inventory['scope_and_semantic_pending_distinct_contents']==3
assert keyword_upload['current_partial_review']['whole_document_reviewed'] and keyword_upload['current_partial_review']['record']=='uploaded_keyword_table_full_review'
d['current_uploaded_keyword_table_review']={'World':'v0.93','Design':'v1.30','pass_records':keyword_full['previous_pass_records']+['uploaded_keyword_table_full_review'],'total_source_data_rows':984,'reviewed_data_rows':984,'remaining_data_rows':0,'all_cells_read':11808,'duplicate_spelling_groups':len(keyword_full['cumulative_same_spelling_groups']),'focused_issues':60,'primary_topics_rechecked_by_pass':[8,8,11],'reader_distinctions':24,'fraction_corrections_checked':fraction_corrections_checked,'new_whole_documents':1,'additional_registered_whole_documents':115,'whole_document_reviewed':True,'foreign_language_translation_quality_verified':False,'all_individual_facts_canon_verified':False,'uploaded_scope_and_semantic_pending_distinct_contents':5,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# Reuse prior full-topic reading only when the actual source text matches after whitespace removal.
basic_reuse=legacy_coherence['uploaded_core_basic_reuse_review'];basic_source=basic_reuse['source'];basic_path=p/basic_source['path_relative_to_plan'];verify_recorded_source_hash(basic_path,basic_source['sha256'])
basic_text=basic_path.read_text(encoding='utf-8-sig');basic_primary=legacy_coherence['foundational_core_time_order_csv_review']['primary_container_closure'];basic_primary_path=p/basic_primary['source_path_relative_to_plan'];verify_recorded_source_hash(basic_primary_path,basic_primary['sha256']);basic_primary_text=basic_primary_path.read_bytes().decode()
assert basic_primary['whole_container_read'] and basic_primary['whole_semantic_review_complete']
assert (basic_source['bytes'],basic_source['lines'])==(len(basic_path.read_bytes()),len(basic_text.splitlines()))==(259518,1605)
assert basic_reuse['primary_source_sha256']==basic_primary['sha256'] and basic_reuse['primary_source_path_relative_to_plan']==basic_primary['source_path_relative_to_plan']
def core_basic_blocks(value):
 heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',value));out=[];counts=collections.Counter()
 for i,h in enumerate(heads):
  end=heads[i+1].start() if i+1<len(heads) else len(value);body=value[h.start():end];counts[h[1]]+=1
  out.append({'topic':h[1],'occurrence':counts[h[1]],'start_line':value[:h.start()].count('\n')+1,'end_line':value[:end].count('\n')+(0 if value[:end].endswith('\n') else 1),'text':body,'text_sha256':hashlib.sha256(body.encode()).hexdigest(),'whitespace_removed_sha256':hashlib.sha256(re.sub(r'\s+','',body).encode()).hexdigest()})
 return value[:heads[0].start()],out
basic_preamble,basic_parts=core_basic_blocks(basic_text);_,basic_primary_parts=core_basic_blocks(basic_primary_text)
assert len(basic_parts)==105 and len(basic_primary_parts)==210 and basic_preamble==basic_reuse['preamble_text'] and basic_reuse['preamble_read']
assert [row['topic'] for row in basic_reuse['topics']]==[f'{n:04d}' for n in range(1,106)]
for source_row,row in zip(basic_parts,basic_reuse['topics']):
 for key in ['topic','occurrence','start_line','end_line','text_sha256','whitespace_removed_sha256']:assert source_row[key]==row[key]
 matches=[part for part in basic_primary_parts if part['topic']==row['topic'] and re.sub(r'\s+','',part['text'])==re.sub(r'\s+','',source_row['text'])]
 assert matches and row['matched_primary_occurrences']==[{key:part[key] for key in ['occurrence','start_line','text_sha256']} for part in matches]
 assert row['prior_whole_topic_reading_reused'] and row['title_only']==(row['topic'] in ['0101','0102'])
 for part in matches:assert any(proof['topic']==part['topic'] and proof['occurrence']==part['occurrence'] and proof['text_sha256']==part['text_sha256'] for proof in basic_primary['occurrence_mapping'])
assert basic_reuse['topics_matched']==105 and basic_reuse['unmatched_topics']==[] and basic_reuse['title_only_topics']==['0101','0102'] and basic_reuse['new_unique_substantive_contents']==0
assert basic_reuse['whole_document_review_evidence_reused'] and not basic_reuse['new_whole_topic_reading_counted'] and not basic_reuse['raw_file_identical_to_primary'] and basic_source['sha256']!=basic_primary['sha256']
for flag in ['source_file_rewritten','all_individual_facts_canon_verified','current_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not basic_reuse[flag]
assert basic_reuse['new_registered_whole_source_files']==1 and basic_reuse['additional_registered_whole_documents']==116 and len(additional_procurement)==117
basic_upload=next(row for row in upload_rows if row['sha256']==basic_source['sha256']);assert basic_upload['semantic_status']=='reused_whole_document' and basic_upload['whole_document_read_evidence'] and basic_upload['review_evidence']=='uploaded_core_basic_reuse_review'
assert any(row['id']=='LEG-UPLOAD-04' and row['sha256']==basic_source['sha256'] and row['whole_document_read'] for row in additional_procurement)
# First draft: comments and selected contexts, never whole-document evidence.
draft_comments=legacy_coherence['first_draft_editorial_comment_review'];draft_source=draft_comments['source'];draft_path=p/draft_source['path_relative_to_plan'];verify_recorded_source_hash(draft_path,draft_source['sha256']);draft_lines=draft_path.read_text(encoding='utf-8-sig').splitlines()
assert (len(draft_path.read_bytes()),len(draft_lines))==(draft_source['bytes'],draft_source['lines'])==(494868,3722)
draft_tail='\n'.join(draft_lines[3700:]);assert draft_comments['tail_lines']==[3701,3722] and draft_comments['tail_text']==draft_tail and draft_comments['tail_text_sha256']==hashlib.sha256(draft_tail.encode()).hexdigest()
draft_heads=list(re.finditer(r'(?m)^\[([a-u])\]',draft_tail));assert len(draft_heads)==len(draft_comments['comments'])==21
for i,(h,row) in enumerate(zip(draft_heads,draft_comments['comments'])):
 end=draft_heads[i+1].start() if i+1<len(draft_heads) else len(draft_tail);body=draft_tail[h.start():end].rstrip('\n')
 assert row['id']==h[1] and row['text']==body and row['text_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['read'] and row['start_line']==3701+draft_tail[:h.start()].count('\n')
 assert row['id'] in draft_comments['issues'][row['decision_index']]['comment_ids']
assert len(draft_comments['issues'])==len(draft_comments['selected_contexts'])==16
assert sorted(cid for issue in draft_comments['issues'] for cid in issue['comment_ids'])==list('abcdefghijklmnopqrstu')
for row in draft_comments['selected_contexts']:
 a,b=row['lines'];body='\n'.join(draft_lines[a-1:b]);assert row['text']==body and row['text_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['selected_context_read'] and row['lines']==[row['marker_line']-1,row['marker_line']+1]
for row in draft_comments['issues']:
 name,anchor=row['destination'].split('#');assert row['decision'] and anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text())
assert draft_comments['main_text_lines']==[1,3700] and draft_comments['new_whole_documents']==0
for flag in ['whole_document_read','whole_document_semantic_review_complete','main_text_whole_read','all_legacy_editorial_comments_resolved','source_file_rewritten','current_engine_changed','actual_participant_reading','actual_participant_playtest']:assert not draft_comments[flag]
draft_upload=next(row for row in upload_rows if row['sha256']==draft_source['sha256']);assert draft_upload['semantic_status']=='new_whole_document' and draft_upload['whole_document_read_evidence'] and draft_upload['current_partial_review']['whole_document_reviewed']
person_guide=world.split('### 인물과 몸을 구분해 읽기',1)[1].split('<a id="fewk-noene"></a>',1)[0]
for phrase in ['인물의 숙련과 관계 기록은 하나','B1의 손을 다쳤다면 B1에 기록','반동 기능이 없는 한','누가 경험하고 선택하는지','74장']:assert phrase in person_guide,phrase
basic_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_core_basic_editorial_regression']
assert (basic_intro['World'],basic_intro['Design'],basic_intro['core_basic_topics_matched'],basic_intro['first_draft_comments_read'],basic_intro['first_draft_selected_contexts_read'])==('v0.94','v1.31',105,21,16)
assert basic_intro['world_sha256']==legacy_coherence['first_draft_prefix_review']['input_world_sha256_before'] and basic_intro['same_scene_actions_and_intro_events'] and basic_intro['same_percentile_engine'] and not basic_intro['whole_first_draft_read'] and not basic_intro['actual_participant_reading']
assert upload_inventory['reused_whole_distinct_contents']==4 and upload_inventory['scope_and_semantic_pending_distinct_contents']==3
d['current_uploaded_core_basic_and_editorial_review']={'World':'v0.94','Design':'v1.31','core_basic_topics_matched':105,'new_unique_substantive_contents':0,'additional_registered_whole_documents':116,'first_draft_comments_read':21,'first_draft_selected_contexts_read':16,'first_draft_issues_reviewed':16,'whole_first_draft_read':False,'uploaded_scope_and_semantic_pending_distinct_contents':4,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
# Initial draft prefix: full reading of 1..500 plus previously selected contexts, not whole draft.
draft_prefix=legacy_coherence['first_draft_prefix_review'];assert draft_prefix['source']==draft_source
assert draft_prefix['versions']=={'World':'v0.95','Design':'v1.32','Core':'v0.48','Sheet':'v0.44','Easy':'P v0.31','Intro':'v0.5','Tarot':'v0.3'}
draft_prefix_text='\n'.join(draft_lines[:500]);assert draft_prefix['prefix_lines']==[1,500] and draft_prefix['prefix_text']==draft_prefix_text and draft_prefix['prefix_text_sha256']==hashlib.sha256(draft_prefix_text.encode()).hexdigest() and draft_prefix['prefix_all_lines_read']
draft_comparison=draft_prefix['comparison_only'];draft_parent=legacy_coherence['foundational_world_bible_appendix_review']['source'];draft_parent_path=p/draft_parent['path_relative_to_plan'];verify_recorded_source_hash(draft_parent_path,draft_parent['sha256'])
assert draft_comparison['parent_source_path_relative_to_plan']==draft_parent['path_relative_to_plan'] and draft_comparison['parent_source_sha256']==draft_parent['sha256'] and draft_parent['whole_document_read'] and draft_parent['semantic_review_complete']
draft_parent_norm=re.sub(r'\s+','',draft_parent_path.read_text(encoding='utf-8-sig'));draft_actual_census=[]
for n,line in enumerate(draft_lines,1):
 normalized=re.sub(r'\s+','',re.sub(r'\[[a-u]\]','',line) if n<=3700 else line);position=draft_parent_norm.find(normalized) if normalized else -1
 draft_actual_census.append({'line':n,'normalized_text_sha256':hashlib.sha256(normalized.encode()).hexdigest(),'parent_normalized_position':position,'classification':'editorial_tail' if n>=3701 else ('blank' if not normalized else ('matching_parent_substring' if position>=0 else 'unique_or_changed'))})
assert draft_actual_census==draft_comparison['all_lines']
assert dict(collections.Counter(row['classification'] for row in draft_actual_census))==draft_comparison['line_counts']=={'blank':1941,'unique_or_changed':1607,'matching_parent_substring':152,'editorial_tail':22}
assert not draft_comparison['semantic_review_inferred_from_substring_match'] and not draft_comparison['all_unique_or_changed_lines_read']
assert dict(collections.Counter(row['classification'] for row in draft_actual_census[:500]))==draft_prefix['prefix_line_counts']=={'unique_or_changed':292,'blank':187,'matching_parent_substring':21}
assert len(draft_prefix['major_section_mapping'])==15
draft_major_covered=[]
for row in draft_prefix['major_section_mapping']:
 a,b=row['lines'];draft_major_covered.extend(range(a,b+1));assert row['all_lines_read'] and row['decision']
 for dest in row['destinations']:
  if '#' in dest:
   name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text())
  else:assert (o/dest).is_file()
assert draft_major_covered==list(range(1,501))
assert len(draft_prefix['focused_issues'])==20 and [row['id'] for row in draft_prefix['focused_issues']]==[f'FD{i:02d}' for i in range(1,21)]
for row in draft_prefix['focused_issues']:
 a,b=row['lines'];name,anchor=row['destination'].split('#');assert 1<=a<=b<=500 and row['decision'] and anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text())
draft_read_lines=set(range(1,501))|set(range(3701,3723))
for row in draft_comments['selected_contexts']:
 a,b=row['lines'];draft_read_lines.update(range(a,b+1))
assert len(draft_read_lines)==draft_prefix['cumulative_distinct_physical_lines_read']==567 and len(draft_lines)-len(draft_read_lines)==draft_prefix['remaining_not_whole_read_lines']==3155
assert draft_prefix['main_text_remaining_continuous_range']==[501,3700] and draft_prefix['new_whole_documents']==0 and draft_prefix['additional_registered_whole_documents']==116 and len(additional_procurement)==117 and draft_prefix['new_mechanical_parameter_values']==[]
for flag in ['whole_document_read','whole_document_semantic_review_complete','current_engine_changed','remote_references_read','all_individual_facts_canon_verified','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not draft_prefix[flag]
assert draft_prefix['mission_hook_lines']==[193,211] and draft_prefix['mission_hooks_read']==19 and all(draft_lines[n-1].startswith('* ') for n in range(193,212))
assert '노인의 구형 임플란트' in draft_lines[197] and '팔기를 거부' in draft_lines[197]
assert '클래스 레벨이 오르면서 인터렉션이 증가' in draft_lines[316] and '생체순도와 합계100%' in draft_lines[275] and '보통 1만셀' in draft_lines[303]
prefix_primary=draft_prefix['primary_source_rechecks'];verify_recorded_source_hash(p/prefix_primary['path_relative_to_plan'],prefix_primary['sha256']);prefix_primary_text=(p/prefix_primary['path_relative_to_plan']).read_text();prefix_primary_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',prefix_primary_text))
assert [row['topic'] for row in prefix_primary['topics']]==['0023','0037','0057','0067','0073'] and prefix_primary['new_whole_documents']==0
for row in prefix_primary['topics']:
 i=next(i for i,head in enumerate(prefix_primary_heads) if head[1]==row['topic']);body=prefix_primary_text[prefix_primary_heads[i].start():prefix_primary_heads[i+1].start()]
 assert row['text']==body and row['text_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['whole_topic_rechecked'] and not row['new_whole_topic_counted']
assert '명시피해경로' in draft_prefix['focused_issues'][4]['decision']
assert draft_prefix['prefix_lines']==[1,500] and not draft_prefix['whole_document_read']
new_implant_scene=world.split('### 초고의 후크에서 이어 쓰기 — 팔지 않는 임플란트',1)[1].split('### 새 도입 — 장부를 돌려주는 저녁',1)[0]
assert '새 인물의 동기와 선택을 붙인 캠페인 예' in new_implant_scene and '매입 대신 현장 검사를 제안' in new_implant_scene and '대체 도구를 마련해 다시 제안' in new_implant_scene and '거절을 전달하고 의뢰를 바꿈/그만둠' in new_implant_scene
assert '### 템플릿의 확인과 실제 작업' in world and '현재 몸에는 맞는 연결부가 없어' in world
prefix_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_first_draft_prefix_regression']
assert (prefix_intro['World'],prefix_intro['Design'],prefix_intro['prefix_lines_read'],prefix_intro['major_parts'],prefix_intro['focused_issues'],prefix_intro['mission_hooks_read'])==('v0.95','v1.32',[1,500],15,20,19)
assert prefix_intro['world_sha256']==legacy_coherence['first_draft_middle_review']['input_world_sha256_before'] and prefix_intro['same_scene_actions_and_intro_events'] and prefix_intro['same_percentile_engine']
assert not prefix_intro['whole_first_draft_read'] and not prefix_intro['new_scene_is_canon_continuation'] and not prefix_intro['actual_participant_reading'] and not prefix_intro['actual_participant_playtest']
d['current_first_draft_prefix_review']={key:value for key,value in prefix_intro.items() if key not in ['world_sha256','same_scene_actions_and_intro_events','same_percentile_engine','new_scene_is_canon_continuation']}
d['current_first_draft_prefix_review'].update(additional_registered_whole_documents=116,new_whole_documents=0,uploaded_scope_and_semantic_pending_distinct_contents=4,primary_topics_rechecked=5,current_engine_changed=False)
# Next continuous draft segment: exact source text, coverage union and bounded source rechecks.
draft_middle=legacy_coherence['first_draft_middle_review'];assert draft_middle['source']==draft_source and draft_middle['previous_record']=='first_draft_prefix_review'
assert draft_middle['versions']=={'World':'v0.96','Design':'v1.33','Core':'v0.48','Sheet':'v0.44','Easy':'P v0.31','Intro':'v0.5','Tarot':'v0.3'}
draft_middle_text='\n'.join(draft_lines[500:1030]);assert draft_middle['part_lines']==[501,1030] and draft_middle['part_text']==draft_middle_text and draft_middle['part_text_sha256']==hashlib.sha256(draft_middle_text.encode()).hexdigest() and draft_middle['part_all_lines_read']
assert draft_middle['new_continuous_lines_reviewed']==530 and draft_middle['cumulative_continuous_prefix_lines']==[1,1030]
assert len(draft_middle['major_section_mapping'])==24
draft_middle_covered=[]
for row in draft_middle['major_section_mapping']:
 a,b=row['lines'];draft_middle_covered.extend(range(a,b+1));assert row['all_lines_read'] and row['decision']
 for dest in row['destinations']:
  name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text())
assert draft_middle_covered==list(range(501,1031))
assert len(draft_middle['focused_issues'])==24 and [row['id'] for row in draft_middle['focused_issues']]==[f'FD{i:02d}' for i in range(21,45)] and len(draft_prefix['focused_issues'])+len(draft_middle['focused_issues'])==draft_middle['cumulative_focused_issues']==44
for row in draft_middle['focused_issues']:
 a,b=row['lines'];assert 501<=a<=b<=1030 and row['decision']
 for dest in row['destinations']:
  name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text())
draft_middle_read_lines=draft_read_lines|set(range(501,1031))
assert len(draft_middle_read_lines)==draft_middle['cumulative_distinct_physical_lines_read']==1088 and len(draft_lines)-len(draft_middle_read_lines)==draft_middle['remaining_not_whole_read_lines']==2634
assert draft_middle['main_text_remaining_continuous_range']==[1031,3700] and draft_middle['new_whole_documents']==0 and draft_middle['additional_registered_whole_documents']==116 and len(additional_procurement)==117 and draft_middle['new_mechanical_parameter_values']==[]
for flag in ['whole_document_read','whole_document_semantic_review_complete','current_engine_changed','all_individual_facts_canon_verified','all_specific_use_profiles_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not draft_middle[flag]
middle_primary=draft_middle['primary_source_rechecks'];assert middle_primary['sha256']==prefix_primary['sha256'] and middle_primary['path_relative_to_plan']==prefix_primary['path_relative_to_plan'] and middle_primary['new_whole_documents']==0
assert [row['topic'] for row in middle_primary['topics']]==['0018','0021','0043','0044','0061','0069','0088']
for row in middle_primary['topics']:
 i=next(i for i,head in enumerate(prefix_primary_heads) if head[1]==row['topic']);body=prefix_primary_text[prefix_primary_heads[i].start():prefix_primary_heads[i+1].start()]
 assert row['text']==body and row['text_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['whole_topic_rechecked'] and not row['new_whole_topic_counted']
middle_primary_by_id={row['topic']:row['text'] for row in middle_primary['topics']}
assert '가장 저렴하면서 가장 뛰어난' in middle_primary_by_id['0021'] and '가장 비싸고 유명한 프로세서' in draft_lines[875]
assert '공군기지만 한 집' in middle_primary_by_id['0061'] and '계; 이동을 위한 연결통로로 쓰긴 무리' in middle_primary_by_id['0061']
assert all(phrase in '\n'.join(draft_lines[668:678]) for phrase in ['A5 멘탈','A4 지능','A2 뉴로','A3 체질'])
middle_wiki=draft_middle['wiki_rechecks'];middle_wiki_path=p/middle_wiki['path_relative_to_plan'];verify_recorded_source_hash(middle_wiki_path,middle_wiki['sha256']);middle_wiki_text=middle_wiki_path.read_text();middle_wiki_heads=list(re.finditer(r'(?m)^--- (.+?) ---',middle_wiki_text))
import urllib.parse
assert [row['decoded_topic'] for row in middle_wiki['topics']]==['집사.txt','수납.txt','심상기록.txt','재생성.txt','마인드_실드.txt'] and not middle_wiki['whole_container_read'] and middle_wiki['new_whole_documents']==0
for row in middle_wiki['topics']:
 i=next(i for i,head in enumerate(middle_wiki_heads) if unicodedata.normalize('NFC',urllib.parse.unquote(head[1]))==row['decoded_topic']);body=middle_wiki_text[middle_wiki_heads[i].start():middle_wiki_heads[i+1].start() if i+1<len(middle_wiki_heads) else len(middle_wiki_text)].strip()
 assert row['text']==body and row['text_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['whole_topic_rechecked'] and not row['new_whole_document_counted']
assert draft_middle['cumulative_continuous_prefix_lines']==[1,1030]
assert draft_middle['cumulative_distinct_physical_lines_read']==1088 and draft_middle['remaining_not_whole_read_lines']==2634 and not draft_middle['whole_document_read']
storage_guide=world.split('### 집사 — 몸과 연결된 창고로 일하기',1)[1].split('### 현물제조사 — 작은 효능으로 생활을 잇는 공방',1)[0]
assert '원본0061' in storage_guide and '물질계의 실제 공간' in storage_guide and '사람이 통행하는 IO' in storage_guide and '집사라는 직업명을 고른 모든 인물의 시작 자산' in storage_guide
assert all(name in storage_guide for name in ['모가','레드','수집가 큐'])
imagery_guide=world.split('### 심상암호와 수신 차단 — 같은 이미지의 다른 쓰임',1)[1].split('<a id="fewk-world-12"></a>',1)[0]
assert all(phrase in imagery_guide for phrase in ['심상암호를 남기기','키를 재생해 사용하기','마인드 실드로 수신을 막기','자기PC의 감정과 관계를 직접 정합니다'])
middle_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_first_draft_middle_regression']
assert (middle_intro['World'],middle_intro['Design'],middle_intro['part_lines_read'],middle_intro['major_parts'],middle_intro['new_focused_issues'],middle_intro['cumulative_focused_issues'])==('v0.96','v1.33',[501,1030],24,24,44)
assert middle_intro['world_sha256']==legacy_coherence['first_draft_market_region_review']['input_world_sha256_before'] and middle_intro['same_scene_actions_and_intro_events'] and middle_intro['same_percentile_engine']
assert not middle_intro['whole_first_draft_read'] and not middle_intro['all_storage_or_imagery_profiles_complete'] and not middle_intro['actual_participant_reading'] and not middle_intro['actual_participant_playtest']
d['current_first_draft_middle_review']={key:value for key,value in middle_intro.items() if key not in ['world_sha256','same_scene_actions_and_intro_events','same_percentile_engine']}
d['current_first_draft_middle_review'].update(additional_registered_whole_documents=116,new_whole_documents=0,uploaded_scope_and_semantic_pending_distinct_contents=4,primary_topics_rechecked=7,wiki_topics_rechecked=5,current_engine_changed=False)
# Market, geography and everyday life draft segment; bounded review is distinct from whole-document closure.
draft_market=legacy_coherence['first_draft_market_region_review'];assert draft_market['source']==draft_source and draft_market['previous_record']=='first_draft_middle_review'
assert draft_market['versions']=={'World':'v0.97','Design':'v1.34','Core':'v0.48','Sheet':'v0.44','Easy':'P v0.31','Intro':'v0.5','Tarot':'v0.3'}
draft_market_text='\n'.join(draft_lines[1030:1791]);assert draft_market['part_lines']==[1031,1791] and draft_market['part_text']==draft_market_text and draft_market['part_text_sha256']==hashlib.sha256(draft_market_text.encode()).hexdigest() and draft_market['part_all_lines_read']
assert draft_market['new_continuous_lines_reviewed']==761 and draft_market['cumulative_continuous_prefix_lines']==[1,1791]
assert len(draft_market['major_section_mapping'])==36
market_coverage=[]
for row in draft_market['major_section_mapping']:
 a,b=row['lines'];market_coverage.extend(range(a,b+1));assert row['all_lines_read'] and row['decision']
 for dest in row['destinations']:
  name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text())
assert market_coverage==list(range(1031,1792))
assert len(draft_market['focused_issues'])==36 and [row['id'] for row in draft_market['focused_issues']]==[f'FD{i:02d}' for i in range(45,81)]
assert draft_middle['cumulative_focused_issues']+len(draft_market['focused_issues'])==draft_market['cumulative_focused_issues']==80
for row in draft_market['focused_issues']:
 a,b=row['lines'];assert 1031<=a<=b<=1791 and row['decision']
 for dest in row['destinations']:
  name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text())
market_read_lines=draft_middle_read_lines|set(range(1031,1792))
assert len(market_read_lines)==draft_market['cumulative_distinct_physical_lines_read']==1837 and len(draft_lines)-len(market_read_lines)==draft_market['remaining_not_whole_read_lines']==1885
assert draft_market['main_text_remaining_continuous_range']==[1792,3700] and draft_market['new_whole_documents']==0 and draft_market['additional_registered_whole_documents']==116 and len(additional_procurement)==117 and draft_market['new_mechanical_parameter_values']==[] and draft_market['pending_bigforest_model_unchanged']
for flag in ['whole_document_read','whole_document_semantic_review_complete','current_engine_changed','all_individual_facts_canon_verified','all_specific_use_profiles_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not draft_market[flag]
market_primary=draft_market['primary_source_rechecks'];assert market_primary['sha256']==prefix_primary['sha256'] and market_primary['path_relative_to_plan']==prefix_primary['path_relative_to_plan'] and market_primary['new_whole_documents']==0
assert [row['topic'] for row in market_primary['topics']]==['0032','0082','0086','0093','0097']
for row in market_primary['topics']:
 i=next(i for i,head in enumerate(prefix_primary_heads) if head[1]==row['topic']);body=prefix_primary_text[prefix_primary_heads[i].start():prefix_primary_heads[i+1].start()]
 assert row['text']==body and row['text_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['whole_topic_rechecked'] and not row['new_whole_topic_counted']
market_wiki=draft_market['wiki_rechecks'];assert market_wiki['sha256']==middle_wiki['sha256'] and market_wiki['path_relative_to_plan']==middle_wiki['path_relative_to_plan']
assert [row['decoded_topic'] for row in market_wiki['topics']]==['루쳄트레일로드역.txt','시장과_거래.txt','유지보수와_개조.txt'] and not market_wiki['whole_container_read'] and market_wiki['new_whole_documents']==0
for row in market_wiki['topics']:
 i=next(i for i,head in enumerate(middle_wiki_heads) if unicodedata.normalize('NFC',urllib.parse.unquote(head[1]))==row['decoded_topic']);body=middle_wiki_text[middle_wiki_heads[i].start():middle_wiki_heads[i+1].start() if i+1<len(middle_wiki_heads) else len(middle_wiki_text)].strip()
 assert row['text']==body and row['text_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['whole_topic_rechecked'] and not row['new_whole_document_counted']
assert draft_market['cumulative_continuous_prefix_lines']==[1,1791]
assert draft_market['cumulative_distinct_physical_lines_read']==1837 and draft_market['remaining_not_whole_read_lines']==1885 and not draft_market['whole_document_read']
market_guide=world.split('### 어느 시장에서 누구에게 부탁할까',1)[1].split('### 만드는 사람의 하루를 가격과 함께 읽기',1)[0]
assert all(phrase in market_guide for phrase in ['대사국·기업 대리점','복사집','야시장','암시장','수집상','조달자','자동으로 곱하거나','가격','사용권','단종 부품을 찾는 오후'])
modification_guide=world.split('### 개조 의뢰 — 바꿀 기능을 먼저 정하기',1)[1].split('### 야간조의 손 — 기술과 생업이 만나는 장면',1)[0]
assert all(phrase in modification_guide for phrase in ['기능병합','경량화','위장','내장','외장','보강','강화','오버','절감','변경 전후 기능','같은 공학'])
assert '지하 개찰구를 거쳐 지상의 장터로 나오는 순서로 읽습니다' in world
market_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_first_draft_market_region_regression']
assert (market_intro['World'],market_intro['Design'],market_intro['part_lines_read'],market_intro['major_parts'],market_intro['new_focused_issues'],market_intro['cumulative_focused_issues'])==('v0.97','v1.34',[1031,1791],36,36,80)
assert market_intro['world_sha256']==legacy_coherence['first_draft_history_dimension_review']['input_world_sha256_before'] and market_intro['same_scene_actions_and_intro_events'] and market_intro['same_percentile_engine']
assert not market_intro['whole_first_draft_read'] and not market_intro['all_market_equipment_region_profiles_complete'] and not market_intro['actual_participant_reading'] and not market_intro['actual_participant_playtest']
d['current_first_draft_market_region_review']={key:value for key,value in market_intro.items() if key not in ['world_sha256','same_scene_actions_and_intro_events','same_percentile_engine']}
d['current_first_draft_market_region_review'].update(additional_registered_whole_documents=116,new_whole_documents=0,uploaded_scope_and_semantic_pending_distinct_contents=4,primary_topics_rechecked=5,wiki_topics_rechecked=3,current_engine_changed=False)
# Exact history/dimension/existence draft coverage and bounded original-topic rechecks.
draft_history=legacy_coherence['first_draft_history_dimension_review'];assert draft_history['source']==draft_source and draft_history['previous_record']=='first_draft_market_region_review'
assert draft_history['versions']=={'World':'v0.98','Design':'v1.35','Core':'v0.48','Sheet':'v0.44','Easy':'P v0.31','Intro':'v0.5','Tarot':'v0.3'}
history_text='\n'.join(draft_lines[1791:2447]);assert draft_history['part_lines']==[1792,2447] and draft_history['part_text']==history_text and draft_history['part_text_sha256']==hashlib.sha256(history_text.encode()).hexdigest() and draft_history['part_all_lines_read']
assert draft_history['new_continuous_lines_reviewed']==656 and draft_history['cumulative_continuous_prefix_lines']==[1,2447] and len(draft_history['major_section_mapping'])==47
history_coverage=[]
for row in draft_history['major_section_mapping']:
 a,b=row['lines'];history_coverage.extend(range(a,b+1));assert row['all_lines_read'] and row['decision']
 for dest in row['destinations']:
  name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text())
assert history_coverage==list(range(1792,2448))
assert len(draft_history['focused_issues'])==47 and [row['id'] for row in draft_history['focused_issues']]==[f'FD{i:03d}' for i in range(81,128)]
assert draft_market['cumulative_focused_issues']+len(draft_history['focused_issues'])==draft_history['cumulative_focused_issues']==127
for row in draft_history['focused_issues']:
 a,b=row['lines'];assert 1792<=a<=b<=2447 and row['decision']
 for dest in row['destinations']:
  name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text())
history_read_lines=market_read_lines|set(range(1792,2448))
assert len(history_read_lines)==draft_history['cumulative_distinct_physical_lines_read']==2472 and len(draft_lines)-len(history_read_lines)==draft_history['remaining_not_whole_read_lines']==1250
assert draft_history['main_text_remaining_continuous_range']==[2448,3700] and draft_history['new_whole_documents']==0 and draft_history['additional_registered_whole_documents']==116 and len(additional_procurement)==117 and draft_history['new_mechanical_parameter_values']==[]
for flag in ['whole_document_read','whole_document_semantic_review_complete','current_engine_changed','all_individual_facts_canon_verified','all_specific_use_profiles_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not draft_history[flag]
history_primary=draft_history['primary_source_rechecks'];assert history_primary['sha256']==prefix_primary['sha256'] and history_primary['path_relative_to_plan']==prefix_primary['path_relative_to_plan'] and history_primary['new_whole_documents']==0
assert [row['topic'] for row in history_primary['topics']]==['0031','0046','0056','0060','0071','0099']
for row in history_primary['topics']:
 i=next(i for i,head in enumerate(prefix_primary_heads) if head[1]==row['topic']);body=prefix_primary_text[prefix_primary_heads[i].start():prefix_primary_heads[i+1].start()]
 assert row['text']==body and row['text_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['whole_topic_rechecked'] and not row['new_whole_topic_counted']
history_wiki=draft_history['wiki_rechecks'];assert history_wiki['sha256']==middle_wiki['sha256'] and history_wiki['path_relative_to_plan']==middle_wiki['path_relative_to_plan']
assert [row['decoded_topic'] for row in history_wiki['topics']]==['광제력.txt','네이티브.txt','에고.txt','연호.txt','코마.txt'] and not history_wiki['whole_container_read'] and history_wiki['new_whole_documents']==0
for row in history_wiki['topics']:
 i=next(i for i,head in enumerate(middle_wiki_heads) if unicodedata.normalize('NFC',urllib.parse.unquote(head[1]))==row['decoded_topic']);body=middle_wiki_text[middle_wiki_heads[i].start():middle_wiki_heads[i+1].start() if i+1<len(middle_wiki_heads) else len(middle_wiki_text)].strip()
 assert row['text']==body and row['text_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['whole_topic_rechecked'] and not row['new_whole_document_counted']
history_wiki_by_id={row['decoded_topic']:row['text'] for row in history_wiki['topics']}
assert '모든 경우에 육체가' in history_wiki_by_id['코마.txt'] and '우리는 모두 [[물질계]]의 [[네이티브]]' in history_wiki_by_id['네이티브.txt']
assert '물질계가 아닌 타 차원계에서 태어난' in draft_lines[2140] and '물질차원계를 포함한 차원계에서 태어난' in draft_lines[2144]
assert [row['dd_first_year'] for row in draft_history['calendar_arithmetic_cases']]==[4227,4230,4274]
for row in draft_history['calendar_arithmetic_cases']:
 assert row['dd_current']==4359 and row['dd_current']-row['dd_first_year']==row['elapsed'] and row['elapsed']+1==row['inclusive_year']
assert [row['inclusive_year'] for row in draft_history['calendar_arithmetic_cases']]==[133,130,86]
assert all(phrase in '\n'.join(draft_lines[1947:1964]) for phrase in ['수평 133년','광제력 130년','디디 4359년','대사력 86년'])
assert draft_upload['current_partial_review']['record']=='first_draft_full_review' and draft_upload['current_partial_review']['prefix_lines_read']==[1,3722]
assert draft_upload['current_partial_review']['cumulative_distinct_physical_lines_read']==3722 and draft_upload['current_partial_review']['remaining_not_whole_read_lines']==0 and draft_upload['current_partial_review']['main_text_whole_read']
calendar_guide=world.split('### 초기1고의 ‘현재’ 표기를 검산하기',1)[1].split('### 확장 연표 안에서도 달라지는 환산',1)[0]
assert all(phrase in calendar_guide for phrase in ['4359−4227+1=133','4359−4230+1=130','4359−4274+1=86','132·129·85년','모든 캠페인의 시작 연도로 고정하지 않습니다'])
coma_guide=world.split('### 연결이 남아 있는 코마 — 구조 의뢰를 읽는 방법',1)[1].split('<a id="fewk-world-10"></a>',1)[0]
assert all(phrase in coma_guide for phrase in ['모든 경우에 물질계 육체도 코마에 빠지는 것은 아니라고','존재 복원 지원','몸의 치료','연결 회수·해제','재진입할 수 없게 되는 차원','모든 에고0에 자동으로 덧붙이지 않습니다','10_CoreRulebook.md#fewk-residence'])
history_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_first_draft_history_dimension_regression']
assert (history_intro['World'],history_intro['Design'],history_intro['part_lines_read'],history_intro['major_parts'],history_intro['new_focused_issues'],history_intro['cumulative_focused_issues'],history_intro['calendar_arithmetic_cases'])==('v0.98','v1.35',[1792,2447],47,47,127,3)
assert history_intro['world_sha256']==legacy_coherence['first_draft_full_review']['input_world_sha256_before'] and history_intro['same_scene_actions_and_intro_events'] and history_intro['same_percentile_engine']
assert not history_intro['whole_first_draft_read'] and not history_intro['all_history_dimension_existence_profiles_complete'] and not history_intro['actual_participant_reading'] and not history_intro['actual_participant_playtest']
d['current_first_draft_history_dimension_review']={key:value for key,value in history_intro.items() if key not in ['world_sha256','same_scene_actions_and_intro_events','same_percentile_engine']}
d['current_first_draft_history_dimension_review'].update(additional_registered_whole_documents=116,new_whole_documents=0,uploaded_scope_and_semantic_pending_distinct_contents=4,primary_topics_rechecked=6,wiki_topics_rechecked=5,current_engine_changed=False)
# Actual first-draft closure: final source segment plus all prior contiguous passes and editorial tail.
draft_full=legacy_coherence['first_draft_full_review'];assert draft_full['source']==draft_source and draft_full['previous_record']=='first_draft_history_dimension_review'
assert draft_full['versions']=={'World':'v0.99','Design':'v1.36','Core':'v0.48','Sheet':'v0.44','Easy':'P v0.31','Intro':'v0.5','Tarot':'v0.3'}
assert draft_full['prior_pass_records']==['first_draft_editorial_comment_review','first_draft_prefix_review','first_draft_middle_review','first_draft_market_region_review','first_draft_history_dimension_review']
final_text='\n'.join(draft_lines[2447:3700]);assert draft_full['part_lines']==[2448,3700] and draft_full['part_text']==final_text and draft_full['part_text_sha256']==hashlib.sha256(final_text.encode()).hexdigest() and draft_full['part_all_lines_read']
assert draft_full['new_continuous_lines_reviewed']==1253 and draft_full['new_distinct_physical_lines_reviewed']==1250 and draft_full['cumulative_continuous_prefix_lines']==[1,3722]
final_coverage=[]
for row in draft_full['major_section_mapping']:
 a,b=row['lines'];final_coverage.extend(range(a,b+1));assert row['all_lines_read'] and row['decision']
 for dest in row['destinations']:
  name,anchor=dest.split('#');assert anchor in re.findall(r'<a id="([^"]+)"',(o/name).read_text())
assert final_coverage==list(range(2448,3701)) and len(draft_full['major_section_mapping'])==69
assert len(draft_full['focused_issues'])==69 and [row['id'] for row in draft_full['focused_issues']]==[f'FD{i:03d}' for i in range(128,197)]
assert draft_history['cumulative_focused_issues']+len(draft_full['focused_issues'])==draft_full['cumulative_focused_issues']==196
for source_row,issue in zip(draft_full['major_section_mapping'],draft_full['focused_issues']):
 assert all(source_row[key]==issue[key] for key in ['lines','topic','decision','destinations'])
final_read_lines=history_read_lines|set(range(2448,3701));assert final_read_lines==set(range(1,3723)) and len(final_read_lines)==draft_full['cumulative_distinct_physical_lines_read']==3722 and draft_full['remaining_not_whole_read_lines']==0
assert draft_full['main_text_remaining_continuous_range']==[] and draft_full['whole_document_read'] and draft_full['whole_document_semantic_review_complete'] and draft_full['new_whole_documents']==1 and draft_full['additional_registered_whole_documents']==len(additional_procurement)==117
assert draft_full['new_mechanical_parameter_values']==[] and draft_full['pending_bigforest_model_unchanged'] and draft_full['pending_crocodile_forms_unchanged']
for flag in ['current_engine_changed','all_individual_facts_canon_verified','all_specific_use_profiles_complete','all_uploaded_unique_contents_semantically_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not draft_full[flag]
final_primary=draft_full['primary_source_rechecks'];assert final_primary['sha256']==prefix_primary['sha256'] and final_primary['path_relative_to_plan']==prefix_primary['path_relative_to_plan'] and final_primary['new_whole_documents']==0
assert [row['topic'] for row in final_primary['topics']]==['0006','0019','0021','0042']
for row in final_primary['topics']:
 i=next(i for i,head in enumerate(prefix_primary_heads) if head[1]==row['topic']);body=prefix_primary_text[prefix_primary_heads[i].start():prefix_primary_heads[i+1].start()]
 assert row['text']==body and row['text_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['whole_topic_rechecked'] and not row['new_whole_topic_counted']
# Verify numerical inconsistencies as inconsistencies, never as inherited engine parameters.
assert [(row['expression'],row['computed'],row['source_claimed'],row['source_values_consistent']) for row in draft_full['arithmetic_cases']]==[('60000*30',1800000,900000,False),('20*30',600,600,True),('40-3-1',36,34,False)]
assert 60000*30==1800000!=900000 and 20*30==600 and 40-3-1==36!=34
assert all(s in draft_lines[2512] for s in ['6만자','30배','90만자','20자','6백자']) and '34개가 이득' in draft_lines[3231]
dup=draft_full['duplicate_passage'];assert dup['first_lines']==[2929,2934] and dup['second_lines']==[3674,3679] and draft_lines[2928:2934]==draft_lines[3673:3679]
assert dup['text_sha256']==hashlib.sha256('\n'.join(draft_lines[2928:2934]).encode()).hexdigest() and dup['exact_same_six_lines'] and dup['new_unique_story_count']==1
assert draft_full['min_continuation_source_lines']==[3052,3056] and '그 가족은 모두 생존했다' in draft_lines[3054] and '사형집행인' in draft_lines[3055]
assert '확실하진 않지만' in draft_lines[2657] and '것 같습니다' in draft_lines[2660]
assert draft_upload['review_evidence']=='first_draft_full_review' and draft_upload['current_partial_review']['prior_records']==draft_full['prior_pass_records']
assert any(row['id']=='LEG-UPLOAD-05' and row['sha256']==draft_source['sha256'] and row['source_relative_to_plan']==draft_source['path_relative_to_plan'] and row['whole_document_read'] for row in additional_procurement)
min_guide=world.split('### 민의 가족 — 능력이 생긴 뒤의 생활',1)[1].split('### 한칸의 기록',1)[0]
assert all(s in min_guide for s in ['초기1고의 민 항목에도 가족이 모두 생존','확장 소설에만 새로 생긴 결말이 아닙니다','원본0006은 샤이닝이라는 말을 떠올리는 곳에서 끝나므로'])
byte_guide=world.split('### 초안의 이동료를 계산할 때',1)[1].split('### 기록의 단위와 살아 있는 주체',1)[0]
assert all(s in byte_guide for s in ['6만×30=180만','20자×30=600자','혼백 표준21자','실제 이동료는 해당 IO와 계약'])
assert '청취·감정 축적은 아직 그 원인을 설명하는 가설입니다' in world and '누가 지시를 넣었는지' in world
final_intro=json.loads((v/'입문시나리오_검토.json').read_text())['world_first_draft_full_regression']
assert (final_intro['World'],final_intro['Design'],final_intro['part_lines_read'],final_intro['major_parts'],final_intro['new_focused_issues'],final_intro['cumulative_focused_issues'])==('v0.99','v1.36',[2448,3700],69,69,196)
assert final_intro['world_sha256']==legacy_coherence['product_content_pass']['input_book_hashes']['11_WorldLorebook.md'] and final_intro['same_scene_actions_and_intro_events'] and final_intro['same_percentile_engine'] and final_intro['whole_first_draft_read'] and final_intro['whole_first_draft_bounded_semantic_review_complete']
for flag in ['all_individual_facts_canon_verified','all_specific_use_profiles_complete','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not final_intro[flag]
d['current_first_draft_full_review']={key:value for key,value in final_intro.items() if key not in ['world_sha256','same_scene_actions_and_intro_events','same_percentile_engine']}
d['current_first_draft_full_review'].update(additional_registered_whole_documents=117,new_whole_documents=1,uploaded_scope_and_semantic_pending_distinct_contents=3,primary_topics_rechecked=4,arithmetic_cases_checked=3,duplicate_passages_compared=1,current_engine_changed=False)
d['current_reference_hash_revalidation']={'id':current_reference_audit['id'],'record':'현재_참고원고_해시검증.json','reference_hashes_verified':358,'Core':129,'World':229,'changed_from_baseline':0,'unread':0,'full_current_worktree_revalidation_complete':True,'all_older_unique_sources_reviewed':False,'content_semantic_review_inferred':False,'actual_participant_evidence':False}
d['named_anchor_links_checked']=len(named_anchor_links);d['missing_named_anchors']=missing_named_anchors
q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
for name,sha in d['updated_document_hashes'].items():verify_recorded_source_hash((p/name),sha)
g=json.loads((v/'완료_관문.json').read_text())
assert g['current_completion_scope']['id']=='FEWK-20261007-MANUSCRIPT-SCOPE'
assert len(g['current_completion_scope']['deferred_not_completion_prerequisites'])==2
if g['goal_status']=='complete':
 assert all(x['passed'] and not x['remaining'] for x in g['gates'])
 assert not g['current_completion_scope']['remaining_actions']
else:
 assert g['goal_status']=='active' and all(not x['passed'] for x in g['gates'])
assert g['current_worktree_hash_revalidation_pending_ids']==[] and g['current_evidence_summary']['current_original_full_hash_revalidation_complete']
assert g['current_evidence_summary']['current_reference_hashes_verified']==358 and g['current_evidence_summary']['current_versions']['Design']=='1.38'
evidence=g['current_evidence_summary']
basic_summary=evidence['uploaded_core_basic_and_editorial_review']
assert basic_summary==d['current_uploaded_core_basic_and_editorial_review']
assert evidence['first_draft_prefix_review']==d['current_first_draft_prefix_review']
assert evidence['first_draft_middle_review']==d['current_first_draft_middle_review']
assert evidence['first_draft_market_region_review']==d['current_first_draft_market_region_review']
assert evidence['first_draft_history_dimension_review']==d['current_first_draft_history_dimension_review']
assert evidence['first_draft_full_review']==d['current_first_draft_full_review']
trial_summary=evidence['reader_start_and_human_trial_preparation']
assert trial_summary['versions']==trial_prep['versions'] and evidence['current_versions']['Easy']=='P0.31'
assert trial_summary['independent_reading_tasks']==['R1','R2','R3','R4','R5'] and trial_summary['human_trial_modes']==['R','P','A','T']
assert trial_summary['participant_evidence_received']==[] and not any(trial_summary[flag] for flag in ['actual_participant_reading','actual_participant_playtest','actual_async_community_test'])
keyword_summary=evidence['uploaded_keyword_table_review']
assert (keyword_summary['World'],keyword_summary['Design'],keyword_summary['logical_data_rows'],keyword_summary['reviewed_prefix_data_rows'],keyword_summary['remaining_data_rows'],keyword_summary['focused_issues'],keyword_summary['primary_topics_rechecked'],keyword_summary['reader_distinctions'])==('v0.91','v1.28',984,250,734,18,8,8)
assert not keyword_summary['whole_document_reviewed'] and not keyword_summary['current_engine_changed'] and not keyword_summary['actual_participant_playtest']
middle_summary=evidence['uploaded_keyword_table_middle_review']
assert (middle_summary['World'],middle_summary['Design'],middle_summary['logical_data_rows'],middle_summary['cumulative_reviewed_prefix_data_rows'],middle_summary['remaining_data_rows'],middle_summary['new_focused_issues'],middle_summary['cumulative_focused_issues'],middle_summary['reader_distinctions'])==('v0.92','v1.29',984,500,484,18,36,16)
assert middle_summary['data_row_range']==[251,500] and not middle_summary['whole_document_reviewed'] and not middle_summary['current_engine_changed'] and not middle_summary['actual_participant_playtest']
full_summary=evidence['uploaded_keyword_table_full_review']
assert (full_summary['World'],full_summary['Design'],full_summary['logical_data_rows'],full_summary['cumulative_reviewed_data_rows'],full_summary['remaining_data_rows'],full_summary['new_focused_issues'],full_summary['cumulative_focused_issues'],full_summary['reader_distinctions'])==('v0.93','v1.30',984,984,0,24,60,24)
assert full_summary['data_row_range']==[501,984] and full_summary['whole_document_reviewed'] and full_summary['additional_registered_whole_documents']==115 and full_summary['uploaded_scope_and_semantic_pending_distinct_contents']==5
assert not full_summary['current_engine_changed'] and not full_summary['all_individual_facts_canon_verified'] and not full_summary['actual_participant_playtest']
upload_summary=evidence['uploaded_author_note_and_outline_review']
assert (upload_summary['World'],upload_summary['Design'],upload_summary['uploaded_file_occurrences'],upload_summary['uploaded_distinct_contents'],upload_summary['new_whole_documents'],upload_summary['issues'],upload_summary['outline_top_sections'],upload_summary['uploaded_scope_and_semantic_pending_distinct_contents'],upload_summary['additional_registered_whole_documents'])==('v0.90','v1.27',14,12,2,10,11,6,114)
assert not upload_summary['current_engine_changed'] and not upload_summary['all_uploaded_unique_contents_semantically_reviewed'] and not upload_summary['actual_participant_playtest']
external_summary=evidence['external_public_handout_review']
assert external_summary['Design']=='1.25' and external_summary['findings']==7
assert (external_summary['Sprawl_public_French_moves_pages_read'],external_summary['Sprawl_public_French_MC_pages_read'],external_summary['Paradise_Fleet_preview_pages_read'])==(4,6,0)
assert not external_summary['current_engine_changed'] and not external_summary['all_requested_external_systems_fully_reviewed'] and not external_summary['actual_participant_playtest']
assert evidence['current_numbered_related_novel_corpus_review']['current_numbered_novels']==evidence['current_numbered_related_novel_corpus_review']['historical_whole_read_evidence_count']==evidence['current_numbered_related_novel_corpus_review']['current_novel_hashes_checked']==18 and not evidence['current_numbered_related_novel_corpus_review']['all_current_numbered_novel_settings_verified']
assert evidence['debt_story_related_novel_review']['issues_reviewed']==10 and evidence['debt_story_related_novel_review']['limited_arithmetic_examples_checked']==5 and not evidence['debt_story_related_novel_review']['original_novel_rewritten']
assert evidence['interaction_body_compatibility_review']['checks_passed']==94 and evidence['interaction_body_compatibility_review']['body_compatibility_condition_cases']==672 and evidence['interaction_body_compatibility_review']['one_person_twelve_skills_total']==440 and not evidence['interaction_body_compatibility_review']['all_formation_results_or_implants_covered']
assert evidence['compatible_io_two_realm_review']['checks_passed']==121 and evidence['compatible_io_two_realm_review']['actual_destination_condition_cases']==2880 and evidence['compatible_io_two_realm_review']['two_realm_preservation_sequences']==169 and not evidence['compatible_io_two_realm_review']['all_io_lineages_verified']
assert evidence['reader_navigation_status_review']['direct_sheet_section_anchors']==32 and not evidence['reader_navigation_status_review']['all_book_editorial_review_complete']
assert evidence['current_versions']['Intro']=='0.5' and evidence['intro_identity_evidence_review']['handouts_written']==4 and evidence['intro_identity_evidence_review']['issues_reviewed']==15
assert not evidence['intro_identity_evidence_review']['identity_canon_answer_fixed'] and not evidence['intro_identity_evidence_review']['actual_participant_playtest']
assert (evidence['current_versions']['Core'],evidence['current_versions']['Sheet'],evidence['current_versions']['Design'])==('0.49','0.44','1.38')
assert evidence['coffin_receiver_support_review']['actual_receiver_and_operator_state_required'] and not evidence['coffin_receiver_support_review']['all_coffin_and_immigration_profiles_complete']
assert evidence['current_versions']['World']=='1.00' and evidence['ghost_cafe_related_novel_review']['new_whole_related_novels_read']==1
assert not evidence['ghost_cafe_related_novel_review']['all_related_novels_reviewed']
assert evidence['current_versions']['World']=='1.00' and evidence['noene_family_related_novels_review']['new_whole_related_novels_read']==2
assert not evidence['noene_family_related_novels_review']['all_related_novels_reviewed']
assert evidence['current_versions']['World']=='1.00' and evidence['mobius_night_shift_related_novel_review']['new_whole_novels_read']==1
assert not evidence['mobius_night_shift_related_novel_review']['all_related_novels_reviewed']
assert (evidence['bounded_older_inventory_cumulative_whole_reviews'],evidence['bounded_older_inventory_cumulative_semantic_pending'])==(90,0)
assert (evidence['world_physics_documents_whole_reviewed'],evidence['world_physics_documents_pending'])==(16,0)
assert (evidence['cyberpunk_pack_documents_whole_reviewed'],evidence['cyberpunk_pack_documents_pending'],evidence['cyberpunk_pack_spec_catalog_entries_mapped'])==(21,0,39)
assert evidence['registered_cyberpunk_pack_whole_review_complete']
assert evidence['cyberpunk_pack_detailed_catalog_entries_whole_read']==39
assert (evidence['cyberpunk_pack_tags_whole_read_and_mapped'],evidence['cyberpunk_pack_presets_whole_read_and_mapped'])==(30,9)
assert evidence['cyberpunk_pack_dsr_dropout_major_sections_mapped']==22
assert evidence['cyberpunk_pack_weapon_main_table_rows_mapped']==100
assert evidence['cyberpunk_pack_NPC_blocks_mapped']==17
assert evidence['cyberpunk_pack_large_entity_blocks_mapped']==11
assert evidence['cyberpunk_pack_glossary_heading_entries_mapped']==259
assert evidence['cyberpunk_pack_deck_audit_major_sections_mapped']==27
assert (evidence['current_framework_foundation_documents_whole_reviewed'],evidence['current_framework_cumulative_documents_whole_reviewed'],evidence['current_framework_documents_pending'],evidence['current_framework_foundation_major_sections_mapped'])==(4,21,0,40)
assert evidence['framework_foundation_reader_review']['same_facts_same_resolution_clarified'] and not evidence['framework_foundation_reader_review']['actual_participant_playtest']
assert (evidence['framework_character_combat_reader_review']['whole_documents'],evidence['framework_character_combat_reader_review']['major_sections_mapped'],evidence['framework_character_combat_reader_review']['limited_legacy_arithmetic_checks'])==(3,47,23)
assert evidence['framework_character_combat_reader_review']['same_actual_distance_and_time_across_maps']
assert (evidence['framework_resource_growth_reader_review']['whole_documents'],evidence['framework_resource_growth_reader_review']['major_sections_mapped'],evidence['framework_resource_growth_reader_review']['limited_legacy_arithmetic_checks'])==(3,43,22)
assert evidence['framework_resource_growth_reader_review']['independent_skill_function_gear_relation_and_residence_changes'] and not evidence['framework_resource_growth_reader_review']['all_legacy_logs_are_complete_histories']
assert (evidence['framework_team_NPC_session_reader_review']['whole_documents'],evidence['framework_team_NPC_session_reader_review']['major_sections_mapped'],evidence['framework_team_NPC_session_reader_review']['limited_legacy_arithmetic_checks'])==(3,40,23)
assert evidence['framework_team_NPC_session_reader_review']['request_agreement_and_execution_separated'] and not evidence['framework_team_NPC_session_reader_review']['all_legacy_logs_are_complete_histories']
assert (evidence['framework_final_reader_review']['whole_documents'],evidence['framework_final_reader_review']['major_sections_mapped'],evidence['framework_final_reader_review']['limited_legacy_arithmetic_checks'],evidence['framework_final_reader_review']['tool_documentation_pages_verified'])==(5,63,21,2)
assert evidence['framework_final_reader_review']['framework_registered_family_complete'] and evidence['framework_final_reader_review']['same_engine_and_state_across_dimension_rulesheets'] and evidence['framework_final_reader_review']['success_level_terms_unified'] and not evidence['framework_final_reader_review']['live_application_execution_verified']
assert (evidence['first_relationship_chronology_reader_review']['whole_documents'],evidence['first_relationship_chronology_reader_review']['major_sections_mapped'],evidence['first_relationship_chronology_reader_review']['limited_legacy_arithmetic_checks'],evidence['first_relationship_chronology_reader_review']['primary_topics_whole_rechecked'],evidence['first_relationship_chronology_reader_review']['wiki_topics_whole_rechecked'])==(4,25,14,10,3)
assert evidence['first_relationship_chronology_reader_review']['relationships_names_and_observed_times_separated'] and evidence['first_relationship_chronology_reader_review']['current_plan_header_refreshed'] and not evidence['first_relationship_chronology_reader_review']['all_first_chronology_dates_canon_verified']
assert (evidence['first_catalog_reader_review']['whole_documents'],evidence['first_catalog_reader_review']['major_sections_mapped'],evidence['first_catalog_reader_review']['limited_legacy_arithmetic_checks'],evidence['first_catalog_reader_review']['primary_topics_whole_rechecked'],evidence['first_catalog_reader_review']['first_family_cumulative_whole_reviews'],evidence['first_catalog_reader_review']['first_family_pending'])==(4,43,10,7,15,17)
assert evidence['first_catalog_reader_review']['names_people_objects_affiliation_separated'] and evidence['first_catalog_reader_review']['catalog_occurrences_are_not_unique_entities'] and not evidence['first_catalog_reader_review']['all_catalog_entries_individually_canon_verified']
assert (evidence['first_life_uncertainty_reader_review']['whole_documents'],evidence['first_life_uncertainty_reader_review']['major_sections_mapped'],evidence['first_life_uncertainty_reader_review']['limited_legacy_arithmetic_checks'],evidence['first_life_uncertainty_reader_review']['primary_topics_whole_rechecked'],evidence['first_life_uncertainty_reader_review']['related_novels_whole_rechecked'],evidence['first_life_uncertainty_reader_review']['new_related_novels_whole_read'],evidence['first_life_uncertainty_reader_review']['first_family_cumulative_whole_reviews'],evidence['first_life_uncertainty_reader_review']['first_family_pending'])==(4,46,11,12,1,0,19,13)
assert evidence['first_life_uncertainty_reader_review']['shared_life_contracts_and_unrevealed_names_separated'] and evidence['first_life_uncertainty_reader_review']['new_cafe_guitar_scene_is_campaign_proposal'] and not evidence['first_life_uncertainty_reader_review']['all_institutions_and_laws_canon_verified']
reader_ev=evidence['first_encyclopedia_scene_glossary_review'];assert (reader_ev['whole_documents'],reader_ev['major_sections_mapped'],reader_ev['limited_legacy_arithmetic_checks'],reader_ev['primary_topics_whole_rechecked'],reader_ev['related_novels_whole_read_in_pass'])==(3,43,11,7,1)
voice_ev=evidence['first_address_nuance_motif_review'];assert (voice_ev['whole_documents'],voice_ev['major_sections_mapped'],voice_ev['limited_legacy_arithmetic_checks'],voice_ev['primary_topics_whole_rechecked'],voice_ev['related_novels_whole_rechecked'],voice_ev['new_related_novels_whole_read'])==(3,93,6,5,1,0)
narrator_ev=evidence['first_letters_narrator_translation_readme_review'];assert (narrator_ev['whole_documents'],narrator_ev['major_sections_mapped'],narrator_ev['limited_legacy_arithmetic_checks'],narrator_ev['primary_topics_whole_rechecked'],narrator_ev['related_novels_whole_read_in_pass'],narrator_ev['new_related_novels_whole_read'],narrator_ev['previously_reviewed_related_novels_rechecked'],narrator_ev['current_wiki_documents_whole_rechecked'])==(4,127,8,6,2,1,1,2)
assert (evidence['cyberpunk_pack_world_correction_major_sections_mapped'],evidence['cyberpunk_pack_correction_detailed_issue_blocks_mapped'],evidence['cyberpunk_pack_correction_label_rows_mapped'])==(27,39,17)
assert evidence['registered_cyberpunk_pack_whole_review_complete'] and evidence['world_correction_reader_review']['limited_legacy_arithmetic_checks']==16
assert evidence['deck_audit_reader_review']['limited_legacy_arithmetic_checks']==12
assert evidence['reader_topic_route_verification']['checks_passed']==72 and not evidence['reader_topic_route_verification']['all_appendix_link_meanings_verified']
assert evidence['glossary_reader_review']['limited_legacy_arithmetic_checks']==14 and not evidence['glossary_reader_review']['actual_participant_playtest']
assert (evidence['large_facility_verification']['checks_passed'],evidence['large_facility_verification']['command_boundary_cases'],evidence['large_facility_verification']['common_attack_boundary_cases'],evidence['large_facility_verification']['percentile_cases'])==(38,12288,6912,900)
assert not evidence['large_facility_verification']['actual_participant_playtest']
assert (evidence['named_NPC_verification']['checks_passed'],evidence['named_NPC_verification']['new_checks'],evidence['named_NPC_verification']['sender_cases'],evidence['named_NPC_verification']['percentile_rolls'])==(83,30,192,700)
assert not evidence['named_NPC_verification']['actual_participant_playtest']
assert evidence['dropout_operation_verification']['checks_passed']==78 and evidence['dropout_operation_verification']['new_local_boundary_checks']==11
assert not evidence['dropout_operation_verification']['actual_participant_playtest']

profile_review=legacy_coherence['first_protagonist_supernatural_profiles_review']
assert (profile_review['whole_documents_read'],len(profile_review['major_section_mapping']),profile_review['major_sections_by_file'])==(3,103,[53,37,13])
assert (profile_review['first_family_cumulative_whole_reviews'],profile_review['first_family_pending'],profile_review['bounded_cumulative_whole_reviews'],profile_review['bounded_cumulative_pending'])==(32,0,90,0)
assert profile_review['versions']=={'Core':'v0.40','World':'v0.69','Sheet':'v0.35','Easy':'P v0.30','Design':'v1.00','Tarot':'v0.3'} and profile_review['new_mechanical_parameter_values']==[]
for flag in ['all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','old_stats_automatically_converted','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not profile_review[flag]
profile_shapes={'07_단편주인공_001-050_간략시트.md':(11145,6143,486,53),'08_단편주인공_051-100_간략시트.md':(9366,5078,373,37),'09_초자연존재_도감.md':(9425,5166,325,13)}
assert {x['name'] for x in profile_review['snapshots']}==set(profile_shapes)
for profile_source in profile_review['snapshots']:
 byte_count,char_count,line_count,section_count=profile_shapes[profile_source['name']];data=profile_source['text'].encode()
 assert profile_source['whole_document_read'] and (len(data),len(profile_source['text']),len(profile_source['text'].splitlines()))==(byte_count,char_count,line_count)
 assert (profile_source['bytes'],profile_source['chars'],profile_source['lines'])==(byte_count,char_count,line_count) and len(profile_source['migration_decisions'])==section_count
 assert hashlib.sha256(data).hexdigest()==profile_source['sha256'];verify_recorded_source_hash(p/profile_source['path_relative_to_plan'],profile_source['sha256'])
 assert any(x['name']==profile_source['name'] and x['sha256']==profile_source['sha256'] and x['whole_document_read'] for x in additional_procurement)
 profile_rows=[x for x in profile_review['major_section_mapping'] if x['source_name']==profile_source['name']];profile_heads=list(re.finditer(r'^## [^\n]+',profile_source['text'],re.M));assert len(profile_rows)==len(profile_heads)==section_count
 for i,(head,entry) in enumerate(zip(profile_heads,profile_rows)):
  end=profile_heads[i+1].start() if i+1<len(profile_heads) else len(profile_source['text'])
  assert entry['title']==head[0][3:] and entry['text']==profile_source['text'][head.start():end] and entry['decision']==profile_source['migration_decisions'][i]
  assert hashlib.sha256(entry['text'].encode()).hexdigest()==entry['sha256'] and entry['start_line']==profile_source['text'][:head.start()].count('\n')+1 and entry['decision']
profile_primary=profile_review['primary_topic_recheck'];verify_recorded_source_hash(p/profile_primary['source_path_relative_to_plan'],profile_primary['sha256']);profile_raw=(p/profile_primary['source_path_relative_to_plan']).read_text();profile_raw_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',profile_raw))
assert not profile_primary['whole_container_read'] and profile_review['primary_topics_whole_rechecked']==len(profile_primary['topics'])==8
assert [x['topic'] for x in profile_primary['topics']]==['0005','0012','0019','0021','0034','0040','0072','0080']
for entry in profile_primary['topics']:
 head=next(x for x in profile_raw_heads if x[1]==entry['topic']);i=profile_raw_heads.index(head);text=profile_raw[head.start():profile_raw_heads[i+1].start()].strip()
 assert entry['whole_topic_read'] and entry['text']==text and len(text)==entry['chars'] and hashlib.sha256(text.encode()).hexdigest()==entry['sha256']
assert profile_review['new_related_novels_whole_read']==0 and profile_review['existing_related_novel_sources_rehashed']==len(profile_review['previously_reviewed_related_novel_references'])==2
for entry in profile_review['previously_reviewed_related_novel_references']:
 verify_recorded_source_hash(p/entry['path_relative_to_plan'],entry['sha256']);assert entry['current_source_file_rehashed'] and entry['new_whole_read_count']==0
 old=legacy_coherence['first_letters_narrator_translation_readme_review']['related_novel_reviews'][0] if entry['novel']=='024' else legacy_coherence['first_encyclopedia_scene_glossary_review']['related_novel_review']
 assert old['whole_document_read'] and old['sha256']==entry['sha256'] and old['path_relative_to_plan']==entry['path_relative_to_plan']
profile_ev=evidence['first_protagonist_supernatural_profiles_review'];assert (profile_ev['whole_documents'],profile_ev['major_sections_mapped'],profile_ev['primary_topics_whole_rechecked'],profile_ev['existing_related_novel_sources_rehashed'],profile_ev['new_related_novels_whole_read'],profile_ev['first_family_cumulative_whole_reviews'],profile_ev['first_family_pending'])==(3,103,8,2,0,32,0)
d['current_first_protagonist_supernatural_profiles_review']={'Core':'v0.40','World':'v0.69','Design':'v1.00','whole_documents_reviewed':3,'major_sections_mapped':103,'primary_topics_whole_rechecked':8,'existing_related_novel_sources_rehashed':2,'new_related_novels_whole_read':0,'bounded_cumulative_whole_reviews':90,'bounded_cumulative_pending':0,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
ship_handover=legacy_coherence['vessel_technical_handover_review']
assert ship_handover['versions']=={'Core':'v0.41','World':'v0.70','Sheet':'v0.36','Easy':'P v0.30','Design':'v1.01','Tarot':'v0.3'}
assert ship_handover['existing_two_models_extended'] and ship_handover['new_universal_stats']==[]
for flag in ['percentile_engine_changed','original_ship_statistics_invented_as_canon','all_specific_use_profiles_complete','all_older_unique_sources_reviewed','all_related_novels_reviewed','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not ship_handover[flag]
ship_primary=ship_handover['primary_topic_recheck'];verify_recorded_source_hash(p/ship_primary['source_path_relative_to_plan'],ship_primary['sha256']);ship_raw=(p/ship_primary['source_path_relative_to_plan']).read_text();ship_raw_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',ship_raw))
assert not ship_primary['whole_container_read'] and ship_handover['primary_topics_whole_rechecked']==len(ship_primary['topics'])==4
assert [x['topic'] for x in ship_primary['topics']]==['0052','0061','0067','0088']
for entry in ship_primary['topics']:
 head=next(x for x in ship_raw_heads if x[1]==entry['topic']);i=ship_raw_heads.index(head);text=ship_raw[head.start():ship_raw_heads[i+1].start()].strip()
 assert entry['whole_topic_read'] and entry['text']==text and len(text)==entry['chars'] and hashlib.sha256(text.encode()).hexdigest()==entry['sha256']
assert (road['vessel_handover_checks_passed'],road['vessel_handover_infeasible_cases'])==(27,9) and not road['vessel_handover_actual_participant_playtest']
assert road['vessel_handover_example']=={'work_seconds':300,'handover_seconds':5,'first_skill':70,'current_skill':30,'roll':40,'repair_HP_gain':0}
ship_ev=evidence['vessel_technical_handover_review'];assert ship_ev['primary_topics_whole_rechecked']==4 and ship_ev['existing_two_models_extended'] and ship_ev['new_universal_stats']==[] and ship_ev['handover_checks_passed']==27 and not ship_ev['actual_participant_playtest']
d['current_vessel_technical_handover']={'Core':'v0.41','World':'v0.70','Sheet':'v0.36','Design':'v1.01','primary_topics_whole_rechecked':4,'handover_checks_passed':27,'infeasible_handover_cases':9,'actual_participant_playtest':False,'all_ships_aircraft_and_vehicle_IO_complete':False}
settings_inventory=legacy_coherence['foundational_settings_root_inventory']
assert (settings_inventory['root_files_inventoried'],settings_inventory['FEWK_source_scope_candidates'],settings_inventory['other_project_scope_candidates'],settings_inventory['whole_documents_reviewed_this_pass'],settings_inventory['semantic_pending_in_eight_source_candidates'])==(11,8,3,0,0)
assert settings_inventory['cumulative_whole_documents_reviewed']==8 and settings_inventory['initial_semantic_pending_in_eight_source_candidates']==8
assert not settings_inventory['all_older_unique_sources_reviewed'] and not settings_inventory['all_setting_sources_inventoried'] and not settings_inventory['old_World_Bible_Ver5_is_current_fifth_edition']
settings_rows=settings_inventory['files'];assert len(settings_rows)==11 and sum(x['FEWK_source_scope_candidate'] for x in settings_rows)==8
settings_root=(p/settings_rows[0]['path_relative_to_plan']).parent
assert {str(x.relative_to(p)) for x in settings_root.iterdir() if x.is_file()}=={x['path_relative_to_plan'] for x in settings_rows}
for entry in settings_rows:
 verify_recorded_source_hash(p/entry['path_relative_to_plan'],entry['sha256']);text=(p/entry['path_relative_to_plan']).read_bytes().decode('utf-8')
 assert entry['opening_preview']==text[:320]
 if entry['whole_document_read']:assert entry['semantic_review_complete'] and entry['review_evidence'] in ['foundational_chronology_csv_review','foundational_world_bible_intentions_review','foundational_world_bible_outline_review','foundational_world_bible_prose_review','foundational_world_bible_laws_review','foundational_world_bible_appendix_review','foundational_core_time_order_csv_review']
 if entry.get('review_evidence')=='foundational_chronology_csv_review':assert entry['name'].endswith('연대표.csv')
 elif not entry['whole_document_read']:assert not entry['semantic_review_complete']
assert sum(x['whole_document_read'] for x in settings_rows)==sum(x['semantic_review_complete'] for x in settings_rows)==8
settings_ev=evidence['foundational_settings_root_inventory'];assert (settings_ev['root_files_inventoried'],settings_ev['FEWK_source_scope_candidates'],settings_ev['whole_documents_reviewed_this_pass'],settings_ev['semantic_pending_in_eight_source_candidates'])==(11,8,0,0)
assert settings_ev['cumulative_whole_documents_reviewed']==8
d['current_foundational_settings_root_inventory']={'root_files_inventoried':11,'FEWK_source_scope_candidates':8,'whole_documents_reviewed_this_pass':0,'cumulative_whole_documents_reviewed':8,'semantic_pending_in_eight_source_candidates':0,'all_older_unique_sources_reviewed':False,'actual_participant_reading':False}
chronology=legacy_coherence['foundational_chronology_csv_review'];chrono_source=chronology['snapshot'];chrono_path=p/chrono_source['path_relative_to_plan']
verify_recorded_source_hash(chrono_path,chrono_source['sha256']);assert chrono_path.read_bytes().decode()==chrono_source['text'] and chrono_source['whole_document_read'] and chrono_source['FEWK_semantic_review_complete']
assert (chronology['whole_documents_read'],chronology['data_rows'],chronology['columns'],chronology['FEWK_nonempty_rows'])==(1,383,21,44)
assert (len(chronology['column_mapping']),len(chronology['FEWK_event_mapping']))==(21,44)
assert all(row['decision'] for row in chronology['column_mapping']+chronology['FEWK_event_mapping'])
assert chronology['versions']['World']=='v0.71' and chronology['versions']['Design']=='v1.02'
assert (chronology['foundational_candidates_cumulative_whole_reviews'],chronology['foundational_candidates_semantic_pending'])==(1,7)
assert any(row['id']=='LEG-FOUND-01' and row['sha256']==chrono_source['sha256'] and row['whole_document_read'] for row in additional_procurement)
for flag in ['global_current_year_or_universal_age_rule_fixed','Chris_funeral_age30_is_necessarily_original20s_contradiction','Chris_counter_after_funeral_proves_original_alive','blank_Juhyeon_proves_age_stopped','real_history_columns_fact_checked','linked_Google_Doc_read','all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not chronology[flag]
chrono_primary=chronology['primary_topic_recheck'];verify_recorded_source_hash(p/chrono_primary['source_path_relative_to_plan'],chrono_primary['sha256']);chrono_raw=(p/chrono_primary['source_path_relative_to_plan']).read_text();chrono_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',chrono_raw))
assert not chrono_primary['whole_container_read'] and [row['topic'] for row in chrono_primary['topics']]==['0022','0032','0046','0054','0092','0099']
for entry in chrono_primary['topics']:
 head=next(x for x in chrono_heads if x[1]==entry['topic']);i=chrono_heads.index(head);text=chrono_raw[head.start():chrono_heads[i+1].start() if i+1<len(chrono_heads) else len(chrono_raw)].strip()
 assert entry['whole_topic_read'] and entry['text']==text and entry['chars']==len(text) and entry['sha256']==hashlib.sha256(text.encode()).hexdigest()
assert chronology['primary_topics_whole_rechecked']==6 and chronology['current_wiki_documents_whole_rechecked']==len(chronology['current_wiki_rechecks'])==5
for entry in chronology['current_wiki_rechecks']:
 verify_recorded_source_hash(p/entry['path_relative_to_plan'],entry['sha256']);assert entry['whole_document_read'] and entry['text']==(p/entry['path_relative_to_plan']).read_bytes().decode() and not entry['compiler_assertion_is_primary_canon']
chrono_ar=legacy['foundational_chronology_csv_arithmetic'];assert (chrono_ar['checks_passed'],chrono_ar['data_rows'],chrono_ar['columns'],chrono_ar['FEWK_nonempty_rows'])==(8,383,21,44)
assert (chrono_ar['Chris_funeral_year_gap'],chrono_ar['Chris_funeral_counter'],chrono_ar['Chris_post_funeral_counter_rows'],chrono_ar['company_first_counter_DD'],chrono_ar['wiki_company_first_year_DD'])==(29,30,6,4255,4254)
chrono_world=(o/'11_WorldLorebook.md').read_text().split('## 42. 달력 —')[1].split('## 43. 시간도보 —')[0]
for phrase in ['**디디(DD)**','**광제력**','**대사력**','### 어느 자료의 ‘현재’인가','### 출생해의1과 실제 나이','수리 작업은300초이고 전체 경과는305초','이름을 이어받은 사람과 원래 연주자']:assert phrase in chrono_world
for phrase in ['| 동단력 |','| 광년력 |','| 황국력 |']:assert phrase not in chrono_world
chrono_ev=evidence['foundational_chronology_csv_review'];assert (chrono_ev['data_rows'],chrono_ev['columns'],chrono_ev['FEWK_nonempty_rows'],chrono_ev['limited_source_arithmetic_checks'])==(383,21,44,8) and not chrono_ev['actual_participant_playtest']
d['current_foundational_chronology_csv_review']={'World':'v0.71','Design':'v1.02','whole_documents_read':1,'FEWK_nonempty_rows_mapped':44,'primary_topics_whole_rechecked':6,'current_wiki_documents_whole_rechecked':5,'limited_source_arithmetic_checks':8,'foundational_candidates_cumulative_whole_reviews':1,'foundational_candidates_semantic_pending':7,'real_history_columns_fact_checked':False,'linked_Google_Doc_read':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
bible_intentions=legacy_coherence['foundational_world_bible_intentions_review']
assert (bible_intentions['whole_documents_read'],bible_intentions['major_sections_by_file'],bible_intentions['chapter_headings_by_file'])==(2,[7,9],[20,28])
assert len(bible_intentions['major_section_mapping'])==16 and len(bible_intentions['chapter_mapping'])==48
assert bible_intentions['versions']['World']=='v0.72' and bible_intentions['versions']['Design']=='v1.03'
assert (bible_intentions['foundational_candidates_cumulative_whole_reviews'],bible_intentions['foundational_candidates_semantic_pending'])==(3,5)
for flag in ['source_complete_book_is_actual_fifth_complete_book','all_six_versioned_plans_whole_reviewed','all_old_proposed_hook_scenes_are_primary_canon','all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','all_art_maps_and_project_archives_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not bible_intentions[flag]
assert bible_intentions['new_mechanical_parameter_values']==[] and bible_intentions['new_related_novels_whole_read']==0
for index,source in enumerate(bible_intentions['snapshots']):
 path=p/source['path_relative_to_plan'];verify_recorded_source_hash(path,source['sha256']);raw=path.read_bytes();text=raw.decode()
 assert source['whole_document_read'] and source['text']==text and (source['bytes'],source['chars'],source['lines'])==(len(raw),len(text),len(text.splitlines()))
 assert any(row['name']==source['name'] and row['sha256']==source['sha256'] and row['whole_document_read'] for row in additional_procurement)
 starts=[0]+[head.start() for head in re.finditer(r'(?m)^(?:제[1-5]부:|서문:|부록(?: A:| B:| \(Appendix\))).*',text)]
 entries=[row for row in bible_intentions['major_section_mapping'] if row['source_name']==source['name']]
 assert len(entries)==bible_intentions['major_sections_by_file'][index]==len(starts)
 for i,(start,row) in enumerate(zip(starts,entries)):
  end=starts[i+1] if i+1<len(starts) else len(text);part=text[start:end]
  assert row['text']==part and row['title']==part.splitlines()[0].lstrip('\ufeff') and row['sha256']==hashlib.sha256(part.encode()).hexdigest()
  assert row['start_line']==text[:start].count('\n')+1 and row['decision']==source['migration_decisions'][i] and row['decision']
 pattern=r'(?m)^\* (?:\* )?\d장:[^\r\n]*' if index==0 else r'(?m)^[ \t]*(?:\*[ \t]*)+\d\.\d\.[^\r\n]*|^\* \(기존 유지\) [AB]\.\d[^\r\n]*'
 headings=list(re.finditer(pattern,text));entries=[row for row in bible_intentions['chapter_mapping'] if row['source_name']==source['name']]
 assert len(entries)==len(headings)==bible_intentions['chapter_headings_by_file'][index]
 for row,h in zip(entries,headings):assert row['title']==h.group(0).strip() and row['start_line']==text[:h.start()].count('\n')+1 and row['current_destination'] and row['scope']
bible_primary=bible_intentions['primary_topic_recheck'];verify_recorded_source_hash(p/bible_primary['source_path_relative_to_plan'],bible_primary['sha256']);bible_raw=(p/bible_primary['source_path_relative_to_plan']).read_text();bible_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',bible_raw))
assert not bible_primary['whole_container_read'] and bible_intentions['primary_topics_whole_rechecked']==4 and [row['topic'] for row in bible_primary['topics']]==['0001','0004','0006','0030']
for row in bible_primary['topics']:
 head=next(x for x in bible_heads if x[1]==row['topic']);i=bible_heads.index(head);text=bible_raw[head.start():bible_heads[i+1].start()].strip()
 assert row['whole_topic_read'] and row['text']==text and row['chars']==len(text) and row['sha256']==hashlib.sha256(text.encode()).hexdigest()
world_intentions=(o/'11_WorldLorebook.md').read_text()
for phrase in ['### 어떤 이야기를 이어가고 싶은가','| 생활과 관계 |','| 정보와 이해관계 |','| 현지의 모험과 전투 |','| 낯선 곳의 개척 |','| 오래 남는 삶 |','생물체가 더미 가치로 화폐 단위에 사용되기도 한다','신규 갈등 소재 — 계산서에 들어간 사람']:assert phrase in world_intentions
assert '인간을 포함한 생물체 역시' in next(row['text'] for row in bible_primary['topics'] if row['topic']=='0004')
bible_ev=evidence['foundational_world_bible_intentions_review'];assert (bible_ev['whole_documents_read'],bible_ev['major_sections_by_file'],bible_ev['chapter_headings_by_file'],bible_ev['primary_topics_whole_rechecked'])==(2,[7,9],[20,28],4) and not bible_ev['all_six_versioned_plans_whole_reviewed'] and not bible_ev['actual_participant_playtest']
d['current_foundational_world_bible_intentions_review']={'World':'v0.72','Design':'v1.03','whole_documents_read':2,'major_sections_mapped':16,'chapter_headings_mapped':48,'primary_topics_whole_rechecked':4,'foundational_candidates_cumulative_whole_reviews':3,'foundational_candidates_semantic_pending':5,'new_mechanical_parameter_values':[],'all_art_maps_and_project_archives_verified':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
bible_outline=legacy_coherence['foundational_world_bible_outline_review'];outline_source=bible_outline['snapshot'];outline_path=p/outline_source['path_relative_to_plan']
verify_recorded_source_hash(outline_path,outline_source['sha256']);outline_raw=outline_path.read_bytes();outline_text=outline_raw.decode();outline_lines=outline_text.splitlines(keepends=True)
assert outline_source['whole_document_read'] and outline_source['text']==outline_text and (outline_source['bytes'],outline_source['chars'],outline_source['lines'])==(54971,30853,588)
assert (bible_outline['whole_documents_read'],bible_outline['major_sections'],bible_outline['numbered_heading_rows'])==(1,18,237)
assert bible_outline['source_outline_versions']==['Ver5.0','Ver3.0'] and not bible_outline['one_file_is_one_final_outline']
assert bible_outline['versions']['World']=='v0.73' and bible_outline['versions']['Design']=='v1.04'
assert (bible_outline['foundational_candidates_cumulative_whole_reviews'],bible_outline['foundational_candidates_semantic_pending'])==(4,4)
assert ''.join(row['text'] for row in bible_outline['major_section_mapping'])==outline_text
entries=bible_outline['major_section_mapping'];assert len(entries)==18
for index,row in enumerate(entries):
 start=row['start_line'];end=entries[index+1]['start_line']-1 if index+1<len(entries) else len(outline_lines);part=''.join(outline_lines[start-1:end])
 assert row['text']==part and row['sha256']==hashlib.sha256(part.encode()).hexdigest() and row['title']==outline_lines[start-1].strip().lstrip('\ufeff') and row['decision']
outline_heading_rx=r'(?m)^[ \t]*(?:\*[ \t]*)+(?P<code>\d+(?:\.\d+)*\.?|[AB]\.\d+(?:\.\d+)*\.?)[ \t]+[^\r\n]*'
outline_headings=list(re.finditer(outline_heading_rx,outline_text));assert len(outline_headings)==237
for row,head in zip(bible_outline['numbered_heading_mapping'],outline_headings):
 assert row['title']==head[0].strip() and row['code']==head['code'] and row['start_line']==outline_text[:head.start()].count('\n')+1 and row['current_destination'] and row['scope']
 assert row['draft_version']==('Ver5.0' if head.start()<outline_text.index('FEWK 월드 바이블: 최종 상세 목차 설계도 (Ver. 3.0)') else 'Ver3.0')
assert len(bible_outline['numbered_heading_mapping'])==237 and any(row['id']=='LEG-FOUND-04' and row['sha256']==outline_source['sha256'] and row['whole_document_read'] for row in additional_procurement)
outline_primary=bible_outline['primary_topic_recheck'];verify_recorded_source_hash(p/outline_primary['source_path_relative_to_plan'],outline_primary['sha256']);primary_text=(p/outline_primary['source_path_relative_to_plan']).read_text();primary_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',primary_text))
assert not outline_primary['whole_container_read'] and bible_outline['primary_topics_whole_rechecked']==8 and [row['topic'] for row in outline_primary['topics']]==['0026','0044','0072','0083','0087','0091','0096','0105']
for row in outline_primary['topics']:
 h=next(x for x in primary_heads if x[1]==row['topic']);i=primary_heads.index(h);part=primary_text[h.start():primary_heads[i+1].start() if i+1<len(primary_heads) else len(primary_text)].strip()
 assert row['whole_topic_read'] and row['text']==part and row['chars']==len(part) and row['sha256']==hashlib.sha256(part.encode()).hexdigest()
for flag in ['source_complete_book_is_actual_fifth_complete_book','outline_lengths_are_actual_written_lengths','all_26_AZi_profiles_or_identity_with_Casey_Milton_verified','all_AI_means_only_cyborg_humans','all_six_versioned_plans_whole_reviewed','all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','all_art_maps_and_project_archives_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not bible_outline[flag]
assert bible_outline['new_mechanical_parameter_values']==[] and bible_outline['new_related_novels_whole_read']==0
outline_ar=legacy['foundational_world_bible_outline_arithmetic'];assert outline_ar['checks_passed']==8 and outline_ar['Ver5_part_sum']==502000 and outline_ar['Ver3_Keiti_allocated_chars']==50000 and outline_ar['Ver3_Keiti_stated_parent_budget']==70000 and outline_ar['Ver3_appendix_AB_budget_sum']==55000 and outline_ar['Ver3_appendix_stated_budget']==75000
assert not outline_ar['outline_lengths_are_actual_written_lengths'] and not outline_ar['all_source_story_ranges_whole_read'] and not outline_ar['all_maps_or_project_archives_delivered'] and not outline_ar['actual_participant_playtest']
outline_world=(o/'11_WorldLorebook.md').read_text();outline_51=outline_world.split('## 51.')[1].split('## 52.')[0]
for phrase in ['### 독백을 듣는 사람들','원본0026','원본0091','원본0096','신규 조사 소재 — 도착한 독백','그 독백 속 발언','이름과 기관의 연결만으로 같은 사람의 연속 전기를 완성하지 않습니다']:assert phrase in outline_51
assert '원본0087에는 인공지능 상담 서비스' in outline_world and '장치·서비스의 인공지능 사례를 지우지 않습니다' in outline_world
outline_ev=evidence['foundational_world_bible_outline_review'];assert (outline_ev['whole_documents_read'],outline_ev['major_sections'],outline_ev['numbered_heading_rows'],outline_ev['primary_topics_whole_rechecked'],outline_ev['limited_outline_budget_arithmetic_checks'])==(1,18,237,8,8) and not outline_ev['actual_participant_playtest']
d['current_foundational_world_bible_outline_review']={'World':'v0.73','Design':'v1.04','whole_documents_read':1,'major_sections_mapped':18,'numbered_heading_rows_mapped':237,'primary_topics_whole_rechecked':8,'outline_budget_arithmetic_checks':8,'foundational_candidates_cumulative_whole_reviews':4,'foundational_candidates_semantic_pending':4,'outline_lengths_are_actual_written_lengths':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
prose_review=legacy_coherence['foundational_world_bible_prose_review'];prose_source=prose_review['snapshot'];prose_path=p/prose_source['path_relative_to_plan']
verify_recorded_source_hash(prose_path,prose_source['sha256']);prose_raw=prose_path.read_bytes();prose_text=prose_raw.decode()
assert prose_source['whole_document_read'] and prose_source['text']==prose_text and (prose_source['bytes'],prose_source['chars'],prose_source['lines'])==(97574,43175,584)
assert (prose_review['whole_documents_read'],prose_review['major_sections'],prose_review['embedded_case_studies'],prose_review['primary_topics_whole_rechecked'])==(1,35,9,13)
assert prose_review['versions']['World']=='v0.74' and prose_review['versions']['Design']=='v1.05'
assert (prose_review['foundational_candidates_cumulative_whole_reviews'],prose_review['foundational_candidates_semantic_pending'])==(5,3)
assert ''.join(x['text'] for x in prose_review['major_section_mapping'])==prose_text
prose_head_rx=r'(?m)^\ufeff?(?:제\d부:|부록:|부록 [BC]:|(?:\d\.[1-4]|[ABC]\.[1-5])\. |FEWK 월드 바이블 전체 원고 분량)[^\r\n]*'
prose_heads=list(re.finditer(prose_head_rx,prose_text));assert len(prose_heads)==len(prose_review['major_section_mapping'])==35
for i,(head,row) in enumerate(zip(prose_heads,prose_review['major_section_mapping'])):
 end=prose_heads[i+1].start() if i+1<len(prose_heads) else len(prose_text);part=prose_text[head.start():end]
 assert row['title']==head[0].lstrip('\ufeff') and row['text']==part and row['start_line']==prose_text[:head.start()].count('\n')+1 and row['sha256']==hashlib.sha256(part.encode()).hexdigest() and row['decision']
case_heads=list(re.finditer(r'(?m)^\[사례 분석 (?P<index>\d+):[^\r\n]*',prose_text));assert len(case_heads)==len(prose_review['case_study_mapping'])==9
for head,row in zip(case_heads,prose_review['case_study_mapping']):
 analysis=prose_text.index('분석:',head.end());end=prose_text.find('\r\n',analysis);end=len(prose_text) if end<0 else end;part=prose_text[head.start():end]
 assert row['index']==int(head['index']) and row['title']==head[0] and row['start_line']==prose_text[:head.start()].count('\n')+1 and row['text']==part and row['sha256']==hashlib.sha256(part.encode()).hexdigest() and row['decision'] and not row['is_separate_whole_novel_read']
assert any(row['id']=='LEG-FOUND-05' and row['sha256']==prose_source['sha256'] and row['whole_document_read'] for row in additional_procurement)
prose_primary=prose_review['primary_topic_recheck'];verify_recorded_source_hash(p/prose_primary['source_path_relative_to_plan'],prose_primary['sha256']);prose_primary_raw=(p/prose_primary['source_path_relative_to_plan']).read_text();prose_primary_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',prose_primary_raw))
assert not prose_primary['whole_container_read'] and [row['topic'] for row in prose_primary['topics']]==['0008','0011','0024','0031','0037','0044','0046','0065','0072','0086','0092','0099','0105']
for row in prose_primary['topics']:
 head=next(x for x in prose_primary_heads if x[1]==row['topic']);i=prose_primary_heads.index(head);part=prose_primary_raw[head.start():prose_primary_heads[i+1].start() if i+1<len(prose_primary_heads) else len(prose_primary_raw)].strip()
 assert row['whole_topic_read'] and row['text']==part and row['chars']==len(part) and row['sha256']==hashlib.sha256(part.encode()).hexdigest()
for flag in ['source_complete_book_is_actual_fifth_complete_book','estimated_lengths_are_actual_written_lengths','embedded_cases_are_nine_separate_whole_novels','all_cloned_wills_explode_or_cannot_work','native_excludes_physical_born','Dropout_is_always_death_or_coma','BP_is_moral_or_forced_emotion_track','all_six_versioned_plans_whole_reviewed','all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','all_art_maps_and_project_archives_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not prose_review[flag]
assert prose_review['new_mechanical_parameter_values']==[] and prose_review['new_related_novels_whole_read']==0
prose_ar=legacy['foundational_world_bible_prose_arithmetic'];assert (prose_ar['checks_passed'],prose_ar['predicted_total_chars'],prose_ar['source_actual_chars'],prose_ar['source_horizon_labels'],prose_ar['source_DD_offsets'])==(3,1100000,43175,[0,1],[4227,4226])
for flag in ['estimated_lengths_are_actual_written_lengths','one_world_calendar_base_fixed','all_source_stories_or_maps_delivered','fifth_engine_changed','actual_participant_playtest']:assert not prose_ar[flag]
prose_world=(o/'11_WorldLorebook.md').read_text()
assert '### 사례의 결말과 지금의 선택' in prose_world and '리듬필러는 그 일을 하는 직업/전문성' in prose_world and '원본0086의 페이는 브리핑 뒤 고심하는 상태에서 이야기가 끝납니다' in prose_world and '정상 고용과 복제도 항상 폭발한다는 보편 규칙' in prose_world
prose_ev=evidence['foundational_world_bible_prose_review'];assert (prose_ev['whole_documents_read'],prose_ev['major_sections'],prose_ev['embedded_case_studies'],prose_ev['primary_topics_whole_rechecked'],prose_ev['limited_source_arithmetic_checks'])==(1,35,9,13,3) and not prose_ev['actual_participant_playtest']
d['current_foundational_world_bible_prose_review']={'World':'v0.74','Design':'v1.05','whole_documents_read':1,'major_sections_mapped':35,'embedded_case_studies':9,'primary_topics_whole_rechecked':13,'limited_source_arithmetic_checks':3,'foundational_candidates_cumulative_whole_reviews':5,'foundational_candidates_semantic_pending':3,'estimated_lengths_are_actual_written_lengths':False,'embedded_cases_are_nine_separate_whole_novels':False,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
laws_review=legacy_coherence['foundational_world_bible_laws_review'];laws_source=laws_review['snapshot'];laws_path=p/laws_source['path_relative_to_plan']
verify_recorded_source_hash(laws_path,laws_source['sha256']);laws_raw=laws_path.read_bytes();laws_text=laws_raw.decode()
assert laws_source['whole_document_read'] and laws_source['text']==laws_text and (laws_source['bytes'],laws_source['chars'],laws_source['lines'])==(95699,41190,351)
assert (laws_review['whole_documents_read'],laws_review['major_sections'],laws_review['numbered_subsections'],laws_review['embedded_case_occurrences'],laws_review['embedded_unique_case_bodies'],laws_review['primary_topics_whole_rechecked'])==(1,36,22,8,7,8)
assert laws_review['versions']['World']=='v0.75' and laws_review['versions']['Design']=='v1.06'
assert (laws_review['foundational_candidates_cumulative_whole_reviews'],laws_review['foundational_candidates_semantic_pending'])==(6,2)
laws_sections=laws_review['major_section_mapping'];assert ''.join(row['text'] for row in laws_sections)==laws_text
laws_rx=r'(?m)^\ufeff?(?:FEWK 월드 바이블|제1부:|1\.[1-4]\. |\[(?:1\.[1-4]\.\d\.|사례 분석 ))[^\r\n]*';laws_heads=list(re.finditer(laws_rx,laws_text));assert len(laws_heads)==len(laws_sections)==36
assert len(list(re.finditer(r'(?m)^\[1\.[1-4]\.\d\.',laws_text)))==22
for i,(h,row) in enumerate(zip(laws_heads,laws_sections)):
 end=laws_heads[i+1].start() if i+1<len(laws_heads) else len(laws_text);part=laws_text[h.start():end]
 assert row['title']==h[0].lstrip('\ufeff') and row['text']==part and row['sha256']==hashlib.sha256(part.encode()).hexdigest() and row['start_line']==laws_text[:h.start()].count('\n')+1 and row['decision']
laws_case_heads=list(re.finditer(r'(?m)^\[사례 분석 (?P<index>\d+):[^\r\n]*',laws_text));laws_cases=laws_review['case_study_mapping'];assert len(laws_case_heads)==len(laws_cases)==8 and [row['index'] for row in laws_cases]==list(range(6,14))
for h,row in zip(laws_case_heads,laws_cases):
 a=laws_text.index('분석:',h.end());end=laws_text.find('\r\n',a);end=len(laws_text) if end<0 else end;part=laws_text[h.start():end];body=laws_text[h.end():end].strip()
 assert row['title']==h[0] and row['text']==part and row['sha256']==hashlib.sha256(part.encode()).hexdigest() and row['body_and_analysis_sha256']==hashlib.sha256(body.encode()).hexdigest() and row['start_line']==laws_text[:h.start()].count('\n')+1 and row['decision'] and not row['is_separate_whole_novel_read']
assert len({row['body_and_analysis_sha256'] for row in laws_cases})==7 and laws_cases[0]['body_and_analysis_sha256']==laws_cases[6]['body_and_analysis_sha256']
assert any(row['id']=='LEG-FOUND-06' and row['sha256']==laws_source['sha256'] and row['whole_document_read'] for row in additional_procurement)
prefix=laws_review['document5_partial_prefix_review'];prefix_path=p/prefix['path_relative_to_plan'];verify_recorded_source_hash(prefix_path,prefix['sha256']);prefix_raw=prefix_path.read_bytes()
assert (prefix['bytes'],prefix['chars'],prefix['lines'])==(473672,213024,2374) and (len(prefix_raw),len(prefix_raw.decode()),len(prefix_raw.decode().splitlines()))==(473672,213024,2374)
assert prefix['prefix_matches_whole_document4_bytes'] and prefix_raw.startswith(laws_raw) and prefix['reviewed_prefix_sha256']==laws_source['sha256']
assert (prefix['reviewed_prefix_bytes'],prefix['reviewed_prefix_chars'],prefix['reviewed_prefix_lines'])==(95699,41190,351)
suffix=prefix_raw[len(laws_raw):];assert suffix.startswith(b'\r\n') and prefix['suffix_starts_with_prefix_line_terminator'] and not laws_raw.endswith(b'\n')
assert (len(suffix),len(suffix.decode()),len(suffix.decode().splitlines()),len(suffix[2:].decode().splitlines()))==(377973,171834,2024,2023)
assert (prefix['unreviewed_suffix_bytes'],prefix['unreviewed_suffix_chars'],prefix['suffix_raw_splitlines'],prefix['unreviewed_suffix_lines'])==(377973,171834,2024,2023)
assert prefix['unreviewed_suffix_sha256']==hashlib.sha256(suffix).hexdigest() and prefix['pending_line_range']==[352,2374] and not prefix['whole_document_read'] and not prefix['semantic_review_complete']
prefix_inventory=next(row for row in settings_rows if row['path_relative_to_plan']==prefix['path_relative_to_plan'])
assert prefix_inventory['whole_document_read'] and prefix_inventory['semantic_review_complete'] and prefix_inventory['review_evidence']=='foundational_world_bible_appendix_review'
laws_primary=laws_review['primary_topic_recheck'];verify_recorded_source_hash(p/laws_primary['source_path_relative_to_plan'],laws_primary['sha256']);lp_raw=(p/laws_primary['source_path_relative_to_plan']).read_text();lp_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',lp_raw))
assert not laws_primary['whole_container_read'] and [row['topic'] for row in laws_primary['topics']]==['0001','0024','0044','0059','0064','0072','0091','0100']
for row in laws_primary['topics']:
 h=next(x for x in lp_heads if x[1]==row['topic']);i=lp_heads.index(h);part=lp_raw[h.start():lp_heads[i+1].start() if i+1<len(lp_heads) else len(lp_raw)].strip()
 assert row['whole_topic_read'] and row['text']==part and row['chars']==len(part) and row['sha256']==hashlib.sha256(part.encode()).hexdigest()
for flag in ['source_complete_book_is_actual_fifth_complete_book','document5_whole_review_complete','all_six_versioned_plans_whole_reviewed','cases_count_is_separate_whole_novels','all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','all_art_maps_and_project_archives_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not laws_review[flag]
assert laws_review['new_mechanical_parameter_values']==[] and laws_review['new_related_novels_whole_read']==0
laws_world=(o/'11_WorldLorebook.md').read_text();laws_33=laws_world.split('## 33.')[1].split('## 34.')[0]
for phrase in ['### 스위트 사건 — 보인 것과 채택되지 않은 증언','원본0059','그 증언은 정식 채택되지 않습니다','기관의 결론을 각각 전달합니다']:assert phrase in laws_33
assert '관시의 전공은 원본0024에서 **돌칩**' in laws_world and '후속 기획의 ‘실력 없는 플라이어 밀턴’' in laws_world
laws_ev=evidence['foundational_world_bible_laws_review'];assert (laws_ev['whole_documents_read'],laws_ev['major_sections'],laws_ev['numbered_subsections'],laws_ev['embedded_case_occurrences'],laws_ev['embedded_unique_case_bodies'],laws_ev['primary_topics_whole_rechecked'],laws_ev['document5_prefix_lines_reviewed'],laws_ev['document5_suffix_lines_pending'])==(1,36,22,8,7,8,351,2023)
assert not laws_ev['document5_whole_review_complete'] and not laws_ev['actual_participant_playtest']
d['current_foundational_world_bible_laws_review']={'World':'v0.75','Design':'v1.06','whole_documents_read':1,'major_sections_mapped':36,'numbered_subsections':22,'embedded_case_occurrences':8,'unique_case_bodies':7,'primary_topics_whole_rechecked':8,'document5_prefix_lines_reviewed':351,'document5_suffix_lines_pending':2023,'document5_whole_review_complete':False,'foundational_candidates_cumulative_whole_reviews':6,'foundational_candidates_semantic_pending':2,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
stage_review=legacy_coherence['foundational_world_bible_stage_review'];stage_src=stage_review['source'];stage_path=p/stage_src['path_relative_to_plan']
verify_recorded_source_hash(stage_path,stage_src['sha256']);stage_raw=stage_path.read_bytes();stage_text=stage_raw.decode();stage_lines=stage_text.splitlines(keepends=True)
assert (len(stage_raw),len(stage_text),len(stage_lines))==(stage_src['bytes'],stage_src['chars'],stage_src['lines'])==(473672,213024,2374)
assert not stage_src['whole_document_read'] and stage_src['sha256']==prefix['sha256']
stage_part=stage_review['reviewed_part'];stage_part_text=''.join(stage_lines[351:846])
assert stage_part['text']==stage_part_text and stage_part['sha256']==hashlib.sha256(stage_part_text.encode()).hexdigest()
assert stage_part['whole_part_read'] and stage_part['semantic_review_complete'] and stage_part['line_range']==[352,846]
assert (stage_part['bytes'],stage_part['chars'],stage_part['lines'])==(94166,41462,495)
stage_sections=stage_review['major_section_mapping'];stage_rx=r'(?m)^(?:제2부:|2\.[123]\. |\[(?:2\.[234]\.|사례 분석 ))[^\r\n]*';stage_heads=list(re.finditer(stage_rx,stage_part_text))
assert len(stage_sections)==len(stage_heads)==stage_review['major_sections']==27 and ''.join(x['text'] for x in stage_sections)==stage_part_text
for i,(h,row) in enumerate(zip(stage_heads,stage_sections)):
 end=stage_heads[i+1].start() if i+1<len(stage_heads) else len(stage_part_text);b=stage_part_text[h.start():end]
 assert row['title']==h[0] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['start_line']==stage_part_text[:h.start()].count('\n')+352 and row['decision']
assert len(stage_review['style_groups'])==6 and stage_review['style_feature_rows']==150
for sty in stage_review['style_groups']:
 row=next(x for x in stage_sections if x['title']==sty['title']);feats=[{'index':int(m[1]),'text':m[0]} for m in re.finditer(r'(?m)^(\d+)\. [^\r\n]*',row['text'])]
 assert sty['features']==feats and [x['index'] for x in feats]==list(range(1,26)) and sty['decision']==row['decision']
assert (stage_review['well_formed_organization_heading_occurrences'],stage_review['malformed_organization_heading_occurrences'])==(17,1)
stage_orgs=[{'start_line':stage_part_text[:m.start()].count('\n')+352,'source_heading':m[0]} for m in re.finditer(r'(?m)^.*조직명:[^\r\n]*',stage_part_text)]
assert stage_review['organization_heading_mapping']==stage_orgs and len(stage_orgs)==17 and '* * 조 "AD 시대"' in stage_part_text
assert stage_review['embedded_case_occurrences']==len(stage_review['case_study_mapping'])==2
for row in stage_review['case_study_mapping']:
 assert not row['is_separate_whole_novel_read'] and any(x['title']==row['title'] and x['text']==row['text'] for x in stage_sections)
stage_progress=stage_review['document5_current_partial_progress'];stage_prefix=''.join(stage_lines[:846]);stage_suffix=''.join(stage_lines[846:])
assert stage_raw.startswith(laws_raw) and stage_raw[len(laws_raw):len(laws_raw)+2]==b'\r\n'
assert stage_prefix==laws_raw.decode()+'\r\n'+stage_part_text
assert (stage_progress['reviewed_prefix_bytes'],stage_progress['reviewed_prefix_chars'],stage_progress['reviewed_prefix_lines'])==(len(stage_prefix.encode()),len(stage_prefix),len(stage_prefix.splitlines()))==(189867,82654,846)
assert stage_progress['reviewed_prefix_sha256']==hashlib.sha256(stage_prefix.encode()).hexdigest() and stage_progress['pending_line_range']==[847,2374]
assert (stage_progress['pending_suffix_bytes'],stage_progress['pending_suffix_chars'],stage_progress['pending_suffix_lines'])==(len(stage_suffix.encode()),len(stage_suffix),len(stage_suffix.splitlines()))==(283805,130370,1528)
assert stage_progress['pending_suffix_sha256']==hashlib.sha256(stage_suffix.encode()).hexdigest() and not stage_progress['whole_document_read'] and not stage_progress['semantic_review_complete']
assert stage_progress['reviewed_prefix_sha256']==hashlib.sha256(stage_prefix.encode()).hexdigest()
stage_primary=stage_review['primary_topic_recheck'];verify_recorded_source_hash(p/stage_primary['source_path_relative_to_plan'],stage_primary['source_sha256']);sp_text=(p/stage_primary['source_path_relative_to_plan']).read_bytes().decode();sp_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',sp_text))
assert [row['topic_id'] for row in stage_primary['topics']]==['0001','0015','0032','0049','0053','0054','0062','0063','0071','0090','0091','0093','0095','0097','0101']
for row in stage_primary['topics']:
 i,h=next((i,h) for i,h in enumerate(sp_heads) if h[1]==row['topic_id']);b=sp_text[h.start():sp_heads[i+1].start() if i+1<len(sp_heads) else len(sp_text)].strip()
 assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest()
 assert row['substantive_body_available']==(row['topic_id']!='0101')
assert stage_review['primary_topics_whole_rechecked']==15 and stage_review['primary_substantive_topics_whole_rechecked']==14 and stage_review['primary_title_only_topics']==['0101']
from urllib.parse import unquote as stage_unquote
stage_wiki=stage_review['current_wiki_rechecks'];verify_recorded_source_hash(p/stage_wiki['source_path_relative_to_plan'],stage_wiki['source_sha256']);sw_text=(p/stage_wiki['source_path_relative_to_plan']).read_bytes().decode();sw_heads=list(re.finditer(r'(?m)^--- (.+?) ---\s*$',sw_text))
assert len(stage_wiki['topics'])==stage_review['wiki_topics_whole_rechecked']==17
for row in stage_wiki['topics']:
 i,h=next((i,h) for i,h in enumerate(sw_heads) if h[1]==row['topic']);b=sw_text[h.start():sw_heads[i+1].start() if i+1<len(sw_heads) else len(sw_text)].strip()
 assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and stage_unquote(row['topic'])==row['decoded_topic']+'.txt'
assert len(stage_review['prior_laws_mapping_corrections'])==2
for correction in stage_review['prior_laws_mapping_corrections']:
 row=next(x for x in laws_sections if x['title']==correction['section'])
 assert row['previous_decision_before_stage_recheck']==correction['previous_decision'] and row['decision']==correction['corrected_decision'] and row['decision_revision_evidence']=='foundational_world_bible_stage_review' and correction['primary_topic']=='0071'
assert stage_review['versions']['World']=='v0.76' and stage_review['versions']['Design']=='v1.07'
assert stage_review['whole_documents_read']==stage_review['new_related_novels_whole_read']==0 and stage_review['new_mechanical_parameter_values']==[]
assert (stage_review['foundational_candidates_cumulative_whole_reviews'],stage_review['foundational_candidates_semantic_pending'],stage_review['additional_registered_whole_documents'])==(6,2,109)
for flag in ['document5_whole_review_complete','all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','all_setting_sources_inventoried','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not stage_review[flag]
stage_ev=evidence['foundational_world_bible_stage_review'];assert (stage_ev['whole_documents_read'],stage_ev['major_sections'],stage_ev['style_feature_rows'],stage_ev['primary_topics_whole_rechecked'],stage_ev['primary_substantive_topics_whole_rechecked'],stage_ev['wiki_topics_whole_rechecked'],stage_ev['document5_prefix_lines_reviewed'],stage_ev['document5_suffix_lines_pending'],stage_ev['prior_laws_mapping_corrections'])==(0,27,150,15,14,17,846,1528,2)
assert not stage_ev['document5_whole_review_complete'] and not stage_ev['actual_participant_playtest']
d['current_foundational_world_bible_stage_review']={'World':'v0.76','Design':'v1.07','whole_documents_read':0,'reviewed_part_lines':495,'major_sections_mapped':27,'style_feature_rows':150,'primary_topics_whole_rechecked':15,'primary_substantive_topics':14,'wiki_topics_whole_rechecked':17,'document5_prefix_lines_reviewed':846,'document5_suffix_lines_pending':1528,'document5_whole_review_complete':False,'prior_laws_mapping_corrections':2,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
chronicle_review=legacy_coherence['foundational_world_bible_chronicle_review'];chronicle_src=chronicle_review['source'];chronicle_path=p/chronicle_src['path_relative_to_plan']
verify_recorded_source_hash(chronicle_path,chronicle_src['sha256']);chronicle_raw=chronicle_path.read_bytes();chronicle_text=chronicle_raw.decode();chronicle_lines=chronicle_text.splitlines(keepends=True)
assert (len(chronicle_raw),len(chronicle_text),len(chronicle_lines))==(chronicle_src['bytes'],chronicle_src['chars'],chronicle_src['lines'])==(473672,213024,2374)
assert not chronicle_src['whole_document_read'] and chronicle_src['sha256']==stage_src['sha256']
chronicle_part=chronicle_review['reviewed_part'];chronicle_part_text=''.join(chronicle_lines[846:1066]);assert chronicle_part['text']==chronicle_part_text and chronicle_part['sha256']==hashlib.sha256(chronicle_part_text.encode()).hexdigest()
assert chronicle_part['whole_part_read'] and chronicle_part['semantic_review_complete'] and chronicle_part['line_range']==[847,1066] and (chronicle_part['bytes'],chronicle_part['chars'],chronicle_part['lines'])==(46054,19998,220)
chronicle_sections=chronicle_review['major_section_mapping'];chronicle_rx=r'(?m)^(?:제3부:|3\.[124]\. |\[3\.[1-4]\.)[^\r\n]*';chronicle_heads=list(re.finditer(chronicle_rx,chronicle_part_text))
assert len(chronicle_sections)==len(chronicle_heads)==chronicle_review['major_sections']==17 and ''.join(x['text'] for x in chronicle_sections)==chronicle_part_text
for i,(h,row) in enumerate(zip(chronicle_heads,chronicle_sections)):
 end=chronicle_heads[i+1].start() if i+1<len(chronicle_heads) else len(chronicle_part_text);b=chronicle_part_text[h.start():end]
 assert row['title']==h[0] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['start_line']==chronicle_part_text[:h.start()].count('\n')+847 and row['decision']
chronicle_cells=[x.strip() for x in chronicle_part_text.split('연호 변환표 (주요 사건 기준):')[1].split('[3.4.2. 상세 연표]')[0].splitlines() if x.strip()];assert len(chronicle_cells)==40
chronicle_table=[dict(zip(['event','DD','H','G','E'],chronicle_cells[i:i+5])) for i in range(5,len(chronicle_cells),5)]
assert chronicle_table==chronicle_review['conversion_table_rows'] and len(chronicle_table)==chronicle_review['conversion_table_row_count']==7
chronicle_bullets=re.findall(r'(?m)^\* (?:AD |수평 |현재 시점)[^\r\n]*',chronicle_part_text.split('[3.4.2. 상세 연표]')[1]);assert chronicle_bullets==chronicle_review['detailed_timeline_entries'] and len(chronicle_bullets)==chronicle_review['detailed_timeline_entry_count']==14
chronicle_progress=chronicle_review['document5_current_partial_progress'];chronicle_prefix=''.join(chronicle_lines[:1066]);chronicle_suffix=''.join(chronicle_lines[1066:])
assert chronicle_prefix==stage_prefix+chronicle_part_text and chronicle_progress['reviewed_prefix_lines']==1066 and chronicle_progress['pending_suffix_lines']==1308 and chronicle_progress['pending_line_range']==[1067,2374]
assert (chronicle_progress['reviewed_prefix_bytes'],chronicle_progress['reviewed_prefix_chars'])==(len(chronicle_prefix.encode()),len(chronicle_prefix)) and chronicle_progress['reviewed_prefix_sha256']==hashlib.sha256(chronicle_prefix.encode()).hexdigest()
assert (chronicle_progress['pending_suffix_bytes'],chronicle_progress['pending_suffix_chars'])==(len(chronicle_suffix.encode()),len(chronicle_suffix)) and chronicle_progress['pending_suffix_sha256']==hashlib.sha256(chronicle_suffix.encode()).hexdigest()
assert not chronicle_progress['whole_document_read'] and not chronicle_progress['semantic_review_complete']
assert chronicle_progress['reviewed_prefix_sha256']==hashlib.sha256(chronicle_prefix.encode()).hexdigest()
chronicle_primary=chronicle_review['primary_topic_recheck'];verify_recorded_source_hash(p/chronicle_primary['source_path_relative_to_plan'],chronicle_primary['sha256']);cp_text=(p/chronicle_primary['source_path_relative_to_plan']).read_text();cp_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',cp_text))
assert not chronicle_primary['whole_container_read'] and [x['topic'] for x in chronicle_primary['topics']]==['0005','0022','0032','0039','0046','0067','0071','0090','0092','0096','0099']
for row in chronicle_primary['topics']:
 i,h=next((i,h) for i,h in enumerate(cp_heads) if h[1]==row['topic']);b=cp_text[h.start():cp_heads[i+1].start() if i+1<len(cp_heads) else len(cp_text)].strip()
 assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['chars']==len(b)
chronicle_wiki=chronicle_review['current_wiki_rechecks'];verify_recorded_source_hash(p/chronicle_wiki['source_path_relative_to_plan'],chronicle_wiki['source_sha256']);cw_text=(p/chronicle_wiki['source_path_relative_to_plan']).read_text();cw_heads=list(re.finditer(r'(?m)^--- (.+?) ---\s*$',cw_text));assert not chronicle_wiki['whole_container_read']
assert len(chronicle_wiki['topics'])==chronicle_review['wiki_topics_whole_rechecked']==6
for row in chronicle_wiki['topics']:
 i,h=next((i,h) for i,h in enumerate(cw_heads) if h[1]==row['topic']);b=cw_text[h.start():cw_heads[i+1].start() if i+1<len(cw_heads) else len(cw_text)].strip()
 assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest()
assert chronicle_review['versions']['World']=='v0.77' and chronicle_review['versions']['Design']=='v1.08' and chronicle_review['primary_topics_whole_rechecked']==11
assert chronicle_review['whole_documents_read']==chronicle_review['new_related_novels_whole_read']==0 and chronicle_review['new_mechanical_parameter_values']==[] and chronicle_review['limited_source_arithmetic_checks']==6
assert (chronicle_review['foundational_candidates_cumulative_whole_reviews'],chronicle_review['foundational_candidates_semantic_pending'],chronicle_review['additional_registered_whole_documents'])==(6,2,109)
for flag in ['document5_whole_review_complete','one_world_calendar_base_fixed','all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','all_setting_sources_inventoried','real_history_fact_checked','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not chronicle_review[flag]
chronicle_ev=evidence['foundational_world_bible_chronicle_review'];assert (chronicle_ev['whole_documents_read'],chronicle_ev['major_sections'],chronicle_ev['conversion_table_row_count'],chronicle_ev['detailed_timeline_entry_count'],chronicle_ev['primary_topics_whole_rechecked'],chronicle_ev['wiki_topics_whole_rechecked'],chronicle_ev['document5_prefix_lines_reviewed'],chronicle_ev['document5_suffix_lines_pending'])==(0,17,7,14,11,6,1066,1308)
assert not chronicle_ev['document5_whole_review_complete'] and not chronicle_ev['actual_participant_playtest']
chronicle_arithmetic=legacy['foundational_world_bible_chronicle_arithmetic'];assert chronicle_arithmetic['checks_passed']==6 and not chronicle_arithmetic['one_world_calendar_base_fixed'] and not chronicle_arithmetic['actual_participant_playtest']
d['current_foundational_world_bible_chronicle_review']={'World':'v0.77','Design':'v1.08','whole_documents_read':0,'reviewed_part_lines':220,'major_sections_mapped':17,'conversion_table_rows':7,'detailed_timeline_entries':14,'primary_topics_whole_rechecked':11,'wiki_topics_whole_rechecked':6,'document5_prefix_lines_reviewed':1066,'document5_suffix_lines_pending':1308,'document5_whole_review_complete':False,'limited_source_arithmetic_checks':6,'one_world_calendar_base_fixed':False,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
import urllib.parse
personnel_review=legacy_coherence['foundational_world_bible_personnel_review'];personnel_src=personnel_review['source'];personnel_path=p/personnel_src['path_relative_to_plan']
verify_recorded_source_hash(personnel_path,personnel_src['sha256']);personnel_raw=personnel_path.read_bytes();personnel_text=personnel_raw.decode();personnel_lines=personnel_text.splitlines(keepends=True)
assert (len(personnel_raw),len(personnel_text),len(personnel_lines))==(personnel_src['bytes'],personnel_src['chars'],personnel_src['lines'])==(473672,213024,2374)
assert not personnel_src['whole_document_read'] and personnel_src['sha256']==chronicle_src['sha256']
personnel_part=personnel_review['reviewed_part'];personnel_part_text=''.join(personnel_lines[1066:1423]);assert personnel_part['text']==personnel_part_text and personnel_part['sha256']==hashlib.sha256(personnel_part_text.encode()).hexdigest()
assert personnel_part['whole_part_read'] and personnel_part['semantic_review_complete'] and personnel_part['line_range']==[1067,1423] and (personnel_part['bytes'],personnel_part['chars'],personnel_part['lines'])==(69198,30911,357)
personnel_sections=personnel_review['major_section_mapping'];personnel_heads=list(re.finditer(r'(?m)^(?:제4부:|4\.[12]\. |\[4\.[12]\.)[^\r\n]*',personnel_part_text))
assert len(personnel_sections)==len(personnel_heads)==personnel_review['major_sections']==19 and ''.join(x['text'] for x in personnel_sections)==personnel_part_text
for i,(h,row) in enumerate(zip(personnel_heads,personnel_sections)):
 end=personnel_heads[i+1].start() if i+1<len(personnel_heads) else len(personnel_part_text);b=personnel_part_text[h.start():end]
 assert row['title']==h[0] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['start_line']==personnel_part_text[:h.start()].count('\n')+1067 and row['decision']
personnel_progress=personnel_review['document5_current_partial_progress'];personnel_prefix=''.join(personnel_lines[:1423]);personnel_suffix=''.join(personnel_lines[1423:])
assert personnel_prefix==chronicle_prefix+personnel_part_text and personnel_progress['reviewed_prefix_lines']==1423 and personnel_progress['pending_suffix_lines']==951 and personnel_progress['pending_line_range']==[1424,2374]
assert (personnel_progress['reviewed_prefix_bytes'],personnel_progress['reviewed_prefix_chars'])==(len(personnel_prefix.encode()),len(personnel_prefix)) and personnel_progress['reviewed_prefix_sha256']==hashlib.sha256(personnel_prefix.encode()).hexdigest()
assert (personnel_progress['pending_suffix_bytes'],personnel_progress['pending_suffix_chars'])==(len(personnel_suffix.encode()),len(personnel_suffix)) and personnel_progress['pending_suffix_sha256']==hashlib.sha256(personnel_suffix.encode()).hexdigest()
assert not personnel_progress['whole_document_read'] and not personnel_progress['semantic_review_complete']
assert personnel_progress['reviewed_prefix_sha256']==hashlib.sha256(personnel_prefix.encode()).hexdigest()
personnel_primary=personnel_review['primary_topic_recheck'];verify_recorded_source_hash(p/personnel_primary['source_path_relative_to_plan'],personnel_primary['sha256']);pp_text=(p/personnel_primary['source_path_relative_to_plan']).read_text();pp_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',pp_text))
assert not personnel_primary['whole_container_read'] and [x['topic'] for x in personnel_primary['topics']]==['0014','0023','0026','0031','0033','0066','0069','0081','0089','0091','0001','0008','0094']
for row in personnel_primary['topics']:
 i,h=next((i,h) for i,h in enumerate(pp_heads) if h[1]==row['topic']);b=pp_text[h.start():pp_heads[i+1].start() if i+1<len(pp_heads) else len(pp_text)].strip()
 assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['chars']==len(b) and row['lines']==len(b.splitlines())
personnel_wiki=personnel_review['current_wiki_rechecks'];verify_recorded_source_hash(p/personnel_wiki['source_path_relative_to_plan'],personnel_wiki['source_sha256']);pw_text=(p/personnel_wiki['source_path_relative_to_plan']).read_text();pw_heads=list(re.finditer(r'(?m)^--- (.+?) ---\s*$',pw_text));assert not personnel_wiki['whole_container_read']
assert len(personnel_wiki['topics'])==personnel_review['wiki_topics_whole_rechecked']==8
for row in personnel_wiki['topics']:
 i,h=next((i,h) for i,h in enumerate(pw_heads) if unicodedata.normalize('NFC',urllib.parse.unquote(h[1]))==row['decoded_topic']);b=pw_text[h.start():pw_heads[i+1].start() if i+1<len(pw_heads) else len(pw_text)].strip()
 assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['chars']==len(b) and row['lines']==len(b.splitlines())
assert personnel_review['versions']['World']=='v0.78' and personnel_review['versions']['Design']=='v1.09' and personnel_review['primary_topics_whole_rechecked']==13
assert personnel_review['whole_documents_read']==personnel_review['new_related_novels_whole_read']==personnel_review['limited_source_arithmetic_checks']==0 and personnel_review['new_mechanical_parameter_values']==[]
assert (personnel_review['foundational_candidates_cumulative_whole_reviews'],personnel_review['foundational_candidates_semantic_pending'],personnel_review['additional_registered_whole_documents'])==(6,2,109)
for flag in ['document5_whole_review_complete','all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','all_setting_sources_inventoried','all_personnel_biographies_canon_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test','existing_character_review_is_new_novel_read']:assert not personnel_review[flag]
personnel_ev=evidence['foundational_world_bible_personnel_review'];assert (personnel_ev['whole_documents_read'],personnel_ev['major_sections'],personnel_ev['primary_topics_whole_rechecked'],personnel_ev['wiki_topics_whole_rechecked'],personnel_ev['document5_prefix_lines_reviewed'],personnel_ev['document5_suffix_lines_pending'])==(0,19,13,8,1423,951)
assert not personnel_ev['document5_whole_review_complete'] and not personnel_ev['actual_participant_playtest']
d['current_foundational_world_bible_personnel_review']={'World':'v0.78','Design':'v1.09','whole_documents_read':0,'reviewed_part_lines':357,'major_sections_mapped':19,'primary_topics_whole_rechecked':13,'wiki_topics_whole_rechecked':8,'document5_prefix_lines_reviewed':1423,'document5_suffix_lines_pending':951,'document5_whole_review_complete':False,'all_personnel_biographies_canon_verified':False,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}
constituent_review=legacy_coherence['foundational_world_bible_constituent_review'];constituent_src=constituent_review['source'];constituent_path=p/constituent_src['path_relative_to_plan']
verify_recorded_source_hash(constituent_path,constituent_src['sha256']);constituent_raw=constituent_path.read_bytes();constituent_text=constituent_raw.decode();constituent_lines=constituent_text.splitlines(keepends=True)
assert (len(constituent_raw),len(constituent_text),len(constituent_lines))==(constituent_src['bytes'],constituent_src['chars'],constituent_src['lines'])==(473672,213024,2374)
assert not constituent_src['whole_document_read'] and constituent_src['sha256']==personnel_src['sha256']
constituent_part=constituent_review['reviewed_part'];constituent_part_text=''.join(constituent_lines[1423:1829]);assert constituent_part['text']==constituent_part_text and constituent_part['sha256']==hashlib.sha256(constituent_part_text.encode()).hexdigest()
assert constituent_part['whole_part_read'] and constituent_part['semantic_review_complete'] and constituent_part['line_range']==[1424,1829] and (constituent_part['bytes'],constituent_part['chars'],constituent_part['lines'])==(79734,35314,406)
constituent_sections=constituent_review['major_section_mapping'];constituent_heads=list(re.finditer(r'(?m)^(?:제5부:|5\.[123]\. |\[5\.[123]\.|\* \[5\.2\.7\.2\.)[^\r\n]*',constituent_part_text))
assert len(constituent_sections)==len(constituent_heads)==constituent_review['major_sections']==27 and ''.join(x['text'] for x in constituent_sections)==constituent_part_text
for i,(h,row) in enumerate(zip(constituent_heads,constituent_sections)):
 end=constituent_heads[i+1].start() if i+1<len(constituent_heads) else len(constituent_part_text);b=constituent_part_text[h.start():end]
 assert row['title']==h[0] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['start_line']==constituent_part_text[:h.start()].count('\n')+1424 and row['decision']
constituent_progress=constituent_review['document5_current_partial_progress'];constituent_prefix=''.join(constituent_lines[:1829]);constituent_suffix=''.join(constituent_lines[1829:])
assert constituent_prefix==personnel_prefix+constituent_part_text and constituent_progress['reviewed_prefix_lines']==1829 and constituent_progress['pending_suffix_lines']==545 and constituent_progress['pending_line_range']==[1830,2374]
assert (constituent_progress['reviewed_prefix_bytes'],constituent_progress['reviewed_prefix_chars'])==(len(constituent_prefix.encode()),len(constituent_prefix)) and constituent_progress['reviewed_prefix_sha256']==hashlib.sha256(constituent_prefix.encode()).hexdigest()
assert (constituent_progress['pending_suffix_bytes'],constituent_progress['pending_suffix_chars'])==(len(constituent_suffix.encode()),len(constituent_suffix)) and constituent_progress['pending_suffix_sha256']==hashlib.sha256(constituent_suffix.encode()).hexdigest()
assert not constituent_progress['whole_document_read'] and not constituent_progress['semantic_review_complete']
assert constituent_progress['reviewed_prefix_sha256']==hashlib.sha256(constituent_prefix.encode()).hexdigest() and constituent_progress['reviewed_prefix_bytes']==len(constituent_prefix.encode()) and constituent_progress['reviewed_prefix_lines']==1829
constituent_primary=constituent_review['primary_topic_recheck'];verify_recorded_source_hash(p/constituent_primary['source_path_relative_to_plan'],constituent_primary['sha256']);ct_text=(p/constituent_primary['source_path_relative_to_plan']).read_text();ct_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',ct_text))
assert not constituent_primary['whole_container_read'] and [x['topic'] for x in constituent_primary['topics']]==['0011','0016','0019','0021','0036','0058','0070','0077','0079','0083','0090','0105']
for row in constituent_primary['topics']:
 i,h=next((i,h) for i,h in enumerate(ct_heads) if h[1]==row['topic']);b=ct_text[h.start():ct_heads[i+1].start() if i+1<len(ct_heads) else len(ct_text)].strip()
 assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['chars']==len(b) and row['lines']==len(b.splitlines())
constituent_wiki=constituent_review['current_wiki_rechecks'];verify_recorded_source_hash(p/constituent_wiki['source_path_relative_to_plan'],constituent_wiki['source_sha256']);cw_text=(p/constituent_wiki['source_path_relative_to_plan']).read_text();cw_heads=list(re.finditer(r'(?m)^--- (.+?) ---\s*$',cw_text));assert not constituent_wiki['whole_container_read']
assert len(constituent_wiki['topics'])==constituent_review['wiki_topics_whole_rechecked']==11
for row in constituent_wiki['topics']:
 i,h=next((i,h) for i,h in enumerate(cw_heads) if unicodedata.normalize('NFC',unquote(h[1]))==row['decoded_topic']);b=cw_text[h.start():cw_heads[i+1].start() if i+1<len(cw_heads) else len(cw_text)].strip()
 assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['chars']==len(b) and row['lines']==len(b.splitlines())
assert constituent_review['versions']['World']=='v0.79' and constituent_review['versions']['Design']=='v1.10' and constituent_review['primary_topics_whole_rechecked']==12
assert constituent_review['whole_documents_read']==constituent_review['new_related_novels_whole_read']==constituent_review['limited_source_arithmetic_checks']==0 and constituent_review['new_mechanical_parameter_values']==[]
assert (constituent_review['foundational_candidates_cumulative_whole_reviews'],constituent_review['foundational_candidates_semantic_pending'],constituent_review['additional_registered_whole_documents'])==(6,2,109)
for flag in ['document5_whole_review_complete','all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','all_setting_sources_inventoried','all_item_provenance_and_biographies_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not constituent_review[flag]
constituent_ev=evidence['foundational_world_bible_constituent_review'];assert (constituent_ev['whole_documents_read'],constituent_ev['major_sections'],constituent_ev['primary_topics_whole_rechecked'],constituent_ev['wiki_topics_whole_rechecked'],constituent_ev['document5_prefix_lines_reviewed'],constituent_ev['document5_suffix_lines_pending'])==(0,27,12,11,1829,545)
assert not constituent_ev['document5_whole_review_complete'] and not constituent_ev['actual_participant_playtest']
d['current_foundational_world_bible_constituent_review']={'World':'v0.79','Design':'v1.10','whole_documents_read':0,'reviewed_part_lines':406,'major_sections_mapped':27,'primary_topics_whole_rechecked':12,'wiki_topics_whole_rechecked':11,'document5_prefix_lines_reviewed':1829,'document5_suffix_lines_pending':545,'document5_whole_review_complete':False,'all_item_provenance_and_biographies_verified':False,'current_engine_changed':False,'actual_participant_reading':False,'actual_participant_playtest':False,'actual_async_community_test':False}

# Document(5) whole-read closure: retain earlier partial-pass records as history.
appendix_review=legacy_coherence['foundational_world_bible_appendix_review'];appendix_source=appendix_review['source']
verify_recorded_source_hash(p/appendix_source['path_relative_to_plan'],appendix_source['sha256'])
appendix_raw=(p/appendix_source['path_relative_to_plan']).read_bytes();appendix_text=appendix_raw.decode();appendix_lines=appendix_text.splitlines(keepends=True)
assert (len(appendix_raw),len(appendix_text),len(appendix_lines))==(473672,213024,2374)
assert appendix_source['whole_document_read'] and appendix_source['semantic_review_complete'] and appendix_source['sha256']=='cf07bd6d10f459a27c3f6c11cd7283e4f907ce3584f4bbae2b4da0eef8ce1d42'
appendix_part=appendix_review['reviewed_part'];appendix_part_text=''.join(appendix_lines[1829:])
assert appendix_part['text']==appendix_part_text and appendix_part['line_range']==[1830,2374]
assert appendix_part['whole_part_read'] and appendix_part['semantic_review_complete'] and (appendix_part['bytes'],appendix_part['chars'],appendix_part['lines'])==(88819,44147,545)
assert appendix_part['sha256']==hashlib.sha256(appendix_part_text.encode()).hexdigest()
appendix_heads=list(re.finditer(r'(?m)^(?:부록 A:|A\.[12]\. |\[[ㄱ-ㅎ]|\[특수|\[A\.2\.|   \* \[A\.2\.2\.)[^\r\n]*',appendix_part_text))
assert appendix_review['major_sections']==len(appendix_heads)==len(appendix_review['major_section_mapping'])==21
for i,(row,h) in enumerate(zip(appendix_review['major_section_mapping'],appendix_heads)):
 b=appendix_part_text[h.start():appendix_heads[i+1].start() if i+1<len(appendix_heads) else len(appendix_part_text)]
 assert row['title']==h[0] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['decision'] and row['start_line']==appendix_part_text[:h.start()].count('\n')+1830
assert ''.join(row['text'] for row in appendix_review['major_section_mapping'])==appendix_part_text
appendix_entry_heads=list(re.finditer(r'(?m)^[ \t]*\*[ \t]+(?:\*[ \t]+)?(.+?):[ \t]*(\[[^\]\r\n]+\])[ \t]*([^\r\n]*)',appendix_part_text.split('A.2. 지도 모음')[0]))
assert appendix_review['glossary_entry_occurrences']==len(appendix_entry_heads)==len(appendix_review['glossary_entry_mapping'])==484
for row,m in zip(appendix_review['glossary_entry_mapping'],appendix_entry_heads):
 assert (row['term'],row['source_category'],row['source_definition'],row['source_row'],row['start_line'])==(m[1],m[2],m[3],m[0],appendix_part_text[:m.start()].count('\n')+1830)
appendix_progress=appendix_review['document5_current_complete_progress']
assert appendix_progress['reviewed_prefix_sha256']==appendix_source['sha256'] and (appendix_progress['reviewed_prefix_bytes'],appendix_progress['reviewed_prefix_chars'],appendix_progress['reviewed_prefix_lines'])==(473672,213024,2374)
assert appendix_progress['whole_document_read'] and appendix_progress['semantic_review_complete'] and appendix_progress['pending_line_range'] is None
assert (appendix_progress['pending_suffix_bytes'],appendix_progress['pending_suffix_chars'],appendix_progress['pending_suffix_lines'])==(0,0,0)
appendix_ranges=[[1,351],[352,846],[847,1066],[1067,1423],[1424,1829],[1830,2374]]
assert [row['line_range'] for row in appendix_progress['whole_document_coverage']]==appendix_ranges
appendix_assembled=[]
for row in appendix_progress['whole_document_coverage']:
 a,b=row['line_range'];piece=''.join(appendix_lines[a-1:b]);appendix_assembled.append(piece)
 assert row['review_evidence'] in legacy_coherence and (row['bytes'],row['chars'],row['lines'],row['sha256'])==(len(piece.encode()),len(piece),b-a+1,hashlib.sha256(piece.encode()).hexdigest())
 if a==1:assert piece.encode()==laws_raw+b'\r\n'
 elif a==1830:assert piece==appendix_part_text
 else:assert legacy_coherence[row['review_evidence']]['reviewed_part']['text']==piece
assert ''.join(appendix_assembled)==appendix_text
assert prefix_inventory['review_evidence']=='foundational_world_bible_appendix_review' and prefix_inventory['whole_document_read']
appendix_procurement=next(row for row in additional_procurement if row['id']=='LEG-FOUND-07')
assert appendix_procurement['whole_document_read'] and appendix_procurement['source_relative_to_plan']==appendix_source['path_relative_to_plan'] and appendix_procurement['sha256']==appendix_source['sha256'] and appendix_procurement['bytes']==len(appendix_raw)
appendix_primary=appendix_review['primary_topic_recheck'];verify_recorded_source_hash(p/appendix_primary['source_path_relative_to_plan'],appendix_primary['sha256'])
appendix_primary_text=(p/appendix_primary['source_path_relative_to_plan']).read_text();appendix_primary_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',appendix_primary_text))
assert not appendix_primary['whole_container_read'] and [row['topic'] for row in appendix_primary['topics']]==['0006','0007','0035','0045','0052','0056','0072','0097','0080']
for row in appendix_primary['topics']:
 i,h=next((i,h) for i,h in enumerate(appendix_primary_heads) if h[1]==row['topic']);b=appendix_primary_text[h.start():appendix_primary_heads[i+1].start() if i+1<len(appendix_primary_heads) else len(appendix_primary_text)].strip()
 assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and (row['chars'],row['lines'])==(len(b),len(b.splitlines()))
appendix_wiki=appendix_review['current_wiki_rechecks'];verify_recorded_source_hash(p/appendix_wiki['source_path_relative_to_plan'],appendix_wiki['source_sha256'])
appendix_wiki_text=(p/appendix_wiki['source_path_relative_to_plan']).read_text();appendix_wiki_heads=list(re.finditer(r'(?m)^--- (.+?) ---\s*$',appendix_wiki_text))
assert not appendix_wiki['whole_container_read'] and [row['decoded_topic'] for row in appendix_wiki['topics']]==['빅포레스트_거리.txt','서울.txt','솔트미러.txt','스타일지구.txt','인터렉션.txt','제제.txt','크로멜로.txt','피스풀.txt','8도_지방.txt']
for row in appendix_wiki['topics']:
 i,h=next((i,h) for i,h in enumerate(appendix_wiki_heads) if unicodedata.normalize('NFC',unquote(h[1]))==row['decoded_topic']);b=appendix_wiki_text[h.start():appendix_wiki_heads[i+1].start() if i+1<len(appendix_wiki_heads) else len(appendix_wiki_text)].strip()
 assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and (row['chars'],row['lines'])==(len(b),len(b.splitlines()))
assert (appendix_review['whole_documents_read'],appendix_review['primary_topics_whole_rechecked'],appendix_review['wiki_topics_whole_rechecked'],appendix_review['map_text_guides'],appendix_review['actual_complete_map_images_delivered'])==(1,9,9,3,0)
assert appendix_review['versions']['World']=='v0.80' and appendix_review['versions']['Design']=='v1.11' and appendix_review['document5_whole_review_complete'] and appendix_review['all_six_versioned_plans_whole_reviewed']
assert (appendix_review['foundational_candidates_cumulative_whole_reviews'],appendix_review['foundational_candidates_semantic_pending'],appendix_review['additional_registered_whole_documents'])==(7,1,110)
assert appendix_review['new_mechanical_parameter_values']==[] and appendix_review['limited_source_arithmetic_checks']==0 and appendix_review['new_related_novels_whole_read']==0
for flag in ['all_glossary_entries_distinct_canonical_terms','all_glossary_entry_provenance_verified','all_older_unique_sources_reviewed','all_related_novels_reviewed','all_specific_use_profiles_complete','all_setting_sources_inventoried','all_art_maps_and_project_archives_verified','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not appendix_review[flag]
appendix_ev=evidence['foundational_world_bible_appendix_review'];assert (appendix_ev['document5_prefix_lines_reviewed'],appendix_ev['document5_suffix_lines_pending'],appendix_ev['major_sections'],appendix_ev['glossary_entry_occurrences'])==(2374,0,21,484)
assert appendix_ev['document5_whole_review_complete'] and not appendix_ev['all_glossary_entry_provenance_verified'] and not appendix_ev['actual_participant_playtest']
d['current_foundational_world_bible_appendix_review']={'World':'v0.80','Design':'v1.11',**appendix_ev}


# Time-order source and original Core container: duplicate coverage is not new works.
import csv,io,collections
time_order_review=legacy_coherence['foundational_core_time_order_csv_review'];time_order_source=time_order_review['snapshot']
verify_recorded_source_hash(p/time_order_source['path_relative_to_plan'],time_order_source['sha256'])
time_order_raw=(p/time_order_source['path_relative_to_plan']).read_bytes();time_order_text=time_order_raw.decode()
assert (len(time_order_raw),len(time_order_text),len(time_order_text.splitlines()))==(274382,119760,1316)
assert time_order_source['whole_document_read'] and time_order_source['semantic_review_complete']
time_order_reader=csv.reader(io.StringIO(time_order_text));time_order_rows=[];time_order_physical=[];time_order_last=0
for row in time_order_reader:
 time_order_rows.append(row);time_order_physical.append([time_order_last+1,time_order_reader.line_num]);time_order_last=time_order_reader.line_num
assert time_order_rows[0]==time_order_review['header'] and len(time_order_rows)==112 and set(map(len,time_order_rows))=={7}
assert (time_order_review['logical_data_rows'],time_order_review['columns'],time_order_review['era_separator_rows'],time_order_review['episode_body_rows'],time_order_review['editorial_note_rows'])==(111,7,8,103,87)
assert sum(bool(row[2]) for row in time_order_rows[1:])==103 and len({row[2] for row in time_order_rows[1:] if row[2]})==103 and sum(bool(row[4]) for row in time_order_rows[1:])==87
assert time_order_review['missing_title_topic']=='0053' and [row[2] for row in time_order_rows[1:] if row[2] and not row[5]]==['0053']
assert [i for i,row in enumerate(time_order_rows[1:],1) if '\x08' in ''.join(row)]==time_order_review['backspace_control_character_rows']==[19,58,69,76,97,101]
time_core=time_order_review['primary_container_closure'];time_core_path=p/time_core['source_path_relative_to_plan'];verify_recorded_source_hash(time_core_path,time_core['sha256'])
time_core_raw=time_core_path.read_bytes();time_core_text=time_core_raw.decode();time_core_normalized=time_core_path.read_text()
assert (len(time_core_raw),len(time_core_text),len(time_core_text.splitlines()))==(521713,233667,4612)
time_core_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',time_core_text));time_core_nheads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',time_core_normalized))
assert len(time_core_heads)==len(time_core_nheads)==time_core['topic_occurrences']==210 and time_core_heads[0].start()==0
assert len({h[1] for h in time_core_heads})==time_core['unique_topics']==105 and time_core['title_only_unique_topics']==['0101','0102'] and time_core['substantive_unique_topics']==103
time_core_parts=collections.defaultdict(list);time_core_joined=[];time_core_nparts={}
for i,h in enumerate(time_core_heads):
 b=time_core_text[h.start():time_core_heads[i+1].start() if i+1<len(time_core_heads) else len(time_core_text)];time_core_parts[h[1]].append(b);time_core_joined.append(b);row=time_core['occurrence_mapping'][i]
 assert (row['topic'],row['occurrence'],row['text_sha256'],row['chars'],row['start_line'])==(h[1],len(time_core_parts[h[1]]),hashlib.sha256(b.encode()).hexdigest(),len(b),time_core_text[:h.start()].count('\n')+1)
assert ''.join(time_core_joined)==time_core_text and all(len(bs)==2 and bs[0].strip().lstrip('\ufeff')==bs[1].strip().lstrip('\ufeff') for bs in time_core_parts.values())
for i,h in enumerate(time_core_nheads):time_core_nparts[h[1]]=time_core_normalized[h.start():time_core_nheads[i+1].start() if i+1<len(time_core_nheads) else len(time_core_normalized)].strip()
def time_core_norm(value):return re.sub(r'\s+',' ',unicodedata.normalize('NFC',value.lstrip('\ufeff'))).strip()
def time_core_prior(route):
 value=legacy_coherence
 for key in route.split('/')[1:]:value=value[int(key)] if isinstance(value,list) else value[key]
 return value
time_core_reused=time_core['reused_topic_evidence'];time_core_new=time_core['new_whole_topics']
assert len(time_core_reused)==93 and [row['topic'] for row in time_core_new]==['0041','0029','0085','0078','0073','0013','0055','0047','0051','0104','0084','0103']
assert set(time_core_reused)|{row['topic'] for row in time_core_new}==set(time_core_parts)
for topic,refs in time_core_reused.items():
 assert refs and any(time_core_norm(time_core_prior(ref)['text'])==time_core_norm(time_core_nparts[topic]) and (time_core_prior(ref).get('whole_topic_read') or time_core_prior(ref).get('whole_document_read')) for ref in refs)
for row in time_core_new:
 b=time_core_nparts[row['topic']];assert row['whole_topic_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and (row['chars'],row['lines'])==(len(b),len(b.splitlines()))
assert time_core['whole_container_read'] and time_core['whole_semantic_review_complete'] and time_core['duplicate_blocks_equivalent']
assert (time_core['unique_substantive_topics_reused_with_matching_prior_text'],time_core['unique_title_only_topics_reused'],time_core['new_unique_substantive_topics_whole_read'])==(91,2,12)
for flag in ['all_105_topics_have_substantive_body','all_primary_topic_facts_independently_verified','all_specific_use_profiles_complete','actual_participant_reading','actual_participant_playtest']:assert not time_core[flag]
time_core_bodies={}
for topic,b in time_core_nparts.items():
 fields=re.split(r'[ \t]{3,}'+topic+r'[ \t]{3,}',b,maxsplit=1)
 if len(fields)==2:time_core_bodies[topic]=fields[1].strip().strip('"')
assert set(time_core_bodies)=={row[2] for row in time_order_rows[1:] if row[2]}
time_order_group='수평선위원회 AD 이전 기록';time_order_group_start=1;time_order_groups=[]
for i,(cells,row) in enumerate(zip(time_order_rows[1:],time_order_review['row_mapping']),1):
 if cells[0]:
  if i>1:time_order_groups.append({'label':time_order_group,'row_range':[time_order_group_start,i-1]})
  time_order_group=cells[0];time_order_group_start=i
 assert (row['logical_data_row'],row['physical_line_range'],row['cells'],row['source_group'])==(i,time_order_physical[i],cells,time_order_group) and row['decision']
 if cells[2]:
  assert row['kind']=='episode' and row['topic']==cells[2] and row['body_sha256']==hashlib.sha256(cells[6].encode()).hexdigest() and row['body_equivalent_to_primary_after_whitespace_normalization'] and time_core_norm(cells[6])==time_core_norm(time_core_bodies[cells[2]])
  assert row['body_review']==('reused_whole_topic' if cells[2] in time_core_reused else 'new_whole_topic')
 else:assert row['kind']=='era_separator'
time_order_groups.append({'label':time_order_group,'row_range':[time_order_group_start,111]});assert time_order_review['groups']==time_order_groups and len(time_order_groups)==9
assert len(time_order_review['row_mapping'])==111 and time_order_review['all_103_bodies_equivalent_to_primary_after_whitespace_normalization']
assert [row['logical_data_row'] for row in time_order_review['expanded_passages']]==[67,68] and time_order_review['expanded_passage_count']==2
for row in time_order_review['expanded_passages']:
 b=time_order_rows[row['logical_data_row']][3];assert row['whole_passage_read'] and row['text']==b and row['sha256']==hashlib.sha256(b.encode()).hexdigest() and row['chars']==len(b) and row['decision'] and not row['counted_as_separate_whole_novel']
for ID,path,expected in [('LEG-FOUND-08',time_order_source['path_relative_to_plan'],time_order_source['sha256']),('LEG-FOUND-09',time_core['source_path_relative_to_plan'],time_core['sha256'])]:
 row=next(row for row in additional_procurement if row['id']==ID);assert row['whole_document_read'] and row['source_relative_to_plan']==path and row['sha256']==expected and row['bytes']==(p/path).stat().st_size
assert (time_order_review['whole_documents_read'],time_order_review['foundational_candidates_cumulative_whole_reviews'],time_order_review['foundational_candidates_semantic_pending'],time_order_review['additional_registered_whole_documents'])==(2,8,0,112)
assert time_order_review['versions']['World']=='v0.81' and time_order_review['versions']['Design']=='v1.12' and time_order_review['new_related_novels_whole_read']==0 and time_order_review['new_mechanical_parameter_values']==[] and time_order_review['limited_source_arithmetic_checks']==0
for flag in ['all_older_unique_sources_reviewed','all_setting_sources_inventoried','all_primary_topic_facts_independently_verified','all_related_novels_reviewed','all_specific_use_profiles_complete','chronological_group_order_is_strict_event_date_order','current_engine_changed','old_100point_build_rewritten','actual_participant_reading','actual_participant_playtest','actual_async_community_test']:assert not time_order_review[flag]
time_order_ev=evidence['foundational_core_time_order_csv_review'];assert (time_order_ev['logical_data_rows'],time_order_ev['episode_body_rows'],time_order_ev['primary_unique_topics'],time_order_ev['primary_topic_occurrences'])==(111,103,105,210)
assert time_order_ev['primary_container_whole_read'] and not time_order_ev['actual_participant_playtest'] and time_order_ev['pending_world_decisions']==time_order_review['pending_world_decisions']
d['current_foundational_core_time_order_csv_review']={'World':'v0.81','Design':'v1.12',**time_order_ev}

record_quarantine=legacy_coherence['record_containment_profile_review']
assert record_quarantine['versions']=={'Core':'v0.42','Sheet':'v0.37','World':'v0.81','Design':'v1.13'}
assert record_quarantine['new_primary_topics_whole_read_count']==0 and not record_quarantine['actual_participant_playtest']
verify_recorded_source_hash(p/record_quarantine['source_path_relative_to_plan'],record_quarantine['source_sha256'])
assert [x['id'] for x in record_quarantine['primary_topics_rechecked']]==['0007','0034','0038']
record_source_text=(p/record_quarantine['source_path_relative_to_plan']).read_text()
record_source_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',record_source_text))
for topic in record_quarantine['primary_topics_rechecked']:
 assert topic['whole_topic_rechecked'] and hashlib.sha256(topic['text'].encode()).hexdigest()==topic['normalized_text_sha256']
 topic_index=next(i for i,m in enumerate(record_source_heads) if m[1]==topic['id'])
 actual_topic_text=record_source_text[record_source_heads[topic_index].start():record_source_heads[topic_index+1].start()]
 assert actual_topic_text==topic['text']
assert local['record_containment_profile']=='REC-QUAR-F1' and local['non_replaying_copy_condition_cases']==32 and local['record_handover_condition_cases']==16
assert 'REC-QUAR-F1' in core and 'REC-QUAR-F1' in (o/'12_룰시트와캐릭터시트.md').read_text()
d['current_record_containment']={'id':'REC-QUAR-F1','Core':'v0.42','Sheet':'v0.37','Design':'v1.13','checks_passed':local['checks_passed'],'copy_condition_cases':32,'handover_condition_cases':16,'actual_participant_playtest':False,'all_matting_transformation_and_treatment_complete':False}
clinical_review=legacy_coherence['implant_clinical_service_review']
assert clinical_review['versions']=={'Core':'v0.43','Sheet':'v0.38','World':'v0.81','Design':'v1.14'}
assert clinical_review['new_primary_topics_whole_read_count']==0 and not clinical_review['all_implants_and_medicine_complete']
clinical_source=clinical_review['primary_source'];clinical_wiki=clinical_review['wiki_source']
for entry in [clinical_source,clinical_wiki]:verify_recorded_source_hash(p/entry['path_relative_to_plan'],entry['sha256'])
clinical_raw=(p/clinical_source['path_relative_to_plan']).read_text();clinical_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',clinical_raw))
for e in clinical_source['topics']:
 i=next(i for i,m in enumerate(clinical_heads) if m[1]==e['id'])
 assert e['text']==clinical_raw[clinical_heads[i].start():clinical_heads[i+1].start()] and e['whole_topic_rechecked'] and hashlib.sha256(e['text'].encode()).hexdigest()==e['text_sha256']
clinical_wiki_raw=(p/clinical_wiki['path_relative_to_plan']).read_text()
for e in clinical_wiki['topics']:assert e['text'] in clinical_wiki_raw and e['whole_topic_rechecked'] and hashlib.sha256(e['text'].encode()).hexdigest()==e['text_sha256']
assert len(clinical_source['topics'])==5 and len(clinical_wiki['topics'])==10
clinical_results=results['임플란트_검증.py']
assert clinical_results['clinical_condition_cases']==64 and clinical_results['clinical_completion_cases']==1600 and clinical_results['body_assessment_cases']==6
assert 'IMPLANT-SERVICE-C1' in core and 'IMPLANT-SERVICE-C1' in (o/'12_룰시트와캐릭터시트.md').read_text()
d['current_implant_clinical_service']={'id':'IMPLANT-SERVICE-C1','Core':'v0.43','Sheet':'v0.38','Design':'v1.14','checks_passed':clinical_results['checks_passed'],'clinical_condition_cases':64,'clinical_completion_cases':1600,'all_implants_and_medicine_complete':False,'actual_participant_playtest':False}
named_weapon_review=legacy_coherence['smart_gun_wrist_axes_review']
assert named_weapon_review['versions']=={'Core':'v0.44','Sheet':'v0.39','World':'v0.81','Design':'v1.15'}
assert named_weapon_review['new_primary_topics_whole_read_count']==0 and not named_weapon_review['all_guns_and_implants_complete']
assert named_weapon_review['three_forms_decision']['assumed_canonical_forms'] is None
for entry in [named_weapon_review['primary_source'],named_weapon_review['wiki_source']]:verify_recorded_source_hash(p/entry['path_relative_to_plan'],entry['sha256'])
named_weapon_raw=(p/named_weapon_review['primary_source']['path_relative_to_plan']).read_text();named_heads=list(re.finditer(r'(?m)^\ufeff?"?FEWK; (\d{4})k',named_weapon_raw))
for e in named_weapon_review['primary_source']['topics']:
 i=next(i for i,m in enumerate(named_heads) if m[1]==e['id'])
 assert e['text']==named_weapon_raw[named_heads[i].start():named_heads[i+1].start()] and e['whole_topic_rechecked'] and hashlib.sha256(e['text'].encode()).hexdigest()==e['text_sha256']
named_wiki_raw=(p/named_weapon_review['wiki_source']['path_relative_to_plan']).read_text()
for e in named_weapon_review['wiki_source']['topics']:assert e['text'] in named_wiki_raw and e['whole_topic_rechecked'] and hashlib.sha256(e['text'].encode()).hexdigest()==e['text_sha256']
assert len(named_weapon_review['primary_source']['topics'])==3 and len(named_weapon_review['wiki_source']['topics'])==5
named_results=results['장비_검증.py']
assert named_results['smart_source_cases']==96 and named_results['smart_fire_cases']==21600 and named_results['wrist_axe_condition_cases']==16
assert 'CROC-C1' in core and 'WRIST-AXE-C1' in core
d['current_named_weapons']={'Core':'v0.44','Sheet':'v0.39','Design':'v1.15','checks_passed':named_results['checks_passed'],'smart_source_cases':96,'smart_fire_cases':21600,'wrist_axe_condition_cases':16,'three_forms_owner_decision_pending':True,'all_guns_and_implants_complete':False,'actual_participant_playtest':False}
result={'docs':len(docs),'links':len(links),'missing':missing,'general_checks':55,'special_checks':results['스페셜_검증.py']['checks_passed'],'tarot_checks':62,'whole_duels':300000,'dimension_profile_checks':dimension['checks_passed'],'coffin_entry_cases':32,'coffin_return_cases':208,'coffin_receiver_cases':5408,'coffin_operator_cases':256,'compatible_destination_cases':2880,'two_realm_sequences':169,'finite_lease_states':78,'current_numbered_related_novels':18,'current_related_novel_hashes_verified':18,'debt_story_limited_arithmetic_examples_checked':5,'focused':358,'pending':0,'gear_checks':results['장비_검증.py']['checks_passed'],'implant_checks':results['임플란트_검증.py']['checks_passed'],'interaction_checks':results['고유효과_검증.py']['checks_passed'],'body_compatibility_checks':26,'body_compatibility_cases':672,'local_effect_computation_checks':local['checks_passed'],'appendix_reference_checks':reference['checks_passed'],'scenario_tools_checks':scenario['checks_passed'],'online_checks':online['checks_passed'],'NPC_checks':NPC['checks_passed'],'GM_checks':GM['checks_passed'],'team_checks':team['checks_passed'],'legacy_arithmetic_checks':legacy['checks_passed'],'scene_checks':scene['checks_passed'],'transport_checks':road['checks_passed'],'transport_feasibility_cases':road['feasibility_cases'],'current_doc_hashes':len(files),'old_archives':'exact hashes verified','time_checks':temporal['checks_passed'],'real_playtest':False,'novel001_whole_document_read':True,'novel001_full_setting_verified':False,'goal':g['goal_status']}
result['large_facility_checks']=facility['checks_passed']
result['large_facility_command_boundary_cases']=facility['command_boundary_cases']
result['large_facility_common_attack_boundary_cases']=facility['common_attack_boundary_cases']
result['large_facility_percentile_cases']=facility['percentile_cases']
result['cyberpunk_pack_glossary_term_heading_entries_mapped']=259
result['cyberpunk_pack_glossary_arithmetic_checks']=14
result['cyberpunk_pack_deck_audit_major_sections_mapped']=27
result['cyberpunk_pack_deck_audit_arithmetic_checks']=12
result['semantic_topic_routes_checked']=reference['semantic_topic_routes_checked']
result['existing_wrong_topic_routes_rejected']=reference['existing_wrong_topic_routes_rejected']
result['cyberpunk_pack_world_correction_major_sections_mapped']=27
result['cyberpunk_pack_correction_detailed_issue_blocks_mapped']=39
result['cyberpunk_pack_correction_label_rows_mapped']=17
result['cyberpunk_pack_world_correction_arithmetic_checks']=16
result['framework_foundation_major_sections_mapped']=40
result['framework_foundation_arithmetic_checks']=13
result['framework_character_combat_major_sections_mapped']=47
result['framework_character_combat_arithmetic_checks']=23
result['framework_resource_growth_major_sections_mapped']=43
result['framework_resource_growth_arithmetic_checks']=22
result['framework_team_NPC_session_major_sections_mapped']=40
result['framework_team_NPC_session_arithmetic_checks']=23
assert len(docs)==11, '본문문서수와외부도구출처수를분리해야함'
result['framework_final_reader_major_sections_mapped']=63
result['framework_final_reader_arithmetic_checks']=21
result['first_relationship_chronology_major_sections_mapped']=25
result['first_relationship_chronology_arithmetic_checks']=14
result['first_catalog_major_sections_mapped']=43
result['first_catalog_arithmetic_checks']=10
result['first_life_uncertainty_major_sections_mapped']=46
result['first_life_uncertainty_arithmetic_checks']=11
result['first_encyclopedia_scene_glossary_major_sections_mapped']=43
result['first_encyclopedia_scene_glossary_arithmetic_checks']=11
result['first_address_nuance_motif_major_sections_mapped']=93
result['first_address_nuance_motif_arithmetic_checks']=6
result['first_letters_narrator_translation_readme_major_sections_mapped']=127
result['first_letters_narrator_translation_readme_arithmetic_checks']=8
result['first_protagonist_supernatural_profiles_major_sections_mapped']=103
result['vessel_technical_handover_checks']=27
result['foundational_chronology_rows_mapped']=44
result['foundational_source_candidates_reviewed']=6
result['foundational_source_candidates_pending']=2
result['foundational_chronology_arithmetic_checks']=8
result['foundational_world_bible_intentions_sections_mapped']=16
result['foundational_world_bible_intentions_chapters_mapped']=48
result['foundational_world_bible_outline_sections_mapped']=18
result['foundational_world_bible_outline_heading_rows_mapped']=237
result['foundational_world_bible_outline_arithmetic_checks']=8
result['foundational_world_bible_prose_sections_mapped']=35
result['foundational_world_bible_prose_embedded_cases_mapped']=9
result['foundational_world_bible_prose_arithmetic_checks']=3
result['foundational_world_bible_laws_sections_mapped']=36
result['foundational_world_bible_laws_case_occurrences']=8
result['foundational_world_bible_laws_unique_case_bodies']=7
result['foundational_world_bible_document5_prefix_reviewed_lines']=2374
result['foundational_world_bible_document5_pending_lines']=0
result['named_anchor_links_checked']=len(named_anchor_links)
result['missing_named_anchors']=missing_named_anchors
result['second_edition_whole_documents_reviewed']=9
result['second_edition_whole_reviews_pending']=0
result['mobius_night_shift_new_whole_novels_read']=1
result['mobius_night_shift_source_arithmetic_examples_checked']=8
result['noene_family_new_whole_related_novels_read']=2
result['noene_family_limited_arithmetic_examples_checked']=10
result['ghost_cafe_new_whole_related_novels_read']=1
result['ghost_cafe_limited_arithmetic_examples_checked']=10
result['intro_identity_source_issues_reviewed']=15
result['intro_identity_participant_documents_written']=4
result['keyword_data_rows_reviewed']=984
result['keyword_data_rows_remaining']=0
result['keyword_focused_issues_reviewed']=60
result['keyword_table_whole_document_reviewed']=True
result['registered_additional_whole_documents']=117
result['core_basic_topics_matched']=105
result['first_draft_editorial_comments_reviewed']=21
result['first_draft_whole_document_read']=True
result['first_draft_prefix_lines_reviewed']=3722
result['first_draft_distinct_physical_lines_reviewed']=3722
result['first_draft_not_whole_read_lines']=0
result['first_draft_prefix_issues_reviewed']=196
result['keyword_fraction_corrections_checked']=fraction_corrections_checked
result['uploaded_source_file_hashes_verified']=14
result['uploaded_new_whole_documents_read']=4
result['uploaded_scope_and_semantic_pending_distinct_contents']=3
result['reader_start_preset_skill_cells_checked']=36
result['human_trial_preparation_modes']=4
result['actual_trial_evidence_received']=0
result['actual_participant_playtest']=False
result['current_worktree_hash_revalidation_pending_ids']=[]
result['full_current_worktree_revalidation_complete']=True
result['current_reference_hashes_verified']=358
result['current_reference_hash_changes']=0
result['current_reference_hash_capture_id']=current_reference_audit['id']
result['other_source_hash_audit_pending_ids']=source_hash_audit_pending_ids
result['source_paths_current_hash_revalidation_pending']=sorted(source_paths_revalidation_pending)
result['audit_mode']='local_package' if local_package_only else 'package_and_available_original_sources'
book_product_review=legacy_coherence['crowdfunding_book_readiness_review']
assert book_product_review==evidence['crowdfunding_book_readiness_review']
# The readiness review identifies the preceding draft; the content pass preserves that input lineage.
content_pass=legacy_coherence['product_content_pass']
assert content_pass==evidence['product_content_pass']
reader_finalization=json.loads((v/'독자편집_대조.json').read_text())
reader_before=json.loads((v/reader_finalization['before_snapshot']).read_text())
reader_before_files={row['path']:row for row in reader_before['files']}
runner_expansion=json.loads((v/'러너와튜터리얼_대조.json').read_text())
book_editing=json.loads((v/'캐릭터와시나리오북_편집.json').read_text())
book_before=json.loads((v/book_editing['before_snapshot']).read_text())
book_before_files={row['path']:row for row in book_before['files']}
assert len(book_before_files)==9
for name,row in book_before_files.items():
 assert hashlib.sha256(row['text'].encode()).hexdigest()==row['sha256']==book_editing['input_hashes'][name]==runner_expansion['output_hashes'][name]
verify_recorded_source_hash(v/'러너와튜터리얼_대조.json',book_editing['previous_finalization_sha256'])

pre_expansion=json.loads((v/runner_expansion['before_snapshot']).read_text())
pre_expansion_files={row['path']:row for row in pre_expansion['files']}
assert len(pre_expansion_files)==7
for row in pre_expansion_files.values():assert hashlib.sha256(row['text'].encode()).hexdigest()==row['sha256']
assert len(reader_before_files)==6
for name,row in reader_before_files.items():
 assert hashlib.sha256(row['text'].encode()).hexdigest()==row['sha256']==reader_finalization['input_hashes'][name]
 assert pre_expansion_files[name]['sha256']==reader_finalization['output_hashes'][name]
 verify_recorded_source_hash(o/name,book_editing['output_hashes'][name])
assert len(reader_finalization['support_comparison'])==22
assert all(row['result']=='consistent_after_edits' for row in reader_finalization['support_comparison'])
assert len([row for row in reader_finalization['reader_structure_review']['11_WorldLorebook.md'] if re.match(r'\d+\.',row['title'])])==77
assert not reader_finalization['human_tests_performed'] and not reader_finalization['final_layout_performed']
if g['goal_status']=='complete':
 assert reader_finalization['status']=='complete' and not reader_finalization['required_remaining_actions']
 assert reader_finalization['verification']['status']=='passed' and reader_finalization['verification']['current_input_suites_verified']==22
for snapshot in book_product_review['source_snapshots']:
 name=snapshot['path_relative_to_fifth']
 if name in content_pass['input_book_hashes']:
  assert snapshot['sha256']==content_pass['input_book_hashes'][name]
 elif name=='01_텀블벅_이지룰_초안.md':
  assert hashlib.sha256(reader_before_files[name]['text'].replace('[Core v0.49]','[Core v0.48]').encode()).hexdigest()==snapshot['sha256']
 else:
  assert reader_before_files[name]['sha256']==snapshot['sha256']
for name,sha in content_pass['output_book_hashes'].items():assert reader_before_files[name]['sha256']==sha
campaign_checks=json.loads((v/'기본캠페인_검증결과.json').read_text())
for name,sha in campaign_checks['artifacts_sha256'].items():verify_recorded_source_hash(o/name,sha)
assert campaign_checks['catalog_items']==20 and campaign_checks['starting_kits']==3
assert (campaign_checks['income_oyat'],campaign_checks['expenses_oyat'],campaign_checks['remaining_oyat'])==(12,9,3)
assert not campaign_checks['actual_participant_playtest'] and not content_pass['all_CF_findings_resolved']
result['product_content_pass']={'Core':'0.49','World':'1.00','Design':'1.38','catalog_items':20,'starting_kits':3,'default_campaigns_written':1,'NPCs':3,'campaign_checks_passed':campaign_checks['checks_passed'],'actual_participant_playtest':False}
sample=json.loads((v/'대표지면_검수.json').read_text())
assert sample['pages']==7 and sample['visual_pages_reviewed']==list(range(1,8))
verify_recorded_source_hash(o/sample['pdf_path_relative_to_fifth'],sample['pdf_sha256'])
verify_recorded_source_hash(v/'대표지면_생성.py',sample['renderer_sha256'])
assert sample['source_revision_is_historical_after_reader_finalization'] and not sample['current_manuscript_layout_preview']
for name,sha in sample['input_book_hashes'].items():assert reader_before_files[name]['sha256']==sha
for name,sha in sample['page_png_sha256'].items():verify_recorded_source_hash(v/'대표지면_QA'/name,sha)
assert len(sample['page_png_sha256'])==7
assert all(not x['out_of_page_spans'] and not x['text_overlap_pairs'] for x in sample['automated_page_bounds'])
assert not any(sample[k] for k in ['final_layout_complete','actual_participant_reading','remote_publication_performed'])
assert content_pass['representative_sample']['pdf_sha256']==sample['pdf_sha256']
result['representative_publication_sample']={'pages':7,'visually_reviewed_pages':sample['visual_pages_reviewed'],'maps':1,'out_of_page_spans':0,'text_overlap_pairs':0,'pdf_sha256':sample['pdf_sha256'],'final_layout_complete':False,'actual_participant_reading':False}

assert book_product_review['unreviewed_uploaded_distinct_contents']==legacy_coherence['uploaded_settings_inventory']['scope_and_semantic_pending_distinct_contents']==3
assert not any(book_product_review[flag] for flag in ['Katie2draft_full_review_required','unread_contents_marked_as_read','whole_two_books_new_semantic_review_complete','book_manuscripts_changed_this_review','basic_engine_changed','actual_participant_reading','actual_participant_playtest','actual_async_community_test','publication_ready_confirmed','crowdfunding_launch_ready_confirmed','physical_production_or_campaign_posting_performed'])
result['crowdfunding_book_readiness_review']={'id':book_product_review['id'],'Design':book_product_review['Design'],'reviewed_snapshot_hashes_verified':len(book_product_review['source_snapshots']),'findings':len(book_product_review['findings']),'publication_ready_confirmed':False,'actual_participant_playtest':False,'Katie2draft_full_review_required':False}
result['reader_finalization']={'id':reader_finalization['id'],'output_manuscripts_verified':6,'semantic_support_topics':22,'world_chapters_reviewed':77,'goal_status':g['goal_status'],'human_tests_performed':False,'final_layout_performed':False}
runner_checks=json.loads((v/'러너와튜터리얼_검증결과.json').read_text())
assert runner_expansion['status']=='complete' and runner_expansion['verification']['status']=='passed'
assert len(runner_expansion['output_hashes'])==9
for edit in runner_expansion['metadata_paragraphs_relocated']:
 current_text=(o/edit['file']).read_text()
 current_notes=current_text.split('<a id="fewk-editorial-source-notes"></a>',1)[1] if edit['file']!='13_입문시나리오.md' else current_text.split('## 편집 참고',1)[1]
 assert edit['before'] in current_notes, (edit['file'],edit['chapter'])
for name,sha in runner_expansion['output_hashes'].items():assert book_before_files[name]['sha256']==sha
for name,sha in book_editing['output_hashes'].items():verify_recorded_source_hash(o/name,sha)
assert book_editing['status']=='complete' and book_editing['verification']['status']=='passed'
assert (book_editing['character_count'],book_editing['tutorial_count'],book_editing['player_handout_count'])==(12,6,6)
for name,sha in runner_checks['artifacts_sha256'].items():verify_recorded_source_hash(o/name,sha)
assert (runner_checks['runners'],runner_checks['complete_bodies'],runner_checks['tutorial_scenarios'])==(12,24,6)
assert not runner_checks['actual_participant_playtest'] and not runner_expansion['final_layout_performed']
result['runner_tutorial_expansion']={'id':runner_expansion['id'],'status':'complete','runners':12,'principal':6,'reserve':6,'tutorial_scenarios':6,'numeric_checks':runner_checks['checks_passed'],'current_manuscripts_verified':9,'historical_reader_finalization_preserved':True,'human_tests_performed':False}
d['current_runner_tutorial_expansion']=result['runner_tutorial_expansion']
result['character_scenario_book_editing']={'id':book_editing['id'],'status':'complete','character_book_version':'1.1','scenario_book_version':'1.1','characters':12,'scenarios':6,'public_handouts':6,'previous_completed_hashes_preserved':9,'current_input_checks':runner_checks['checks_passed'],'human_tests_performed':False,'final_layout_performed':False}
d['current_character_scenario_book_editing']=result['character_scenario_book_editing']
(v/'자료_구조검증.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(v/'원고묶음_구조검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
