'use strict';
const assert = require('node:assert/strict');
const {summarize} = require('../retail_media/web/clusters.js');
const plp = {
  clusters: {groups: {winners: {actions: [1], mean_reference_lift: .01}, others: {actions: [2, 3], mean_reference_lift: -.01}}},
  ads: [{action: 1, impressions: 4}, {action: 2, impressions: 6}, {action: 3, impressions: 0}],
  timeline: [{visits: 0, impressions: [0, 0, 0]}, {visits: 10, impressions: [4, 6, 0]}]
};
const totals = summarize(plp);
assert.deepEqual(totals.map(g => g.total), [4, 6]);
assert.deepEqual(totals.map(g => g.count), [1, 2]);
assert.deepEqual(totals.map(g => g.share), [.4, .6]);
assert.deepEqual(summarize(plp, 'mean').map(g => g.values.at(-1).value), [4, 3]);
assert.deepEqual(summarize(plp, 'mean').map(g => g.perAd), [4, 3]);
assert.equal(summarize(plp, 'mean')[1].count, 2, 'Include zero-exposure ads in mean denominator');
const reversed = structuredClone(plp);
reversed.ads.reverse();
assert.deepEqual(summarize(reversed), totals, 'Sorting display rows must not change membership');
const invalid = structuredClone(plp);
invalid.clusters.groups.others.actions = [1, 2];
assert.deepEqual(summarize(invalid), [], 'Reject duplicate or missing cluster membership');
const zero = structuredClone(plp);
zero.ads.forEach(a => { a.impressions = 0; });
assert.equal(summarize(zero)[0].share, null, 'No impressions is not a measured zero share');
const empty = structuredClone(plp);
empty.clusters.groups.winners.actions = [];
empty.clusters.groups.others.actions = [1, 2, 3];
assert.equal(summarize(empty, 'mean')[0].perAd, 0);
assert.deepEqual(summarize(null), []);
const secondPlp = {clusters:{groups:{winners:{actions:[17]},others:{actions:[18]}}},
  ads:[{action:17,impressions:7},{action:18,impressions:3}],
  timeline:[{visits:5,impressions:Array.from({length:48},(_,i)=>i===16?7:i===17?3:0)}]};
assert.deepEqual(summarize(secondPlp).map(g=>g.values[0].value),[7,3], 'Global action IDs of another PLP must align with the trajectory');
console.log('Cluster totals, normalization, empty states and membership tests passed');
