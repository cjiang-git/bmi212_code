import json
import pandas as pd
import os

def extract_confidence(summary_json_path, prediction_name):
    scores = {}

    with open(summary_json_path, 'r') as f:
        data = json.load(f)

    scores['model_name'] = prediction_name
    
    scores['ptm'] = data.get('ptm')
    scores['iptm'] = data.get('iptm') 
    scores['ranking_score'] = data.get('ranking_score')
    chain_ptm_data = data.get('chain_ptm')

    scores['chain_0_ptm'] = chain_ptm_data[0]
    scores['chain_1_ptm'] = chain_ptm_data[1]
    scores['fraction_disordered'] = data.get('fraction_disordered')
    scores['has_clash'] = data.get('has_clash')


    chain_pair_iptm_data = data.get('chain_pair_iptm')
    scores['interface_chains_0_1_iptm'] = chain_pair_iptm_data[0][1]

    chain_pair_pae_min_data = data.get('chain_pair_pae_min')
    scores['interface_chains_0_1_pae_min'] = chain_pair_pae_min_data[0][1]


    return scores


af_output_dir = './af_output_temp' 
output_csv_path = './alphafold3_notemp_combined_summary.csv'
all_model_scores = []


for prediction_name in os.listdir(af_output_dir):
    prediction_dir_path = os.path.join(af_output_dir, prediction_name)
    
    if os.path.isdir(prediction_dir_path):
        summary_filename = f"{prediction_name}_summary_confidences.json"
        summary_path = os.path.join(prediction_dir_path, summary_filename)

        if os.path.isfile(summary_path):
            extracted_data = extract_confidence(summary_path, prediction_name)
            if extracted_data:
                all_model_scores.append(extracted_data)
        else:
            print(f"Summary JSON file not found for prediction {prediction_name} at {summary_path}")
    else:
        print(f"{prediction_name} is not a directory.")




df = pd.DataFrame(all_model_scores)

column_order = [
    'model_name', 
    'ranking_score', 
    'ptm', 
    'iptm', 
    'interface_chains_0_1_iptm', 
    'interface_chains_0_1_pae_min', 
    'chain_0_ptm', 
    'chain_1_ptm',
    'fraction_disordered',
    'has_clash'
]

df_ordered = pd.DataFrame()
for col in column_order:
    if col in df.columns:
        df_ordered[col] = df[col]
    else:
        df_ordered[col] = None 
df_ordered.to_csv(output_csv_path, index=False)

