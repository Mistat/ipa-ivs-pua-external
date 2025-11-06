#!/usr/bin/env node
// Snapshot the effective IVS→PUA map and base fallback map
// into tmp/effective_maps.snapshot.json so we can diff after regeneration.
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

(async () => {
  const root = path.join(__dirname, '..');
  const ivsMapUrl = pathToFileURL(path.join(root, 'src/utils/ivsCharacterMap.js')).href;
  const overridesUrl = pathToFileURL(path.join(root, 'src/utils/ivsOverrides.js')).href;
  const ivsMap = await import(ivsMapUrl);
  let overrides = {};
  try { overrides = await import(overridesUrl); } catch (_) { overrides = {}; }
  const ivs = { ...(ivsMap.ivsToExternalCharMap || {}), ...(overrides.ivsToExternalCharMap || {}) };
  // Note: fallback is generated + overrides merged (same形で実行時と揃える)
  const fallback = { ...(ivsMap.baseCharFallbackToExternalMap || {}), ...(overrides.baseCharFallbackToExternalMap || {}) };

  const outDir = path.join(root, 'tmp');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, 'effective_maps.snapshot.json');
  const payload = {
    createdAt: new Date().toISOString(),
    counts: { ivs: Object.keys(ivs).length, fallback: Object.keys(fallback).length },
    ivs,
    fallback,
  };
  fs.writeFileSync(outPath, JSON.stringify(payload, null, 2));
  console.log('Wrote snapshot:', outPath, '(ivs:', Object.keys(ivs).length, 'fallback:', Object.keys(fallback).length + ')');
})();

