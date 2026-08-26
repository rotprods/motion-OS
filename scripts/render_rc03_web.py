from pathlib import Path
import asyncio, subprocess, shutil
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data/rc03'; FR=OUT/'frames'; W,H,FPS,DUR=1080,1920,30,10
async def main():
    if FR.exists(): shutil.rmtree(FR)
    FR.mkdir(parents=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--allow-file-access-from-files','--disable-gpu']);server=subprocess.Popen(['python','-m','http.server','8765','--bind','127.0.0.1','--directory',str(OUT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);await asyncio.sleep(.35);page=await browser.new_page(viewport={'width':W,'height':H},device_scale_factor=1);await page.goto('http://127.0.0.1:8765/index.html',wait_until='load')
        for n in range(FPS*DUR): await page.evaluate('(t)=>window.setMotionTime(t)',n/FPS); await page.screenshot(path=str(FR/f'{n:04d}.png'),type='png')
        await browser.close();server.terminate()
    silent=OUT/'rc03_silent.mp4';final=OUT/'MOTION_OS_RC03.mp4';subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',str(FR/'%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','17','-preset','medium',str(silent)],check=True);score=ROOT/'data/rc_candidate/score.wav';shutil.copy2(silent,final) if not score.exists() else subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(silent),'-i',str(score),'-c:v','copy','-c:a','aac','-b:a','192k','-shortest',str(final)],check=True);print(final)
if __name__=='__main__':asyncio.run(main())
