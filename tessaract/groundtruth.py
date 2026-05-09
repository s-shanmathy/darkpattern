import os
import json
import pandas as pd

dataset_path = r"D:\SEM6\DL\DARK\web_data"

all_ground_truths = []

for root, dirs, files in os.walk(dataset_path):

    if "metadata.json" in files:

        meta_path = os.path.join(root, "metadata.json")

        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract text
        ground_truth = data.get("text", "")

        # Clean whitespace
        ground_truth = " ".join(ground_truth.split())

        all_ground_truths.append({
            "folder": root,
            "ground_truth": ground_truth
        })

# Convert to DataFrame
df = pd.DataFrame(all_ground_truths)

# Save to CSV
output_path = r"D:\SEM6\DL\DARK\ground_truths.csv"

df.to_csv(output_path, index=False, encoding="utf-8")

print("Ground truth file saved at:")
print(output_path)

print("\nTotal samples:", len(df))