from pathlib import Path
import wave,math,struct
def synth_score(path,duration=10.0,sr=48000,bpm=112):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);n=int(duration*sr);beat=60/bpm;impacts=[0,.95,2.85,4.35,5.35,7.25,8.85]
    with wave.open(str(path),'w') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);frames=bytearray()
        for i in range(n):
            t=i/sr;s=.07*math.sin(2*math.pi*55*t)+.035*math.sin(2*math.pi*110*t)
            for hit in impacts:
                dt=t-hit
                if 0<=dt<.18:s+=.26*math.exp(-dt*22)*math.sin(2*math.pi*(90+220*dt)*dt)
            phase=t%beat
            if phase<.035:s+=.05*math.exp(-phase*80)*math.sin(2*math.pi*1200*t)
            q=int(max(-1,min(1,s))*32767);frames.extend(struct.pack('<hh',q,q))
        w.writeframes(frames)
    return {'path':str(path),'duration':duration,'sample_rate':sr,'bpm':bpm,'cues':impacts}
