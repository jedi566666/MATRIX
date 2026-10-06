"""Offline CLI. No credentials, network, or agent execution."""
import argparse, json
from .team_store import Store

def main():
    parser=argparse.ArgumentParser(description='MATRIX local mission workspace')
    parser.add_argument('--data-dir')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    sub.add_parser('gui')
    create=sub.add_parser('create')
    for name in ('project','agent','objective','deliverables'): create.add_argument('--'+name,required=True)
    state=sub.add_parser('transition');state.add_argument('id');state.add_argument('state')
    state.add_argument('--producer',action='store_true');state.add_argument('--note',default='')
    attach=sub.add_parser('attach');attach.add_argument('id');attach.add_argument('path');attach.add_argument('--kind',choices=['input','report','evidence','deliverable'],default='input')
    args=parser.parse_args()
    if args.command=='gui':
        from .desktop import run
        run(args.data_dir);return
    store=Store(args.data_dir)
    if args.command=='list':result=store.list()
    elif args.command=='create':result=store.create(args.project,args.agent,args.objective,args.deliverables)
    elif args.command=='attach':result=store.attach(args.id,args.path,args.kind)
    else:result=store.transition(args.id,args.state,note=args.note,producer=args.producer)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
