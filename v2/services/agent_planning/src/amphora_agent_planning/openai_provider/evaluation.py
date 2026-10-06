"""Frozen live suite gate; original Planning issuance remains the only caller."""
from types import MappingProxyType

from ..context.policy import require
from .adapter import OpenAIProvider
from .input import PreparedInput
from .pricing import UNIT


class FrozenOpenAIEvaluation:
    revision = OpenAIProvider.revision
    def __init__(self, protocol, batch, provider):
        require(type(provider) is OpenAIProvider, "evaluation_live_provider")
        require(protocol.manifest.mode == "live" and protocol.manifest.adapter_revision == self.revision, "evaluation_live_profile")
        require(batch.protocol_sha256 == protocol.sha256, "evaluation_live_protocol")
        require(protocol.manifest.limits.accounting_unit == UNIT and protocol.manifest.limits.total_accounting_units <= 1000000000, "evaluation_live_initial_ceiling")
        require(1 <= len(batch.tasks) <= 24, "evaluation_live_call_ceiling")
        prepared={}
        for task in batch.tasks:
            packet=PreparedInput.bind(task.binding,provider.content)
            require(task.demand.accounting_units >= packet.reservation, "evaluation_live_reservation")
            prepared[task.request.sha256]=packet
        require(len(prepared)==len(batch.tasks),"evaluation_live_duplicate_request")
        require(sum(item.reservation for item in prepared.values()) <= batch.accounting_units <= 1000000000, "evaluation_live_initial_ceiling")
        self.protocol_sha256,self.batch_sha256=protocol.sha256,batch.sha256
        self.provider,self.prepared=provider,MappingProxyType(prepared)
    def validate(self, protocol, batch):
        require(protocol.sha256==self.protocol_sha256 and batch.sha256==self.batch_sha256, "evaluation_live_binding")
    def supports(self,model):return self.provider.supports(model)
    def reply(self,attempt):
        packet=self.prepared.get(attempt.request.sha256)
        require(packet is not None and attempt.ordinal==1,"evaluation_live_request")
        return self.provider.reply_prepared(packet)
