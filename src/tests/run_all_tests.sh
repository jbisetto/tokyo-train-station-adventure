#!/bin/bash
# Main test runner script for Tokyo Train Station Adventure

echo "===================================================================="
echo "                TOKYO TRAIN STATION ADVENTURE TESTS                  "
echo "===================================================================="

# Set Python path to include the repository root
export PYTHONPATH="${PYTHONPATH}:$(cd ../../ && pwd)"
echo "PYTHONPATH set to: $PYTHONPATH"

# Change to the tests directory
cd "$(dirname "$0")/../../tests"

# Run unit tests
echo "===================================================================="
echo "                       RUNNING UNIT TESTS                            "
echo "===================================================================="
python -m pytest backend/ai/companion/core -v

# Run tier1 tests
echo "===================================================================="
echo "                      RUNNING TIER1 TESTS                            "
echo "===================================================================="
python -m pytest backend/ai/companion/tier1 -v

# Run tier2 tests
echo "===================================================================="
echo "                      RUNNING TIER2 TESTS                            "
echo "===================================================================="
python -m pytest backend/ai/companion/tier2 -v

# Run tier3 tests
echo "===================================================================="
echo "                      RUNNING TIER3 TESTS                            "
echo "===================================================================="
python -m pytest backend/ai/companion/tier3 -v

# Run API tests
echo "===================================================================="
echo "                       RUNNING API TESTS                             "
echo "===================================================================="
python -m pytest backend/api -v

# Run integration tests for tier2
echo "===================================================================="
echo "                RUNNING TIER2 INTEGRATION TESTS                      "
echo "===================================================================="
cd backend/integration/tier2
./run_tests.sh
cd ../../..

# Run integration tests for tier3
echo "===================================================================="
echo "                RUNNING TIER3 INTEGRATION TESTS                      "
echo "===================================================================="
# Check if Bedrock test should be run
read -p "Do you want to run Bedrock integration tests? (y/n) " RUN_BEDROCK
if [ "$RUN_BEDROCK" = "y" ]; then
    python -m pytest backend/integration/tier3 -v
else
    echo "Skipping Bedrock integration tests."
fi

echo "===================================================================="
echo "                    ALL TESTS COMPLETED                              "
echo "====================================================================" 