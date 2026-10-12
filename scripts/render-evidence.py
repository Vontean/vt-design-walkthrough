#!/usr/bin/env python3
"""Crop and frame real screenshots using normalized original-image coordinates. Requires Pillow."""
import argparse, json, re
from pathlib import Path
from PIL import Image, ImageDraw

def rect(v):
    if not isinstance(v,list) or len(v)!=4 or any(not isinstance(x,(int,float)) or isinstance(x,bool) for x in v):
        raise ValueError('矩形必须是 [x,y,width,height]')
    x,y,w,h=v
    if x<0 or y<0 or w<=0 or h<=0 or x+w>1.000001 or y+h>1.000001: raise ValueError('矩形超出原图或尺寸无效')
    return x,y,w,h

def panel(spec,base,width,colour):
    source=Path(spec['source']); source=source if source.is_absolute() else base/source
    with Image.open(source) as im:
        im=im.convert('RGBA'); iw,ih=im.size
        x,y,w,h=rect(spec.get('crop',[0,0,1,1]))
        left,top,right,bottom=round(x*iw),round(y*ih),round((x+w)*iw),round((y+h)*ih)
        if right-left<2 or bottom-top<2: raise ValueError('裁切区域过小')
        cropped=im.crop((left,top,right,bottom)); scale=width/cropped.width
        cropped=cropped.resize((width,max(1,round(cropped.height*scale))),Image.Resampling.LANCZOS)
        output=Image.new('RGB',cropped.size,'white'); output.paste(cropped,mask=cropped.getchannel('A'))
    draw=ImageDraw.Draw(output); stroke=max(2,round(width/120))
    for b in spec.get('boxes',[]):
        bx,by,bw,bh=rect(b)
        if bx<x-1e-6 or by<y-1e-6 or bx+bw>x+w+1e-6 or by+bh>y+h+1e-6: raise ValueError('裁切必须包含完整标注框')
        coords=[round((bx*iw-left)*scale),round((by*ih-top)*scale),round(((bx+bw)*iw-left)*scale),round(((by+bh)*ih-top)*scale)]
        coords[0]=max(stroke//2,coords[0]);coords[1]=max(stroke//2,coords[1])
        coords[2]=min(width-1-stroke//2,coords[2]);coords[3]=min(output.height-1-stroke//2,coords[3])
        draw.rectangle(coords,outline=colour,width=stroke)
    return output

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--config',type=Path,help='Default: RUN/annotations.json; source paths relative to RUN')
    p.add_argument('--width',type=int,default=600)
    a=p.parse_args()
    if not 100<=a.width<=2400: p.error('width 必须为 100–2400')
    config=json.loads((a.config or a.run/'annotations.json').read_text(encoding='utf-8')); out=a.run/'evidence';out.mkdir(exist_ok=True)
    results=[];seen=set()
    for item in config['items']:
        ident=item['id']
        if not re.fullmatch(r'[A-Za-z0-9_-]+',ident) or ident in seen: raise ValueError('无效或重复 ID')
        seen.add(ident)
        parts=[panel(s,a.run,a.width,'#ff1717') for s in item.get('extra_problems',[])+[item['problem']]]
        actual=Image.new('RGB',(a.width,sum(i.height for i in parts)+20*(len(parts)-1)),'white'); y=0
        for part in parts: actual.paste(part,(0,y));y+=part.height+20
        design=panel(item['design'],a.run,a.width,'#2489e7')
        comparison=Image.new('RGB',(a.width*2+20,max(actual.height,design.height)),'white')
        comparison.paste(actual,(0,0));comparison.paste(design,(a.width+20,0))
        entry={'id':ident}
        for key,im in [('problem',actual),('design',design),('comparison',comparison)]:
            file=out/f'{ident}-{key}.png'; im.save(file);entry[key+'_image']=str(file.relative_to(a.run));entry[key+'_size']=list(im.size)
        results.append(entry)
    (out/'render-manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'rendered':len(results),'manifest':str(out/'render-manifest.json')},ensure_ascii=False))
if __name__=='__main__': main()
