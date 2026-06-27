import { access, mkdir, readdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const worldsDir = path.join(root, 'worlds');
const outputFile = path.join(root, 'data', 'world-illustration-prompts.json');
const styleGuideFile = path.join(root, 'data', 'world-style-guide.json');
const imageRoot = path.join(root, 'assets', 'worlds', 'pages');
const imageExtensions = ['jpg', 'jpeg', 'png', 'webp'];

const worlds = [
  ['h1-gongdong', '공동', '게이트, 등급사회, 무특성의 변칙을 다루는 현대 헌터형 세계관.', 'blue system holograms, mana concentration contour lines, modern Seoul, gates, rank society, one colorless unclassified figure'],
  ['h2-hyanggung', '향궁', '향과 마나, 황실과 조향 길드가 권력을 이루는 세계관.', 'perfume smoke, imperial palace, aromatic magic currents, guild politics, ritual vessels'],
  ['h3-seongra-gangho', '성라강호', '천기, 별, 본명성, 강호의 은원이 교차하는 무협 세계관.', 'starry martial world, celestial fate, mountain sects, sword light, astral constellations'],
  ['h4-gyunsahae', '균사해', '균사망, 접속, 공생과 부패의 윤리를 다루는 생태형 세계관.', 'bioluminescent mycelium networks, fungal sea, symbiosis, spores, organic infrastructure'],
  ['h5-sangyeoho', '상여호', '명로, 망자항법, 물 위의 의례와 기억을 다루는 세계관.', 'shamanic funeral rites, obangsaek spirit colors, ritual boats, talisman paper, ancestral tablets, the dead and navigation'],
  ['h6-rosy-hollow', '로지할로우', '장미빛 교외의 완벽함과 감시, 균열을 다루는 세계관.', 'faded family photo, photographed dollhouse suburb, rose wallpaper, surveillance, flash glare, domestic unease'],
  ['h7-jeonsuseo', '전수서', '조리와 향신, 전승과 신화적 레시피를 다루는 세계관.', 'rough woodcut cookbook plate, mythic kitchen frieze, spices, knives, steam, ritual cooking implements'],
  ['h8-nubi', '누비의 땅', '천과 실, 단추와 봉합의 논리로 이루어진 누비 지형 세계관.', 'scanned fabric collage, bojagi patches, appliqué roads, buttons, raw seams, paper patterns, handmade terrain'],
  ['h9-usabu', '우사부', '비와 하늘, 산악 관청과 농경 질서를 다루는 세계관.', 'rain-blotted land registry, mountain offices, monsoon fields, stamped survey marks, paddies, ritual umbrellas'],
  ['h10-daesu', '대수의 등', '거대한 생명체의 등 위에서 살아가는 마을과 약속의 세계관.', 'rural mural field plate, colossal living back, tiny villages, dry-brush anatomy, forests, vows, migration']
];

const collator = new Intl.Collator('ko', { numeric: true, sensitivity: 'base' });

function titleFromFile(file) {
  return file
    .replace(/\.md$/u, '')
    .replace(/^\d+_/u, '')
    .replace(/_/gu, ' ');
}

function cleanMarkdown(markdown) {
  return markdown
    .replace(/```[\s\S]*?```/gu, ' ')
    .replace(/^#+\s+/gmu, '')
    .replace(/^>\s?/gmu, '')
    .replace(/!\[[^\]]*\]\([^)]+\)/gu, ' ')
    .replace(/\[([^\]]+)\]\([^)]+\)/gu, '$1')
    .replace(/[*_`|>#-]/gu, ' ')
    .replace(/\s+/gu, ' ')
    .trim()
    .slice(0, 1500);
}

async function exists(file) {
  try {
    await access(file);
    return true;
  } catch {
    return false;
  }
}

async function findImageExtension(worldId, chapter) {
  for (const extension of imageExtensions) {
    if (await exists(path.join(imageRoot, worldId, `${chapter}.${extension}`))) {
      return extension;
    }
  }
  return null;
}

const styleGuide = JSON.parse(await readFile(styleGuideFile, 'utf8'));

function buildPrompt({ worldId, worldTitle, premise, visualCode, chapterTitle, excerpt }) {
  const style = styleGuide.worlds[worldId] || {};

  return [
    'Use case: illustration-story',
    'Asset type: MEJEwiki lorebook chapter illustration, wide page banner',
    `Primary request: Create one original wide cinematic illustration for the specific chapter "${worldTitle} - ${chapterTitle}". The image must be tailored to this chapter's content, not a generic cover.`,
    `World premise: ${premise}`,
    `Chapter source excerpt: ${excerpt}`,
    `Visual continuity code: ${visualCode}`,
    `World art direction: ${style.styleMedium || 'polished narrative concept art with a coherent world-specific visual language'}.`,
    `Tone and manner: ${style.tone || 'atmospheric, story-rich, coherent with the world premise and chapter subject'}.`,
    `Color palette: ${style.palette || 'use the established palette of this world'}.`,
    `Materials and texture: ${style.texture || 'show tactile materials and atmospheric detail tied to the chapter'}.`,
    'Scene/backdrop: Choose a concrete scene, place, ritual, social mechanism, map-like view, or symbolic event directly implied by the chapter excerpt.',
    'Subject: Show the chapter concept through characters, environments, artifacts, energy flows, institutions, or landscape logic described in the excerpt.',
    `Style/medium: ${style.styleMedium || 'polished narrative concept art, cinematic digital painting, sophisticated lorebook illustration, detailed but readable'}.`,
    `Composition/framing: very wide horizontal banner, about 21:9 ratio, ${style.composition || 'strong focal point, no decorative border, suitable for a website chapter header'}.`,
    `Lighting/mood: ${style.tone || 'atmospheric, story-rich, coherent with the world premise and chapter subject'}.`,
    'Text: no readable text, no captions, no labels, no logos, no watermark.',
    `Constraints: one coherent scene, not a collage; avoid generic fantasy stock imagery; avoid gore; avoid UI text or legible letters; keep it visually distinct from the world main hero image; avoid ${style.avoid || 'styles that conflict with the world art direction'}.`
  ].join('\n');
}

const prompts = [];

for (const [worldId, worldTitle, premise, visualCode] of worlds) {
  const dir = path.join(worldsDir, worldId);
  const entries = await readdir(dir);
  const files = entries
    .filter((entry) => /^\d{2}_.+\.md$/u.test(entry))
    .filter((entry) => !entry.startsWith('00_'))
    .sort((a, b) => collator.compare(a, b));

  for (const file of files) {
    const chapter = file.match(/^(\d{2})_/u)?.[1];
    const extension = await findImageExtension(worldId, chapter);
    const chapterTitle = titleFromFile(file);
    const markdown = await readFile(path.join(dir, file), 'utf8');
    const excerpt = cleanMarkdown(markdown);
    const preferredExtension = extension || 'jpg';

    prompts.push({
      worldId,
      worldTitle,
      chapter,
      file,
      chapterTitle,
      imagePath: `assets/worlds/pages/${worldId}/${chapter}.${preferredExtension}`,
      exists: Boolean(extension),
      prompt: buildPrompt({ worldId, worldTitle, premise, visualCode, chapterTitle, excerpt })
    });
  }
}

await mkdir(path.dirname(outputFile), { recursive: true });
await writeFile(outputFile, `${JSON.stringify({
  generatedAt: new Date().toISOString(),
  count: prompts.length,
  missing: prompts.filter((item) => !item.exists).length,
  prompts
}, null, 2)}\n`, 'utf8');

if (process.argv.includes('--next')) {
  const next = prompts.find((item) => !item.exists);
  console.log(next ? JSON.stringify(next, null, 2) : 'null');
} else {
  console.log(`Wrote ${prompts.length} prompts (${prompts.filter((item) => !item.exists).length} missing images) to ${path.relative(root, outputFile)}`);
}
