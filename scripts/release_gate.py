"""Conservative public-file/history scanner. Prints locations, never secret values."""
from pathlib import Path
import re, subprocess, sys, ast
root=Path(__file__).resolve().parents[1]
patterns=[r'AKIA[0-9A-Z]{16}',r'ASIA[0-9A-Z]{16}',r'gh[pousr]_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{40,}',r'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{30,}',r'AIza[0-9A-Za-z_-]{35}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'(?:api_key|password|secret|access_token)\s*[:=]\s*["\'][A-Za-z0-9_+/=-]{16,}["\']']
private=[r'[CD]:[/\\](?:Users|MTP|DELA|BD-)',r'm\.souissi@',r'@[a-z0-9.-]*gmx\.',r'0x[0-9a-fA-F]{40}']
failures=[]
tracked=subprocess.run(['git','ls-files'],cwd=root,capture_output=True,text=True)
files=tracked.stdout.splitlines() if tracked.returncode==0 and tracked.stdout.strip() else [str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ('.git','.venv','build','dist','__pycache__')) and '.egg-info' not in str(p)]
for name in files:
    p=root/name
    if p.suffix.lower() in ('.pdf','.png','.jpg','.jpeg','.sqlite3','.zip') or p.name.startswith('.env') and p.name!='.env.example':failures.append(name+': prohibited artifact')
    content=p.read_text(encoding='utf-8',errors='replace')
    if any(re.search(pattern,content,re.I) for pattern in patterns+private):failures.append(name+': sensitive pattern')
    if p.suffix=='.py':
        try:ast.parse(content,filename=name)
        except SyntaxError:failures.append(name+': syntax error')
history=subprocess.run(['git','rev-list','--all'],cwd=root,capture_output=True,text=True)
for commit in history.stdout.splitlines():
    listing=subprocess.check_output(['git','ls-tree','-r','--name-only',commit],cwd=root,text=True)
    for name in listing.splitlines():
        content=subprocess.check_output(['git','show',commit+':'+name],cwd=root).decode('utf-8',errors='replace')
        if any(re.search(pattern,content,re.I) for pattern in patterns+private):failures.append('history '+commit[:8]+' '+name+': sensitive pattern')
emails=subprocess.run(['git','log','--all','--format=%ae%n%ce'],cwd=root,capture_output=True,text=True).stdout.splitlines()
for email in emails:
    if email and not email.endswith('@users.noreply.github.com') and not email.endswith('@github.com'):failures.append('history: personal commit email; use a GitHub noreply address')
if failures:
    print('NO-GO\n'+'\n'.join(failures));sys.exit(1)
print('PASS: syntax, tracked-file secret/private artifact scan and all-ref Git history scan; '+str(len(files))+' files')
