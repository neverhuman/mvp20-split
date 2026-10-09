"""Pinned operator policy; public eligibility is still checked by its owner."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_campaign_launch import LaunchProfileView

from .intent import LaunchError, LaunchIntent


def profile_digest(document: dict) -> str:
    content = {key: value for key, value in document.items() if key != 'reference'}
    content.update(profile_id=document['reference']['profile_id'], version=document['reference']['version'])
    return hashlib.sha256(json.dumps(content, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class LaunchProfilePolicy:
    view: LaunchProfileView

    @classmethod
    def from_bytes(cls, raw: bytes):
        def unique(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise LaunchError('launch_profile_invalid')
                value[key] = item
            return value
        try:
            if len(raw) > 65536:
                raise ValueError()
            json.loads(raw, object_pairs_hook=unique)
            view = LaunchProfileView.model_validate_json(raw)
            if profile_digest(view.model_dump(mode='json')) != view.reference.sha256:
                raise ValueError()
            if len({(t.capability_id, t.contract_version, t.release, t.image_sha256) for t in view.tools}) != len(view.tools):
                raise ValueError()
            return cls(view)
        except ValueError:
            raise LaunchError('launch_profile_invalid') from None

    def check(self, intent: LaunchIntent):
        if intent.profile != self.view.reference or intent.request.identity.scope != self.view.scope:
            raise LaunchError('launch_profile_mismatch')
        payload = json.loads(intent.admission.canonical_bytes)['payload']
        if payload['budget']['limit'] > self.view.maximum_invocations or payload['limits']['deadline_seconds'] > self.view.maximum_deadline_seconds:
            raise LaunchError('launch_profile_limit')

    def permits(self, tool: dict) -> bool:
        return any(binding.model_dump(mode='json') == tool for binding in self.view.tools)
