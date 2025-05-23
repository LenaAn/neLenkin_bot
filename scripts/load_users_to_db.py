import re
import ast
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

            user = User(**user_data)

            # Use merge to insert or update by primary key if id is provided
            session.merge(user)
            inserted_count += 1

    session.commit()
    session.close()
    print(f"Users inserted/updated successfully: {inserted_count}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 load_users_to_db.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]
    main(filename)
