# Mug – XML Schema Validator (XSD 1.0 / 1.1)

> ⚠️ This project is in early development (pre-release/alpha).
> APIs and behavior will change rapidly as features are added.

Mug validates XML instance documents against an XSD schema, with full support for **XSD 1.1** (including `xs:assert` and XPath 2.0 functions) via the [xmlschema](https://pypi.org/project/xmlschema/) library.

---

## Installation

### From PyPI

```bash
pip install mug
```

### From Source

```bash
git clone https://github.com/bynbb/mug/mug.git
cd mug
pip install -e .
```

---

## Usage

After installation (either via PyPI or from source), the command is the same:

```bash
mug-validate <xml-file> <xsd-file> [options]
```

---

### Options

| Option                    | Description                                              |
| ------------------------- | -------------------------------------------------------- |
| `--xsd-version {1.0,1.1}` | Selects which version of XSD to use. Default is **1.1**. |
| `--fail-fast`             | Stop at the first validation error.                      |
| `--quiet`                 | Suppress the `"OK"` message when validation passes.      |
| `-h`, `--help`            | Show usage help.                                         |

---

## Exit Codes

* **0** → Validation successful
* **1** → Validation failed (errors found)
* **2** → Input read error or missing dependency
* **3** → Schema read/parse error

---

## Example

Validate `requirements-spec-example.xml` against `requirements-v1.xsd`:

```bash
mug-validate requirements-spec-example.xml requirements-v1.xsd
```

Output on success:

```
OK
```

Output on error (example):

```
requirements-spec-example.xml:12:5: ERROR: Element 'Requirement': Missing attribute 'id'.
```

---

## Development

### Local editable install & CLI test

```bash
git clone https://github.com/youruser/mug.git
cd mug
pip install -e .

# verify CLI is available
mug-validate --help

# sample validation
mug-validate requirements-spec-example.xml requirements-v1.xsd
```

---

## Notes

* Errors are printed in a style similar to `lxml`:

  ```
  file:line:column: LEVEL: message
  ```
* For XSD 1.1 features (like `xs:assert`), use `--xsd-version 1.1` (default).
* The validator streams errors, so it can handle large XML files efficiently.
