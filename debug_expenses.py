from app import create_app, db
from app.models.expense import Expense, ExpenseCategory
from app.models.user import User
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("--- Database Debug ---")
    users = User.query.all()
    print(f"Users found: {len(users)}")
    
    for user in users:
        print(f"\nUser: {user.username} (ID: {user.id})")
        count = Expense.query.filter_by(created_by=user.id).count()
        print(f"Expenses count: {count}")
        
        if count > 0:
            expenses = Expense.query.filter_by(created_by=user.id).limit(5).all()
            for e in expenses:
                print(f" - Expense {e.id}: {e.description} | Paid: {e.is_paid} | Cat: {e.category_ref.name if e.category_ref else 'None'}")
                try:
                    d = e.to_dict()
                    print(f"   to_dict() success: {d['amount']}")
                except Exception as ex:
                    print(f"   to_dict() FAILED: {ex}")

    cats = ExpenseCategory.query.count()
    print(f"\nTotal Categories: {cats}")
