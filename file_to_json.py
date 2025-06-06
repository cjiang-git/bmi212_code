import csv
import os
import json
import argparse

def load_protein_sequences(protein_seq_csv_path):
    protein_sequences = {}

    with open(protein_seq_csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_cols = ['tf_gene', 'amino_acid_sequence']

        for row_num, row in enumerate(reader, 1):
            tf_gene = row.get('tf_gene')
            aa_seq = row.get('amino_acid_sequence')
            if not tf_gene:
                print(f"Missing 'tf_gene' at row {row_num}.")
                continue
            if not aa_seq:
                print(f"Missing '{tf_gene}' at row {row_num}")
                continue
            if tf_gene in protein_sequences:
                continue
            else:
                protein_sequences[tf_gene] = aa_seq.strip().upper()

    if not protein_sequences:
        print(f"Warning: No protein sequences were loaded from {protein_seq_csv_path}. This may lead to failures if these TFs are needed.")
    return protein_sequences


# AI was used

def main():
    parser = argparse.ArgumentParser(
        description="Prepare AlphaFold 3 formatted JSON inputs for protein-DNA complexes using two CSV files."
    )
    parser.add_argument("complex_data_csv", help="Path to CSV with complex data. Required columns: unique_id, tf_gene, sequence (DNA).")
    parser.add_argument("protein_seq_csv", help="Path to CSV with protein sequences. Required columns: tf_gene, amino_acid_sequence.")
    parser.add_argument("a3m_dir", help="Directory containing the .a3m MSA files (e.g., your 'msa_colabfold' directory).")
    parser.add_argument("output_json_dir", help="Directory to save the output AlphaFold 3 JSON files.")

    args = parser.parse_args()

    if not os.path.exists(args.output_json_dir):
        os.makedirs(args.output_json_dir)
        print(f"Created output directory: {args.output_json_dir}")

    # --- Step 1: Load Protein Sequences ---
    try:
        tf_to_protein_sequence = load_protein_sequences(args.protein_seq_csv)
        if not tf_to_protein_sequence:
            print(f"Critical Warning: No protein sequences were loaded from '{args.protein_seq_csv}'. JSON generation will likely fail for all entries if TFs are not found.")
    except Exception as e:
        print(f"Critical Error loading protein sequences: {e}. Cannot proceed.")
        return
    print(f"Successfully loaded {len(tf_to_protein_sequence)} protein sequences map entries.")

    # --- Step 2: Read Complex Data CSV and collect tf_genes for A3M verification ---
    complex_data_rows = []
    tf_genes_for_complexes = set()
    try:
        with open(args.complex_data_csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            required_cols = ['unique_id', 'tf_gene', 'sequence']
            if not reader.fieldnames or not all(col in reader.fieldnames for col in required_cols):
                 print(f"Error: Complex data CSV '{args.complex_data_csv}' must contain columns: {', '.join(required_cols)}.")
                 return
            for row in reader:
                complex_data_rows.append(row)
                if row.get('tf_gene'):
                    tf_genes_for_complexes.add(row['tf_gene'])
    except FileNotFoundError:
        print(f"Error: Complex data CSV not found at {args.complex_data_csv}")
        return
    except Exception as e:
        print(f"Error reading complex data CSV {args.complex_data_csv}: {e}")
        return

    if not complex_data_rows:
        print("Complex data CSV is empty or no data rows found.")
        return

    print("\nVerifying A3M files...")
    missing_a3m_tf_genes = set()
    tf_gene_to_a3m_path = {}

    if tf_genes_for_complexes:
        for tf_gene in tf_genes_for_complexes:
            expected_a3m_file = os.path.join(args.a3m_dir, f"{tf_gene}.a3m")
            if os.path.isfile(expected_a3m_file):
                tf_gene_to_a3m_path[tf_gene] = os.path.abspath(expected_a3m_file)
            else:
                print(f"MISSING A3M: File not found at '{expected_a3m_file}' for tf_gene '{tf_gene}'")
                missing_a3m_tf_genes.add(tf_gene)
    else:
        print("No non-empty TF gene names found in complex data CSV to verify A3M files for.")

    if missing_a3m_tf_genes:
        print(f"\nSummary of Missing A3M Files: .a3m files are missing for the following tf_genes: {', '.join(sorted(list(missing_a3m_tf_genes)))}")
        print(f"These files were expected in directory: {args.a3m_dir}")
        print("Rows in the complex data CSV that require these tf_genes will be skipped during JSON generation.")

    print("A3M file verification complete.")
    print("\nGenerating AlphaFold 3 JSON inputs...")
    successful_json_count = 0
    failed_json_count = 0

    for i, row in enumerate(complex_data_rows):
        row_num = i + 1
        unique_id = row.get('unique_id')
        tf_gene = row.get('tf_gene')
        dna_sequence_from_csv = row.get('sequence')

        if not all([unique_id, tf_gene, dna_sequence_from_csv]):
            missing_fields = [f for f, v in [('unique_id', unique_id), ('tf_gene', tf_gene), ('sequence', dna_sequence_from_csv)] if not v]
            print(f"Skipping row {row_num} from complex data CSV due to missing essential field(s): {', '.join(missing_fields)}. Row content: {row}")
            failed_json_count += 1
            continue

        protein_aa_sequence = tf_to_protein_sequence.get(tf_gene)
        if not protein_aa_sequence:
            print(f"Skipping row {row_num} (ID: {unique_id}): Protein sequence for tf_gene '{tf_gene}' not found in the loaded protein sequences (from {args.protein_seq_csv}).")
            failed_json_count += 1
            continue

        if tf_gene in missing_a3m_tf_genes:
            expected_a3m_path = os.path.join(args.a3m_dir, f"{tf_gene}.a3m")
            print(f"Skipping row {row_num} (ID: {unique_id}): Required A3M file for tf_gene '{tf_gene}' is missing (expected at '{expected_a3m_path}').")
            failed_json_count += 1
            continue

        a3m_file_path = tf_gene_to_a3m_path.get(tf_gene)
        if not a3m_file_path:
            print(f"Skipping row {row_num} (ID: {unique_id}): A3M file path for tf_gene '{tf_gene}' could not be resolved, though it wasn't listed as globally missing. Check consistency.")
            failed_json_count +=1
            continue

        valid_protein_chars = "ACDEFGHIKLMNPQRSTVWYX"
        cleaned_protein_aa_sequence = ''.join(c for c in protein_aa_sequence if c in valid_protein_chars)
        if len(cleaned_protein_aa_sequence) != len(protein_aa_sequence):
            print(f"Warning: Protein sequence for {tf_gene} (ID: {unique_id}) from protein CSV contained non-standard amino acid characters. Using filtered version for JSON.")
        if not cleaned_protein_aa_sequence:
            print(f"Skipping row {row_num} (ID: {unique_id}): Protein sequence for tf_gene '{tf_gene}' became empty after filtering for valid characters ({valid_protein_chars}).")
            failed_json_count += 1
            continue

        try:
            valid_dna_chars = "ATCGN"
            cleaned_dna_sequence = ''.join(c for c in dna_sequence_from_csv.upper() if c in valid_dna_chars)

            if len(cleaned_dna_sequence) != len(dna_sequence_from_csv) and dna_sequence_from_csv:
                print(f"Warning: DNA sequence for {unique_id} (row {row_num}) contained non-ATCGN characters. Using cleaned version for JSON.")
            if not cleaned_dna_sequence:
                raise ValueError(f"DNA sequence for {unique_id} (row {row_num}) is empty or invalid after cleaning.")

            output_data = {
                "name": unique_id,
                "modelSeeds": [0],  # Changed to a single seed
                "sequences": [
                    {
                        "protein": {
                            "id": "A",
                            "sequence": cleaned_protein_aa_sequence,
                            "unpairedMsaPath": a3m_file_path,
                            "pairedMsa":"",
                            "templates": []  #new run without templates
                        }
                    },
                    {
                        "dna": {
                            "id": "B",
                            "sequence": cleaned_dna_sequence
                        }
                    }
                ],
                "dialect": "alphafold3",
                "version": 3
            }

            output_json_filename = os.path.join(args.output_json_dir, f"{unique_id}.json")
            with open(output_json_filename, 'w', encoding='utf-8') as oj:
                json.dump(output_data, oj, indent=2)
            successful_json_count += 1

        except ValueError as ve:
            print(f"Error processing row {row_num} (ID: {unique_id}) for JSON generation: {ve}. Skipping.")
            failed_json_count += 1
        except Exception as e:
            print(f"An unexpected error occurred generating JSON for row {row_num} (ID: {unique_id}): {e}. Skipping.")
            failed_json_count += 1

    print(f"\n--- Summary ---")
    print(f"Processed {len(complex_data_rows)} rows from the complex data CSV.")
    print(f"Successfully generated {successful_json_count} JSON files adhering to AlphaFold 3 format.")
    if failed_json_count > 0:
        print(f"Failed to generate or skipped {failed_json_count} JSON file(s) due to missing data or errors.")
    print(f"Output JSON files are located in: {os.path.abspath(args.output_json_dir)}")

if __name__ == "__main__":
    main()