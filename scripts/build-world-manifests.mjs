import { copyFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const worldsDir = path.join(root, 'worlds');
const template = path.join(worldsDir, '_world-reader-template.html');

const worlds = [
  ['h1-gongdong', '공동', '게이트, 등급사회, 무특성의 변칙을 다루는 헌터형 세계관.', '농도 등고선과 게이트가 떠 있는 미래 도시 전경'],
  ['h2-hyanggung', '향궁', '향과 마나, 황실과 조향 길드가 권력을 이루는 세계관.', '향 연기와 바람길이 흐르는 황궁 도시 전경'],
  ['h3-seongra-gangho', '성라강호', '천기, 별, 본명성, 강호의 은원이 교차하는 무협 세계관.', '별자리 하늘 아래 산맥과 강호 문파가 펼쳐진 야경'],
  ['h4-gyunsahae', '균사해', '균사망, 접속, 공생과 부패의 윤리를 다루는 생태형 세계관.', '빛나는 균사망과 거대 버섯 탑이 이어진 생태 행성'],
  ['h5-sangyeoho', '상여호', '명로, 망자항법, 물 위의 의례와 기억을 다루는 세계관.', '안개 낀 호수 위 장례 배와 등불 항로'],
  ['h6-rosy-hollow', '로지할로우', '로지할로우 세계관 로어북.', '완벽하게 정돈된 장미빛 교외 마을과 감시 탑'],
  ['h7-jeonsuseo', '전수서', '전수서 세계관 로어북.', '향신료와 조리 기구가 가득한 신화적 요리 도시'],
  ['h8-nubi', '누비의 땅', '누비의 땅 세계관 로어북.', '천과 실과 단추로 이루어진 누비 지형 전경'],
  ['h9-usabu', '우사부', '우사부 세계관 로어북.', '비와 하늘을 관장하는 산악 관청과 논 terraces'],
  ['h10-daesu', '대수의 등', '거대한 짐승의 등 위에서 살아가는 마을과 약속의 세계관.', '거대한 생명체의 등 위에 자리한 숲과 마을']
];

const collator = new Intl.Collator('ko', { numeric: true, sensitivity: 'base' });

function titleFromFile(file) {
  return file
    .replace(/\.md$/u, '')
    .replace(/^\d+_/u, '')
    .replace(/_/gu, ' ');
}

for (const [id, title, description, heroAlt] of worlds) {
  const dir = path.join(worldsDir, id);
  const entries = await readdir(dir);
  const files = entries
    .filter((entry) => entry.endsWith('.md'))
    .sort((a, b) => collator.compare(a, b))
    .map((entry) => ({
      path: entry,
      title: titleFromFile(entry)
    }));

  await writeFile(path.join(dir, 'manifest.json'), `${JSON.stringify({
    id,
    title,
    description,
    version: '8고',
    status: 'live',
    heroImage: `../../assets/worlds/${id}-hero.png`,
    heroAlt,
    files
  }, null, 2)}\n`, 'utf8');

  await copyFile(template, path.join(dir, 'index.html'));
}
