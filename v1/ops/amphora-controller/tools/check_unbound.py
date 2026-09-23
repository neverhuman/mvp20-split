"""Flag variables USED before they are ASSIGNED at top level -- the set -u trap.
Heuristic (no control-flow analysis) but it catches the exact class that broke 13:00."""
import re,sys
src=open(sys.argv[1]).read().splitlines()
assign=re.compile(r'^\s*(?:export\s+|local\s+)?([A-Z_][A-Z0-9_]*)=')
forvar=re.compile(r'^\s*for\s+([A-Z_][A-Z0-9_]*)\s+in\b')
dynamic_fd=re.compile(r'\bexec\s+\{([A-Z_][A-Z0-9_]*)\}(?:>>?|<<?)')
use=re.compile(r'\$\{?([A-Z_][A-Z0-9_]*)\b')
ENV={'PATH','HOME','USER','PWD','SHELL','LANG','HOSTNAME','LOGNAME','TERM','SSH_AUTH_SOCK',
     'BASH_SOURCE','BASH_LINENO','LINENO','FUNCNAME','IFS','RANDOM','SECONDS','PPID','UID','OSTYPE','EUID','BASH'}
first={}
for n,l in enumerate(src,1):
    for rx in (assign,forvar):
        m=rx.match(l)
        if m and m.group(1) not in first: first[m.group(1)]=n
    # env-prefixed invocation: FOO=bar cmd
    for m in re.finditer(r'(?:^|\s)([A-Z_][A-Z0-9_]*)=\S', l):
        if m.group(1) not in first: first[m.group(1)]=n
    # Bash's `exec {NAME}>file` syntax assigns an fd number to NAME at run
    # time.  It commonly appears after helper function definitions which close
    # that fd, so source-line ordering is not a use-before-assignment signal.
    for m in dynamic_fd.finditer(l):
        first[m.group(1)] = 0
bad=[]
for n,l in enumerate(src,1):
    if l.strip().startswith('#'): continue
    for m in use.finditer(l):
        v=m.group(1)
        if v in ENV or v.isdigit(): continue
        if ':-' in l[m.end():m.end()+3] or ':=' in l[m.end():m.end()+3]: continue  # defaulted
        f=first.get(v)
        if f is None: bad.append((n,v,'NEVER ASSIGNED'))
        elif f>n: bad.append((n,v,f'assigned later at line {f}'))
if bad:
    for n,v,why in bad: print(f"  line {n}: ${v} -- {why}")
    print(f"{len(bad)} potential set -u fault(s)")
    sys.exit(1)
print("  no use-before-assignment found")
