import re
import ast
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from models import User
from settings import DATABASE_URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def parse_user_line(line):
    # Extract inside parentheses
    match = re.search(r'User\((.*)\)', line)
    if not match:
        return None
    args_str = match.group(1)

    # Convert to dict-like string: replace = with :
    dict_str = "{" + re.sub(r'(\w+)=', r'"\1":', args_str) + "}"

    try:
        user_dict = ast.literal_eval(dict_str)
    except Exception as e:
        print(f"Failed to parse line: {line}\nError: {e}")
        return None

    user_dict['tg_id'] = user_dict.pop('id')
    if 'username' in user_dict:
        user_dict['tg_username'] = user_dict.pop('username')

    unwanted_fields = ['is_bot', 'language_code', 'is_premium']
    for field in unwanted_fields:
        user_dict.pop(field, None)  # safely remove if exists

    return user_dict


def main(users_file: str):
    session = Session()
    inserted_count = 0

    with open(users_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            user_data = parse_user_line(line)
            if user_data is None:
                continue

            # tg_id is required, skip if missing
            if 'tg_id' not in user_data:
                print(f"Skipping line because tg_id missing: {line}")
                continue

            try:
                user = User(**user_data)
                session.add(user)
                session.commit()
                inserted_count += 1
            except IntegrityError as e:
                session.rollback()
                print(f"Didn't add users to db, it already exists: {e}")
            finally:
                print(f"Users inserted successfully: {inserted_count}")
                session.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 load_users_to_db.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]
    main(filename)
