"""Pinned model, exact prepared input, bounded output and conservative measured cost."""
import json

from amphora_contracts_planning import ProviderUsage

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..providers.capture import unknown_usage
from ..providers.port import ProviderReply
from .input import PreparedInput, tokenizer_reference
from .pricing import MODEL, OpenAIPrice


class OpenAIProvider:
    revision = "openai-responses-synthetic-v1"
    def __init__(self, transport, content):
        self.transport,self.content = transport,content
    def supports(self, model):
        return (model.provider_id,model.model_id,model.model_revision)==("openai",MODEL,MODEL) and model.tokenizer==tokenizer_reference()
    def reply(self, attempt):
        prepared=PreparedInput.bind(attempt,self.content)
        raw=self.transport.send(prepared.body)
        require(type(raw) is bytes and 0<len(raw)<=1048576,"openai_response_limit")
        value=json.loads(raw.decode("utf-8"),object_pairs_hook=_object,parse_constant=_constant)
        require(type(value) is dict and value.get("model")==MODEL,"openai_response_model")
        usage=unknown_usage()
        counts=value.get("usage")
        if type(counts) is dict:
            input_tokens,output_tokens=counts.get("input_tokens"),counts.get("output_tokens")
            if all(type(x) is int and 0<=x<=100000000 for x in (input_tokens,output_tokens)):
                usage=ProviderUsage(input_tokens=input_tokens,output_tokens=output_tokens,
                    accounting_units=OpenAIPrice().estimate(input_tokens,output_tokens),certainty="reported")
        output=value.get("output")
        require(type(output) is list,"openai_response_output")
        parts=[]
        refused=False
        for item in output:
            require(type(item) is dict,"openai_response_item")
            if item.get("type")=="reasoning": continue
            require(item.get("type")=="message" and item.get("role")=="assistant","openai_response_item")
            content=item.get("content")
            require(type(content) is list,"openai_response_content")
            for block in content:
                require(type(block) is dict,"openai_response_content")
                if block.get("type")=="refusal": refused=True;continue
                require(block.get("type")=="output_text" and type(block.get("text")) is str,"openai_response_content")
                parts.append(block["text"].encode("utf-8"))
        def chunks():
            yield b"".join(parts)
            if refused or value.get("status")!="completed":
                raise TimeoutError("openai_output_incomplete")
        return ProviderReply(chunks(),usage)
