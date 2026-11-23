#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const pkg = require('../package.json');

const SKILL_NAME = 'building-design';
const AGENTS = {
  claude: '.claude',
  kimi: '.kimi-code',
};
const SOURCE_ROOT = path.resolve(__dirname, '..');
const SOURCE_PATHS = ['SKILL.md', 'references', 'scripts'];

function usage() {
  console.log(`building-design ${pkg.version}

Usage:
  npx building-design install [--agent claude|kimi|both] [--project [dir]] [--force]
  npx building-design status [--project [dir]]
  npx building-design --help
  npx building-design --version

Without --project, installs into the user skill directories. The default agent is both.
Existing files are preserved unless --force is supplied.`);
}

function parse(argv) {
  const args = [...argv];
  const command = args[0] && !args[0].startsWith('-') ? args.shift() : 'status';
  const options = { agents: [], force: false, help: false, project: false, root: process.cwd() };

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === '--help' || arg === '-h') options.help = true;
    else if (arg === '--force') options.force = true;
    else if (arg === '--project') {
      options.project = true;
      if (args[i + 1] && !args[i + 1].startsWith('-')) {
        options.root = path.resolve(args[i + 1]);
        i += 1;
      }
    } else if (arg === '--agent') {
      const agent = args[i + 1];
      if (!agent || !['claude', 'kimi', 'both'].includes(agent)) {
        throw new Error('--agent expects claude, kimi, or both');
      }
      if (agent === 'both') options.agents.push(...Object.keys(AGENTS));
      else options.agents.push(agent);
      i += 1;
    } else throw new Error(`Unknown option: ${arg}`);
  }

  if (!['install', 'status'].includes(command)) throw new Error(`Unknown command: ${command}`);
  options.agents = [...new Set(options.agents.length ? options.agents : Object.keys(AGENTS))];
  return { command, options };
}

function sourceFiles() {
  const files = [];
  function visit(relative) {
    const source = path.join(SOURCE_ROOT, relative);
    const stat = fs.statSync(source);
    if (stat.isDirectory()) {
      for (const entry of fs.readdirSync(source)) {
        if (entry === '__pycache__' || entry.endsWith('.pyc') || entry === '.DS_Store') continue;
        visit(path.join(relative, entry));
      }
    } else files.push(relative);
  }
  for (const sourcePath of SOURCE_PATHS) visit(sourcePath);
  return files;
}

function destination(root, project, agent) {
  const base = project ? root : os.homedir();
  return path.join(base, AGENTS[agent], 'skills', SKILL_NAME);
}

function skillState(target) {
  const required = ['SKILL.md', 'references/variants.md', 'scripts/check_design.py'];
  const missing = required.filter((relative) => !fs.existsSync(path.join(target, relative)));
  return { target, installed: missing.length === 0, missing };
}

function printStatus(options) {
  let incomplete = false;
  for (const agent of options.agents) {
    const state = skillState(destination(options.root, options.project, agent));
    console.log(`${agent}: ${state.installed ? 'installed' : 'not installed'} — ${state.target}`);
    if (state.missing.length) console.log(`  missing: ${state.missing.join(', ')}`);
    incomplete ||= !state.installed;
  }
  if (incomplete) {
    const scope = options.project ? ` --project "${options.root}"` : '';
    console.log(`Next: npx building-design install${scope}`);
  } else {
    console.log('Next: invoke /building-design in Claude Code or /skill:building-design in Kimi Code.');
  }
}

function installOne(agent, options) {
  const target = destination(options.root, options.project, agent);
  const targetType = fs.lstatSync(target, { throwIfNoEntry: false });
  if (targetType && !targetType.isDirectory()) {
    if (!options.force) {
      console.log(`${agent}: skipped existing non-directory ${target} (use --force to replace)`);
      return;
    }
    fs.rmSync(target, { force: true });
  }
  fs.mkdirSync(target, { recursive: true });

  let copied = 0;
  let skipped = 0;
  for (const relative of sourceFiles()) {
    const source = path.join(SOURCE_ROOT, relative);
    const output = path.join(target, relative);
    if (fs.existsSync(output) && !options.force) {
      skipped += 1;
      continue;
    }
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.copyFileSync(source, output);
    fs.chmodSync(output, fs.statSync(source).mode);
    copied += 1;
  }
  console.log(`${agent}: ${target} (${copied} copied, ${skipped} preserved)`);
  const state = skillState(target);
  if (!state.installed) throw new Error(`Incomplete install at ${target}: ${state.missing.join(', ')}`);
}

function main() {
  if (process.argv.includes('--version') || process.argv.includes('-v')) {
    console.log(pkg.version);
    return;
  }
  const { command, options } = parse(process.argv.slice(2));
  if (options.help) {
    usage();
    return;
  }
  if (command === 'status') printStatus(options);
  else for (const agent of options.agents) installOne(agent, options);
}

try {
  main();
} catch (error) {
  console.error(`building-design: ${error.message}`);
  process.exitCode = 1;
}
