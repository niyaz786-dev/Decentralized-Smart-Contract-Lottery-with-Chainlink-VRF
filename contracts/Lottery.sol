// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.8/vrf/dev/VRFConsumerBaseV2Plus.sol";
import "@chainlink/contracts/src/v0.8/vrf/dev/libraries/VRFV2PlusClient.sol";

contract Lottery is VRFConsumerBaseV2Plus {
    address payable[] public players;
    address payable public winner;
    uint256 public usdEntryFee;
    uint256 public randomness;

    AggregatorV3Interface internal ethUsdPriceFeed;

    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }

    LOTTERY_STATE public lottery_state;

    // Chainlink VRF v2.5 variables
    bytes32 public keyHash;
    uint256 public subscriptionId;
    uint32 public callbackGasLimit = 200000;
    uint16 public requestConfirmations = 3;
    uint32 public numWords = 1;

    uint256 public requestId;

    event RequestedRandomness(uint256 requestId);
    event WinnerPicked(address indexed winner);

    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        bytes32 _keyHash,
        uint256 _subscriptionId
    ) VRFConsumerBaseV2Plus(_vrfCoordinator) {
        usdEntryFee = 50 * (10 ** 18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        keyHash = _keyHash;
        subscriptionId = _subscriptionId;
        lottery_state = LOTTERY_STATE.CLOSED;
    }

    function enter() public payable {
        require(lottery_state == LOTTERY_STATE.OPEN, "Lottery is not open!");
        require(msg.value >= getEntranceFee(), "Not enough ETH!");
        players.push(payable(msg.sender));
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 answer, , , ) = ethUsdPriceFeed.latestRoundData();
        require(answer > 0, "Invalid price feed");
        uint256 adjustedPrice = uint256(answer) * 10 ** 10;
        uint256 costToEnter = (usdEntryFee * 10 ** 18) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Can't start a new lottery yet!"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        require(lottery_state == LOTTERY_STATE.OPEN, "Lottery not open!");
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;

        requestId = s_vrfCoordinator.requestRandomWords(
            VRFV2PlusClient.RandomWordsRequest({
                keyHash: keyHash,
                subId: subscriptionId,
                requestConfirmations: requestConfirmations,
                callbackGasLimit: callbackGasLimit,
                numWords: numWords,
                extraArgs: VRFV2PlusClient._argsToBytes(
                    VRFV2PlusClient.ExtraArgsV1({nativePayment: false})
                )
            })
        );

        emit RequestedRandomness(requestId);
    }

    function fulfillRandomWords(
        uint256 _requestId,
        uint256[] calldata _randomWords
    ) internal override {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "Not calculating winner!"
        );
        require(_randomWords.length > 0, "No randomness returned");
        require(_requestId == requestId, "Wrong requestId");

        uint256 winnerIndex = _randomWords[0] % players.length;
        winner = players[winnerIndex];
        winner.transfer(address(this).balance);

        randomness = _randomWords[0];
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;

        emit WinnerPicked(winner);
    }

    function resetLottery() public onlyOwner {
        lottery_state = LOTTERY_STATE.CLOSED;
        players = new address payable[](0);
        winner = payable(address(0));
        randomness = 0;
        requestId = 0;
    }
}
