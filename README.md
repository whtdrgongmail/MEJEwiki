# MEJEwiki

MEJEwiki is the public static archive for WhtDrgon / Kim Dongeun worldbuilding projects.

GitHub Pages target:

```text
https://whtdrgongmail.github.io/MEJEwiki/
```

## Structure

```text
MEJEwiki/
├── index.html
├── data/
│   └── catalog.json
├── fewk/
│   └── ...
├── worlds/
│   └── index.html
└── licenses/
    └── index.html
```

## Notes

- `fewk/` preserves the existing FEWKbooks static reader.
- `worlds/` is a public placeholder until the release set and license for each lorebook are confirmed.
- Links are intentionally relative so the site works cleanly under the GitHub Pages project path.

## FEWK 제5판 추가 (2026-10-13)

기존 `fewk/` 독서기와 3판 카탈로그 항목을 유지하고, `fewk/fifth-edition.html`과 별도의 제5판 카탈로그 항목을 추가했습니다. 제5판 원문 8종과 관련 자료는 `fewk/content/fifth/`에 있습니다. 기존 에디션의 원문·주소·열람 방식은 그대로 사용합니다.

## FEWK 삽화

`fewk/artwork.html`에서 현재 채택된 삽화 696장(기본 100, 확장 200, 인물 396)을 검색합니다. 같은 이미지를 5판 독서기의 관련 장·러너·튜터리얼에도 표시합니다. 출처에 본문 장이 없는 인물은 인물 모음에서 열람할 수 있습니다. 구버전 시안은 포함하지 않습니다.

원본 아트워크 폴더의 세 `제작현황.json`과 현재 이미지 파일을 사용해 다시 내보냅니다(Python 3 + Pillow):

```powershell
python fewk/scripts/build_web_artwork.py --source "<아트워크 폴더>" --workers 4
```

`fewk/assets/fifth-art/manifest.json`은 제목·설명·출처 해시·본문 위치를, `web-image-info.csv`는 같은 이미지의 변환 정보를 기록합니다. 본 이미지는 긴 변 최대 1600px/품질 84, 썸네일은 최대 480px/품질 78의 WebP입니다. 원본 비율과 투명도를 보존하며 자르거나 확대하지 않습니다. 파일명에 원본 SHA-256을 포함합니다. 원본 PNG와 생성 프롬프트·제작 기록은 원본 아트워크 폴더에 유지합니다.

본문 배치는 내보내기 스크립트의 `placements()`에서 관리하고, 실제 원고 앵커 존재 여부를 검사합니다. `fifth-art.js`가 독서기와 이미지 모음의 표시·확대 보기를 공유합니다. 새 채택본을 내보낸 후 이미지 수와 본문 위치, 모바일 표시를 확인하고 함께 배포합니다.
