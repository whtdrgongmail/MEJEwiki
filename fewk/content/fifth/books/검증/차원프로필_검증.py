"""Declared worksheet/state boundaries for leased bodies and gear restrictions.
No participant trial, no unverified canon or full campaign balance claim.
Coffin scope: actual receiver state and assisted operator action budget;
not biological simulation or a full local character action scheduler.
"""
from pathlib import Path
from copy import deepcopy
import json,hashlib
v=Path(__file__).parent;o=v.parent
p=json.loads((v/'차원프로필.json').read_text());intro=json.loads((v/'입문_프로필.json').read_text())
checks=[]
def check(n,c):
 assert c,n
 checks.append(n)
def prepared(skill,body_bonus,situation):return max(1,min(99,skill+body_bonus+situation))
def authorized_controller(body,person,safe,valid):
 if not safe or not valid or body['controller'] is not None:return False
 body['controller']=person;return True
def release(body):body['controller']=None
def damage(body,n):body['hp']=max(0,body['hp']-max(0,n-body['armor']))
sae=p['profiles']['CAMP-SAE-TEST'];orc=p['profiles']['CAMP-ORC-TEST']
body=deepcopy(sae['body']);base={'P-S1':12,'P-S2':12};people={'P-S1':{'해킹':70,'사격':30},'P-S2':{'해킹':10,'사격':70}}
check('approved safe empty-body control',authorized_controller(body,'P-S1',True,True))
check('owner and current controller distinct',body['owner']=='REG-SAE-TEST' and body['controller']=='P-S1')
check('second simultaneous controller rejected',not authorized_controller(body,'P-S2',True,True))
check('no prior skill inheritance',prepared(people['P-S1']['해킹'],0,0)==70)
body['shield']-=1;damage(body,4)
check('printed body damage HP9 to5 armor0',body['hp']==5)
check('printed shield one tozero',body['shield']==0)
body['treated_since_full_recovery']=True;before=deepcopy(body);release(body)
check('release preserves injury/charge/treatment',all(body[k]==before[k] for k in ['hp','shield','treated_since_full_recovery']))
check('approved next controller',authorized_controller(body,'P-S2',True,True))
check('next user skill own10 not prior70',prepared(people['P-S2']['해킹'],0,0)==10)
check('next user reads sameHP5 shield0',body['hp']==5 and body['shield']==0)
check('both original bodies untouched',base=={'P-S1':12,'P-S2':12})
check('shared damaged body no treatment reset',body['treated_since_full_recovery'] is True)
release(body)
check('combat handoff not supplied',not authorized_controller(body,'P-S1',False,True))
check('unauthorized handoff rejected',not authorized_controller(body,'P-S1',True,False))
check('rejected control leaves owner/body unchanged',body['controller'] is None and body['hp']==5 and body['owner']=='REG-SAE-TEST')
# All finite starting HP/charge states preserve physical state under legal identity changes.
finite=0
for hp in range(13):
 for charge in range(3):
  for treated in (False,True):
   b=deepcopy(sae['body']);b.update(hp=hp,shield=charge,treated_since_full_recovery=treated)
   assert authorized_controller(b,'P-S1',True,True);release(b);assert authorized_controller(b,'P-S2',True,True)
   assert (b['hp'],b['shield'],b['treated_since_full_recovery'])==(hp,charge,treated)
   finite+=1
check('78 injury/charge/treatment states preserve across controllers',finite==78)
damage(body,5);release(body);assert authorized_controller(body,'P-S1',True,True)
check('HP0 still HP0 after new user controls it',body['hp']==0 and body['controller']=='P-S1')
check('ordinary person skill remains distinct from body resistance',people['P-S2']['해킹']==10 and body['resistance']==50)
check('same situation+20 used with new user',prepared(10,0,20)==30)
check('negative situation still feasible-risk clamp1',prepared(10,0,-20)==1)
check('high situational target cap99',prepared(95,0,20)==99)
# Independent expected artifacts/state: gear stays on base while approved local tool is present.
base_items={'GUN-O':{'ammo':12},'SHIELD-O':{'charge':2},'IMPLANT-O':{'active_on_base':True}}
base_before=deepcopy(base_items);local_items={orc['local_weapon']['id']:deepcopy(orc['local_weapon'])}
check('external gun absent locally','GUN-O' not in local_items)
check('external shield absent locally','SHIELD-O' not in local_items)
check('external implant not copied','IMPLANT-O' not in local_items)
check('external state preserved by blocked import',base_items==base_before)
check('local authorized melee has same skill',local_items['LOCAL-O-M1']['skill']=='격투')
check('local tool uses same contact1m',local_items['LOCAL-O-M1']['reach_m']==1)
check('local supplied damage6',local_items['LOCAL-O-M1']['damage']==6)
check('local gear source marked not transported',local_items['LOCAL-O-M1']['permission']=='authorized_local_loan')
check('no phantom shield/armor',orc['armor_provided']==orc['shield_provided']==0)
check('no mechanical ammo invented for contact tool',local_items['LOCAL-O-M1']['ammo'] is None)
check('same P body baseline',intro['body']['hp_max']==12 and intro['body']['round_seconds']==5)
check('two controller skills remain unchanged',people=={'P-S1':{'해킹':70,'사격':30},'P-S2':{'해킹':10,'사격':70}})
check('forbidden gear no probability bypass',orc['import_external_gear'] is False)
check('known local rule names explicit threshold',orc['violation']=='repeat_explicit_weapon_threat_after_warning_in_play_zone')
bans=set();rights={'OTHER-A','OTHER-B'};original_hp=12;ego=10;local_hp=8
bans.add(('P-O1',orc['realm_id']))
check('ban targets person and named realm',('P-O1','ORC-TEST') in bans)
check('no other person inherited ban',('P-O2','ORC-TEST') not in bans)
check('new body does not clear person ban',('P-O1','ORC-TEST') in bans)
check('other world rights retained',rights=={'OTHER-A','OTHER-B'} and orc['other_realm_rights_affected'] is False)
check('ban not original/local/ego damage',(original_hp,local_hp,ego)==(12,8,10) and orc['automatic_base_damage']==orc['automatic_ego_loss']==0)
check('ban not automatic safe return',orc['automatic_return'] is False)
check('play zone distinct from banned realm',orc['play_zone_id']!=orc['realm_id'])
check('no real participant claim',p['actual_participant_playtest'] is False)
# Declared common-IO worksheet model; actual fabrication/medical/network behavior
# is not simulated. Conditions and state preservation are the tested contract.
import itertools
cof=p['profiles']['CAMP-COF-TEST']
class CoffinTrial:
 def __init__(self):
  self.destination=cof['realm_id'];self.destinations=deepcopy(cof['compatible_destinations'])
  self.saved_by_realm={};self.visited_realms=set();self.constructed_realms=set();self.storage_slots=cof['stored_body_slot_count']
  self.active=cof['base_body_id'];self.local=None;self.base_hp=cof['base_hp'];self.base_location=cof['original_location'];self.exit_clear=True
  self.base_alive=cof['base_alive'];self.route_online=cof['route_online'];self.receiver_enabled=cof['receiver_enabled'];self.support=deepcopy(cof['support_operator'])
  self.batches=cof['construction_batches'];self.ampoules=cof['first_entry_ampoules'];self.revision=0
  self.ego=10;self.skills={'격투':70,'사격':70};self.bans=set()
 @property
 def saved(self):return self.saved_by_realm.get(self.destination)
 @property
 def visited(self):return self.destination in self.visited_realms
 @property
 def constructed(self):return self.destination in self.constructed_realms
 def enter(self,conditions,expected_revision=None,destination=None):
  if expected_revision is not None and expected_revision!=self.revision:return False
  target=self.destination if destination is None else destination
  if self.active!=cof['base_body_id'] or not self.base_alive or self.base_hp<=0 or not self.route_online or not all(conditions.get(k,False) for k in cof['entry_requirements']):return False
  profile=self.destinations.get(target)
  if profile is None or profile['io']!=cof['io'] or not all(profile.get(k,False) for k in ('charted','compatible','brain_updated','permission')):return False
  ids=[x['local_body_id'] for x in self.destinations.values()]
  if len(ids)!=len(set(ids)) or cof['base_body_id'] in ids:return False
  if (cof['person_id'],target) in self.bans:return False
  saved=self.saved_by_realm.get(target);constructed=target in self.constructed_realms
  batch_cost=cof['recall_batch_cost'] if saved is not None else cof['construction_batch_cost']
  ampoule_cost=0 if target in self.visited_realms else cof['first_entry_ampoule_cost']
  if self.batches<batch_cost or self.ampoules<ampoule_cost:return False
  if saved is None and constructed:return False
  # Reserve supported storage for each actual body, including the active body.
  # The ordinary profile does not silently gain a second slot on another visit.
  if len(self.constructed_realms)+(0 if constructed else 1)>self.storage_slots:return False
  local=deepcopy(saved) if saved is not None else deepcopy(profile['initial_local_body'])
  self.destination=target;self.local=local;self.saved_by_realm.pop(target,None);self.active=profile['local_body_id']
  self.batches-=batch_cost;self.ampoules-=ampoule_cost;self.visited_realms.add(target);self.constructed_realms.add(target);self.revision+=1
  return True
 def support_ready(self):
  s=self.support;pc_bodies={cof['base_body_id']}|{x['local_body_id'] for x in self.destinations.values()}
  return bool(s and s.get('id') and s.get('person_id') and s.get('body_id')
   and s['person_id']!=cof['person_id'] and s['body_id'] not in pc_bodies
   and s.get('location')==self.base_location and s.get('alive') and s.get('capable')
   and s.get('authorized') and s.get('connected') and s.get('main_remaining',0)>=cof['support_action_main'])
 def exit(self,link=True,receiver_ready=True,actual_support=False,expected_revision=None):
  if expected_revision is not None and expected_revision!=self.revision:return False
  if self.active!=self.destinations[self.destination]['local_body_id'] or self.local is None or not self.base_alive:return False
  if not self.route_online or not self.receiver_enabled or not link or not receiver_ready:return False
  assisted=self.local['hp']<=0
  if assisted and (not actual_support or not self.support_ready()):return False
  # Voluntary main-action ownership belongs to the common engine; this bounded
  # worksheet models the actual external operator budget for HP0 assistance.
  if assisted:self.support['main_remaining']-=cof['support_action_main']
  self.saved_by_realm[self.destination]=deepcopy(self.local);self.local=None;self.active=cof['base_body_id'];self.revision+=1
  return True
ready={k:True for k in cof['entry_requirements']}
q=CoffinTrial();before=deepcopy(vars(q));missing=dict(ready,charted=False)
check('uncharted realm no commoncoffinentry',not q.enter(missing))
check('rejected uncharted preserves batches/ampoules/body',vars(q)==before)
for key in ['compatible','brain_updated','permission','base_capable']:
 missing=dict(ready);missing[key]=False
 check('missing '+key+' does not start entry',not q.enter(missing) and vars(q)==before)
entry_matrix=0
for flags in itertools.product([False,True],repeat=len(cof['entry_requirements'])):
 x=CoffinTrial();before=deepcopy(vars(x));conditions=dict(zip(cof['entry_requirements'],flags));accepted=x.enter(conditions)
 assert accepted==all(flags)
 if accepted:assert (x.batches,x.ampoules,x.active)==(1,0,cof['local_body_id']) and x.saved is None
 else:assert vars(x)==before
 entry_matrix+=1
check('32 entry condition combinations preserve or consume once',entry_matrix==32)
q=CoffinTrial();q.base_hp=0;before=deepcopy(vars(q))
check('incapacitated base cannot independently startnewbody',not q.enter(ready) and vars(q)==before)
q=CoffinTrial();check('printed firstentry completes',q.enter(ready,expected_revision=0))
check('firstentry consumes onebatch oneampoule',(q.batches,q.ampoules)==(1,0) and q.visited)
check('no active plus saved duplicatebody',q.active==cof['local_body_id'] and q.saved is None)
check('firstbody uses givenHP12',q.local['hp']==cof['new_body_hp']==12)
check('firstbody prepared actual gear12shots2charge',(q.local['ammo'],q.local['shield'])==(12,2))
check('sameactivebody cannot enter a second time',not q.enter(ready))
q.local.update(cof['snapshot_example']);before=deepcopy(vars(q))
check('brokenroute no automatic return',not q.exit(link=False,actual_support=True) and vars(q)==before)
check('unsupportedreceiver no automatic return',not q.exit(receiver_ready=False,actual_support=True) and vars(q)==before)
check('printed normalexit completes',q.exit(expected_revision=1))
check('exit records damagedHP5ammo3shield0',q.saved==cof['snapshot_example'] and q.local is None)
check('baseHP12ego10 and learnedskills unchanged',(q.base_hp,q.ego,q.skills,q.bans)==(12,10,{'격투':70,'사격':70},set()))
check('exit no construction resource recovery',(q.batches,q.ampoules)==(1,0))
check('printed recall uses lastconstructionbatch',q.enter(ready))
check('recall doesnotheal/charge/resupply',q.local==cof['snapshot_example'] and q.saved is None)
check('revisit no firstampoule repeat',(q.batches,q.ampoules)==(0,0))
check('printed secondexit completes',q.exit())
before=deepcopy(vars(q));check('thirdentry no sparebatch rejected',not q.enter(ready) and vars(q)==before)
q=CoffinTrial();q.ampoules=0;before=deepcopy(vars(q))
check('firstvisit without actualampoule rejected',not q.enter(ready) and vars(q)==before)
q=CoffinTrial();assert q.enter(ready);q.local['hp']=0;before=deepcopy(vars(q))
check('HP0 no voluntaryexit',not q.exit() and vars(q)==before)
check('HP0 explicit supportedexit succeeds',q.exit(actual_support=True))
check('HP0 remains0 in saved body',q.saved['hp']==0 and q.base_hp==12)
check('recall HP0 preserves incapacitation',q.enter(ready) and q.local['hp']==0)
check('recalledHP0 still no voluntaryexit',not q.exit())
q=CoffinTrial();assert q.enter(ready);q.base_location='MOVED-COFFIN-C';q.exit_clear=False;q.base_hp=9
check('moved trapped coffin still receives ifrouteworks',q.exit())
check('return targets currentbaseplace not initialdepot',q.base_location=='MOVED-COFFIN-C' and q.active==cof['base_body_id'])
check('return doesnotopenexit orhealpriorbaseinjury',q.exit_clear is False and q.base_hp==9)
check('trapped exit no extraego/globalban',q.ego==10 and q.bans==set())
# All HP0..12, link/receiver/support/access combinations follow the declared
# return predicate while independently checking state/construction conservation.
return_matrix=0
for hp in range(13):
 for link,receiver,support,clear in itertools.product([False,True],repeat=4):
  x=CoffinTrial();assert x.enter(ready);x.local.update(hp=hp,ammo=3,shield=0,treated_since_full_recovery=True);x.exit_clear=clear;x.base_location='ACTUAL-C';x.support['location']='ACTUAL-C';before=deepcopy(vars(x))
  accepted=x.exit(link=link,receiver_ready=receiver,actual_support=support)
  assert accepted==(link and receiver and (hp>0 or support))
  if accepted:
   assert x.active==cof['base_body_id'] and x.local is None and x.saved==before['local']
   assert (x.batches,x.ampoules,x.base_hp,x.ego,x.base_location,x.exit_clear)==(before['batches'],before['ampoules'],before['base_hp'],before['ego'],'ACTUAL-C',clear)
  else:assert vars(x)==before
  return_matrix+=1
check('208 localHP/route/receiver/support/exitclear states preserved',return_matrix==208)
q=CoffinTrial();assert q.enter(ready);before=deepcopy(vars(q))
check('stale parallel exit log rejected',not q.exit(expected_revision=0) and vars(q)==before)
check('supported normalexit updates revision',q.exit(expected_revision=1) and q.revision==2)
check('stale parallel recall log rejected',not q.enter(ready,expected_revision=1))

# Actual receiver state cannot be replaced by caller-supplied booleans.
q=CoffinTrial();q.base_alive=False;before=deepcopy(vars(q))
check('dead base HP12 cannot start new local body',not q.enter(ready) and vars(q)==before)
q=CoffinTrial();assert q.enter(ready);q.base_alive=False;before=deepcopy(vars(q))
check('dead original rejects return despite working receiver and support',not q.exit(actual_support=True) and vars(q)==before)
check('lost original does not kill local or impose reentry ban',q.local['hp']==12 and q.active==cof['local_body_id'] and q.ego==10 and q.bans==set())
q=CoffinTrial();assert q.enter(ready);q.local['hp']=0;q.support=None;before=deepcopy(vars(q))
check('support request alone cannot supply absent operator',not q.exit(actual_support=True) and vars(q)==before)
q=CoffinTrial();assert q.enter(ready);q.local['hp']=0;q.support['person_id']=cof['person_id'];before=deepcopy(vars(q))
check('same person in another body is not independent operator',not q.exit(actual_support=True) and vars(q)==before)
for used_body in (cof['base_body_id'],cof['local_body_id']):
 q=CoffinTrial();assert q.enter(ready);q.local['hp']=0;q.support['body_id']=used_body;before=deepcopy(vars(q))
 check('support cannot reuse PC body '+used_body,not q.exit(actual_support=True) and vars(q)==before)
q=CoffinTrial();assert q.enter(ready);q.local['hp']=0;q.base_location='MOVED-C';before=deepcopy(vars(q))
check('operator at old depot cannot act at moved coffin',not q.exit(actual_support=True) and vars(q)==before)
q.support['location']='MOVED-C'
check('operator physically arrived can perform assisted return',q.exit(actual_support=True) and q.support['main_remaining']==0 and q.base_location=='MOVED-C')
check('recall does not replenish external operator action',q.enter(ready) and q.support['main_remaining']==0)
before=deepcopy(vars(q))
check('same operator action cannot be spent twice',not q.exit(actual_support=True) and vars(q)==before)
# A separately declared next action window, not body switching, renews budget.
q.support['main_remaining']=1
check('next declared operator action can assist again',q.exit(actual_support=True) and q.support['main_remaining']==0 and q.saved['hp']==0)
q=CoffinTrial();assert q.enter(ready);q.local['hp']=0;before=deepcopy(vars(q))
check('stale supported exit cannot consume external action',not q.exit(actual_support=True,expected_revision=0) and vars(q)==before)
check('fresh supported exit consumes action and revision once',q.exit(actual_support=True,expected_revision=1) and q.support['main_remaining']==0 and q.revision==2)
q=CoffinTrial();assert q.enter(ready);q.local.update(cof['snapshot_example']);q.base_hp=0;q.exit_clear=False;q.receiver_enabled=False;q.route_online=False;q.bans.add(('P-C1','UNRELATED'));before=deepcopy(vars(q))
check('broken actual receiver and route ignore positive request flags',not q.exit(link=True,receiver_ready=True,actual_support=True) and vars(q)==before)
# These two updates stand for separately completed, authorized repair events.
# No repair duration, medicine, spare parts or arbitrary healing is simulated.
q.receiver_enabled=True;before=deepcopy(vars(q))
check('receiver repair alone does not restore broken actual route',not q.exit(actual_support=True) and vars(q)==before)
q.route_online=True;before=deepcopy(vars(q))
check('living incapacitated base receives capable local body',q.exit(actual_support=True))
check('return preserves baseHP0 trapped exit and unrelated ban',q.base_alive and q.base_hp==0 and q.exit_clear is False and q.bans==before['bans'])
check('receiver repair preserves local damage ammo shield treatment',q.saved==cof['snapshot_example'])
check('voluntary return does not also consume helper action',q.support['main_remaining']==before['support']['main_remaining']==1)
before=deepcopy(vars(q))
check('returned HP0 original cannot independently reenter',not q.enter(ready) and vars(q)==before)
# Base alive/dead, both HP ranges, actual route/receiver, actual operator
# readiness and explicit support request. Expected predicate is independent.
receiver_matrix=0
for base_hp in range(13):
 for local_hp in range(13):
  for alive,route,receiver,operator_ready,requested in itertools.product([False,True],repeat=5):
   x=CoffinTrial();assert x.enter(ready)
   x.base_hp=base_hp;x.base_alive=alive;x.route_online=route;x.receiver_enabled=receiver
   x.local.update(hp=local_hp,ammo=3,shield=0,treated_since_full_recovery=True)
   x.support['capable']=operator_ready;x.bans.add(('P-C1','OTHER-REALM'));before=deepcopy(vars(x))
   accepted=x.exit(link=True,receiver_ready=True,actual_support=requested)
   expected=alive and route and receiver and (local_hp>0 or (requested and operator_ready))
   assert accepted==expected
   if accepted:
    assert x.saved==before['local'] and x.local is None and x.active==cof['base_body_id'] and x.revision==before['revision']+1
    for key in ('base_hp','base_alive','base_location','exit_clear','route_online','receiver_enabled','batches','ampoules','ego','skills','bans'):
     assert vars(x)[key]==before[key]
    assert x.support['main_remaining']==before['support']['main_remaining']-(1 if local_hp==0 else 0)
   else:assert vars(x)==before
   receiver_matrix+=1
check('5408 actual receiver/operator/HP states preserve bounded contract',receiver_matrix==5408)
# An actual HP0 helper needs all seven independently meaningful conditions.
# A capable local body returns on its own budget regardless of helper state.
operator_matrix=0
for hp in (0,1):
 for present,alive,capable,authorized,connected,action,independent in itertools.product([False,True],repeat=7):
  x=CoffinTrial();assert x.enter(ready);x.local['hp']=hp
  x.support.update(location=x.base_location if present else 'OTHER-SITE',alive=alive,capable=capable,authorized=authorized,connected=connected,main_remaining=int(action),person_id='P-SUP-C' if independent else cof['person_id'])
  before=deepcopy(vars(x));accepted=x.exit(actual_support=True)
  assert accepted==(hp>0 or all((present,alive,capable,authorized,connected,action,independent)))
  if accepted:
   assert x.saved==before['local'] and x.support['main_remaining']==int(action)-(1 if hp==0 else 0)
  else:assert vars(x)==before
  operator_matrix+=1
check('256 operator condition cases require actual independent action',operator_matrix==256)

# One person, compatible IO, separate actual local bodies and storage.
two=cof['two_realm_prepared_case']
def two_ready():
 x=CoffinTrial();x.batches=two['construction_batches'];x.ampoules=two['first_entry_ampoules'];x.storage_slots=two['stored_body_slot_count'];return x
compatibility_matrix=0
for target in ('TEST-COF','TEST-COF-B'):
 for flags in itertools.product((False,True),repeat=5):
  for batches in range(5):
   for ampoules in range(3):
    for slots in range(3):
     x=two_ready();x.batches=batches;x.ampoules=ampoules;x.storage_slots=slots
     d=x.destinations[target]
     for key,value in zip(('charted','compatible','brain_updated','permission'),flags[:4]):d[key]=value
     d['io']=cof['io'] if flags[4] else 'UNSUPPORTED-IO'
     before=deepcopy(vars(x));accepted=x.enter(ready,destination=target)
     assert accepted==(all(flags) and batches>=1 and ampoules>=1 and slots>=1)
     if accepted:
      assert x.active==d['local_body_id'] and x.local==d['initial_local_body']
      assert (x.batches,x.ampoules,x.visited_realms,x.constructed_realms)==(batches-1,ampoules-1,{target},{target})
     else:assert vars(x)==before
     compatibility_matrix+=1
check('2880 actual destination compatibility/resources/slots cases',compatibility_matrix==2880)
two_realm_sequences=0
for hp_a in range(13):
 for hp_b in range(13):
  x=two_ready();snapshots={'TEST-COF':{'hp':hp_a,'ammo':3,'shield':0,'treated_since_full_recovery':True},'TEST-COF-B':{'hp':hp_b,'ammo':0,'shield':1,'treated_since_full_recovery':False}}
  for step,target in enumerate(two['route']):
   prior=deepcopy(x.saved_by_realm);assert x.enter(ready,destination=target)
   assert x.active==('B-C1' if target=='TEST-COF' else 'B-C2')
   if step<2:x.local.update(snapshots[target])
   else:assert x.local==snapshots[target]
   assert all(x.saved_by_realm[k]==value for k,value in prior.items() if k!=target)
   # Each stage below occurs in a separately declared next action window.
   # Body switching itself never replenishes the helper's action budget.
   x.support['main_remaining']=1
   assert x.exit(actual_support=True)
   assert x.saved_by_realm[target]==snapshots[target]
   assert x.support['main_remaining']==(0 if snapshots[target]['hp']==0 else 1)
  assert x.saved_by_realm==snapshots and x.visited_realms==set(snapshots)
  assert (x.batches,x.ampoules,x.active,x.base_hp,x.ego)==(0,0,'B-C0',12,10)
  two_realm_sequences+=1
check('169 two-realm HP sequences preserve both actual bodies and resources',two_realm_sequences==169)
q=two_ready();before=deepcopy(vars(q))
check('unknown destination no caller-invented compatibility',not q.enter(ready,destination='UNKNOWN') and vars(q)==before)
q=two_ready();q.destinations['TEST-COF-B']['io']='OTHER-IO';before=deepcopy(vars(q))
check('positive request flag cannot override actual IO mismatch',not q.enter(ready,destination='TEST-COF-B') and vars(q)==before)
q=two_ready();q.route_online=False;before=deepcopy(vars(q))
check('actual broken entry route cannot be overridden',not q.enter(ready,destination='TEST-COF-B') and vars(q)==before)
q=two_ready();q.ampoules=1;assert q.enter(ready,destination='TEST-COF') and q.exit();before=deepcopy(vars(q))
check('same IO does not waive first visit preparation for second realm',not q.enter(ready,destination='TEST-COF-B') and vars(q)==before)
q=two_ready();q.storage_slots=1;assert q.enter(ready,destination='TEST-COF');q.local.update(cof['snapshot_example']);assert q.exit();before=deepcopy(vars(q))
check('one actual slot cannot overwrite first body with second body',not q.enter(ready,destination='TEST-COF-B') and vars(q)==before)
q=two_ready();q.destinations['TEST-COF-B']['local_body_id']='B-C1';before=deepcopy(vars(q))
check('two destinations cannot alias same local body ID',not q.enter(ready,destination='TEST-COF-B') and vars(q)==before)
q=two_ready();assert q.enter(ready,destination='TEST-COF');before=deepcopy(vars(q))
check('ordinary IO cannot silently perform direct local-to-local Flying',not q.enter(ready,destination='TEST-COF-B') and vars(q)==before)
q.skills['격투']=75;assert q.exit() and q.enter(ready,destination='TEST-COF-B')
check('learned person skill persists without carrying first realm gear',q.skills['격투']==75 and q.local['ammo']==0 and q.local['shield']==1 and q.base_hp==12)
q=two_ready();q.bans.add(('P-C1','TEST-COF'));before=deepcopy(vars(q))
check('named realm Dropout rejects entry without consuming resources',not q.enter(ready,destination='TEST-COF') and vars(q)==before)
check('named realm ban leaves compatible second realm usable',q.enter(ready,destination='TEST-COF-B') and q.bans=={('P-C1','TEST-COF')})
q=two_ready();q.bans.add(('OTHER-PERSON','TEST-COF'))
check('another person ban is not inherited through shared IO',q.enter(ready,destination='TEST-COF'))
assert q.exit();before=deepcopy(vars(q))
check('stale second destination log preserves both storage and shared resources',not q.enter(ready,destination='TEST-COF-B',expected_revision=1) and vars(q)==before)
q=two_ready();assert q.enter(ready,destination='TEST-COF-B');q.local['hp']=0;q.support['body_id']='B-C1';before=deepcopy(vars(q))
check('inactive first realm PC body is not independent second realm rescuer',not q.exit(actual_support=True) and vars(q)==before)
check('second supported capacity is declared preparation not baseline upgrade',cof['stored_body_slot_count']==1 and two['stored_body_slot_count']==2 and two['additional_capacity_explicitly_prepared'])

result={'date':'2026-10-07','profiles':list(p['profiles']),'checks_passed':len(checks),'checks':checks,'exhaustive_lease_states':finite,'coffin_entry_condition_cases':entry_matrix,'coffin_return_state_cases':return_matrix,'coffin_receiver_state_cases':receiver_matrix,'coffin_operator_condition_cases':operator_matrix,'compatible_destination_condition_cases':compatibility_matrix,'two_realm_preservation_sequences':two_realm_sequences,'base_alive_distinct_from_HP0':True,'actual_receiver_and_operator_state_required':True,'local_action_scheduler_implemented':False,'scope':'고지한 시험 프로필'+'의 제한된 워크시트 상태/산술 모델 검사; 실제 게임 구현/플레이 시험 아님','full_encounter_balance_verified':False,'all_world_profiles_verified':False,'actual_participant_playtest':False,'actual_async_community_test':False,'artifacts_sha256':{str(f.relative_to(o)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [v/'차원프로필.json',Path(__file__),o/'10_CoreRulebook.md',o/'12_룰시트와캐릭터시트.md',o/'11_WorldLorebook.md']}}
(v/'차원프로필_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks_passed':len(checks),'finite_lease_states':finite,'coffin_entry_cases':entry_matrix,'coffin_return_cases':return_matrix,'coffin_receiver_cases':receiver_matrix,'coffin_operator_cases':operator_matrix,'compatible_destination_cases':compatibility_matrix,'two_realm_sequences':two_realm_sequences,'actual_participant_playtest':False},ensure_ascii=False))
