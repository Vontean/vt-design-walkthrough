#!/usr/bin/env python3
"""Build a local review table, plus optional native HTML row fragments. Never writes online."""
import argparse, hashlib, html, json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from workflow_data import ordered_findings, COLUMN_ROLES, load_profile

KINDS={'implementation':'实现偏差','needs_confirmation':'待确认','design_change':'设计调整','coverage_request':'覆盖请求'}
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def groups(items):
    ordered={}
    for i in items: ordered.setdefault(i['module'],[]).append(i)
    return list(ordered.items())
def resolve(run,path):
    p=Path(path);return p if p.is_absolute() else run/p

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--confluence',type=Path,help='Confluence template JSON; enables HTML output')
    p.add_argument('--user-profile',type=Path,help='User preferences JSON; required with --confluence')
    p.add_argument('--date',default=date.today().isoformat(),help='Local date YYYY-MM-DD')
    p.add_argument('--attachments',type=Path,help='SHA256 to {file_id,collection,filename}')
    a=p.parse_args();date.fromisoformat(a.date);items=load(a.run/'findings.json');cases=load(a.run/'cases.json');items=ordered_findings(load(a.run/'run.json'),cases,items)
    def cell(s): return str(s).replace('|','\\|').replace('\n','<br>')
    def local_image(i,key):
        v=i.get(key)
        if not v:return '待补充'
        path=resolve(a.run,v).resolve()
        return f'![{cell(i["id"])}]({path.as_uri()})'
    lines=['# 设计走查复核稿','', '问题事实维护于 findings.json；请将审阅意见同步回数据后重新生成。','']
    for module,rows in groups(items):
        lines.extend([f'## {module}','', '| ID / 性质 / 平台 | 问题定位 | 设计稿表现 | 反馈 | 用户评价 |','| --- | --- | --- | --- | --- |'])
        for i in rows:
            scope=' → '.join(s for c in cases if c['id'] in i.get('case_ids',[]) for s in c['steps'])
            problem=cell(i['title']+'\n'+scope+'\n'+i['actual'])+'<br>'+local_image(i,'problem_image')
            design=cell(i['expected'])+'<br>'+local_image(i,'design_image')+f'<br>[Figma]({i["figma_url"]})'
            lines.append(f'| {cell(i["id"])} / {KINDS[i["kind"]]} / {cell(i["platform"])} | {problem} | {design} | {cell(i["feedback"])} | {cell(i["review"]+": "+i.get("review_note",""))} |')
        lines.append('')
    # 本地应用使用绝对文件路径，支持点击和图片预览。
    text='\n'.join(lines)
    for i in items:
        for key in ['problem_image','design_image']:
            if i.get(key):
                path=resolve(a.run,i[key]).resolve();text=text.replace(path.as_uri(),str(path).replace(' ','%20'))
    (a.run/'RECORD.md').write_text(text+'\n',encoding='utf-8')
    if not a.confluence:
        print(json.dumps({'local_records':len(items),'record':str(a.run/'RECORD.md')},ensure_ascii=False));return
    if not a.user_profile:p.error('--confluence requires --user-profile')
    profile=load_profile(a.confluence,a.user_profile); selected=[i for i in items if i.get('publish') and i['review']=='confirmed']
    if profile.get('column_roles')!=COLUMN_ROLES or len(profile['columns'])!=len(COLUMN_ROLES):
        raise ValueError('列角色顺序不匹配；当前 HTML adapter 只支持声明的九列，需显式适配新模板')
    mapping=load(a.attachments or a.run/'attachments.json')
    esc=lambda v:html.escape(str(v),quote=True)
    para=lambda v:'<p>'+esc(v).replace('\n','<br/>')+'</p>'
    def status(value,colour):return f'<span data-type="status" data-color="{esc(colour)}" data-status-style="bold">{esc(value)}</span>'
    def media(i,key,width):
        path=resolve(a.run,i[key]);digest=hashlib.sha256(path.read_bytes()).hexdigest();m=mapping[digest]
        return f'<figure data-type="media-single" data-layout="align-start" data-width="{int(width)}" data-width-type="pixel"><div data-type="media" data-media-type="file" data-id="{esc(m["file_id"])}" data-collection="{esc(m["collection"])}" data-alt="{esc(m.get("filename",path.name))}"></div></figure>'
    fragments=[];ordered=[];separator=0;cases=load(a.run/'cases.json')
    for index,(module,rows) in enumerate(groups(selected)):
        if index and profile.get('separator_rows'):
            fragments.append('<tr>'+('<td><p></p></td>'*9)+'</tr>');separator+=1
        for i in rows:
            if i['issue_type'] not in profile['issue_types']:raise ValueError('未知 issue_type: '+i['issue_type'])
            if urlparse(i['figma_url']).scheme!='https':raise ValueError('Figma link must be HTTPS')
            scope=' → '.join(s for c in cases if c['id'] in i.get('case_ids',[]) for s in c['steps'])
            problem=para(i['id']+' | '+i['title'])+para('性质：'+KINDS[i['kind']])+para('路径：'+scope)+para('实际：'+i['actual'])+media(i,'problem_image',profile['problem_width'])
            discussion=f'<p><strong><span style="color: {esc(profile["author_colour"])}">{esc(profile["author"])}</span></strong> <time datetime="{a.date}">{a.date}</time></p>'
            discussion+=para(i['feedback'])+para('期望：'+i['expected'])+para('用户评价：'+i.get('review_note',''))
            discussion+=f'<p><a href="{esc(i["figma_url"])}">Figma 正确位置 / 规则依据</a></p>'+media(i,'design_image',profile['design_width'])
            values=['<p></p>',para('').replace('<p></p>','<p>'+status(profile['issue_status'],profile['status_colour'])+'</p>'),'<p>'+status(i['issue_type'],profile.get('type_colours',{}).get(i['issue_type'],'neutral'))+'</p>',para(i['platform']),para(module),problem,discussion,'<p></p>','<p></p>']
            fragments.append('<tr>'+''.join('<td>'+v+'</td>' for v in values)+'</tr>');ordered.append(i['id'])
    (a.run/'confluence-rows.html').write_text('\n'.join(fragments)+'\n',encoding='utf-8')
    (a.run/'confluence-plan.json').write_text(json.dumps({'ids':ordered,'separator_count':separator,'date':a.date,'profile':profile['name'],'rows_file':'confluence-rows.html'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'local_records':len(items),'selected':len(selected),'separator_rows':separator},ensure_ascii=False))
if __name__=='__main__':main()
