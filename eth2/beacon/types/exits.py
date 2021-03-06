import rlp
from rlp.sedes import (
    binary,
)
from eth2.beacon.sedes import (
    uint24,
    uint64,
)
from eth2.beacon.typing import (
    BLSSignature,
    SlotNumber,
    ValidatorIndex,
)
from eth2.beacon.constants import EMPTY_SIGNATURE


class Exit(rlp.Serializable):
    """
    Note: using RLP until we have standardized serialization format.
    """
    fields = [
        # Minimum slot for processing exit
        ('slot', uint64),
        # Index of the exiting validator
        ('validator_index', uint24),
        # Validator signature
        ('signature', binary),
    ]

    def __init__(self,
                 slot: SlotNumber,
                 validator_index: ValidatorIndex,
                 signature: BLSSignature=EMPTY_SIGNATURE) -> None:
        super().__init__(
            slot,
            validator_index,
            signature,
        )
