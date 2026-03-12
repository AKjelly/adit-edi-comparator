import requests
import pandas as pd
import re
import io

def to_csv_url(url):
    # 
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        return None
    sheet_id = match.group(1)

    # Tab ID (gid) nikalo agar ho
    gid_match = re.search(r"gid=(\d+)", url)
    gid = gid_match.group(1) if gid_match else "0"

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def fetch_sheet(url, label="Sheet"):
    csv_url = to_csv_url(url)
    
    if not csv_url:
        raise ValueError(f"{label}: Invalid Google Sheets URL")
    
    response = requests.get(csv_url, timeout=15)
    
    if response.status_code == 403:
        raise PermissionError(f"{label}: Sheet public nahi hai. Share → Anyone with link → Viewer karo")
    
    if response.status_code != 200:
        raise ConnectionError(f"{label}: HTTP Error {response.status_code}")
    
    df = pd.read_csv(io.StringIO(response.text))
    df.columns = df.columns.str.strip()  # column names se spaces hatao
    
    return df