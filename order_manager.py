orders = {}

def get_order(user_id):
    if user_id not in orders:
        orders[user_id] = {
            "items": [],      # list of dicts: {item, qty}
            "name": None,
            "phone": None,
            "address": None,
            "stage": "START"  # START → ITEM → QTY → ADD_MORE → NAME → PHONE → ADDRESS → DONE
        }
    return orders[user_id]

def reset_order(user_id):
    if user_id in orders:
        del orders[user_id]
