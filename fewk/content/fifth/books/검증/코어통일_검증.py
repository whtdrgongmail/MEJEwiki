"""CORE-UNIFY-01: executable cross-document examples and timing boundaries."""
import contextlib,io,json,hashlib,importlib.util,re
from copy import deepcopy
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent
with contextlib.redirect_stdout(io.StringIO()):
    from 일반플레이_검증 import Body,move,new_round,attack,aid,recover_at

def run():
    passed=[]
    def check(name,value):
        assert value,name
        passed.append(name)
    def invalid(fn):
        try:fn()
        except ValueError:return True
        return False
    core=(SOURCE/'10_CoreRulebook.md').read_text(encoding='utf-8')
    sheet=(SOURCE/'12_룰시트와캐릭터시트.md').read_text(encoding='utf-8')
    roster=(SOURCE/'14_레디메이드_러너.md').read_text(encoding='utf-8')
    tutorial=(SOURCE/'15_표준튜터리얼_시나리오.md').read_text(encoding='utf-8')
    # One actual turn: movement can precede or follow a main action.
    a=Body();b=Body();move(a,10)
    check('10m approach leaves one main',a.move==0 and a.main==1)
    check('contact attack after approach',attack(a,b,'동력 근접 도구',distance=1,roll=20)==('damage',5) and b.hp==7)
    a=Body();move(a,20,extra=True)
    check('sprint spends main',a.move==0 and a.main==0)
    check('no attack after extra movement',invalid(lambda:attack(a,Body(),'권총',distance=10)))
    a=Body();move(a,4);attack(a,Body(),'권총',distance=10);move(a,6)
    check('split movement preserves total',(a.move,a.main,a.ammo)==(0,0,11))
    check('no extra movement beyond budget',invalid(lambda:move(a,1)))
    before_hp=a.hp;a.charges=1;a.first_aid_effect=True;new_round(a)
    check('new round resets budgets only',(a.main,a.reaction,a.move,a.blocked,a.hp,a.ammo,a.charges,a.first_aid_effect)==(1,1,10,False,before_hp,11,1,True))
    # First aid failure spends supplies; success gate ends only at full HP.
    b=Body(hp=0,main=0,reaction=0,move=0);kits=aid(b,3,False)
    check('failed first aid leaves gate open',(b.hp,kits,b.first_aid_effect)==(0,2,False))
    kits=aid(b,kits,True)
    check('first aid stabilizes zero HP',(b.hp,kits,b.first_aid_effect)==(1,1,True))
    check('stabilization does not reset budgets',(b.main,b.reaction,b.move)==(0,0,0))
    check('cannot repeat aid until full',invalid(lambda:aid(b,kits)))
    b=Body(hp=5);kits=aid(b,1)
    check('Miso first aid example',(b.hp,kits,b.first_aid_effect)==(7,0,True))
    check('clinic after first aid is independent',recover_at(b,6*3600,clinic=True) and b.hp==11 and b.first_aid_effect)
    before=deepcopy(b)
    check('24h after scene start is too early',not recover_at(b,24*3600,clinic=True) and b==before)
    check('one second before rolling boundary denied',not recover_at(b,30*3600-1,clinic=True) and b==before)
    check('exact 24h since previous completion allowed',recover_at(b,30*3600,clinic=True) and b.hp==12 and not b.first_aid_effect)
    check('full HP keeps recovery clock',b.last_recovery_s==30*3600)
    b.hp=9;before=deepcopy(b)
    check('new wound does not reset recovery clock',not recover_at(b,36*3600) and b==before)
    kits=aid(b,1)
    check('aid reopens after full HP independently',(b.hp,kits,b.first_aid_effect)==(11,0,True))
    check('rest at next boundary clamps max',recover_at(b,54*3600) and b.hp==12 and not b.first_aid_effect)
    b=Body(hp=0)
    check('rest cannot stabilize',not recover_at(b,21600))
    check('clinic can stabilize zero',recover_at(b,21600,clinic=True) and b.hp==1 and not b.first_aid_effect)
    check('clinic stabilization does not consume aid gate',aid(b,1)==0 and b.hp==3 and b.first_aid_effect)
    b=Body(hp=7)
    check('insufficient actual work no recovery',not recover_at(b,21600,work_s=21599))
    check('storage passive time not treatment',not recover_at(b,21600,stored=True))
    b=Body(hp=0,destroyed=True)
    check('destroyed body no ordinary treatment',not recover_at(b,21600,clinic=True) and invalid(lambda:aid(b,1)))
    # Standard damage and shield timing are shared with runner and tutorial books.
    defender=Body(shield_types=('프로젝타일','레이저'))
    check('Husky first laser blocked',attack(Body(ammo=6),defender,'레이저 단말',distance=10)==('shield',0))
    check('Husky second projectile hits',attack(Body(),defender,'권총',distance=10)==('damage',3) and defender.hp==9 and defender.charges==1)
    new_round(defender)
    check('next round one remaining charge',attack(Body(),defender,'권총',distance=10)==('shield',0) and defender.charges==0)
    # Titles, canonical vocabulary and source links guard stale rule copies.
    check('obsolete aid shop wording removed','HP0 안정화/회복과 같은24시간 창' not in core)
    check('HP0 and confirmed death distinguished','현지 몸 HP0/소실만으로' not in core and '파견 몸의 확정 사망으로 이어진 전투 소실' in core)
    check('operation and injury state separated','운용 상태:' in sheet and '몸의 생존·손상:' in sheet)
    check('all twelve runner recovery records updated',roster.count('| 응급 효과(완전 회복 전1회) |')==12 and roster.count('| 휴식/거점 마지막 적용·다음 가능 |')==12)
    check('no universal arrival delay','접수/적재/인계처럼 도착 뒤의 행동을 지정한 경우 다음 라운드' not in tutorial)
    check('T01 worked total20','15-20초 D→A+인계=20초' in tutorial)
    check('card lessons are separate setups','독립 연습' in tutorial)
    check('three participant actions share one round','같은5초이며' in tutorial)
    check('ready action expires in reserved round','그 라운드가 끝날 때까지' in core and '예약은 라운드 끝에 만료' in tutorial)
    profile=json.loads((HERE/'입문_프로필.json').read_text(encoding='utf-8'))
    check('current profile recovery completion gap',profile['healing']['completion_gap_seconds']==86400 and profile['healing']['work_seconds']==21600)
    check('current profile ready expiry',profile['action_clarification']['ready_attack_expires']=='end_of_reserved_round')
    # Reuse all existing card category, Hold, dot and four-exchange boundary checks.
    spec=importlib.util.spec_from_file_location('tarot_current',HERE/'타롯_도트_검증.py');tarot=importlib.util.module_from_spec(spec);spec.loader.exec_module(tarot)
    card_checks,trace=tarot.checks();check('unchanged tarot checks pass',len(card_checks)==47 and trace[-1]['dots']==[2,0])
    active=['01_텀블벅_이지룰_초안.md','02_타롯_해킹과_지능전_초안.md','10_CoreRulebook.md','12_룰시트와캐릭터시트.md','13_입문시나리오.md','14_레디메이드_러너.md','15_표준튜터리얼_시나리오.md']
    links=0
    from urllib.parse import unquote
    for name in active:
        p=SOURCE/name;text=p.read_text(encoding='utf-8')
        ids=re.findall(r'<a id="([^"]+)"',text);check(name+' unique anchors',len(ids)==len(set(ids)))
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if target.startswith(('https:','http:','mailto:')):continue
            path,_,anchor=unquote(target).partition('#')
            if anchor.startswith('fewk-'):
                q=p.parent/path if path else p
                assert q.exists() and f'id="{anchor}"' in q.read_text(encoding='utf-8'),(name,target)
                links+=1
    return dict(id='CORE-UNIFY-01',date='2026-10-13',checks_passed=len(passed),checks=passed,tarot_checks=len(card_checks),named_links_checked=links,profile='Core0.51 / TAR-P-03 v0.5',human_playtest=False,scope='Rule arithmetic, timing boundaries, inherited card tests and current cross-document examples. Human comprehension, selection/wait time and encounter balance are not simulated here.')

if __name__=='__main__':
    r=run();(HERE/'코어통일_검증결과.json').write_bytes((json.dumps(r,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps({k:r[k] for k in ('id','checks_passed','tarot_checks','named_links_checked','human_playtest')},ensure_ascii=False))
