"""AP-4 guards the two reference-impl names it adds to the public surface.
(AP-5 will lock the *entire* cairn.__all__ surface with a broader contract test.)
"""

from cairn.runtime.checkpoint_store import CheckpointStore as _ConcreteStore
from cairn.runtime.effect_ledger import EffectLedger as _ConcreteLedger


def test_file_backed_store_and_ledger_are_public_aliases():
    import cairn

    # The public names are exactly the concrete runtime classes (no wrapper, no drift).
    assert cairn.FileCheckpointStore is _ConcreteStore
    assert cairn.FileEffectLedger is _ConcreteLedger


def test_file_backed_names_are_in_all():
    import cairn

    assert "FileCheckpointStore" in cairn.__all__
    assert "FileEffectLedger" in cairn.__all__


def test_public_store_and_ledger_construct_and_work(tmp_path):
    import cairn

    store = cairn.FileCheckpointStore(str(tmp_path / "ck"))
    ledger = cairn.FileEffectLedger(str(tmp_path / "e.jsonl"), "run")
    assert store.load_latest() is None          # empty store
    assert ledger.current_offset() == 0         # empty ledger
