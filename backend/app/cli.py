import argparse
import getpass
import sys

from pydantic import ValidationError

from app.db.session import SessionLocal
from app.models import UserRole
from app.schemas import UserCreate
from app.services import EmailAlreadyRegisteredError, create_user


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="astratickets")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser(
        "create-staff",
        help="Create an agent or administrator account",
    )
    create_parser.add_argument("--email", required=True)
    create_parser.add_argument("--full-name", required=True)
    create_parser.add_argument(
        "--role",
        required=True,
        choices=[UserRole.AGENT.value, UserRole.ADMIN.value],
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 1

    try:
        user_data = UserCreate(
            email=args.email,
            password=password,
            full_name=args.full_name,
        )
    except ValidationError as error:
        print(f"Invalid account details: {error.errors()[0]['msg']}", file=sys.stderr)
        return 1

    with SessionLocal() as session:
        try:
            user = create_user(session, user_data, UserRole(args.role))
        except EmailAlreadyRegisteredError:
            print("An account with this email already exists.", file=sys.stderr)
            return 1

    print(f"Created {user.role.value} account for {user.email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
