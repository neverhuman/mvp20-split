"""Cross-check retained summaries against original intent and included graph slices."""
from ..context.policy import require
from ..curation_context import CurationIntent
from ..campaign_context.records import canonical
from ..campaign_knowledge_access.reader import PEER_CODES


def validate_knowledge(request, slices):
    summaries = [row for row in slices if row['lane'] == 'curation_knowledge']
    if not summaries:
        return
    intents = [row for row in slices if row['lane'] == 'curation']
    require(len(summaries) == len(intents) == 1, 'curation_knowledge_intent')
    intent = CurationIntent.from_payload(request, intents[0]['payload'])
    value = summaries[0]['payload']
    require(set(value) == {'format', 'authority', 'curation', 'request_sha256', 'graphs', 'selection_policy'}
            and value['format'] == 'planning-curation-knowledge.v1'
            and value['authority'] == 'selected_metadata_only' and value['curation'] == intent.identity
            and value['request_sha256'] == request.sha256
            and value['selection_policy'] == 'whole_head_or_explicit_gap'
            and summaries[0]['identity'] == intent.identity, 'curation_knowledge_summary')
    selected = intents[0]['payload']['command']['payload']['context']['knowledge']
    require(type(value['graphs']) is list and len(value['graphs']) == len(selected), 'curation_knowledge_coverage')
    available = []
    for row, head in zip(value['graphs'], selected, strict=True):
        require(type(row) is dict and set(row) == {'head', 'status', 'reason', 'calls', 'bytes'}
                and row['head'] == head, 'curation_knowledge_head')
        require(type(row['calls']) is int and 0 <= row['calls'] <= 3
                and type(row['bytes']) is int and 0 <= row['bytes'] <= 18087936, 'curation_knowledge_accounting')
        if row['status'] == 'available':
            require(row['reason'] is None and row['calls'] == 3, 'curation_knowledge_available')
            available.append(head)
        else:
            require(row['status'] == 'unavailable' and row['reason'] in PEER_CODES |
                    {'campaign_graph_invalid', 'campaign_graph_projection_limit'}, 'curation_knowledge_failure')
    graphs = [row['payload'] for row in slices if row['lane'] == 'graph']
    require(len(graphs) == len(available) and all(row['status'] == 'available' for row in graphs),
            'curation_knowledge_projection_coverage')
    require([canonical(row['selection']['base']) for row in graphs] == [canonical(head) for head in available],
            'curation_knowledge_projection_binding')
