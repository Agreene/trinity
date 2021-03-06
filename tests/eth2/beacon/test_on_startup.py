import pytest

from eth.constants import (
    ZERO_HASH32,
)

from eth2.beacon.constants import (
    EMPTY_SIGNATURE,
    GWEI_PER_ETH,
)
from eth2.beacon.types.blocks import BeaconBlock
from eth2.beacon.types.crosslink_records import CrosslinkRecord
from eth2.beacon.types.deposits import Deposit
from eth2.beacon.types.deposit_data import DepositData
from eth2.beacon.types.deposit_input import DepositInput
from eth2.beacon.types.eth1_data import Eth1Data
from eth2.beacon.types.forks import Fork

from eth2.beacon.on_startup import (
    get_genesis_block,
    get_initial_beacon_state,
)
from eth2.beacon.tools.builder.validator import (
    sign_proof_of_possession,
)
from eth2.beacon.typing import (
    Gwei,
)


def test_get_genesis_block():
    startup_state_root = b'\x10' * 32
    genesis_slot = 10
    genesis_block = get_genesis_block(startup_state_root, genesis_slot, BeaconBlock)
    assert genesis_block.slot == genesis_slot
    assert genesis_block.parent_root == ZERO_HASH32
    assert genesis_block.state_root == startup_state_root
    assert genesis_block.randao_reveal == ZERO_HASH32
    assert genesis_block.eth1_data == Eth1Data.create_empty_data()
    assert genesis_block.signature == EMPTY_SIGNATURE
    assert genesis_block.body.is_empty


@pytest.mark.parametrize(
    (
        'num_validators,'
    ),
    [
        (10)
    ]
)
def test_get_initial_beacon_state(
        privkeys,
        pubkeys,
        num_validators,
        genesis_slot,
        genesis_fork_version,
        genesis_start_shard,
        shard_count,
        latest_block_roots_length,
        epoch_length,
        target_committee_size,
        max_deposit,
        latest_penalized_exit_length,
        latest_randao_mixes_length,
        entry_exit_delay,
        sample_eth1_data_params):
    withdrawal_credentials = b'\x22' * 32
    randao_commitment = b'\x33' * 32
    custody_commitment = b'\x44' * 32
    fork = Fork(
        previous_version=genesis_fork_version,
        current_version=genesis_fork_version,
        slot=genesis_slot,
    )

    validator_count = 5

    initial_validator_deposits = (
        Deposit(
            branch=(
                b'\x11' * 32
                for j in range(10)
            ),
            index=i,
            deposit_data=DepositData(
                deposit_input=DepositInput(
                    pubkey=pubkeys[i],
                    withdrawal_credentials=withdrawal_credentials,
                    randao_commitment=randao_commitment,
                    custody_commitment=custody_commitment,
                    proof_of_possession=sign_proof_of_possession(
                        deposit_input=DepositInput(
                            pubkey=pubkeys[i],
                            withdrawal_credentials=withdrawal_credentials,
                            randao_commitment=randao_commitment,
                            custody_commitment=custody_commitment,
                        ),
                        privkey=privkeys[i],
                        fork=fork,
                        slot=genesis_slot,
                    ),
                ),
                amount=max_deposit * GWEI_PER_ETH,
                timestamp=0,
            ),
        )
        for i in range(validator_count)
    )
    genesis_time = 10
    latest_eth1_data = Eth1Data(**sample_eth1_data_params)

    state = get_initial_beacon_state(
        initial_validator_deposits=initial_validator_deposits,
        genesis_time=genesis_time,
        latest_eth1_data=latest_eth1_data,
        genesis_slot=genesis_slot,
        genesis_fork_version=genesis_fork_version,
        genesis_start_shard=genesis_start_shard,
        shard_count=shard_count,
        latest_block_roots_length=latest_block_roots_length,
        epoch_length=epoch_length,
        target_committee_size=target_committee_size,
        max_deposit=max_deposit,
        latest_penalized_exit_length=latest_penalized_exit_length,
        latest_randao_mixes_length=latest_randao_mixes_length,
        entry_exit_delay=entry_exit_delay,
    )

    # Misc
    assert state.slot == genesis_slot
    assert state.genesis_time == genesis_time
    assert state.fork.previous_version == genesis_fork_version
    assert state.fork.current_version == genesis_fork_version
    assert state.fork.slot == genesis_slot

    # Validator registry
    assert len(state.validator_registry) == validator_count
    assert len(state.validator_balances) == validator_count
    assert state.validator_registry_update_slot == genesis_slot
    assert state.validator_registry_exit_count == 0

    # Randomness and committees
    assert len(state.latest_randao_mixes) == latest_randao_mixes_length
    assert len(state.latest_vdf_outputs) == latest_randao_mixes_length // epoch_length

    # TODO: `persistent_committees`, `persistent_committee_reassignments` will be removed
    assert len(state.persistent_committees) == 0
    assert len(state.persistent_committee_reassignments) == 0
    assert state.previous_epoch_start_shard == genesis_start_shard
    assert state.current_epoch_start_shard == genesis_start_shard
    assert state.previous_epoch_calculation_slot == genesis_slot
    assert state.current_epoch_calculation_slot == genesis_slot
    assert state.previous_epoch_randao_mix == ZERO_HASH32
    assert state.current_epoch_randao_mix == ZERO_HASH32

    # Custody challenges
    assert len(state.custody_challenges) == 0

    # Finality
    assert state.previous_justified_slot == genesis_slot
    assert state.justified_slot == genesis_slot
    assert state.justification_bitfield == 0
    assert state.finalized_slot == genesis_slot

    # Recent state
    assert len(state.latest_crosslinks) == shard_count
    assert state.latest_crosslinks[0] == CrosslinkRecord(
        slot=genesis_slot,
        shard_block_root=ZERO_HASH32,
    )
    assert len(state.latest_block_roots) == latest_block_roots_length
    assert state.latest_block_roots[0] == ZERO_HASH32
    assert len(state.latest_penalized_balances) == latest_penalized_exit_length
    assert state.latest_penalized_balances[0] == Gwei(0)

    assert len(state.latest_attestations) == 0
    assert len(state.batched_block_roots) == 0

    # Ethereum 1.0 chain data
    assert state.latest_eth1_data == latest_eth1_data
    assert len(state.eth1_data_votes) == 0

    assert state.validator_registry[0].is_active(genesis_slot)
