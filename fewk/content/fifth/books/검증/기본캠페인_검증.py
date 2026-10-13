"""Check the default campaign's actual budgets, page data, routes and existing combat engine."""
from pathlib import Path
import contextlib,io,json,hashlib,re

HERE=Path(__file__).resolve().parent
O=HERE.parent
with contextlib.redirect_stdout(io.StringIO()):
    from 일반플레이_검증 import Body, attack, move, new_round, grade, target

profile=json.loads((HERE/'기본캠페인_프로필.json').read_text())
catalog={x['id']:x for x in profile['catalog']}
core=(O/'10_CoreRulebook.md').read_text()
checks=0
def check(condition):
    global checks
    assert condition
    checks+=1

check(len(catalog)==len(profile['catalog'])==20)
check(all(isinstance(x['price_oyat'],int) and x['price_oyat']>0 for x in catalog.values()))
check(profile['engine']=='P-FEWK-0.2' and not profile['new_universal_stats'] and not profile['prices_apply_globally'])
section=core.split('<a id="fewk-starting-catalog"></a>',1)[1].split('#### 생활과 경험을 성장에 남기기',1)[0]
for x in catalog.values():
    row=next(l for l in section.splitlines() if l.startswith('| '+x['name']+' |'))
    cells=[c.strip() for c in row.split('|')[1:-1]]
    check(int(cells[1])==x['price_oyat'] and cells[2]==x['skill'])
for kit in profile['starter_kits']:
    cost=sum(catalog[k]['price_oyat']*qty for k,qty in kit['items'].items())
    check(cost==profile['starting_personal_money_oyat']==6)
    check(all(qty>0 for qty in kit['items'].values()))
check(catalog['IM-COMM']['price_oyat']+profile['body']['implant_service_price_oyat']==6)
check(catalog['IM-REFLEX']['price_oyat']+profile['body']['implant_service_price_oyat']==8)
check(profile['body']['implant_service_seconds']==6*3600)
m=profile['mission'];s=profile['settlement_example']
check(m['personal_payroll_chars']+m['machine_log_chars']==m['evidence_chars']==10000)
check(profile['players']*m['advance_per_person_oyat']==3)
check(profile['players']*m['completion_per_person_oyat']==9)
income=profile['players']*(m['advance_per_person_oyat']+m['completion_per_person_oyat'])
expenses=sum(s[k]*catalog[item]['price_oyat'] for k,item in [('ammo_packs','AMMO'),('shield_packs','CHARGE'),('aid_kits','MED'),('repair_parts','PART')])+s['lodging_person_nights']*s['lodging_price_oyat']
check(income==12 and expenses==9 and income-expenses==3)
# Check six actual purchase/settlement decisions from the default package.
budgets_checked=6
check(profile['starting_personal_money_oyat']-catalog['IM-COMM']['price_oyat']-2==0)
check(profile['starting_personal_money_oyat']<catalog['IM-REFLEX']['price_oyat']+2)
check(income-expenses==catalog['SHIELD-P']['price_oyat'])
check(profile['players']*m['advance_per_person_oyat']==s['lodging_person_nights']*s['lodging_price_oyat'])
check(3+(income-expenses)//profile['players']==catalog['IM-COMM']['price_oyat'])
check(3+(income-expenses)//profile['players']<catalog['IM-COMM']['price_oyat']+2)
# All roll outcomes use the same engine; situation cancellation never stacks benefits.
for skill in [10,30,50,70,95]:
    for situation in [-20,0,20]:
        t=target(skill,situation)
        check(sum(grade(t,r)>0 for r in range(1,101))==t)
# A normal move + major extra move reaches the alternative exit before the declared patrol arrives.
b=Body();move(b,20,extra=True)
check(b.main==0 and b.move==0 and b.hp==12 and b.ammo==12)
try:attack(b,Body(),'권총',distance=1)
except ValueError:check(b.main==0 and b.ammo==12)
else:raise AssertionError('movement granted an additional attack')
check(1<m['alarm_arrival_rounds_after_detection']==3)
new_round(b);check(b.main==1 and b.move==10)
# Existing guard/weapon/shield mechanics, including the melee and laser alternatives.
guard=Body(hp=m['guard_hp'],armor=m['guard_armor'],charges=m['guard_shield_charges'])
shooter=Body()
check(attack(shooter,guard,'권총',roll=1,distance=20)==('shield',0))
check(guard.hp==12 and guard.charges==0 and shooter.ammo==11)
new_round(shooter);new_round(guard)
check(attack(shooter,guard,'권총',roll=1,distance=20)==('damage',3))
check(guard.hp==9)
weapon_data=json.loads((HERE/'입문_프로필.json').read_text())['weapons']
melee_key=next(k for k,x in weapon_data.items() if x['type']=='근접' and x['damage']==6)
laser_key=next(k for k,x in weapon_data.items() if x['type']=='레이저')
guard=Body(charges=1);fighter=Body()
check(attack(fighter,guard,melee_key,roll=1,distance=1,defense_roll=100,defense_skill=30)==('damage',5))
check(guard.hp==7 and guard.charges==1)
guard=Body(charges=1);laser=Body(ammo=6)
check(attack(laser,guard,laser_key,roll=1,distance=20)==('damage',3))
check(guard.hp==9 and guard.charges==1 and laser.ammo==5)
hidden=Body();attacker=Body()
try:attack(attacker,hidden,'권총',roll=1,distance=20,cover='full')
except ValueError:check(attacker.main==1 and attacker.ammo==12 and hidden.hp==12)
else:raise AssertionError('full cover did not prevent direct fire')
check(not profile['actual_participant_playtest'] and not profile['balance_confirmed'])
inputs=['10_CoreRulebook.md','11_WorldLorebook.md','검증/기본캠페인_프로필.json','검증/기본캠페인_검증.py','검증/일반플레이_검증.py','검증/백분율_코어검증.py','검증/입문_프로필.json']
result={'id':'FEWK-DISTRICT-C1-VERIFY','checks_passed':checks,'budget_scenarios_checked':budgets_checked,'catalog_items':len(catalog),'starting_kits':3,'income_oyat':income,'expenses_oyat':expenses,'remaining_oyat':income-expenses,'engine':'P-FEWK-0.2','actual_participant_playtest':False,'balance_confirmed':False,'artifacts_sha256':{name:hashlib.sha256((O/name).read_bytes()).hexdigest() for name in inputs}}
(HERE/'기본캠페인_검증결과.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:x for k,x in result.items() if k!='artifacts_sha256'},ensure_ascii=False))
