#!/usr/bin/env node
// Minimal draft-07 JSON Schema validator, stdlib Node only — no third-party
// dependency. Covers exactly the keyword set used by tools/contracts/schemas/:
// type, enum, const, pattern, format (date-time, uri, uri-reference),
// minLength/maxLength, minimum/maximum, minItems/maxItems, uniqueItems,
// items, properties, additionalProperties (bool or schema), required, $ref
// (same-document "#/..." and cross-file "<file>#/...").
//
// Usage: node validate-contracts.cjs <examples-dir>
//
// Each example file is a JSON object with a top-level "$schemaRef" string
// naming the schema to validate against (its basename without the
// ".schema.json" suffix, e.g. "work-contract"). The key is stripped before
// validation — it is not part of the instance data.

'use strict';

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const schemaDir = path.join(root, 'schemas');

function loadSchemas() {
  const store = new Map();
  for (const filename of fs.readdirSync(schemaDir).filter((n) => n.endsWith('.schema.json'))) {
    store.set(filename, JSON.parse(fs.readFileSync(path.join(schemaDir, filename), 'utf8')));
  }
  return store;
}

function typeOf(value) {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  return typeof value;
}

function matchesType(value, type) {
  const actual = typeOf(value);
  if (type === 'integer') return actual === 'number' && Number.isInteger(value);
  return actual === type;
}

function isValidDateTime(value) {
  return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/.test(value);
}

function isValidUri(value) {
  try {
    // eslint-disable-next-line no-new
    new URL(value);
    return true;
  } catch {
    return false;
  }
}

function isValidUriReference(value) {
  if (isValidUri(value)) return true;
  try {
    // eslint-disable-next-line no-new
    new URL(value, 'https://example.invalid/');
    return true;
  } catch {
    return false;
  }
}

const FORMAT_CHECKS = {
  'date-time': isValidDateTime,
  uri: isValidUri,
  'uri-reference': isValidUriReference,
};

function jsonPointer(doc, pointer) {
  if (pointer === '') return doc;
  if (!pointer.startsWith('/')) throw new Error(`Invalid JSON pointer: ${pointer}`);
  let node = doc;
  for (const raw of pointer.slice(1).split('/')) {
    const key = raw.replace(/~1/g, '/').replace(/~0/g, '~');
    if (node == null || !(key in node)) throw new Error(`Pointer not found: ${pointer}`);
    node = node[key];
  }
  return node;
}

function resolveRef(ref, ctx) {
  const hashIndex = ref.indexOf('#');
  const filePart = hashIndex === -1 ? ref : ref.slice(0, hashIndex);
  const pointerPart = hashIndex === -1 ? '' : ref.slice(hashIndex + 1);
  const doc = filePart ? ctx.store.get(filePart) : ctx.doc;
  if (!doc) throw new Error(`Unresolvable $ref target file: ${ref}`);
  return {
    schema: jsonPointer(doc, pointerPart),
    ctx: { doc, file: filePart || ctx.file, store: ctx.store },
  };
}

function validate(schema, data, ctx, instancePath, errors) {
  if (schema.$ref) {
    const resolved = resolveRef(schema.$ref, ctx);
    validate(resolved.schema, data, resolved.ctx, instancePath, errors);
    return;
  }
  if (schema.const !== undefined && data !== schema.const) {
    errors.push(`${instancePath}: expected const ${JSON.stringify(schema.const)}`);
  }
  if (schema.enum && !schema.enum.includes(data)) {
    errors.push(`${instancePath}: ${JSON.stringify(data)} not in enum ${JSON.stringify(schema.enum)}`);
  }
  if (schema.type) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some((t) => matchesType(data, t))) {
      errors.push(`${instancePath}: expected type ${types.join('|')}, got ${typeOf(data)}`);
      return;
    }
  }
  if (typeof data === 'string') {
    if (schema.pattern && !new RegExp(schema.pattern).test(data)) {
      errors.push(`${instancePath}: does not match pattern ${schema.pattern}`);
    }
    if (schema.format && FORMAT_CHECKS[schema.format] && !FORMAT_CHECKS[schema.format](data)) {
      errors.push(`${instancePath}: does not match format ${schema.format}`);
    }
    if (schema.minLength !== undefined && data.length < schema.minLength) {
      errors.push(`${instancePath}: shorter than minLength ${schema.minLength}`);
    }
    if (schema.maxLength !== undefined && data.length > schema.maxLength) {
      errors.push(`${instancePath}: longer than maxLength ${schema.maxLength}`);
    }
  }
  if (typeof data === 'number') {
    if (schema.minimum !== undefined && data < schema.minimum) {
      errors.push(`${instancePath}: below minimum ${schema.minimum}`);
    }
    if (schema.maximum !== undefined && data > schema.maximum) {
      errors.push(`${instancePath}: above maximum ${schema.maximum}`);
    }
  }
  if (Array.isArray(data)) {
    if (schema.minItems !== undefined && data.length < schema.minItems) {
      errors.push(`${instancePath}: fewer than minItems ${schema.minItems}`);
    }
    if (schema.maxItems !== undefined && data.length > schema.maxItems) {
      errors.push(`${instancePath}: more than maxItems ${schema.maxItems}`);
    }
    if (schema.uniqueItems) {
      const seen = new Set(data.map((item) => JSON.stringify(item)));
      if (seen.size !== data.length) errors.push(`${instancePath}: items are not unique`);
    }
    if (schema.items) {
      data.forEach((item, index) => validate(schema.items, item, ctx, `${instancePath}[${index}]`, errors));
    }
  } else if (data && typeof data === 'object') {
    for (const key of schema.required || []) {
      if (!(key in data)) errors.push(`${instancePath}: missing required property '${key}'`);
    }
    const propertySchemas = schema.properties || {};
    for (const key of Object.keys(data)) {
      if (Object.prototype.hasOwnProperty.call(propertySchemas, key)) {
        validate(propertySchemas[key], data[key], ctx, `${instancePath}.${key}`, errors);
      } else if (schema.additionalProperties === false) {
        errors.push(`${instancePath}: additional property '${key}' is not allowed`);
      } else if (schema.additionalProperties && typeof schema.additionalProperties === 'object') {
        validate(schema.additionalProperties, data[key], ctx, `${instancePath}.${key}`, errors);
      }
    }
  }
}

function validateInstance(schemaName, data, store) {
  const filename = `${schemaName}.schema.json`;
  const doc = store.get(filename);
  if (!doc) throw new Error(`Unknown schema '${schemaName}' (expected schemas/${filename})`);
  const errors = [];
  validate(doc, data, { doc, file: filename, store }, '$', errors);
  return errors;
}

function main() {
  const targetDir = process.argv[2];
  if (!targetDir) {
    console.error('Usage: node validate-contracts.cjs <examples-dir>');
    process.exit(2);
  }
  const store = loadSchemas();
  const absDir = path.resolve(targetDir);
  const files = fs
    .readdirSync(absDir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith('.json'))
    .map((entry) => entry.name)
    .sort();

  if (files.length === 0) {
    console.error(`No .json example files found in ${absDir}`);
    process.exit(2);
  }

  let failed = false;
  for (const filename of files) {
    const filePath = path.join(absDir, filename);
    const raw = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const { $schemaRef: schemaName, ...instance } = raw;
    if (!schemaName) {
      failed = true;
      console.error(`${filename}: missing top-level "$schemaRef"`);
      continue;
    }
    let errors;
    try {
      errors = validateInstance(schemaName, instance, store);
    } catch (error) {
      failed = true;
      console.error(`${filename}: ${error.message}`);
      continue;
    }
    if (errors.length > 0) {
      failed = true;
      console.error(`${filename} (${schemaName}): INVALID`);
      for (const message of errors) console.error(`  ${message}`);
    } else {
      console.log(`${filename} (${schemaName}): valid`);
    }
  }

  if (failed) process.exit(1);
  console.log(`Validated ${files.length} example(s) in ${targetDir}.`);
}

main();
