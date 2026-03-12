import re

def extract_adit_ids(df, column_name):
    ids = set()
    for val in df[column_name].dropna().astype(str):
        val = val.strip()
        
        # Format: stedi_1234
        if val.lower().startswith("stedi_"):
            ids.add(val.split("_", 1)[1].split('.')[0])
        
        # Format: stedi_id(1234)
        elif re.search(r'\(([^)]+)\)', val):
            match = re.search(r'\(([^)]+)\)', val)
            ids.add(match.group(1).strip().split('.')[0])
        
        # Format: plain ID
        else:
            ids.add(val.split('.')[0])
    
    return ids

def extract_edi_ids(df, column_name):
    ids = set()
    for val in df[column_name].dropna().astype(str):
        val = val.strip().split('.')[0]
        if val:
            ids.add(val)
    return ids