// Generate PNG icons from SVG using sharp
// Sizes: 32, 64, 128, 256, 512
import { readFile, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import sharp from 'sharp';

const root = resolve(process.cwd());
const srcSvg = resolve(root, 'public', 'logo-agrisense-mark-v2.svg');
const outDir = resolve(root, 'public', 'icons');

const sizes = [32, 64, 128, 256, 512];

async function ensureDir(dir) {
  await mkdir(dir, { recursive: true });
}

async function generate() {
  try {
    const svgBuffer = await readFile(srcSvg);
    await ensureDir(outDir);
    for (const size of sizes) {
      const out = resolve(outDir, `icon-${size}.png`);
      await sharp(svgBuffer, { density: 384 })
        .resize(size, size, { fit: 'cover' })
        .png({ compressionLevel: 9 })
        .toFile(out);
      console.log(`Generated ${out}`);
    }
    // Also generate a 512 favicon.png at project root public
    const faviconOut = resolve(root, 'public', 'favicon.png');
    await sharp(svgBuffer, { density: 384 })
      .resize(512, 512, { fit: 'cover' })
      .png({ compressionLevel: 9 })
      .toFile(faviconOut);
    console.log(`Generated ${faviconOut}`);
  } catch (err) {
    console.error('Icon generation failed:', err);
    process.exit(1);
  }
}

generate();
