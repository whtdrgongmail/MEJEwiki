from pathlib import Path
import sys,re,json,hashlib
from xml.sax.saxutils import escape

# Optional local runtime for this workstation; normal installations import these packages directly.
runtime=Path('/private/tmp/fewk_pdf_runtime')
if runtime.exists():sys.path.insert(0,str(runtime))
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Flowable
import pymupdf

V=Path(__file__).resolve().parent;O=V.parent
OUT=O/'출간샘플';QA=V/'대표지면_QA'
OUT.mkdir(exist_ok=True);QA.mkdir(exist_ok=True)
FONT=Path('/Users/whtdrgon/Library/Fonts')
pdfmetrics.registerFont(TTFont('FEWK',str(FONT/'NanumGothic-Regular.ttf')))
pdfmetrics.registerFont(TTFont('FEWK-Bold',str(FONT/'NanumGothic-Bold.ttf')))
pdfmetrics.registerFontFamily('FEWK',normal='FEWK',bold='FEWK-Bold',italic='FEWK',boldItalic='FEWK-Bold')
W,H=A4;WIDTH=W-88
NAVY=colors.HexColor('#142632');TEAL=colors.HexColor('#167B81');OCHRE=colors.HexColor('#B66836');INK=colors.HexColor('#20333D');LIGHT=colors.HexColor('#F2F5F4')
styles={
 'body':ParagraphStyle('body',fontName='FEWK',fontSize=10.2,leading=17.5,textColor=INK,spaceAfter=12,wordWrap='CJK'),
 'small':ParagraphStyle('small',fontName='FEWK',fontSize=8.6,leading=13.2,textColor=INK,spaceAfter=7,wordWrap='CJK'),
 'title':ParagraphStyle('title',fontName='FEWK-Bold',fontSize=24,leading=31,textColor=NAVY,spaceAfter=19,wordWrap='CJK'),
 'sub':ParagraphStyle('sub',fontName='FEWK-Bold',fontSize=13,leading=19,textColor=TEAL,spaceBefore=9,spaceAfter=10,wordWrap='CJK'),
 'hero':ParagraphStyle('hero',fontName='FEWK-Bold',fontSize=30,leading=39,textColor=OCHRE,spaceBefore=10,spaceAfter=18,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='FEWK',fontSize=8.7,leading=13,textColor=INK,wordWrap='CJK'),
 'head':ParagraphStyle('head',fontName='FEWK-Bold',fontSize=8.7,leading=13,textColor=colors.white,wordWrap='CJK'),
}
def clean(s):
 s=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',s)
 s=re.sub(r'<a[^>]+></a>','',s)
 return s.strip().replace('−','-')
def para(s,kind='body'):
 s=escape(clean(s));s=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)
 return Paragraph(s,styles[kind])
def prose(text,kind='body'):
 return [para(s,kind) for s in clean(text).split('\n\n') if s.strip() and not s.startswith('#')]
def section(source,start,end):return source.split(start,1)[1].split(end,1)[0].strip()
def markdown_rows(text):
 return [[clean(c.strip()) for c in l.strip().split('|')[1:-1]] for l in text.splitlines() if l.startswith('|') and not re.match(r'^\|[- :|]+$',l)]
def table(rows,widths=None):
 grid=[[para(c,'head' if i==0 else 'cell') for c in row] for i,row in enumerate(rows)]
 t=Table(grid,colWidths=widths or [WIDTH/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),1,TEAL)]))
 return t
class Map(Flowable):
 def __init__(self):
  super().__init__();self.width=WIDTH;self.height=146
 def wrap(self,availWidth,availHeight):
  return self.width,self.height
 def draw(self):
  c=self.canv;nodes=[(0,'북쪽 수신실','귀환·전송 / 북문'),(174,'정비실','포트·작업대 / 부분 엄폐'),(348,'남쪽 정비소','대체 귀환·전송')]
  for x,title,subtitle in nodes:
   c.setFillColor(LIGHT);c.setStrokeColor(TEAL);c.roundRect(x,50,155,62,6,fill=1,stroke=1)
   c.setFont('FEWK-Bold',11);c.setFillColor(NAVY);c.drawCentredString(x+77.5,88,title)
   c.setFont('FEWK',8);c.drawCentredString(x+77.5,69,subtitle)
  for x in [155,329]:
   c.setStrokeColor(TEAL);c.line(x,80,x+19,80)
   c.setFont('FEWK',8);c.setFillColor(INK);c.drawCentredString(x+9.5,123,'20m')
  c.setFont('FEWK',9);c.setFillColor(INK)
  c.drawString(0,26,'정비실 안: 작업대 ↔ 서비스 포트 10m. 측면 수리 통로로 사선을 끊는다.')
  c.setFont('FEWK',8);c.drawString(0,9,'구역 연결도 · 거리 표기는 실제 보행 경로 기준 · 닫힌 북문은 완전 엄폐')

core=(O/'10_CoreRulebook.md').read_text();world=(O/'11_WorldLorebook.md').read_text();P=json.loads((V/'기본캠페인_프로필.json').read_text())
story=[]
def heading(kicker,title):
 story.append(para(kicker,'sub'));story.append(para(title,'title'))
def br():story.append(PageBreak())
# WORLD / 1
heading('WORLD LORE 01 · 세계의 입구','다른 몸으로 출근해도,\n내일은 이어진다')
story.extend(prose(section(world,'### 다른 몸으로 출근해도, 내일은 이어진다','### 가족여행에서 시작된 변화')))
story.append(Spacer(1,17));story.append(para('일터와 기술,\n그 곁의 사람을 읽는 세계.','hero'))
story.append(para('FEWK의 도시는 익숙한 생활과 낯선 기술을 함께 품는다. 이 지면은 World1.00 도입 본문을 발췌했다.','small'))
br()
# WORLD / 2
heading('WORLD LORE 02 · 일터와 생활','공단계에 산다는 것')
story.extend(prose(section(world,'### 공단계에 산다는 것','### 그림자의 하루와 아직 펼쳐지지 않은 역할')))
story.append(Spacer(1,12));story.append(para('오늘의 정산이\n다음 달의 삶을 바꾼다.','hero'))
br()
# WORLD / 3
heading('WORLD LORE 03 · 소속과 이해관계','기업이 삶에 들어오는 자리')
story.extend(prose(section(world,'### 기업이 사람의 삶에 들어오는 자리','### 같은 도시에서 부딪치는 이해관계'),'small'))
story.append(para('기존 설정에서 시작하는 새 캠페인 갈등','sub'))
conflicts=markdown_rows(section(world,'### 같은 도시에서 부딪치는 이해관계','다음은 위키 종합 기업목록'))
story.append(table(conflicts,[167,WIDTH-167]))
br()
# CORE / 4
heading('CORE RULEBOOK 01 · 인물과 몸','한 사람, 두 몸, 하나의 숙련')
pc=section(core,'#### 시트에 그대로 옮길 자료 러너 한 사람','#### 처음 만나는 세 사람')
intro=pc.split('| 기록 |',1)[0];story.extend(prose(intro,'small'))
story.append(table(markdown_rows(pc),[83,WIDTH-83]))
br()
# CORE / 5
heading('CORE RULEBOOK 02 · 시작 장비','고르고, 맡기고, 다음 일을 준비하기')
story.append(para('C1 인물당 시작 예치금6오얏. 아래 가격은 공동 작업실과 현지 공급소의 협약 값이다. 기본 판정은 백분율 하나이며 도구·장치가 가능한 행동을 연다.','small'))
summaries={
 'MELEE':'접촉1m / 피해6 / 격투', 'PISTOL':'30m·최대60m / 피해4·P / 12발', 'CARBINE':'60m·최대120m / 피해5·P / 12발', 'LASER':'30m·최대60m / 피해4·L / 6회',
 'ARMOR':'장치 방호 뒤 피해1 감소','SHIELD-P':'P적중 차단 / 충전2','SHIELD-L':'L적중 차단 / 충전2',
 'HACKTERM':'현지 서비스 포트·망 접속','COMTERM':'지정망 연락 / 전술 주요1·5초','ENGTOOLS':'외부 연결부 점검·수리 공구','JOBTOOLS':'생성 때 정한 생활 전문 도구','TRANSLATOR':'한국어·영어 말과 문자 번역','STORAGE':'빈 공간1만자 / 읽기·반출 조건 적용','MED':'응급 처치1회분','AMMO':'지정 권총/카빈12발1탄창','LCELL':'지정 레이저6회1셀','CHARGE':'안전 거점에서 공유 충전2로','PART':'외부 수리1회 / 작업5분','IM-COMM':'지원 몸에서 손을 비우고 연락','IM-REFLEX':'개인 반응으로 관측 가능한P/L회피',
}
story.append(table([['품목','오얏','선택의 내용']]+[[x['name'],str(x['price_oyat']),summaries[x['id']]] for x in P['catalog']],[123,40,WIDTH-163]))
story.append(Spacer(1,8));story.append(para('P/L방호를 함께 장착하면 충전2·라운드1회를 공유한다. 지정 정규 시술은 장치값에2오얏/6시간이 더 든다. 원거리 방호와 개인 반응은 서로 다른 예산이다.','small'))
br()
# CORE / 6
heading('CORE RULEBOOK 03 · 기본 캠페인C1','공단계의 저녁 교대')
story.append(para('연수의 급여에는 쉬는 동안의 장비 사용료가 붙었다. 다음 교대 정리 전에 자기 정산4000자와 기계 운용 로그6000자를 확보해 지정 수신처로 보내 달라는 의뢰다. 보수는1인1오얏 선지급+완수3오얏.','body'))
story.append(Map())
npcs=markdown_rows(section(core,'#### 처음 만나는 세 사람','#### 첫 의뢰 —'))
story.append(table(npcs,[92,WIDTH-184,92]))
story.append(Spacer(1,8));story.append(para('접근은 협상·정비 협조·잠입/접속 중 고른다. 정상 권한으로 할 수 있는 일은 무판정. 포트의 관리자 잠금은 주요1·5초의 해킹 한 번으로 처리한다. 실패 시 위치가 통보되고3라운드 뒤 순찰2명이 북문에 도착한다.','small'))
story.append(para('현지30분 뒤 원시 로그는 요약된다. 이미 얻은 사본·명세·증언은 남는다. 귀환은 정상 지원 단말에서 주요1. 남쪽 정비소는 대체 경로로 유지된다. 같은 현지 전투와 몸/물품 기록을 사용한다.','small'))
story.append(para('수선골목·인물·사건·IO와 가격은 제5판의 새 캠페인이다. 공단계 전체의 확정 법률/정책을 뜻하지 않는다.','small'))
br()
# CORE / 7
heading('CORE RULEBOOK 04 · 의뢰 뒤의 생활','돌아온 뒤에 남는 것')
story.append(para('12 − 9 = 3오얏','hero'))
story.append(para('3명의 선지급3오얏과 완수 보수9오얏을 같은 예치 장부에 기록한다. 다음은 실제 소모와 숙박을 보충한 한 번의 예다.','body'))
settlement=section(core,'#### 보수를 받아 다음 일을 준비하기','## 스페셜 시나리오')
rows=markdown_rows(settlement)
# Two source tables, rendered independently.
break_at=next(i for i,row in enumerate(rows) if row[0]=='실제로 보충/사용한 것')
story.append(table(rows[break_at:],[WIDTH-160,70,90]))
story.append(Spacer(1,16));story.append(para('남는 돈으로 무엇을 바꿀까','sub'))
story.append(para('시작 물품을 다르게 골라3오얏을 남겼다면 이번 분배1오얏을 더해 통신 모듈4오얏을 살 수 있다. 정규 설치2오얏은 더 준비해야 한다. 외장 도구로 먼저 일할지, 몸의 기능을 바꿀지 고른다.','body'))
story.append(para('정산에는 보수뿐 아니라 대여품 반납, 몸의 손상과 잔량, 처치 시점, 자료의 도착, 다음 약속과 숙련 성장 한 건을 남긴다. 인물의 경험과 사람 사이의 관계는 다음 장면으로 이어진다.','body'))
story.append(para('자료를 확보한 뒤에는 오류의 정정 기회를 줄지, 어떤 범위로 알릴지 선택할 수 있다. 누구의 정보인지와 공개 권한을 확인하고 동료의 생활과 다음 의뢰를 이어 간다.','body'))

pdf=OUT/'FEWK5_대표지면_시안.pdf'
def frame(c,doc):
 c.saveState();c.setFillColor(NAVY);c.rect(0,H-48,W,48,fill=1,stroke=0)
 c.setFillColor(colors.white);c.setFont('FEWK-Bold',13);c.drawString(44,H-29,'FEWK  /  FIFTH EDITION')
 c.setFillColor(colors.HexColor('#7AD1C8'));c.setFont('FEWK',8);c.drawRightString(W-44,H-29,'WORLD LORE · CORE RULEBOOK')
 c.setStrokeColor(TEAL);c.setLineWidth(0.6);c.line(44,34,W-44,34)
 c.setFillColor(INK);c.setFont('FEWK',7.4);c.drawString(44,22,'2026-10-07 · Core0.49 / World1.00 · 대표 지면 시안')
 c.drawRightString(W-44,22,f'{doc.page:02d}')
 c.restoreState()
doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=68,bottomMargin=46,title='FEWK 제5판 대표 지면 시안',author='FEWK')
doc.build(story,onFirstPage=frame,onLaterPages=frame)
D=pymupdf.open(pdf);bounds=[];texts=[]
for i,page in enumerate(D,1):
 text=page.get_text();texts.append(text)
 violations=[];spans=[]
 for block in page.get_text('dict')['blocks']:
  for line in block.get('lines',[]):
   for span in line.get('spans',[]):
    x0,y0,x1,y1=span['bbox'];spans.append(span)
    if x0<0 or y0<0 or x1>W+0.5 or y1>H+0.5:violations.append(span['text'])
 overlaps=[]
 for j,a in enumerate(spans):
  for b in spans[j+1:]:
   ax,ay,ar,ab=a['bbox'];bx,by,br,bb=b['bbox']
   if min(ar,br)-max(ax,bx)>1 and min(ab,bb)-max(ay,by)>1:
    overlaps.append([a['text'],b['text']])
 bounds.append({'page':i,'text_characters':len(text),'out_of_page_spans':violations,'text_overlap_pairs':overlaps})
 page.get_pixmap(matrix=pymupdf.Matrix(1.65,1.65)).save(QA/f'page_{i:02d}.png')
assert all(not x['out_of_page_spans'] for x in bounds),bounds
assert all(not x['text_overlap_pairs'] for x in bounds),bounds
assert len(D)==7,('unexpected page flow',len(D))
for term in ['다른 몸으로 출근','공단계에 산다는','기업이 삶에','한 사람','고르고','저녁 교대','돌아온 뒤']:
 assert term in '\n'.join(texts),term
manifest={'id':'FEWK-PUBLICATION-SAMPLE-01','date':'2026-10-07','pages':len(D),'pdf_path_relative_to_fifth':str(pdf.relative_to(O)),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'input_book_hashes':{n:hashlib.sha256((O/n).read_bytes()).hexdigest() for n in ['10_CoreRulebook.md','11_WorldLorebook.md']},'fonts':[{'name':n,'sha256':hashlib.sha256((FONT/n).read_bytes()).hexdigest()} for n in ['NanumGothic-Regular.ttf','NanumGothic-Bold.ttf']],'automated_page_bounds':bounds,'visual_pages_reviewed':[],'final_layout_complete':False,'actual_participant_reading':False,'remote_publication_performed':False}
(V/'대표지면_검수.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pdf':str(pdf),'pages':len(D),'bytes':pdf.stat().st_size,'out_of_page_spans':sum(len(x['out_of_page_spans']) for x in bounds)},ensure_ascii=False))
