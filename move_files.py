import os
import shutil
from tqdm import tqdm

base_dir = './af_output_msa'
out_dir = './af_input_native'

for dir_name in tqdm(os.listdir(base_dir)):
    dir_path = os.path.join(base_dir, dir_name)
    
    old_name = f"{dir_name}_data.json"
    old_path = os.path.join(base_dir,dir_name,old_name)

    new_name = f"{dir_name}.json"
    new_path = os.path.join(out_dir, new_name)
    os.makedirs(out_dir, exist_ok=True)

    shutil.copy(old_path, new_path)


print("\nProcess complete.")