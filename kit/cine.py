import math, random, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W,H,FPS=1080,1920,30
FONT="/home/claude/fonts/Cairo.ttf"
def font(sz,wt="Black"):
    f=ImageFont.truetype(FONT,sz); f.set_variation_by_name(wt); return f
SPEED=1.07
K=1/SPEED
ORANGE=(255,128,40); WHITE=(255,255,255); CREAM=(255,236,214)
# ---------------- content ----------------
SCENES=[ # start(orig s), label, light color, hero text, card
 (0.0 ,"الهوك",      (255,90,40),  "لا!",       None),
 (3.26,"الخطوة ١",   (255,140,40), "1",       "A"),
 (8.0 ,"الخطوة ٢",   (60,120,255), "2",       "C"),
 (11.92,"الخطوة ٣",  (170,80,255), "3",       "D"),
 (15.7,"ترجمة",      (0,200,170),  "A = ع",  "F"),
 (19.04,"مجاني",     (255,190,40), "$0",      None),
]
CARD_SWITCH=[(3.26,"A"),(5.5,"B"),(8.0,"C"),(11.92,"D"),(13.42,"E"),(15.7,"F"),(19.04,None)]
PHRASES=[ # start, words, key, pose
 (0.0 ,"لا تكتب الملزمة","الملزمة","surprised"),
 (1.2 ,"بإيدك بعد!","بإيدك","surprised"),
 (1.82,"شوف هالحركة","هالحركة","point"),
 (3.26,"افتح كوكل","كوكل","point"),
 (4.3 ,"واضغط أيقونة الكاميرا","الكاميرا","point"),
 (6.04,"الي بخانة البحث","البحث","think"),
 (8.0 ,"وجّه الكاميرا على الورقة","الورقة","point"),
 (9.84,"واضغط كلمة «نص»","«نص»","wave"),
 (11.92,"حدد الكلام","حدد","think"),
 (12.62,"واضغط نسخ","نسخ","point"),
 (13.42,"والصقه وين ما تريد","تريد","laugh"),
 (14.56,"حتى بالواتساب","بالواتساب","laugh"),
 (15.7,"وإذا الملزمة إنكليزي","إنكليزي","surprised"),
 (17.4,"اضغط ترجمة","ترجمة","point"),
 (18.12,"ويطلعلك عربي","عربي","laugh"),
 (19.04,"مجاني","مجاني","thumbs"),
 (20.4,"وموجود بكل تلفون","تلفون","wave"),
 (21.6,"اكتب «جربتها»","«جربتها»","point"),
 (22.48,"بالتعليقات","بالتعليقات","point"),
 (23.08,"واشترك حتى يوصلك","اشترك","thumbs"),
 (24.34,"كل يوم شي جديد","جديد","laugh"),
]
END=26.0  # where logo starts (orig)
SRC='/home/claude/brand/out/ep02_google_lens_real_v2.mp4'
# ---------------- assets ----------------
POSES={n:Image.open(f'/home/claude/mascot/pose_{n}.png').convert('RGBA') for n in ['point','wave','surprised','laugh','think','thumbs']}
PH=560
POSES={k:v.resize((int(v.width*PH/v.height),PH),Image.LANCZOS) for k,v in POSES.items()}
sys.path.insert(0,'/home/claude/ep02'); 
import os; os.chdir('/home/claude/ep02')
def card(k):
    CROPS={"A":(300,150,1000,330),"B":(300,190,1000,560),"C":(400,80,1000,440),"D":(400,80,1000,440),"E":(400,100,1000,630),"F":(330,330,760,641)}
    im=Image.open(f"shots/{k}.jpg").convert("RGB")
    im.paste(im.crop((0,20,90,90)).filter(ImageFilter.GaussianBlur(14)),(0,20))
    x0,y0,x1,y1=CROPS[k]; CW=820; s=CW/(x1-x0)
    im=im.crop(CROPS[k]).resize((CW,int((y1-y0)*s)),Image.LANCZOS).convert("RGBA")
    if im.height>620: im=im.crop((0,0,CW,620))
    m=Image.new("L",im.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,im.size[0]-1,im.size[1]-1],radius=28,fill=255); im.putalpha(m)
    out=Image.new("RGBA",(im.width+120,im.height+120),(0,0,0,0))
    sh=Image.new("RGBA",out.size,(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([60,80,60+im.width,80+im.height],radius=30,fill=(0,0,0,200))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
    bd=Image.new("RGBA",out.size,(0,0,0,0)); ImageDraw.Draw(bd).rounded_rectangle([57,57,63+im.width,63+im.height],radius=31,outline=(255,255,255,70),width=3)
    out.alpha_composite(im,(60,60)); out.alpha_composite(bd)
    return out
CARDS={k:card(k) for k in "ABCDEF"}
os.chdir('/home/claude/cine')
# background base + particles
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
BASE=np.zeros((H,W,3),np.float32)+np.array([8,6,10],np.float32)
vign=np.clip(1-((xx-W/2)**2/(W*0.75)**2+(yy-H*0.55)**2/(H*0.7)**2),0,1)[...,None]
pool=np.exp(-(((xx-W/2)/(W*0.55))**2+((yy-H*0.62)/(H*0.33))**2))[...,None]
cone=(np.clip(1-np.abs(xx-W/2)/(120+ (yy/H)*380),0,1)*np.clip(yy/H*1.4,0,1)*(yy<H*0.98))[...,None]*0.35
rng=np.random.default_rng(3)
PART=[(rng.uniform(0,W),rng.uniform(0,H),rng.uniform(1.5,4),rng.uniform(8,30),rng.uniform(0,6.28)) for _ in range(70)]
GRAIN=[(rng.normal(0,7,(H//2,W//2,1))).astype(np.float32) for _ in range(6)]
def lerpc(a,b,t): return tuple(a[i]+(b[i]-a[i])*t for i in range(3))
def scene_at(t):
    i=max(j for j,s in enumerate(SCENES) if s[0]<=t); return i
def light_color(t):
    i=scene_at(t); c=SCENES[i][2]
    if i>0 and t-SCENES[i][0]<0.45:
        c=lerpc(SCENES[i-1][2],c,(t-SCENES[i][0])/0.45)
    return np.array(c,np.float32)
def background(t,fi):
    c=light_color(t)
    img=BASE+pool*c*0.55+cone*np.array([255,240,220],np.float32)*0.5
    img=img*(0.45+0.55*vign)
    g=GRAIN[fi%6]; g=np.repeat(np.repeat(g,2,0),2,1)
    img=np.clip(img+g,0,255).astype(np.uint8)
    im=Image.fromarray(img).convert('RGBA'); d=ImageDraw.Draw(im,'RGBA')
    for (x,y,r,sp,ph) in PART:
        yy_=(y-t*sp)%H; xx_=x+math.sin(t*0.7+ph)*12
        a=int(90+70*math.sin(t*2+ph))
        d.ellipse([xx_-r,yy_-r,xx_+r,yy_+r],fill=(255,210,160,max(0,a)))
    return im
# text helpers
_tc={}
def text_img(s,sz,fill,wt="Black"):
    key=(s,sz,fill,wt)
    if key in _tc: return _tc[key]
    f=font(sz,wt); tmp=ImageDraw.Draw(Image.new('RGBA',(10,10)))
    bb=tmp.textbbox((0,0),s,font=f,direction='rtl',language='ar')
    im=Image.new('RGBA',(bb[2]-bb[0]+40,bb[3]-bb[1]+40),(0,0,0,0))
    ImageDraw.Draw(im).text((20-bb[0],20-bb[1]),s,font=f,fill=fill,direction='rtl',language='ar')
    _tc[key]=im; return im
def phrase_img(words,key):
    parts=words.split(' ')
    imgs=[]
    for w in parts:
        if w==key:
            ti=text_img(w,92,(20,12,8))
            box=Image.new('RGBA',(ti.width+24,ti.height+6),(0,0,0,0))
            ImageDraw.Draw(box).rounded_rectangle([0,4,box.width-1,box.height-1],radius=18,fill=ORANGE+(255,))
            box.alpha_composite(ti,(12,0)); imgs.append(box)
        else: imgs.append(text_img(w,92,WHITE))
    gap=14; Wt=sum(i.width for i in imgs)+gap*(len(imgs)-1); Ht=max(i.height for i in imgs)
    out=Image.new('RGBA',(Wt,Ht),(0,0,0,0)); x=Wt
    for i in imgs:  # RTL: first word on the right
        x-=i.width; out.alpha_composite(i,(x,(Ht-i.height)//2)); x-=gap
    if out.width>W-80:
        s=(W-80)/out.width; out=out.resize((int(out.width*s),int(out.height*s)),Image.LANCZOS)
    sh=out.copy(); sh=Image.new('RGBA',out.size,(0,0,0,0)); 
    a=out.split()[3].filter(ImageFilter.GaussianBlur(10)); sh.putalpha(a.point(lambda v:int(v*0.8)))
    res=Image.new('RGBA',(out.width+30,out.height+30),(0,0,0,0)); res.alpha_composite(sh,(15,22)); res.alpha_composite(out,(15,15))
    return res
PHI=[phrase_img(p[1],p[2]) for p in PHRASES]
def hero_img(s,color):
    f=210 if len(s)<=2 else 150
    t=text_img(s,f,color)
    glow=t.copy(); glow=glow.filter(ImageFilter.GaussianBlur(22))
    out=Image.new('RGBA',(t.width+80,t.height+80),(0,0,0,0)); out.alpha_composite(glow,(40,40)); out.alpha_composite(glow,(40,40)); out.alpha_composite(t,(40,40))
    return out
HERO=[hero_img(s[3],(255,150,60) if s[3] not in ('$0',) else (255,214,60)) for s in SCENES]
LAB=[text_img(f"0{i+1} / 0{len(SCENES)}  ·  {s[1]}",34,(255,255,255,200),"SemiBold") for i,s in enumerate(SCENES)]
def ease_out_back(t):
    t=max(0,min(1,t)); c1=1.70158; c3=c1+1; return 1+c3*(t-1)**3+c1*(t-1)**2
def ease(t): t=max(0,min(1,t)); return t*t*(3-2*t)
def place(fr,im,cx,cy,sc=1.0,alpha=1.0,rot=0):
    if sc!=1: im=im.resize((max(1,int(im.width*sc)),max(1,int(im.height*sc))),Image.BILINEAR)
    if rot: im=im.rotate(rot,resample=Image.BICUBIC,expand=True)
    if alpha<1:
        im=im.copy(); a=im.split()[3].point(lambda v:int(v*alpha)); im.putalpha(a)
    fr.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))
def frame(t,fi):
    fr=background(t,fi)
    si=scene_at(t); s0=SCENES[si][0]; ds=t-s0
    # top counter + progress
    fr.alpha_composite(LAB[si],(W-LAB[si].width-40,60))
    d=ImageDraw.Draw(fr,'RGBA'); d.line([(60,128),(W-60,128)],fill=(255,255,255,40),width=3)
    d.line([(W-60-(W-120)*min(1,t/END),128),(W-60,128)],fill=ORANGE+(220,),width=3)
    # hero
    hs=ease_out_back(ds/0.45); fl=math.sin(t*2.2)*8
    if SCENES[si][4] is None or si==0:
        place(fr,HERO[si],W/2,520+fl,sc=0.6+0.4*hs,alpha=min(1,ds/0.2))
    else:
        place(fr,HERO[si],W/2,330+fl,sc=(0.6+0.4*hs)*0.62,alpha=min(1,ds/0.2))
    # card
    ck=None; ct=0
    for (st,k) in CARD_SWITCH:
        if t>=st: ck=k; ct=st
    if ck:
        dt=t-ct; k=ease_out_back(dt/0.5)
        rot=(-3 if CARD_SWITCH.index((ct,ck))%2 else 3)*(1-0.4*ease(dt/0.5))+math.sin(t*1.3)*0.6
        place(fr,CARDS[ck],W/2+(1-ease(dt/0.4))*(220 if CARD_SWITCH.index((ct,ck))%2 else -220),760+math.sin(t*1.7)*6,sc=0.85+0.15*k,alpha=min(1,dt/0.15),rot=rot)
    # phrase
    pi=max(j for j,p in enumerate(PHRASES) if p[0]<=t)
    dp=t-PHRASES[pi][0]
    place(fr,PHI[pi],W/2,1215,sc=0.75+0.25*ease_out_back(dp/0.25),alpha=min(1,dp/0.08))
    # character
    pose=PHRASES[pi][3]; im=POSES[pose]
    pop=ease_out_back(dp/0.3) if (pi==0 or PHRASES[pi-1][3]!=pose) else 1
    breathe=1+0.012*math.sin(t*3.1)
    hop=max(0,math.sin(min(1,dp/0.3)*math.pi))*40 if (pi==0 or PHRASES[pi-1][3]!=pose) else 0
    sc=(0.82+0.18*pop)*breathe
    # shadow
    d=ImageDraw.Draw(fr,'RGBA'); sw=170*(1-hop/200)
    d.ellipse([W/2-sw,1872,W/2+sw,1902],fill=(0,0,0,150))
    imr=im.resize((int(im.width*sc),int(im.height*sc)),Image.BILINEAR)
    fr.alpha_composite(imr,(int(W/2-imr.width/2),int(1888-imr.height-hop)))
    return fr
def render(out='cine_ep02.mp4'):
    n_main=int(END/SPEED*FPS)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','main_silent.mp4'],stdin=subprocess.PIPE)
    for n in range(n_main):
        t=n/FPS*SPEED
        enc.stdin.write(frame(t,n).tobytes())
    enc.stdin.close(); enc.wait()
if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='test':
        for tt in [0.5,2.5,4.5,9,13,16.5,19.5,23.5]:
            frame(tt,int(tt*30)).convert('RGB').resize((270,480)).save(f'test_{tt}.jpg')
        sys.exit()
