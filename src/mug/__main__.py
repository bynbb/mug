# src/mug/__main__.py
from .bootstrap import init_app_logging


def main() -> int:
    init_app_logging()
    print("mug CLI ok")  # replace with real CLI logic
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
