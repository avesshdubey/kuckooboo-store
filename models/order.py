class Order:
    def __init__(self, id, user_id, total_amount, payment_method, payment_status, created_at):
        self.id = id
        self.user_id = user_id
        self.total_amount = total_amount
        self.payment_method = payment_method
        self.payment_status = payment_status
        self.created_at = created_at
