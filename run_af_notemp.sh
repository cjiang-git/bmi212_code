#!bin/bash

docker run -it \
    --volume ./af3_inputs_no_temp/:/root/af_input \
    --volume ./af_output_temp/:/root/af_output_temp \
    --volume ./model/:/root/models \
    --volume ./msa_colabfold/:/home/ubuntu/af3/alphafold3/msa_colabfold \
    --volume ../af_data/:/root/public_databases \
    -e DB_DIR="/root/public_databases" \
    --gpus all \
    alphafold3 \
    python run_alphafold.py\
    --input_dir=/root/af_input/\
    --model_dir=/root/models \
    --output_dir=/root/af_output_temp