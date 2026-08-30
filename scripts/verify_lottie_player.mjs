import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function parseArgs(argv) {
  const out = {root: path.join(ROOT, 'runtime', 'lottie'), chrome: '', playerVersion: ''};
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (key === '--root') out.root = path.resolve(argv[++i]);
    else if (key === '--chrome') out.chrome = argv[++i];
    else if (key === '--player-version') out.playerVersion = argv[++i];
    else throw new Error(`unsupported argument: ${key}`);
  }
  if (!out.chrome) throw new Error('--chrome is required');
  if (!out.playerVersion) throw new Error('--player-version is required');
  return out;
}

function sha256(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

async function sha256File(filePath) {
  return sha256(await fs.readFile(filePath));
}

function mime(filePath) {
  if (filePath.endsWith('.html')) return 'text/html; charset=utf-8';
  if (filePath.endsWith('.js')) return 'text/javascript; charset=utf-8';
  if (filePath.endsWith('.json')) return 'application/json; charset=utf-8';
  if (filePath.endsWith('.png')) return 'image/png';
  return 'application/octet-stream';
}

async function startServer(root) {
  const rootPath = path.resolve(root);
  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://127.0.0.1');
      if (url.pathname === '/favicon.ico') {
        res.writeHead(204, {'cache-control': 'no-store'});
        res.end();
        return;
      }
      const relative = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname).replace(/^\/+/, '');
      const resolved = path.resolve(rootPath, relative);
      const prefix = `${rootPath}${path.sep}`;
      if (resolved !== rootPath && !resolved.startsWith(prefix)) {
        res.writeHead(403); res.end('forbidden'); return;
      }
      const payload = await fs.readFile(resolved);
      res.writeHead(200, {'content-type': mime(resolved), 'cache-control': 'no-store'});
      res.end(payload);
    } catch (error) {
      res.writeHead(error?.code === 'ENOENT' ? 404 : 500);
      res.end('error');
    }
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  return server;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const animationPath = path.join(args.root, 'animation.json');
  const contractPath = path.join(args.root, 'player_contract.json');
  const compilerEvidencePath = path.join(args.root, 'compiler_evidence.json');
  const bundlePath = path.join(args.root, 'lottie.min.js');
  const integrityPath = path.join(args.root, 'npm_integrity.txt');
  const puppeteerIntegrityPath = path.join(args.root, 'puppeteer_integrity.txt');
  const screenshots = path.join(args.root, 'screenshots');
  await fs.mkdir(screenshots, {recursive: true});

  const document = JSON.parse(await fs.readFile(animationPath, 'utf8'));
  const contract = JSON.parse(await fs.readFile(contractPath, 'utf8'));
  const compilerEvidence = JSON.parse(await fs.readFile(compilerEvidencePath, 'utf8'));
  const animationFileHash = await sha256File(animationPath);
  if (animationFileHash !== compilerEvidence.animation_file_sha256) {
    throw new Error('animation.json bytes do not match compiler evidence');
  }
  if (contract.document_sha256 !== compilerEvidence.document_sha256) {
    throw new Error('player contract document hash does not match compiler evidence');
  }
  if (Number(contract.expected_frame_count) !== Number(compilerEvidence.expected_frame_count)) {
    throw new Error('player contract frame count does not match compiler evidence');
  }
  const expectedFrames = Number(contract.expected_frame_count);
  if (!Number.isInteger(expectedFrames) || expectedFrames <= 0) throw new Error('player contract frame count missing');
  const frames = [0, Math.floor(expectedFrames / 2), expectedFrames - 1];

  const server = await startServer(args.root);
  const {port} = server.address();
  const browser = await puppeteer.launch({
    executablePath: args.chrome,
    headless: true,
    args: ['--no-sandbox', '--disable-gpu'],
  });
  const frameEvidence = [];
  try {
    for (const frame of frames) {
      const page = await browser.newPage();
      await page.setViewport({width: 640, height: 360, deviceScaleFactor: 1});
      const consoleErrors = [];
      const pageErrors = [];
      page.on('console', (message) => {
        if (message.type() === 'error') consoleErrors.push(message.text());
      });
      page.on('pageerror', (error) => pageErrors.push(String(error)));
      const url = `http://127.0.0.1:${port}/index.html?frame=${frame}`;
      await page.goto(url, {waitUntil: 'networkidle0', timeout: 15000});
      await page.waitForFunction(
        () => ['true', 'error'].includes(document.documentElement.dataset.ready || ''),
        {timeout: 10000},
      );
      const state = await page.evaluate(() => ({
        ready: document.documentElement.dataset.ready ?? null,
        errorType: document.documentElement.dataset.errorType ?? null,
        requestedFrame: document.documentElement.dataset.requestedFrame ?? null,
        currentFrame: document.documentElement.dataset.currentFrame ?? null,
        totalFrames: document.documentElement.dataset.totalFrames ?? null,
        svgCount: document.documentElement.dataset.svgCount ?? null,
      }));
      if (state.ready !== 'true') {
        throw new Error(`lottie player readiness failure frame=${frame} state=${JSON.stringify(state)} console=${JSON.stringify(consoleErrors)} page=${JSON.stringify(pageErrors)}`);
      }
      const requested = Number(state.requestedFrame);
      const current = Number(state.currentFrame);
      const total = Number(state.totalFrames);
      const svgCount = Number(state.svgCount);
      if (requested !== frame || current !== frame) throw new Error(`lottie frame seek mismatch requested=${frame} current=${current}`);
      if (total !== expectedFrames) throw new Error(`lottie totalFrames mismatch ${total}!=${expectedFrames}`);
      if (svgCount !== 1) throw new Error(`expected exactly one SVG player surface, observed ${svgCount}`);
      if (consoleErrors.length || pageErrors.length) throw new Error(`browser errors at frame ${frame}: ${JSON.stringify({consoleErrors, pageErrors})}`);

      const screenshot = path.join(screenshots, `frame_${String(frame).padStart(4, '0')}.png`);
      await page.screenshot({path: screenshot, type: 'png'});
      const stat = await fs.stat(screenshot);
      frameEvidence.push({
        frame,
        requested_frame: requested,
        current_frame: current,
        total_frames: total,
        svg_count: svgCount,
        png_sha256: await sha256File(screenshot),
        png_bytes: stat.size,
      });
      await page.close();
    }
  } finally {
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }

  if (new Set(frameEvidence.map((item) => item.png_sha256)).size < 2) {
    throw new Error('physical Lottie frame evidence is visually invariant across sampled frames');
  }

  const evidence = {
    schema: 'motion-os.lottie-physical-player/v2',
    renderer: 'lottie-web',
    browser_transport: 'puppeteer-core-devtools',
    player_version: args.playerVersion,
    player_bundle_sha256: await sha256File(bundlePath),
    npm_dist_integrity: (await fs.readFile(integrityPath, 'utf8')).trim(),
    puppeteer_dist_integrity: (await fs.readFile(puppeteerIntegrityPath, 'utf8')).trim(),
    compiler_evidence_sha256: await sha256File(compilerEvidencePath),
    document_sha256: contract.document_sha256,
    animation_file_sha256: animationFileHash,
    expected_frame_count: expectedFrames,
    visual_duration_authority: 'frame_count/fps',
    fps: document.fr,
    frame_evidence: frameEvidence,
    stable_layer_ids: contract.stable_layer_ids ?? [],
    authority: 'RENDERER_EXECUTED',
    creative_authority: 'none',
  };
  await fs.writeFile(path.join(args.root, 'player_evidence.json'), `${JSON.stringify(evidence, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify(evidence, null, 2));
}

main().catch((error) => {
  console.error(error?.stack || String(error));
  process.exitCode = 1;
});
