import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const source=path.join(ROOT,'runtime','lottie');
const frames=path.join(source,'frames');
fs.rmSync(frames,{recursive:true,force:true}); fs.mkdirSync(frames,{recursive:true});
const chrome=process.env.CHROME_BIN; if(!chrome) throw new Error('CHROME_BIN missing');
const mime={'.html':'text/html','.js':'application/javascript','.json':'application/json','.png':'image/png'};
const server=http.createServer((req,res)=>{const raw=new URL(req.url,'http://127.0.0.1').pathname; const rel=raw==='/'?'index.html':raw.slice(1); const p=path.resolve(source,rel); if(!p.startsWith(source)){res.writeHead(403);res.end();return;} if(!fs.existsSync(p)){res.writeHead(rel==='favicon.ico'?204:404);res.end();return;} res.writeHead(200,{'content-type':mime[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);});
await new Promise(r=>server.listen(0,'127.0.0.1',r)); const port=server.address().port;
let browser; const errors=[];
try{
  browser=await puppeteer.launch({executablePath:chrome,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  const page=await browser.newPage(); await page.setViewport({width:640,height:360,deviceScaleFactor:1});
  page.on('console',msg=>{if(msg.type()==='error') errors.push('console:'+msg.text())}); page.on('pageerror',err=>errors.push('page:'+String(err)));
  await page.goto(`http://127.0.0.1:${port}/`,{waitUntil:'networkidle0'}); await page.waitForFunction(()=>document.documentElement.dataset.ready==='true',{timeout:20000});
  const hashes=[];
  for(let i=0;i<90;i++){
    const state=await page.evaluate(frame=>window.__seek(frame),i); if(state.frame!==i||state.total!==90||state.svg!==1) throw new Error(`frame-contract:${i}:${JSON.stringify(state)}`);
    await new Promise(r=>setTimeout(r,5));
    const out=path.join(frames,`frame-${String(i).padStart(3,'0')}.png`); await page.screenshot({path:out,omitBackground:true,clip:{x:0,y:0,width:640,height:360}});
    hashes.push(crypto.createHash('sha256').update(fs.readFileSync(out)).digest('hex'));
  }
  if(errors.length) throw new Error(errors.join('|')); if(new Set(hashes).size<10) throw new Error('insufficient-frame-diversity');
  const evidence={schema:'motion-os.lottie-sequence/v1',player:'lottie-web@5.13.0',transport:'puppeteer-core@24.16.0',frame_count:90,width:640,height:360,unique_frame_hashes:new Set(hashes).size,frame_hashes:{first:hashes[0],mid:hashes[45],last:hashes[89]},browser_errors:errors,authority:'PHYSICALLY_EXECUTED'};
  fs.writeFileSync(path.join(source,'sequence_evidence.json'),JSON.stringify(evidence,null,2)+'\n'); console.log(JSON.stringify(evidence,null,2));
} finally {if(browser) await browser.close(); server.close();}
