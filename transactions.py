## TRANSACTION LISTS (EACH CHANGE RETURNS A NEW LIST AND LEAVES THE OLD ONE AS IT WAS) ##
# A transaction is {"amount", "timestamp", "category", "note", "retailer", "brand"}; older ones may lack the last two #
# Transactions are told apart by their place in the saved list #

def add_transaction(transactions, entry):
    return transactions + [entry]

def update_transaction(transactions, index, changes):
    # `changes` holds just the fields being changed #
    return [{**entry, **changes} if i == index else entry for i, entry in enumerate(transactions)]

def delete_transaction(transactions, index):
    return [entry for i, entry in enumerate(transactions) if i != index]

def rename_in_transactions(transactions, key, old, new):
    # A retailer or brand (`key`) renamed in every transaction that used it #
    return [{**entry, key: new} if entry.get(key) == old else entry for entry in transactions]

def replace_category(transactions, old_name, category):
    # An edited category swapped into every transaction that used it #
    return [
        {**entry, "category": category} if entry.get("category") and entry["category"]["name"] == old_name else entry
        for entry in transactions
    ]

## SORTING ##

def sorted_transactions(transactions, start, end, sort_by, descending):
    # The (index, transaction) pairs from `start` up to `end`, by date or by amount (equal amounts by date) #
    # The index is the transaction's place in the full list, so a row can open the right one to edit #
    def key(pair):
        entry = pair[1]
        return (entry["amount"], entry["timestamp"]) if sort_by == "amount" else entry["timestamp"]

    in_range = ((i, entry) for i, entry in enumerate(transactions) if start <= entry["timestamp"] < end)
    return sorted(in_range, key=key, reverse=descending)
