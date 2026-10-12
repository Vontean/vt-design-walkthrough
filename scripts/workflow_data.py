"""Shared deterministic grouping by declared functional order and case order."""
COLUMN_ROLES=['acceptance','issue_status','issue_type','platform','module','problem','discussion','owner','resolution']

def ordered_findings(run,cases,items):
    modules=run.get('module_order',[])
    rank={m:n for n,m in enumerate(modules)}
    case_rank={c['id']:n for n,c in enumerate(cases)}
    def key(pair):
        n,item=pair
        return (rank.get(item['module'],len(rank)),min((case_rank.get(i,len(cases)) for i in item.get('case_ids',[])),default=len(cases)),n)
    return [item for _,item in sorted(enumerate(items),key=key)]


def load_profile(confluence_path,user_path):
    import json
    from pathlib import Path
    template=json.loads(Path(confluence_path).read_text(encoding='utf-8'))
    user=json.loads(Path(user_path).read_text(encoding='utf-8'))
    if not isinstance(user.get('author'),str) or not user['author'].strip():
        raise ValueError('先在 user-profile.json 填写 author，再生成在线行或校验回读')
    required=['author','author_colour','problem_width','design_width']
    missing=[k for k in required if k not in user]
    if missing:raise ValueError('用户配置缺字段：'+', '.join(missing))
    for key in ['problem_width','design_width']:
        if not isinstance(user[key],int) or isinstance(user[key],bool) or user[key]<=0:
            raise ValueError(key+' 必须为正整数')
    return {**template,**{k:user[k] for k in required}}
