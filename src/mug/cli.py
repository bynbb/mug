#!/usr/bin/env python3
import sys
import argparse
from typing import Optional, Tuple
try:
    import xmlschema
except Exception as e:
    print("ERROR: The 'xmlschema' package is required. Install it with: pip install xmlschema", file=sys.stderr)
    sys.exit(2)


def extract_position(err) -> Tuple[Optional[int], Optional[int]]:
    """
    Best-effort extraction of (line, column) from an xmlschema validation error.
    xmlschema may set .position, or we can look at .obj/.elem.sourceline.
    Column often isn't available; return None if unknown.
    """
    line = None
    col = None

    # Try explicit position attribute
    pos = getattr(err, "position", None)
    if isinstance(pos, tuple) and pos:
        # xmlschema generally uses (line, column) or just (line,)
        if len(pos) >= 1 and isinstance(pos[0], int):
            line = pos[0]
        if len(pos) >= 2 and isinstance(pos[1], int):
            col = pos[1]

    # Try underlying element/object sourceline
    if line is None:
        for attr in ("obj", "elem"):
            node = getattr(err, attr, None)
            if node is not None:
                line = getattr(node, "sourceline", None)
                if line is not None:
                    break

    return line, col


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate an XML file against an XSD schema using the 'xmlschema' library (with XSD 1.1 support)."
    )
    parser.add_argument("xml", help="Path to the XML instance document")
    parser.add_argument("xsd", help="Path to the XSD schema")
    parser.add_argument("--xsd-version", choices=["1.0", "1.1"], default="1.1",
                        help="XSD version to use (default: 1.1)")
    parser.add_argument("--fail-fast", action="store_true",
                        help="Stop at the first validation error")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress 'OK' message on success")
    args = parser.parse_args()

    # Load schema (use XMLSchema11 when requested)
    try:
        if args.xsd_version == "1.1":
            schema = xmlschema.XMLSchema11(args.xsd)  # full XSD 1.1 validation incl. xs:assert
        else:
            schema = xmlschema.XMLSchema(args.xsd)
    except xmlschema.XMLSchemaException as e:
        print(f"{args.xsd}: SCHEMA ERROR: {e}", file=sys.stderr)
        sys.exit(3)
    except OSError as e:
        print(f"{args.xsd}: SCHEMA READ ERROR: {e}", file=sys.stderr)
        sys.exit(3)

    # Validate
    error_count = 0
    try:
        for err in schema.iter_errors(args.xml):
            line, col = extract_position(err)
            line_str = str(line) if line is not None else "0"
            col_str = str(col) if col is not None else "0"
            # Mimic lxml-like format: file:line:col: LEVEL: message
            print(f"{args.xml}:{line_str}:{col_str}: ERROR: {err.reason}", file=sys.stderr)
            error_count += 1
            if args.fail_fast:
                break
    except OSError as e:
        print(f"{args.xml}: INPUT READ ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    if error_count == 0:
        if not args.quiet:
            print("OK")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
