import pandas as pd
import io
import requests
import time
import csv


def get_uniprot_sequence(gene_name):
    hgnc_api_url = f"https://rest.genenames.org/fetch/symbol/{gene_name.upper()}"
    hgnc_headers = {"Accept": "application/json"}

    try:
        hgnc_response = requests.get(hgnc_api_url, headers=hgnc_headers, timeout=10)
        if hgnc_response.status_code == 200:
            hgnc_data = hgnc_response.json()
            if hgnc_data.get('response', {}).get('numFound', 0) > 0:
                doc = hgnc_data['response']['docs'][0]

                uniprot_ids = doc.get('uniprot_ids') 
                if uniprot_ids:
                    uniprot_id = uniprot_ids[0] 
                    uniprot_direct_url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}?format=fasta"
                    try:
                        u_response = requests.get(uniprot_direct_url, timeout=10)
                        if u_response.status_code == 200:
                            fasta_data = u_response.text
                            if fasta_data and fasta_data.startswith(">"):
                                lines = fasta_data.splitlines()
                                sequence = "".join(lines[1:])
                                return sequence
                    except Exception as e:
                        pass
    except Exception as e: 
        print(f"Error fetching sequence for {gene_name}: {e}")
        pass

def process_tf_genes_to_sequences_pandas(csv_path):

    df = pd.read_csv(csv_path)

    print(df.columns)

    if 'tf_gene' not in df.columns:
        return "CSV does not contain 'tf_gene' column."

    tf_genes = df['tf_gene'].dropna().astype(str).unique()
    unique_tf_genes = set()
    for gene_name_entry in tf_genes:
        if '+' in gene_name_entry:
            parts = gene_name_entry.split('+')
            for part in parts:
                cleaned_part = part.strip()
                if cleaned_part:
                    unique_tf_genes.add(cleaned_part)
        else:
            cleaned_entry = gene_name_entry.strip()
            if cleaned_entry:
                 unique_tf_genes.add(cleaned_entry)

    print(f"{len(unique_tf_genes)} unique gene names")

    gene_data_for_df = []
    processed_count = 0
    for gene in sorted(list(unique_tf_genes)):
        processed_count += 1
        sequence = get_uniprot_sequence(gene)
        gene_data_for_df.append({'tf_gene': gene, 'amino_acid_sequence': sequence})
        
        time.sleep(0.1)

    output_df = pd.DataFrame(gene_data_for_df, columns=['tf_gene', 'amino_acid_sequence'])
    output_csv_string = output_df.to_csv(index=False)
    return output_csv_string


csv_input_data = '/home/cjiang/Stanford_Classes/AlphaFactor/alpha-factor_tf-seq-pairs_complete.csv'

output_csv_data = process_tf_genes_to_sequences_pandas(csv_input_data)


output_path = 'af_tf_gene_aa_complete_2.csv'
with open(output_path, 'w') as outfile:
    outfile.write(output_csv_data)
print(f"\nOutput saved to {output_path}")