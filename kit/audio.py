import numpy as np, subprocess, wave, json
import cine
SR=48000; SP=cine.SPEED
# voice main sped up
subprocess.run(['ffmpeg','-v','error','-y','-i',cine.SRC,'-t',str(cine.END),'-vn','-af',f'atempo={SP},volume=1.05','-ac','2','-ar',str(SR),'voice_main.wav'],check=True)
def rd(p):
    w=wave.open(p); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)/32768; return a
v=rd('voice_main.wav')
N=int(cine.END/SP*SR); v=np.pad(v,((0,max(0,N-len(v))),(0,0)))[:N]
rng=np.random.default_rng(1)
def whoosh(d=0.45):
    n=int(d*SR); x=rng.normal(0,1,n)
    # band sweep via simple moving lowpass with changing window
    out=np.zeros(n); acc=0
    for i in range(n):
        a=0.02+0.4*(i/n); acc+= a*(x[i]-acc); out[i]=acc
    out-= np.convolve(out,np.ones(40)/40,'same')
    env=np.sin(np.linspace(0,np.pi,n))**2
    return out*env*0.5
def pop(f0=900,f1=380,d=0.07):
    n=int(d*SR); t=np.arange(n)/SR; f=np.linspace(f0,f1,n)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*45)*0.28
def ding():
    n=int(0.9*SR); t=np.arange(n)/SR
    return (np.sin(2*np.pi*1320*t)+0.5*np.sin(2*np.pi*1980*t))*np.exp(-t*5)*0.18
W_=whoosh(); P=pop(); D=ding()
def add(sig,t0,g=1.0):
    i=int(t0/SP*SR); j=min(N,i+len(sig))
    if i<N: v[i:j]+=sig[:j-i,None]*g
for st,k in cine.CARD_SWITCH: add(W_,max(0,st-0.15),0.8)
for s in cine.SCENES[1:]: add(W_,max(0,s[0]-0.1),0.5)
prev=None
for p in cine.PHRASES:
    add(P,p[0],0.55 if p[3]!=prev else 0.3); prev=p[3]
add(D,19.04,1.0)
v=np.clip(v,-1,1)
w=wave.open('main_audio.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((v*32767).astype(np.int16).tobytes()); w.close()
