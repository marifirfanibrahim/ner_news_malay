import random
import json

# ordinal
with open('malay_ordinal_data.json', 'r', encoding='utf-8') as f:
    ordinal_data = json.load(f)
    
# norp
with open('malay_norp_data.json', 'r', encoding='utf-8') as f:
    norp_data = json.load(f)

# merge & shuffle 
combined_data = ordinal_data + norp_data
random.shuffle(combined_data)

# save as json file
with open('training_data.json', 'w', encoding='utf-8') as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=2)