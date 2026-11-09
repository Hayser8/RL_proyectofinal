'use strict';
(function (root) {
  function describe(key, manifest) {
    const item = manifest?.images?.[key], atlas = manifest?.atlases?.[item?.atlas];
    if (!item || !atlas || !/^\/images\/catalogue\/[a-z-]+\.webp$/.test(atlas.url) ||
        ![atlas.width, atlas.height, atlas.columns, atlas.rows].every(v => Number.isInteger(v) && v > 0) ||
        !Number.isInteger(item.column) || !Number.isInteger(item.row) ||
        item.column < 0 || item.column >= atlas.columns || item.row < 0 || item.row >= atlas.rows) return null;
    const rect = item.bounds || {
      left: item.column * atlas.width / atlas.columns, top: item.row * atlas.height / atlas.rows,
      width: atlas.width / atlas.columns, height: atlas.height / atlas.rows
    };
    if (![rect.left, rect.top, rect.width, rect.height].every(Number.isFinite) ||
        rect.left < 0 || rect.top < 0 || rect.width <= 0 || rect.height <= 0 ||
        rect.left + rect.width > atlas.width || rect.top + rect.height > atlas.height) return null;
    return {url: atlas.url, rect, width: atlas.width, height: atlas.height};
  }
  const api = {describe};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.LabCatalogImages = api;
})(globalThis);
