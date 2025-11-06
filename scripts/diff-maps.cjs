#!/usr/bin/env node
// Diff current effective maps vs the snapshot created by snapshot-maps.cjs
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

(async () => {
  const root = path.join(__dirname, '..');
  const shotPath = path.join(root, 'tmp', 'effective_maps.snapshot.json');
  if (!fs.existsSync(shotPath)) {
    console.error('Snapshot not found:', shotPath, '\nRun: npm run snapshot:maps');
    process.exit(2);
  }
  const before = JSON.parse(fs.readFileSync(shotPath, 'utf-8'));

  const ivsMapUrl = pathToFileURL(path.join(root, 'src/utils/ivsCharacterMap.js')).href;
  const overridesUrl = pathToFileURL(path.join(root, 'src/utils/ivsOverrides.js')).href;
  const ivsMap = await import(ivsMapUrl);
  let overrides = {};
  try { overrides = await import(overridesUrl); } catch (_) { overrides = {}; }
  const currIvs = { ...(ivsMap.ivsToExternalCharMap || {}), ...(overrides.ivsToExternalCharMap || {}) };
  const currFallback = { ...(ivsMap.baseCharFallbackToExternalMap || {}), ...(overrides.baseCharFallbackToExternalMap || {}) };

  function diffMaps(prev, curr) {
    const missing = [];
    const changed = [];
    for (const [k, v] of Object.entries(prev)) {
      if (!(k in curr)) missing.push(k);
      else if (curr[k] !== v) changed.push({ key: k, before: v, after: curr[k] });
    }
    return { missing, changed };
  }

  const ivsDiff = diffMaps(before.ivs || {}, currIvs);
  const fbDiff = diffMaps(before.fallback || {}, currFallback);

  const summary = {
    counts: {
      before: before.counts,
      current: { ivs: Object.keys(currIvs).length, fallback: Object.keys(currFallback).length },
    },
    ivs: { missing: ivsDiff.missing.length, changed: ivsDiff.changed.length },
    fallback: { missing: fbDiff.missing.length, changed: fbDiff.changed.length },
  };
  console.log('Map diff summary:', summary);

  if (ivsDiff.missing.length || fbDiff.missing.length || ivsDiff.changed.length || fbDiff.changed.length) {
    const outDir = path.join(root, 'tmp');
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
    fs.writeFileSync(path.join(outDir, 'map_diff_ivs.missing.json'), JSON.stringify(ivsDiff.missing, null, 2));
    fs.writeFileSync(path.join(outDir, 'map_diff_ivs.changed.json'), JSON.stringify(ivsDiff.changed, null, 2));
    fs.writeFileSync(path.join(outDir, 'map_diff_fallback.missing.json'), JSON.stringify(fbDiff.missing, null, 2));
    fs.writeFileSync(path.join(outDir, 'map_diff_fallback.changed.json'), JSON.stringify(fbDiff.changed, null, 2));
    console.log('Diff details written under tmp/*.json');
    // Non-zero to signal regression in CI if needed
    process.exit(1);
  }
})();

