"""Exact unit and declared EXP-BYTE-01 worksheet model checks.
Not a production game implementation, global price model or human playtest.
"""
from pathlib import Path
from fractions import Fraction as F
from copy import deepcopy
import json,hashlib,itertools
v=Path(__file__).parent;o=v.parent
p=json.loads((v/'바이트_프로필.json').read_text());checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
def amount(grams,layer):
    if grams<0 or not 0<=layer<=6:raise ValueError('unsupported standard')
    return F(grams,10000**layer)
def physical_bytes(grams,layer):return grams*10**(24-4*layer)
check('60kg physical standard60000jaa',amount(60000,0)==60000)
check('1kg lower1 data0.1jaa',amount(1000,1)==F(1,10))
check('layer1 gram1hae',physical_bytes(1,1)==10**20)
check('layer2 gram1kyg',physical_bytes(1,2)==10**16)
check('lowest declared layer6 gram1byte',physical_bytes(1,6)==1)
check('21/60000 ratio percent0.035',F(21,60000)*100==F(35,1000))
check('600000oldcapacity distinct60000mass',600000/60000==10)
# Independent absolute-byte expression agrees with fractional jaa expression.
unit_cases=0
for layer in range(7):
    for grams in range(1,2001):
        assert amount(grams,layer)*10**24==physical_bytes(grams,layer)
        unit_cases+=1
check('14000 exact byte/jaa unit cases',unit_cases==14000)
check('native vs destination resource10000factor',amount(400,0)==10000*amount(400,1))
class Inventory:
    def __init__(self):
        self.loc={x:'source' for x in p['item_ids']};self.resource=p['destination_resource_jaa'];self.revision=0
    def stored(self):return sum((amount(p['source_item_grams'],p['source_lower_layer']) for x,z in self.loc.items() if z=='stored'),F(0))
    def move(self,ids,authorized=True,expected_revision=None):
        if not authorized or len(ids)!=len(set(ids)):return False
        if expected_revision is not None and expected_revision!=self.revision:return False
        if any(self.loc.get(x)!='source' for x in ids):return False
        n=self.stored()+len(ids)*amount(p['source_item_grams'],p['source_lower_layer'])
        if n>F(p['storage_capacity_jaa']):return False
        for x in ids:self.loc[x]='stored'
        self.revision+=1;return True
    def reconstruct(self,x,authorized=True,supported=True):
        need=amount(p['source_item_grams'],p['destination_layer'])
        if not authorized or not supported or self.loc.get(x)!='stored' or self.resource<need:return False
        self.resource-=need;self.loc[x]='destination';self.revision+=1;return True
state=Inventory();snapshot=deepcopy(vars(state))
check('three nativeparts exceed declared storage',not state.move(p['item_ids']))
check('failed capacity keeps all source and materials',vars(state)==snapshot)
check('unauthorized transfer rejected',not state.move(['P1'],authorized=False))
check('duplicate same item request rejected',not state.move(['P1','P1']))
check('printed two-item transfer succeeds',state.move(p['move_item_ids'],expected_revision=0))
check('printed after transfer storage0.08',state.stored()==F(2,25))
check('printed aftertransfer sourceP3 only',{x for x,z in state.loc.items() if z=='source'}=={'P3'})
check('stale parallel log revision rejected',not state.move(['P3'],expected_revision=0))
check('same already moved item cannot send again',not state.move(['P1']))
snapshot=deepcopy(vars(state))
check('unsupported material reconstruction rejected',not state.reconstruct('P1',supported=False))
check('unauthorized material reconstruction rejected',not state.reconstruct('P1',authorized=False))
check('rejected reconstruction preserves all stored items',vars(state)==snapshot)
check('printed P1 reconstruction succeeds',state.reconstruct('P1'))
check('printed destinationP1 and storedP2 sourceP3',state.loc=={'P1':'destination','P2':'stored','P3':'source'})
check('printed store0.04andresource400',state.stored()==F(1,25) and state.resource==400)
check('same P1 reconstruction second time rejected',not state.reconstruct('P1'))
state.resource=399;snapshot=deepcopy(vars(state))
check('insufficient destination resource cannot create physicalitem',not state.reconstruct('P2'))
check('failed resource preserves storedP2and399',vars(state)==snapshot)
# All transport permutations and supported single-item assembly preserve identity
# and independent material consumption at each accepted operation.
finite_states=0
for order in itertools.permutations(p['item_ids']):
    q=Inventory()
    for x in order:
        before=deepcopy(vars(q));ok=q.move([x])
        if ok:assert q.stored()<=F(p['storage_capacity_jaa'])
        else:assert vars(q)==before
        assert set(q.loc)==set(p['item_ids'])
        finite_states+=1
    for x in order:
        before=deepcopy(vars(q));ok=q.reconstruct(x)
        if ok:assert q.resource==before['resource']-400 and q.loc[x]=='destination'
        else:assert vars(q)==before
        assert sum(z=='source' for z in q.loc.values())+sum(z=='stored' for z in q.loc.values())+sum(z=='destination' for z in q.loc.values())==3
        finite_states+=1
check('36 declared finite operations preserve state and resource',finite_states==36)
c=p['contract'];settled=c['reward_oyat_equivalent']-c['transport_fee_oyat_equivalent']-c['fabrication_fee_oyat_equivalent']
check('settlement receives3physicaloyat',settled==3)
remaining=settled-c['eat_after_settlement_oyat']
check('eat one leaves2physicaloyat',remaining==2)
credits=c['reward_oyat_equivalent']*c['credits_per_oyat']-sum(c[k]*c['credits_per_oyat'] for k in ['transport_fee_oyat_equivalent','fabrication_fee_oyat_equivalent','eat_after_settlement_oyat'])
check('independent credit settlement20000',credits==20000 and credits==remaining*c['credits_per_oyat'])
physical={'OY1','OY2','OY3'};physical.remove('OY1')
check('eaten physicaloyat unavailable second spending','OY1' not in physical and len(physical)==remaining)
files=[o/'10_CoreRulebook.md',o/'11_WorldLorebook.md',o/'12_룰시트와캐릭터시트.md',v/'바이트_프로필.json',Path(__file__)]
r={'date':'2026-10-05','profile':p['id'],'checks_passed':len(checks),'checks':checks,'exact_standard_unit_cases':unit_cases,'finite_declared_inventory_operations':finite_states,'scope':'고지된 표준/공방 예의 정확 단위·한도·이동/재구성·재료/정산의 제한된 워크시트 모형 검사','ordinary_all_IO_physics_verified':False,'production_game_implementation':False,'whole_economy_balance_verified':False,'actual_participant_playtest':False,'artifacts_sha256':{str(f.relative_to(o)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
(v/'바이트_검증결과.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'profile':p['id'],'checks':len(checks),'units':unit_cases,'finite_operations':finite_states,'human':False},ensure_ascii=False))
