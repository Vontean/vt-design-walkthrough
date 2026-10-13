#!/usr/bin/env python3
"""Validate coverage, evidence, review selection and optional server readback. Exit nonzero on errors."""
import argparse,json
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from workflow_data import ordered_findings, load_profile

KINDS={'implementation','needs_confirmation','design_change','coverage_request'}
STATES={'pending','pass','issue','blocked','not_applicable'}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--confluence',type=Path)
    p.add_argument('--user-profile',type=Path)
    p.add_argument('--writeback',action='store_true')
    p.add_argument('--final',action='store_true',help='Require all cases and Pages to be resolved')
    a=p.parse_args();errors=[]
    def read(name):return json.loads((a.run/name).read_text(encoding='utf-8'))
    def check(ok,message):
        if not ok:errors.append(message)
    def ids(rows,label):
        result={}
        for i in rows:
            ident=i.get('id');check(bool(ident) and ident not in result,label+'：缺失或重复 ID '+str(ident));result[ident]=i
        return result
    run=read('run.json');cases=read('cases.json');findings=read('findings.json');cm=ids(cases,'case');fm=ids(findings,'finding');pm=ids(run['pages'],'page')
    for c in cases:
        label=c['id'];check(c.get('page_id') in pm,label+'：未知 Page');check(c.get('platform') in run['platforms'],label+'：未知平台')
        check(c.get('status') in STATES,label+'：无效状态')
        for key in ['module','expected','figma_url','steps']:check(bool(c.get(key)),label+'：缺 '+key)
        for key in ['steps','preconditions']:check(isinstance(c.get(key),list),label+'：'+key+' 应为数组')
        if c.get('status') in {'blocked','not_applicable'}:check(bool(c.get('reason')),label+'：需说明原因')
        if c.get('status')=='issue':check(bool(c.get('finding_ids')) and all(i in fm for i in c['finding_ids']),label+'：问题关联无效')
        if a.final:
            check(c.get('status')!='pending',label+'：仍待执行')
            if c.get('status')=='pass':check(bool(c.get('actual')),label+'：通过项缺实际观察')
    manifest_path=a.run/'evidence/render-manifest.json'
    rendered=ids(json.loads(manifest_path.read_text(encoding='utf-8')),'render') if manifest_path.exists() else {}
    for i in findings:
        label=i['id'];check(i.get('kind') in KINDS,label+'：无效性质');check(i.get('review') in {'pending','confirmed','rejected'},label+'：无效审阅状态')
        check(i.get('platform') in run['platforms'],label+'：未知平台')
        check(all(c in cm for c in i.get('case_ids',[])) and (bool(i.get('case_ids')) or not a.final),label+'：需关联有效用例')
        check(isinstance(i.get('publish'),bool),label+'：publish 应为布尔值')
        for cid in i.get('case_ids',[]):
            if cid in cm:check(i.get('platform')==cm[cid].get('platform'),label+'：平台与关联用例不符')
        for key in ['title','module','actual','expected','feedback','figma_url']:check(bool(i.get(key)),label+'：缺 '+key)
        u=urlparse(i.get('figma_url',''));check(u.scheme=='https' and (u.hostname=='figma.com' or (u.hostname or '').endswith('.figma.com')),label+'：无效 Figma 依据')
        for key in ['problem_image','design_image','problem_source','design_source']:
            v=i.get(key)
            if a.final:check(bool(v),label+'：缺 '+key)
            if not v:continue
            path=Path(v);path=path if path.is_absolute() else a.run/path
            try:
                with Image.open(path) as im: im.verify()
            except Exception as ex:errors.append(label+'：图片不可用 '+str(path)+' '+str(ex))
        if a.final and label in rendered:
            entry=rendered[label]
            check(entry.get('context_mode')=='full',label+'：请重新渲染完整上下文主图')
            for key in ['problem_image','design_image']:
                actual=Path(i.get(key,''));actual=actual if actual.is_absolute() else a.run/actual
                expected_image=a.run/entry[key]
                check(actual.resolve()==expected_image.resolve(),label+'：'+key+' 必须引用完整主图，局部图仅作补充')
        if i.get('publish'):check(i.get('review')=='confirmed',label+'：拟写入项尚未确认')
    if a.final:
        check(bool(cases),'用例为空');check(bool(pm),'Page 为空')
        modules=run.get('module_order',[])
        check(len(modules)==len(set(modules)),'功能顺序重复')
        check(all(c.get('module') in modules for c in cases) and all(i.get('module') in modules for i in findings),'功能未列入 module_order')
        for ident,page in pm.items():
            check(page.get('status')=='done',ident+'：Page 尚未完成')
            check(any(c.get('page_id')==ident for c in cases) or bool(page.get('scope_note')),ident+'：无用例或排除理由')
            reqs=page.get('requirements',[])
            check(bool(reqs) or bool(page.get('scope_note')),ident+'：缺设计要求清单')
            ids(reqs,ident+' requirement')
            for req in reqs:
                linked=req.get('case_ids',[])
                check(bool(req.get('summary')) and bool(req.get('figma_url')),ident+'：设计要求缺摘要/依据')
                check(bool(linked) or bool(req.get('excluded_reason')),req.get('id','')+'：设计要求没有用例或排除理由')
                check(all(cid in cm and cm[cid].get('page_id')==ident for cid in linked),req.get('id','')+'：用例关联不属于该 Page')
                if linked:
                    check(all(any(cid in cm and cm[cid].get('platform')==platform for cid in linked) for platform in run['platforms']),req.get('id','')+'：某平台缺用例；不适用时建立带理由的用例')
    selected=ordered_findings(run,cases,[i for i in findings if i.get('publish') and i.get('review')=='confirmed']);grouped={}
    for i in selected:grouped.setdefault(i['module'],[]).append(i)
    expected=[i['id'] for group in grouped.values() for i in group]
    if a.writeback:
        if not a.confluence or not a.user_profile:p.error('--writeback requires --confluence and --user-profile')
        profile=load_profile(a.confluence,a.user_profile);w=read('writeback.json');rows=w['rows'];ids(rows,'writeback')
        check([r.get('id') for r in rows]==expected,'回读条目顺序/数量不符')
        check(w.get('separator_count')==(max(0,len(grouped)-1) if profile.get('separator_rows') else 0),'模块空行不符')
        check(w.get('visual_verified') is True,'尚未验证实际页面显示')
        check(bool(w.get('snapshot_file')) and (a.run/w.get('snapshot_file','')).is_file(),'缺服务器回读快照')
        plan=read('confluence-plan.json')
        for r in rows:
            i=fm.get(r.get('id'))
            if not i:continue
            pairs={'issue_status':profile['issue_status'],'issue_type':i.get('issue_type'),'platform':i['platform'],'module':i['module'],'author':profile['author'],'date':plan['date'],'problem_width':profile['problem_width'],'design_width':profile['design_width'],'media_count':2,'figma_url':i['figma_url']}
            for key,value in pairs.items():check(r.get(key)==value,str(r['id'])+'：回读 '+key+' 不符')
    report={'ok':not errors,'cases':len(cases),'findings':len(findings),'selected':len(selected),'case_status_counts':{s:sum(c.get('status')==s for c in cases) for s in sorted(STATES)},'finding_kind_counts':{k:sum(i.get('kind')==k for i in findings) for k in sorted(KINDS)},'errors':errors}
    (a.run/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if report['ok'] else 1)
if __name__=='__main__':main()
