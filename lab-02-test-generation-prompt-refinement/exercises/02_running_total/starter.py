def get_running_total(transactions: list) -> list:
    running_totals = []
    current_balance = 0
    
    for transaction in transactions:
        amount = transaction['amount']
        transaction_type = transaction['type']
        
        if transaction_type == 'credit':
            current_balance += amount
        elif transaction_type == 'debit':
            current_balance -= amount
        
        running_totals.append(current_balance)
    
    return running_totals
