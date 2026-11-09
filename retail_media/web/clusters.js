'use strict';
(function (root) {
  function summarize(plp, mode = 'total') {
    if (!plp?.clusters?.groups || !plp.ads?.length) return [];
    const ads = new Map(plp.ads.map(ad => [ad.action, ad]));
    const groups = ['winners', 'others'].map(key => ({key, ...plp.clusters.groups[key]}));
    const members = groups.flatMap(g => g.actions || []);
    if (members.length !== ads.size || new Set(members).size !== ads.size || members.some(a => !ads.has(a))) return [];
    const total = plp.ads.reduce((n, ad) => n + ad.impressions, 0);
    return groups.map(group => {
      const count = group.actions.length;
      const impressions = group.actions.reduce((n, action) => n + ads.get(action).impressions, 0);
      const divisor = mode === 'mean' ? Math.max(1, count) : 1;
      return {...group, label: group.key === 'winners' ? 'Winners' : 'Losers',
        count, total: impressions, perAd: count ? impressions / count : 0,
        share: total ? impressions / total : null,
        values: (plp.timeline || []).map(point => ({visits: point.visits,
          value: group.actions.reduce((n, action) => n + point.impressions[action - 1], 0) / divisor}))};
    });
  }
  const api = {summarize};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.LabClusters = api;
})(globalThis);
