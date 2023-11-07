USE_CASES = [
    {
        "Name": "SBO1",
        "Project": "proj134",
        "Partition": "prod",
        "Resources": {
            "Nodes": 1,
            "Runtime": "14400s",
            "Memory": 0,
            "Exclusive": "true",
            "Comment": "certs",
        },
        "Executable": """#!/bin/bash
source /etc/profile.d/bb5.sh
source /etc/profile.d/modules.sh

export BRAYNS_PORT=5000
export BRAYNS_LOG_LEVEL=info
export BACKEND_PORT=8000
export BACKEND_LOG_LEVEL=INFO

echo Brayns Circuit Studio startup script
echo ----------------------
echo BACKEND_PORT=$BACKEND_PORT
echo BRAYNS_PORT=$BRAYNS_PORT
echo ----------------------
echo
echo Loading brayns/3.4.0 from unstable...

module purge
module load unstable
module load brayns/3.4.0

braynsService \
    --uri 0.0.0.0:${BRAYNS_PORT} \
    --log-level ${BRAYNS_LOG_LEVEL} \
    --plugin braynsCircuitExplorer \
    --plugin braynsAtlasExplorer &

while true; do nc -z localhost ${BRAYNS_PORT}; if [ $? -eq 0 ]; then break; fi; sleep 1; done

module load py-bcsb/2.1.1

bcsb \
    --host 0.0.0.0 \
    --port ${BACKEND_PORT} \
    --log_level ${BACKEND_LOG_LEVEL} \
    --base_directory /gpfs/bbp.cscs.ch &

BACKEND_PID=$!

while true; do nc -z localhost ${BACKEND_PORT}; if [ $? -eq 0 ]; then break; fi; sleep 1; done

echo "HOSTNAME=$(hostname -f)"

wait $BACKEND_PID
""",
    },
    {
        "Name": "AWS_TEST",
    },
]
