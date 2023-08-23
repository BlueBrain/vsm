UNICORE_DEFAULT_EXECUTABLE_SCRIPT = "/bin/bash input.sh"

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
            
            export BACKEND_DIR=/gpfs/bbp.cscs.ch/project/proj3/software/BraynsCircuitStudio/backend/
            export BACKEND_PORT=8000
            export BRAYNS_PORT=5000
            export LOG_LEVEL=DEBUG
            export USE_TLS=0
            export UNICORE_HOSTNAME=$(hostname -f)
            export UNICORE_CERT_FILEPATH=${TMPDIR}/${UNICORE_HOSTNAME}.crt
            export UNICORE_PRIVATE_KEY_FILEPATH=${TMPDIR}/${UNICORE_HOSTNAME}.key
            
            echo Brayns Circuit Studio startup script
            echo ----------------------
            echo "HOSTNAME=$(hostname -f)"
            echo UNICORE_HOSTNAME=$UNICORE_HOSTNAME
            echo UNICORE_CERT_FILEPATH=$UNICORE_CERT_FILEPATH
            echo UNICORE_PRIVATE_KEY_FILEPATH=$UNICORE_PRIVATE_KEY_FILEPATH
            echo TMPDIR=$TMPDIR
            echo BACKEND_PORT=$BACKEND_PORT
            echo BRAYNS_PORT=$BRAYNS_PORT
            echo ----------------------
            echo
            echo Loading brayns/3.2.0 from unstable...
            module purge
            module load unstable
            module load brayns/3.2.0
            braynsService \
                --uri 0.0.0.0:${BRAYNS_PORT} \
                --log-level debug \
                --plugin braynsCircuitExplorer \
                --plugin braynsAtlasExplorer &
        
            source ${BACKEND_DIR}venv/bin/activate
            
            python ${BACKEND_DIR}src/main.py \
                 --port=$BACKEND_PORT 
        """,
    },
    {
        "Name": "SBO-multi-v1",
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
            
            export BRAYNS_0_PORT=5000
            export BRAYNS_1_PORT=5001
            export BRAYNS_2_PORT=5002
            export BRAYNS_3_PORT=5003
            export BRAYNS_4_PORT=5004
            export BRAYNS_5_PORT=5005
            export BRAYNS_6_PORT=5006
            export BRAYNS_7_PORT=5007
            export BRAYNS_8_PORT=5008
            export LOG_LEVEL=DEBUG
            export USE_TLS=0
            export UNICORE_HOSTNAME=$(hostname -f)
            export UNICORE_CERT_FILEPATH=${TMPDIR}/${UNICORE_HOSTNAME}.crt
            export UNICORE_PRIVATE_KEY_FILEPATH=${TMPDIR}/${UNICORE_HOSTNAME}.key
            
            echo Brayns Circuit Studio startup script
            echo ----------------------
            echo "HOSTNAME=$(hostname -f)"
            echo UNICORE_HOSTNAME=$UNICORE_HOSTNAME
            echo UNICORE_CERT_FILEPATH=$UNICORE_CERT_FILEPATH
            echo UNICORE_PRIVATE_KEY_FILEPATH=$UNICORE_PRIVATE_KEY_FILEPATH
            echo TMPDIR=$TMPDIR
            echo BRAYNS_PORT from $BRAYNS_0_PORT to $BRAYNS_8_PORT
            echo ----------------------
            echo
            echo Loading brayns/3.2.0 from unstable...
            module purge
            module load unstable
            module load brayns/3.2.0
            braynsService \
                --uri 0.0.0.0:${BRAYNS_0_PORT} \
                --log-level debug \
                --plugin braynsCircuitExplorer \
                --plugin braynsAtlasExplorer &
            braynsService \
                --uri 0.0.0.0:${BRAYNS_1_PORT} \
                --log-level debug \
                --plugin braynsCircuitExplorer \
                --plugin braynsAtlasExplorer &
            braynsService \
                --uri 0.0.0.0:${BRAYNS_2_PORT} \
                --log-level debug \
                --plugin braynsCircuitExplorer \
                --plugin braynsAtlasExplorer &
            braynsService \
                --uri 0.0.0.0:${BRAYNS_3_PORT} \
                --log-level debug \
                --plugin braynsCircuitExplorer \
                --plugin braynsAtlasExplorer &
            braynsService \
                --uri 0.0.0.0:${BRAYNS_4_PORT} \
                --log-level debug \
                --plugin braynsCircuitExplorer \
                --plugin braynsAtlasExplorer &
            braynsService \
                --uri 0.0.0.0:${BRAYNS_5_PORT} \
                --log-level debug \
                --plugin braynsCircuitExplorer \
                --plugin braynsAtlasExplorer &
            braynsService \
                --uri 0.0.0.0:${BRAYNS_6_PORT} \
                --log-level debug \
                --plugin braynsCircuitExplorer \
                --plugin braynsAtlasExplorer &
            braynsService \
                --uri 0.0.0.0:${BRAYNS_7_PORT} \
                --log-level debug \
                --plugin braynsCircuitExplorer \
                --plugin braynsAtlasExplorer &
            braynsService \
                --uri 0.0.0.0:${BRAYNS_8_PORT} \
                --log-level debug \
                --plugin braynsCircuitExplorer \
                --plugin braynsAtlasExplorer &

            wait
        """,
    }
]
