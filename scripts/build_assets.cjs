// Keep readable CSS sources; publish small, deterministic stylesheets.
const fs = require('node:fs');
const path = require('node:path');
const CleanCSS = require('clean-css');

const root = path.resolve(__dirname, '..');
const { assets } = JSON.parse(fs.readFileSync(path.join(root, 'assets/asset-manifest.json'), 'utf8'));
const bundles = {
  'styles.min.css': ['fonts.css', 'styles.css'],
  'home.min.css': ['home.css'],
  'blog.min.css': ['blog.css'],
  'echipa.min.css': ['echipa.css'],
};
for (const [output, sources] of Object.entries(bundles)) {
  const input = sources.map(file => fs.readFileSync(path.join(root, file), 'utf8')).join('\n');
  const versioned = input.replace(/url\((["']?)(assets\/fonts\/[^?"')]+)(?:\?[^"')]+)?\1\)/g,
    (_, quote, file) => {
      if (!assets[file]) throw new Error(`Missing fingerprinted font: ${file}`);
      return `url("${assets[file]}")`;
    });
  // Level 1 preserves rule order and avoids restructuring the cascade.
  const result = new CleanCSS({ level: 1, rebase: false }).minify(versioned);
  if (result.errors.length || result.warnings.length) {
    throw new Error([...result.errors, ...result.warnings].join('\n'));
  }
  fs.writeFileSync(path.join(root, output), result.styles + '\n');
  console.log(`${output}: ${Buffer.byteLength(input)} → ${Buffer.byteLength(result.styles)} bytes`);
}
