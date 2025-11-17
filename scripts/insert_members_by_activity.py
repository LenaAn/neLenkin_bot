import sys
import os
from sqlalchemy.orm import sessionmaker

# Add parent directory to Python path so we can import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import User, MembershipByActivity, engine  # now this import works


Session = sessionmaker(bind=engine)
session = Session()


def add_memberships_from_file(filename: str):
    with open(filename, 'r', encoding='utf-8') as f:
        usernames = [line.strip() for line in f if line.strip()]

    for username in usernames:
        user = session.query(User).filter(User.tg_username == username).first()
        if not user:
            print(f"⚠️ User '{username}' not found in Users table.")

            # Check if an entry already exists for this username
            existing = session.query(MembershipByActivity).filter(
                MembershipByActivity.tg_username == username
            ).first()

            if existing:
                print(f"⏭️  Username '{username}' already inserted earlier (tg_id is NULL), skipping.")
                continue

            # Insert row with only tg_username
            new_entry = MembershipByActivity(
                tg_id=None,
                tg_username=username,
                expires_at=None
            )
            session.add(new_entry)
            print(f"➕ Added '{username}' to MembershipByActivity without tg_id.")
            continue

        # --- user exists in Users table ---
        existing = session.query(MembershipByActivity).filter(
            MembershipByActivity.tg_id == user.tg_id
        ).first()

        if existing:
            print(f"✅ User '{username}' already in MembershipByActivity, skipping.")
            continue

        new_entry = MembershipByActivity(tg_id=user.tg_id, tg_username=user.tg_username)
        session.add(new_entry)
        print(f"➕ Added '{username}' to MembershipByActivity.")

    session.commit()
    print("\n✅ Done.")


if __name__ == "__main__":
    add_memberships_from_file("usernames.txt")
