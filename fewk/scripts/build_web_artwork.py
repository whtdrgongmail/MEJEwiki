"""Export current reviewed FEWK illustrations as WebP, with reader placements.

Usage: python scripts/build_web_artwork.py --source <5th-edition artwork folder>
Requires Pillow. Source PNGs and generation records are never modified.
"""
import argparse
import collections
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from PIL import Image, ImageOps, features

ROOT=Path(__file__).resolve().parents[1]
WORLD='fifth/books/11_WorldLorebook'
CORE='fifth/books/10_CoreRulebook'
RUNNERS='fifth/books/14_레디메이드_러너'
TUTORIAL='fifth/books/15_표준튜터리얼_시나리오'
TAROT='fifth/books/02_타롯_해킹과_지능전_초안'
SHEETS='fifth/books/12_룰시트와캐릭터시트'
EASY='fifth/books/01_텀블벅_이지룰_초안'
INTRO='fifth/books/13_입문시나리오'
GROUPS=[('base','', '기본 삽화'),('expanded','확장200','세계와 생활'),('profiles','인물프로필','인물 프로필'),('rules','규칙삽화','규칙과 예시')]

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(data):return hashlib.sha256(data).hexdigest()
def clean(value):return re.sub(r'\s+',' ',str(value or '')).strip().replace('~','-')

def placements(a,group):
    result=[]
    def add(page,anchor='',role='gallery'):
        value={'page':page,'anchor':anchor,'role':role}
        if value not in result:result.append(value)
    def world(ch,role='gallery'):add(WORLD,f'fewk-world-{int(ch):02}',role)
    ident=a['id']
    if group=='rules':
        return a['placements']
    if group!='base':
        for ch in a.get('source_chapters',[])[:2]:
            if str(ch).isdigit():world(ch)
        if group=='profiles':
            for entry in a.get('source_entries',[]):
                runner=entry.get('runner_id','')
                if re.fullmatch(r'R\d{2}',runner):add(RUNNERS,'fewk-runner-'+runner.lower())
        return result
    family=ident[0];n=int(ident[1:])
    if family=='A':
        if n==1:add('home',role='hero');add(EASY,role='hero');add(RUNNERS,role='hero')
        elif n==2:add(CORE,role='hero')
        elif n==3:add(WORLD,role='hero')
        elif n==4:add(TUTORIAL,role='hero')
        elif n==5:add(CORE,'fewk-make');add(SHEETS,role='hero')
        else:world(52)
    elif family=='B':world(39 if n==1 else 35)
    elif family=='C':world(69 if n in [1,2,3,5] else 70)
    elif family=='D':add(RUNNERS,f'fewk-runner-r{n:02}')
    elif family=='E':
        if n<=12:world([1,9,12,18,21,25,35,39,45,58,66,72][n-1],'feature')
        else:add(CORE,['fewk-percent','fewk-import','fewk-frontier','fewk-scenario','fewk-online','fewk-npc','fewk-marking','fewk-core-reference'][n-13],'feature')
    elif family=='F':
        chapters={1:45,2:22,3:3,4:16,5:55,6:15,7:14,8:47,9:21,10:43,11:25,12:27,13:30,14:32,19:33,20:52,21:59,22:60,23:61,24:67}
        if n in chapters:world(chapters[n])
        elif n==15:add(CORE,'fewk-residence')
        elif n in [16,17]:add(CORE,'fewk-combat')
        elif n==18:add(TAROT,role='hero');add(CORE,'fewk-hacking-operation')
        if n==7:add(INTRO,role='hero')
    elif family=='G':add(TUTORIAL,f'fewk-tutorial-t{n:02}','feature')
    elif family=='H':
        if n>=10:add(TAROT)
        else:world({1:22,2:21,3:3,4:20,5:70,6:33,7:30,8:29,9:57}[n])
    return result

def caption(a,group):
    title=clean(a['title'])
    if group=='profiles':return title,clean(a.get('form'))
    if a['id'].startswith(('A','E')) and ' — ' in title:title=title.split(' — ',1)[1]
    text=clean(a.get('scene') or a.get('description'))
    text=re.split(r'(?<!\d)\.\s+',text,maxsplit=1)[0].rstrip('.')
    return title,text

def build(source,workers):
    assert features.check('webp'), 'Pillow requires WebP support'
    records=[]
    for group,folder,label in GROUPS:
        directory=source/folder
        for a in read(directory/'제작현황.json')['assets']:
            if a.get('status')=='generated_reviewed' and a.get('file'):
                records.append((a,group,label,directory/a['file']))
    assert len(records)==len({group+'/'+a['id'] for a,group,_,_ in records})
    destination=ROOT/'assets/fifth-art'
    (destination/'thumbs').mkdir(parents=True,exist_ok=True)
    def export(record):
        a,group,label,path=record
        data=path.read_bytes();source_hash=sha(data)
        assert source_hash==a['sha256'],str(path)
        title,description=caption(a,group)
        filename=f"{group}-{a['id'].lower()}-{source_hash[:10]}.webp"
        main=destination/filename;thumb=destination/'thumbs'/filename
        with Image.open(io.BytesIO(data)) as opened:
            original=ImageOps.exif_transpose(opened)
            transparent=original.mode in ('RGBA','LA') and original.getchannel('A').getextrema()[0]<255
            picture=original.convert('RGBA' if transparent else 'RGB')
            picture.thumbnail((1600,1600),Image.Resampling.LANCZOS)
            if not main.exists():picture.save(main,'WEBP',quality=84,method=6,exact=True)
            small=picture.copy();small.thumbnail((480,480),Image.Resampling.LANCZOS)
            if not thumb.exists():small.save(thumb,'WEBP',quality=78,method=6,exact=True)
            with Image.open(main) as check:
                check.load();assert check.format=='WEBP' and check.size==picture.size
                if transparent:assert check.getchannel('A').tobytes()==picture.getchannel('A').tobytes()
            with Image.open(thumb) as check:
                check.load();assert check.format=='WEBP' and check.size==small.size
            width,height=picture.size
        version=re.search(r'_v(\d+)\.',path.name)
        return {'id':group+'-'+a['id'].lower(),'source_id':a['id'],'group':label,'category':a.get('category') or {'A':'표지','B':'문장과 표식','C':'문장과 표식','D':'러너','E':'장별 삽화','F':'생활과 사건','G':'튜터리얼','H':'장비와 물건'}.get(a['id'][0],'삽화'),'title':title,'description':description,'character':a.get('character_name',''),'character_id':a.get('character_id',''),'outfit':clean(a.get('outfit')),'form':clean(a.get('form')),'version':int(version.group(1)) if version else 1,'width':width,'height':height,'transparent':transparent,'src':'assets/fifth-art/'+filename,'thumb':'assets/fifth-art/thumbs/'+filename,'thumb_width':small.width,'thumb_height':small.height,'bytes':main.stat().st_size,'thumb_bytes':thumb.stat().st_size,'sha256':sha(main.read_bytes()),'thumb_sha256':sha(thumb.read_bytes()),'source':path.relative_to(source).as_posix(),'source_sha256':source_hash,'source_bytes':len(data),'placements':placements(a,group)}
    assets=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for item in pool.map(export,records):
            assets.append(item)
            if len(assets)%25==0:print(json.dumps({'converted':len(assets),'total':len(records)}),flush=True)
    # Validate every location against published manuscript anchors.
    for a in assets:
        for p in a['placements']:
            file=ROOT/('content/fifth/home.md' if p['page']=='home' else 'content/'+p['page']+'.md')
            assert file.exists(),p
            if p['anchor']:assert f'id="{p["anchor"]}"' in file.read_text(encoding='utf-8'),p
    summary={'images':len(assets),'groups':dict(collections.Counter(a['group'] for a in assets)),'full_bytes':sum(a['bytes'] for a in assets),'thumb_bytes':sum(a['thumb_bytes'] for a in assets),'source_bytes':sum(a['source_bytes'] for a in assets),'transparent':sum(a['transparent'] for a in assets),'images_with_reader_placements':sum(bool(a['placements']) for a in assets),'encoding':{'format':'WebP','full_max_edge':1600,'full_quality':84,'thumbnail_max_edge':480,'thumbnail_quality':78,'alpha':'preserved','crop':False,'upscale':False}}
    payload={'schema':1,'summary':summary,'assets':assets}
    (destination/'manifest.json').write_bytes((json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    with (destination/'web-image-info.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        fields=['id','source_id','group','category','title','description','character','outfit','version','source','source_sha256','src','thumb','width','height','transparent','bytes','thumb_bytes','sha256','thumb_sha256','placements']
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader()
        for a in assets:writer.writerow({**a,'placements':json.dumps(a['placements'],ensure_ascii=False)})
    print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args();build(args.source.resolve(),args.workers)
