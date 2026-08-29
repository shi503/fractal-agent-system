#!/usr/bin/env node
// Projects a declared/observed work graph from a coherent contract bundle.
// Stdlib Node only.

'use strict';

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const fixture = JSON.parse(
  fs.readFileSync(path.join(root, 'examples', 'fixtures', 'graph-demo-bundle.json'), 'utf8')
);

function projectGraph(source) {
  const contract = source.workContract;
  const nodes = new Map();
  const edges = [];

  const addNode = (id, type, state, label, sourceId) => {
    const candidate = { id, type, state, label, source: sourceId };
    const existing = nodes.get(id);
    if (existing && JSON.stringify(existing) !== JSON.stringify(candidate)) {
      throw new Error(`Conflicting definitions for node ${id}`);
    }
    nodes.set(id, candidate);
  };
  const addEdge = (from, to, type, state, sourceId) => {
    edges.push({ from, to, type, state, source: sourceId });
  };

  const outcomeId = `out:${contract.job_id.split(':')[1]}`;
  addNode(contract.job_id, 'job', 'declared', contract.title, 'workContract');
  addNode(outcomeId, 'outcome', 'declared', contract.outcome, 'workContract');
  addNode(contract.workstream_id, 'workstream', 'declared', contract.title, 'workContract');
  addEdge(contract.job_id, outcomeId, 'realizes', 'declared', 'workContract');
  addEdge(contract.job_id, contract.workstream_id, 'decomposes_into', 'declared', 'workContract');

  for (const scoped of contract.scope) {
    addNode(scoped.repository_id, 'repository', 'declared', scoped.repository_id, 'workContract');
    addEdge(contract.workstream_id, scoped.repository_id, 'scoped_to', 'declared', 'workContract');
  }
  for (const context of contract.context) {
    addNode(context.id, 'context', 'declared', `${context.id}@${context.version}`, 'workContract');
    addEdge(contract.workstream_id, context.id, 'uses', 'declared', 'workContract');
  }
  for (const capabilityId of contract.capabilities) {
    addNode(capabilityId, 'capability', 'declared', capabilityId, 'workContract');
    addEdge(contract.workstream_id, capabilityId, 'requires', 'declared', 'workContract');
  }
  for (const [edgeType, principal] of [
    ['requested_by', contract.requested_by],
    ['assigned_to', contract.assigned_to],
  ]) {
    if (!principal) continue;
    addNode(
      principal.principal_id,
      'actor',
      'declared',
      principal.display_name || principal.principal_id,
      'workContract'
    );
    addEdge(contract.workstream_id, principal.principal_id, edgeType, 'declared', 'workContract');
  }

  addNode(source.evidence.evidence_id, 'evidence', 'observed', source.evidence.subject, 'evidence');
  for (const event of source.events) {
    addNode(event.id, 'event', 'observed', event.type, event.id);
    if (!nodes.has(event.data.actor.principal_id)) {
      addNode(
        event.data.actor.principal_id,
        'actor',
        'observed',
        event.data.actor.display_name || event.data.actor.principal_id,
        event.id
      );
    }
    addEdge(event.id, event.data.workstream_id, 'observed_for', 'observed', event.id);
    addEdge(event.id, event.data.actor.principal_id, 'emitted_by', 'observed', event.id);
    if (event.data.parent_event_id) {
      addEdge(event.data.parent_event_id, event.id, 'caused', 'observed', event.id);
    }
    for (const evidenceId of event.data.evidence_refs || []) {
      addEdge(event.id, evidenceId, 'references', 'observed', event.id);
    }
  }

  const nodeList = [...nodes.values()].sort((a, b) => a.id.localeCompare(b.id));
  const edgeList = edges.sort((a, b) =>
    `${a.from}|${a.type}|${a.to}`.localeCompare(`${b.from}|${b.type}|${b.to}`)
  );
  const ids = new Set(nodeList.map((node) => node.id));
  for (const edge of edgeList) {
    if (!ids.has(edge.from) || !ids.has(edge.to)) {
      throw new Error(`Edge ${edge.from} -[${edge.type}]-> ${edge.to} has an unknown endpoint`);
    }
  }

  return {
    graph_version: '1.0.0',
    source_versions: [
      `work-contract:${contract.schema_version}`,
      `event:${source.events[0].data.schema_version}`,
    ],
    nodes: nodeList,
    edges: edgeList,
  };
}

const graph = projectGraph(fixture);
if (process.argv.includes('--json')) {
  console.log(JSON.stringify(graph, null, 2));
} else {
  const declared = graph.nodes.filter((node) => node.state === 'declared').length;
  const observed = graph.nodes.filter((node) => node.state === 'observed').length;
  console.log(
    `Work graph valid: ${graph.nodes.length} nodes (${declared} declared, ${observed} observed), ${graph.edges.length} edges.`
  );
}

const broken = JSON.parse(JSON.stringify(fixture));
broken.events[1].data.evidence_refs = ['evidence:missing'];
let rejected = false;
try {
  projectGraph(broken);
} catch (error) {
  rejected = /unknown endpoint/.test(error.message);
}
if (!rejected) throw new Error('Negative graph fixture was not rejected');
console.log('Negative graph fixture: rejected as expected.');
