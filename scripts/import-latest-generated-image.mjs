import { copyFile, mkdir, readdir, stat } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import os from 'node:os';
import path from 'node:path';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';

const execFileAsync = promisify(execFile);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const generatedRoot = path.join(os.homedir(), '.codex', 'generated_images');
const targetArg = process.argv[2];

if (!targetArg) {
  console.error('Usage: node scripts/import-latest-generated-image.mjs <project-relative-target>');
  process.exit(1);
}

async function collectPngs(dir, files = []) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const current = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await collectPngs(current, files);
    } else if (entry.isFile() && entry.name.endsWith('.png')) {
      const info = await stat(current);
      files.push({ file: current, mtimeMs: info.mtimeMs });
    }
  }
  return files;
}

const images = await collectPngs(generatedRoot);
images.sort((a, b) => b.mtimeMs - a.mtimeMs);

if (!images.length) {
  console.error(`No generated PNGs found under ${generatedRoot}`);
  process.exit(1);
}

const source = images[0].file;
const target = path.resolve(root, targetArg);
const extension = path.extname(target).toLowerCase();

await mkdir(path.dirname(target), { recursive: true });

if (extension === '.jpg' || extension === '.jpeg') {
  await execFileAsync('sips', ['-s', 'format', 'jpeg', '-s', 'formatOptions', '86', source, '--out', target]);
} else {
  await copyFile(source, target);
}

console.log(JSON.stringify({
  source,
  target: path.relative(root, target)
}, null, 2));
