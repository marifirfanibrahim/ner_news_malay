import random
import json

ordinal_path = 'ner_news_malay\model_gliner\\fine_tuning\malay_norp.json'  # Try alternative names if needed
norp_path = 'malay_norp.json'

# ordinal
with open(ordinal_path, 'r', encoding='utf-8') as f:
    ordinal_data = json.load(f)
    
# norp
with open(norp_path, 'r', encoding='utf-8') as f:
    norp_data = json.load(f)

# merge & shuffle 
combined_data = ordinal_data + norp_data
random.shuffle(combined_data)

# save as json file
with open('training_data.json', 'w', encoding='utf-8') as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=2)

print("JSON merged successfully!")
print(f"Ordinal : {len(ordinal_data)}")
print(f"NORP    : {len(norp_data)}")
print(f"Total   : {len(combined_data)}")
print("Saved as JSON file.")