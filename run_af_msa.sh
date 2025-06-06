#!bin/bash

docker run -it \
    --volume ./af3_inputs_no_msa/:/root/af_input \
    --volume ./af_output_msa/:/root/af_output_msa \
    --volume ./model/:/root/models \
    --volume ./msa_colabfold/:/home/ubuntu/af3/alphafold3/msa_colabfold \
    --volume ../af_data/:/root/public_databases \
    -e DB_DIR="/root/public_databases" \
    --gpus all \
    alphafold3 \
    python run_alphafold.py --norun_inference\
    --input_dir=/root/af_input/\
    --model_dir=/root/models \
    --output_dir=/root/af_output_msa
