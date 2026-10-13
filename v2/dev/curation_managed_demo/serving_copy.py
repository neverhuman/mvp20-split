"""Rebase frozen serving references by resolved path, including mapped NAS aliases."""
import json
import shutil
from pathlib import Path


CONFIGURATIONS = ('owners', 'access', 'native', 'launch', 'launch-prepared', 'gateway',
                  'artifact', 'runtime', 'registry', 'knowledge', 'research', 'planning')


def copy_serving(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    assert source.parent == target.parent and source.parent.name == '.test-results'
    assert source != target and not target.exists()
    assert all(p.name.startswith('curation-demo-serving-') for p in (source, target))
    changes = []

    def relocate(value, field=None):
        if isinstance(value, dict):
            return {key: relocate(item, key) for key, item in value.items()}
        if isinstance(value, list):
            return [relocate(item) for item in value]
        if not isinstance(value, str) or not Path(value).is_absolute():
            return value
        original = Path(value).resolve()
        owner = next((p for p in (original, *original.parents) if
                      p.parent == source.parent and p.name.startswith('curation-demo-serving-')), None)
        if owner is None:
            return value
        relative = original.relative_to(owner)
        retained = source / relative
        assert retained.exists(), 'Serving reference has no retained counterpart: ' + str(relative)
        if field == 'schema_path':
            assert original.read_bytes() == retained.read_bytes(), 'Pinned schema changed: ' + str(relative)
        replacement = target / relative
        changes.append({'original': value, 'replacement': str(replacement)})
        return str(replacement)

    rewritten = {}
    for name in CONFIGURATIONS:
        path = source / (name + '.json')
        if path.exists():
            before = json.loads(path.read_bytes())
            after = relocate(before)
            if before != after:
                rewritten[path.name] = after
    # Validate all references before creating a new copy; never edit its ancestors.
    shutil.copytree(source, target)
    for name, value in rewritten.items():
        (target / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return changes
