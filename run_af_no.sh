#!bin/bash

docker run -it \
    --volume ./af_input_native/:/root/af_input \
    --volume ./af_output_native/:/root/af_output_native \
    --volume ./model/:/root/models \
    --volume ./msa_colabfold/:/home/ubuntu/af3/alphafold3/msa_colabfold \
    --volume ../af_data/:/root/public_databases \
    -e DB_DIR="/root/public_databases" \
    --gpus all \
    alphafold3 \
    python run_alphafold.py\
    --input_dir=/root/af_input/\
    --model_dir=/root/models \
    --output_dir=/root/af_output_native