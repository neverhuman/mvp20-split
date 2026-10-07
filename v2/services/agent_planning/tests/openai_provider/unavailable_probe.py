"""Installed adapter with actual loopback 503/refusal; never contacts a model provider."""

from datetime import datetime
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import socket
import threading

from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.openai_provider import MODEL, OpenAIProvider
from amphora_agent_planning.openai_provider.http import OpenAIHTTP
from amphora_agent_planning.openai_provider.input import tokenizer_reference
from amphora_agent_planning.providers.capture import observe
from amphora_contracts_core import Scope
from amphora_contracts_planning import reference_proposal_schema


def main():
    value=json.loads((Path(__file__).parents[1]/'providers/fixtures/request.json').read_bytes())
    context=value['context']; bodies={}
    context['output_schema']=reference_proposal_schema().model_dump(mode='json')
    references=[context['prompt'],context['objective'],context['policy'],context['model']['configuration'],
                *(entry['artifact'] for entry in context['entries'])]
    for reference in references:
        raw=b'Return JSON only. Synthetic engineering probe; abstain when uncertain.'
        reference.update(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))
        bodies[reference['sha256']]=raw
    context['model'].update(provider_id='openai',model_id=MODEL,model_revision=MODEL,context_window_tokens=400000,
                            tokenizer=tokenizer_reference().model_dump(mode='json'))
    context['limits'].update(max_input_tokens=8192,max_output_tokens=2048,max_attempts=1,total_tokens=10240,
                             total_accounting_units=1000000000,accounting_unit='usd_nanodollars')
    attempt=AttemptBinding(RequestSnapshot.from_bytes(json.dumps(value).encode(),actor_id=value['actor_id'],
                           scope=Scope.model_validate(value['reference']['scope'])),1)
    class Unavailable(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            self.server.calls+=1
            self.rfile.read(int(self.headers['Content-Length']))
            raw=b'{"error":{"message":"private synthetic error must not escape"}}'
            self.send_response(503);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    server=HTTPServer(('127.0.0.1',0),Unavailable);server.calls=0
    thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.05));thread.start()
    records=[]
    try:
        with socket.socket() as refused:
            refused.bind(('127.0.0.1',0))  # Retain bound, non-listening port; no other process can claim it.
            for label,port,expected in [('http503',server.server_port,'unavailable'),('connection_refused',refused.getsockname()[1],'unknown')]:
                calls=[]
                def factory(host,timeout):
                    assert host=='api.openai.com'
                    calls.append(host)
                    return http.client.HTTPConnection('127.0.0.1',port,timeout=timeout)
                transport=OpenAIHTTP('synthetic-not-a-provider-credential',timeout_seconds=2,connection_factory=factory)
                result=observe(attempt,OpenAIProvider(transport,lambda ref:bodies[ref.sha256])).document()
                assert result.status==expected and result.usage.certainty=='unknown' and result.proposal is None
                assert result.usage.accounting_units is None and len(calls)==1
                assert 'private synthetic' not in result.model_dump_json()
                records.append({'scenario':label,'status':result.status,'reason_code':result.reason_code,
                                'usage_certainty':result.usage.certainty,'calls':len(calls)})
        assert server.calls==1
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
    print(json.dumps({'checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),'status':'passed',
                      'observations':records,'external_calls':0,'limits':'Test-only loopback connection factory; installed production adapter/capture. No SQL issuance, live provider, billing or scientific claim.'}))


if __name__=='__main__':
    try: main()
    except Exception: raise SystemExit('Installed provider-unavailable probe failed; raw diagnostics suppressed.') from None
