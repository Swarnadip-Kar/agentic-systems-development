from typing import List, Dict

def merge_customer_records(records: List[Dict]) -> Dict[str, Dict]:
    merged_records = {}
    
    for record in records:
        customer_id = record['customer_id']
        updated_at = record['updated_at']
        
        if customer_id not in merged_records or merged_records[customer_id]['updated_at'] < updated_at:
            merged_records[customer_id] = record.copy()
        else:
            # Update the existing record with the fields from the newer record
            for key, value in record.items():
                if key != 'customer_id' and key != 'updated_at':
                    merged_records[customer_id][key] = value
    
    return merged_records
