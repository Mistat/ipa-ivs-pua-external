#!/usr/bin/env node
// Backup the generated ivsCharacterMap.js to tmp/backup with timestamp
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = path.join(root, 'src/utils/ivsCharacterMap.js');
const dir = path.join(root, 'tmp', 'backup');
if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 14);
const dst = path.join(dir, `ivsCharacterMap.${stamp}.js`);
fs.copyFileSync(src, dst);
console.log('Backed up to', dst);

