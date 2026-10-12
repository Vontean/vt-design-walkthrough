#!/usr/bin/env python3
"""Create a resumable walkthrough without overwriting existing artifacts."""
import argparse, json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--design-url', required=True)
    p.add_argument('--platform', action='append', choices=['iOS','Android'], required=True)
    p.add_argument('--target-url', default='')
    a=p.parse_args(); a.run.mkdir(parents=True, exist_ok=True)
    (a.run/'evidence').mkdir(exist_ok=True)
    initial={'run.json':{'schema_version':1,'phase':'scope','design_url':a.design_url,'target_url':a.target_url,'platforms':a.platform,'environment':{},'pages':[],'module_order':[],'current_page':None,'active_case':None,'current_step':0,'last_observation':'','batch':0,'next_action':'读取设计 Page 清单并建立当前 Page 用例'},'cases.json':[],'findings.json':[],'annotations.json':{'items':[]},'attachments.json':{}}
    created=[]
    for name,value in initial.items():
        path=a.run/name
        if not path.exists():
            path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); created.append(name)
    log=a.run/'LOG.md'
    if not log.exists(): log.write_text('# 走查执行日志\n\n记录时间、阶段、操作路径、观察、决策依据与下一步；不保存凭据。\n',encoding='utf-8')
    print(json.dumps({'run':str(a.run.resolve()),'created':created},ensure_ascii=False))
if __name__=='__main__': main()
