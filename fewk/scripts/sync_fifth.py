"""Copy FEWK fifth-edition text data without editing its source or legacy books."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

BOOKS = [
    ('11_WorldLorebook.md', 'World Lorebook', '세계와 사람들의 삶', '1.05'),
    ('10_CoreRulebook.md', 'Core Rulebook', '공통 백분율 규칙', '0.49'),
    ('01_텀블벅_이지룰_초안.md', '이지룰', '처음 시작하는 판정과 플레이', 'P0.31'),
    ('12_룰시트와캐릭터시트.md', '룰시트·캐릭터시트', '인물·몸·차원·장면 기록', '0.44'),
    ('14_레디메이드_러너.md', '캐릭터북 · 러너 12인', '고른 인물로 바로 시작하기', '1.1'),
    ('15_표준튜터리얼_시나리오.md', '튜터리얼 · 6편', '첫 플레이와 진행 연습', '1.1'),
    ('13_입문시나리오.md', '입문 시나리오', '함께 맡는 첫 의뢰', '0.5'),
    ('02_타롯_해킹과_지능전_초안.md', '타롯 · 해킹과 지능전', '선택해서 쓰는 대결 모듈', '0.3'),
]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def sync(source, destination):
    source, destination = source.resolve(), destination.resolve()
    if source == destination or source in destination.parents:
        raise ValueError('Output must be outside the source directory')
    paths = list(source.glob('*.md')) + list(source.glob('*.json'))
    paths += [p for p in (source / '검증').rglob('*') if p.is_file() and p.suffix in {'.md', '.json', '.py', '.csv'}]
    entries = []
    for path in sorted(set(paths)):
        relative = Path('content/fifth/books') / path.relative_to(source)
        data = path.read_bytes()
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if target.read_bytes() != data:
            raise IOError(f'Copy verification failed: {relative}')
        entries.append({'path': relative.as_posix(), 'source': path.relative_to(source).as_posix(), 'bytes': len(data), 'sha256': digest(data)})
    for name in ('00_최신본_기준.md', '01_작업계획.md'):
        path = source.parent / name
        relative = Path('content/fifth') / name
        data = path.read_bytes()
        (destination / relative).write_bytes(data)
        entries.append({'path':relative.as_posix(), 'source':'../'+name, 'bytes':len(data), 'sha256':digest(data)})
    documents = [{'page':'fifth/books/'+Path(name).stem, 'file':'content/fifth/books/'+name, 'title':title, 'description':description, 'version':version} for name,title,description,version in BOOKS]
    manifest = {'edition':5, 'manuscript_closeout':'2026-10-10', 'publication_status':'manuscript; typesetting and participant playtesting pending', 'documents':documents, 'files':entries, 'excluded':['artwork binaries and production work in progress']}
    target = destination / 'content/fifth/manifest.json'
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(entries),'bytes':sum(e['bytes'] for e in entries),'documents':len(documents)},ensure_ascii=False))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    sync(args.source,args.destination)
