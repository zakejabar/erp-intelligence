import json
import os
from langchain_core.tools import tool
from typing import List, Dict

# 1. Define where our mock data lives
# We use os.path to make sure it works on Windows and Mac
MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), "../../../data_mocks/invoices.json")

@tool
def get_open_invoices(vendor_name: str = None) -> str:
    """
    Fetches a list of unpaid or overdue invoices. 
    Useful for checking debts, cash flow obligations, or vendor status.
    
    Args:
        vendor_name (Optional[str]): If provided, filters by this vendor name.
    """
    try:
        # A. Open the fake database
        if not os.path.exists(MOCK_DATA_PATH):
            return "Error: Mock database not found."
            
        with open(MOCK_DATA_PATH, "r") as f:
            invoices = json.load(f)
            
        # B. The Filtering Logic (The "Database Query")
        results = []
        for inv in invoices:
            # If the user asked for a specific vendor, we filter for it.
            # We use .lower() to make it case-insensitive (AI is messy with casing).
            if vendor_name:
                if vendor_name.lower() in inv["vendor"].lower():
                    results.append(inv)
            else:
                # If no vendor specified, return everything (or maybe just top 5)
                results.append(inv)
                
        # C. Return the result as a string
        # The AI reads text, so we dump the JSON list back to a string.
        if not results:
            return f"No invoices found for vendor: {vendor_name}"
            
        return json.dumps(results, indent=2)

    except Exception as e:
        return f"Error fetching invoices: {str(e)}"

def process_file(file_path: str) -> str:

    try: 
        if not os.path.exists(file_path): 
            return "File not found"

        if file_path.endswith(".csv"):
            with open(file_path, "r") as f:
                return f.read()
        elif file_path.endswith(".json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        else:
            with open(file_path, "r") as f:
                return f.read()

    except Exception as e:
        return f"Error processing file: {str(e)}"

# 2. Export the list so agent.py can import it
finance_tools = [get_open_invoices, process_file]