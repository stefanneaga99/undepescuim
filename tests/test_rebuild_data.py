from pathlib import Path

import rebuild_data


def test_scratch_rebuild_copies_locality_inputs():
    assert "data/raw/localities" in rebuild_data.SCRATCH_COPY_DIRS
    for rel in rebuild_data.SCRATCH_COPY_DIRS:
        assert (Path(rebuild_data.ROOT) / rel).is_dir(), rel
