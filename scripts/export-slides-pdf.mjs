#!/usr/bin/env node
/**
 * Export slide decks to 16:9 multi-page PDFs.
 *
 *   pnpm slides:pdf              every module → pdf/<module>.pdf and pdf/slides.pdf
 *   pnpm slides:pdf 10           module 10 only
 *   pnpm slides:pdf 00 langchain several modules, also concatenated when more than one
 *
 * Uses the installed Google Chrome (or Edge / Playwright Chromium) to print
 * each deck's /print route. Page size matches scripts and SlideDeck.jsx.
 */

import { spawn } from 'node:child_process';
import { mkdir, readdir, readFile, writeFile } from 'node:fs/promises';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { PDFDocument } from 'pdf-lib';
import { chromium } from 'playwright-core';

const SLIDE_WIDTH = 1920;
const SLIDE_HEIGHT = 1080;

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const outDir = path.join(root, 'pdf');
const servers = new Set();

function stopServer(child) {
  if (!child?.pid || child.killed) return;
  try {
    process.kill(-child.pid, 'SIGTERM');
  } catch {
    child.kill('SIGTERM');
  }
}

function shutdown(code) {
  for (const child of servers) stopServer(child);
  if (code !== undefined) process.exit(code);
}

process.on('SIGINT', () => shutdown(130));
process.on('SIGTERM', () => shutdown(143));

function printHelp() {
  console.log(`Export slide decks to multi-page PDFs in pdf/.

Usage:
  pnpm slides:pdf              all modules, plus pdf/slides.pdf
  pnpm slides:pdf 10           one module, by number
  pnpm slides:pdf 03 langchain several modules, concatenated when more than one
`);
}

async function listModules() {
  const entries = await readdir(root, { withFileTypes: true });
  const modules = [];
  for (const entry of entries) {
    if (!entry.isDirectory() || !entry.name.startsWith('module-')) continue;
    const slidesDir = path.join(root, entry.name, 'slides');
    try {
      await readFile(path.join(slidesDir, 'package.json'), 'utf8');
    } catch {
      continue;
    }
    modules.push({ name: entry.name, slidesDir });
  }
  modules.sort((a, b) => a.name.localeCompare(b.name));
  return modules;
}

function matches(folder, arg) {
  const name = folder.toLowerCase();
  const query = arg.toLowerCase();
  if (name === query || name === `module-${query}`) return true;
  if (/^\d+$/.test(query)) {
    const num = query.padStart(2, '0');
    return name.startsWith(`module-${num}-`) || name === `module-${num}`;
  }
  return name.includes(query);
}

function selectModules(modules, args) {
  if (args.length === 0) return modules;
  const chosen = [];
  const missing = [];
  for (const arg of args) {
    const hits = modules.filter((mod) => matches(mod.name, arg));
    if (hits.length === 0) missing.push(arg);
    else chosen.push(...hits);
  }
  if (missing.length > 0) {
    const names = modules.map((mod) => mod.name).join('\n  ');
    throw new Error(`No slide deck matched: ${missing.join(', ')}\n\nModules:\n  ${names}`);
  }
  return [...new Map(chosen.map((mod) => [mod.name, mod])).values()];
}

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

function startVite(slidesDir, port) {
  const child = spawn(
    'pnpm',
    ['exec', 'vite', '--port', String(port), '--strictPort', '--host', '127.0.0.1'],
    { cwd: slidesDir, detached: true, stdio: ['ignore', 'pipe', 'pipe'] },
  );
  servers.add(child);

  let logs = '';
  const ready = new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`Vite did not start within 60s\n${logs}`));
    }, 60_000);

    const onData = (chunk) => {
      logs += chunk.toString();
      if (/Local:\s+http/.test(logs)) {
        clearTimeout(timer);
        resolve();
      }
    };

    child.stdout.on('data', onData);
    child.stderr.on('data', onData);
    child.on('error', (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on('exit', (code) => {
      clearTimeout(timer);
      if (code !== 0 && code !== null) {
        reject(new Error(`Vite exited with code ${code}\n${logs}`));
      }
    });
  });

  return { child, ready };
}

async function launchBrowser() {
  const attempts = [{ channel: 'chrome' }, { channel: 'msedge' }, {}];
  const errors = [];
  for (const options of attempts) {
    try {
      return await chromium.launch({ ...options, headless: true });
    } catch (error) {
      const label = options.channel ?? 'playwright chromium';
      errors.push(`${label}: ${error.message.split('\n')[0]}`);
    }
  }
  throw new Error(
    `Could not launch a browser for PDF export.\n${errors.join('\n')}\n` +
      'Install Google Chrome, or download Playwright Chromium with `pnpm exec playwright install chromium` after installing the playwright package.',
  );
}

async function concatenate(files, dest) {
  const merged = await PDFDocument.create();
  let expected = 0;
  for (const file of files) {
    const source = await PDFDocument.load(await readFile(file));
    expected += source.getPageCount();
    const pages = await merged.copyPages(source, source.getPageIndices());
    for (const page of pages) merged.addPage(page);
  }
  if (merged.getPageCount() !== expected) {
    throw new Error(`Combined PDF has ${merged.getPageCount()} pages, expected ${expected}`);
  }
  await writeFile(dest, await merged.save());
  return merged.getPageCount();
}

async function pdfPageCount(file) {
  const text = (await readFile(file)).toString('latin1');
  return text.match(/\/Type\s*\/Page(?!s)/g)?.length ?? 0;
}

async function exportDeck(browser, url, dest) {
  const page = await browser.newPage({
    viewport: { width: SLIDE_WIDTH, height: SLIDE_HEIGHT },
    deviceScaleFactor: 1,
  });
  try {
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.locator('#print-deck').waitFor();
    const slideCount = await page.locator('.print-slide').count();
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all(
        [...document.images].map((img) =>
          img.complete ? undefined : img.decode().catch(() => {}),
        ),
      );
    });
    await page.emulateMedia({ media: 'screen' });
    await page.pdf({
      path: dest,
      width: `${SLIDE_WIDTH}px`,
      height: `${SLIDE_HEIGHT}px`,
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: '0', right: '0', bottom: '0', left: '0' },
    });
    return slideCount;
  } finally {
    await page.close();
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) {
    printHelp();
    return;
  }

  const modules = selectModules(await listModules(), args);
  await mkdir(outDir, { recursive: true });
  const browser = await launchBrowser();
  const failures = [];
  const exported = [];

  try {
    for (const mod of modules) {
      const port = await freePort();
      const dest = path.join(outDir, `${mod.name}.pdf`);
      process.stdout.write(`${mod.name} … `);
      const { child, ready } = startVite(mod.slidesDir, port);
      try {
        await ready;
        const slideCount = await exportDeck(browser, `http://127.0.0.1:${port}/print`, dest);
        const pages = await pdfPageCount(dest);
        if (pages !== slideCount) {
          throw new Error(`PDF has ${pages} pages, deck has ${slideCount} slides`);
        }
        exported.push(dest);
        console.log(`${slideCount} slides → ${path.relative(root, dest)}`);
      } catch (error) {
        console.log('failed');
        console.error(error.message);
        failures.push(mod.name);
      } finally {
        stopServer(child);
        servers.delete(child);
      }
    }
  } finally {
    await browser.close();
  }

  if (exported.length > 1) {
    const combined = path.join(outDir, 'slides.pdf');
    const pages = await concatenate(exported, combined);
    console.log(`combined ${pages} slides → ${path.relative(root, combined)}`);
  }

  if (failures.length > 0) {
    console.error(`\nFailed: ${failures.join(', ')}`);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(error.message);
  shutdown(1);
});
