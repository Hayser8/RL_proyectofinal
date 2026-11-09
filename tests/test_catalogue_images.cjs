'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const images = require('../retail_media/web/catalogue-images.js');
const publicRoot = path.resolve(__dirname, '../retail_media/web');
const manifest = JSON.parse(fs.readFileSync(path.join(publicRoot, 'images/catalogue/manifest.json')));
assert.equal(Object.keys(manifest.images).length, 78);
const cropKeys = new Set();
for (const [key, item] of Object.entries(manifest.images)) {
  const style = images.describe(key, manifest);
  assert.ok(style, key);
  assert.ok(fs.existsSync(path.join(publicRoot, style.url)), key);
  const crop = `${item.atlas}/${item.column}/${item.row}`;
  assert.ok(!cropKeys.has(crop), `Duplicate image region: ${key}`);
  cropKeys.add(crop);
}
assert.equal(images.describe('unknown', manifest), null);
assert.equal(images.describe('bad', {images:{bad:{atlas:'x',column:0,row:0}},atlases:{x:{url:'https://example.com/image.webp',width:1,height:1,columns:1,rows:1}}}), null);
console.log('All 78 catalogue images have unique valid local atlas regions');
