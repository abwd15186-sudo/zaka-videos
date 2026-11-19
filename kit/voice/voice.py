"""Voice polish for «ذكاء بالعراقي»: python3 voice.py in.(wav|m4a|mp3|mp4) out.wav [--speed 1.06] [--gap 0.25]
1) word timings (faster-whisper) -> cut pauses longer than --gap and filler words
2) ffmpeg chain: highpass, denoise, presence EQ, de-ess, compressor, speed, loudnorm -14 LUFS / -1 dBTP
Writes out.wav and out.json (kept segments, for syncing captions)."""
import sys,json,subprocess,argparse,numpy as np
ap=argparse.ArgumentParser();ap.add_argument('inp');ap.add_argument('out');ap.add_argument('--speed',type=float,default=1.06);ap.add_argument('--gap',type=float,default=0.25);ap.add_argument('--keep',type=float,default=0.12)
a=ap.parse_args()
FILLERS={'اممم','امم','ام','اه','آه','ااا','إمم','ممم','um','uh'}
sr=16000
raw=subprocess.run(['ffmpeg','-v','error','-i',a.inp,'-ac','1','-ar',str(sr),'-f','f32le','-'],capture_output=True).stdout
x=np.frombuffer(raw,np.float32)
from faster_whisper import WhisperModel
m=WhisperModel('small',compute_type='int8')
segs,_=m.transcribe(x,language='ar',word_timestamps=True,vad_filter=True)
words=[w for s in segs for w in s.words if w.word.strip(' .،,') not in FILLERS]
keep=[]
for w in words:
    s,e=max(0,w.start-a.keep),w.end+a.keep
    if keep and s-keep[-1][1]<a.gap: keep[-1][1]=e
    else: keep.append([s,e])
dur=len(x)/sr
keep=[[round(s,3),round(min(e,dur),3)] for s,e in keep]
sel='+'.join(f'between(t,{s},{e})' for s,e in keep)
chain=(f"aselect='{sel}',asetpts=N/SR/TB,highpass=f=80,afftdn=nf=-25,"
       "equalizer=f=200:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1:g=3,"
       "deesser=i=0.4,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=3,"
       f"atempo={a.speed},loudnorm=I=-14:TP=-1:LRA=7")
subprocess.run(['ffmpeg','-y','-v','error','-i',a.inp,'-af',chain,'-ar','48000','-ac','1',a.out],check=True)
json.dump({'keep':keep,'speed':a.speed,'words':[(w.word,w.start,w.end) for w in words]},open(a.out.rsplit('.',1)[0]+'.json','w'),ensure_ascii=False)
print(f'in {dur:.1f}s -> segments {len(keep)}, kept {sum(e-s for s,e in keep)/a.speed:.1f}s')
