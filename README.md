# Mug

> - ⚠️ This project is in early development (pre-release/alpha).  
> - APIs and behavior will change rapidly as features are added.  
> - **Pre-1.0.0 Policy:** _Anything goes before v1.0.0._  
> - Stability guarantees begin only at `v1.0.0`.

* * *

## XML Schema Validator (XSD 1.0 / 1.1)

Mug validates XML instance documents against an XSD schema, with full support for **XSD 1.1** (including `xs:assert` and XPath 2.0 functions) via the [xmlschema](https://pypi.org/project/xmlschema/?utm_source=chatgpt.com) library.

* * *

## Installation

### From PyPI

```bash
pip install mug
```

### From Source

```bash
git clone https://github.com/bynbb/mug.git
cd mug
pip install -e .
```

> **Note:** Console commands (like `mug`) are available only after install.  
> If you prefer not to install, you can run via module from the repo root:  
> `PYTHONPATH=src python -m mug <xml> <xsd>`

* * *

## Usage

After installation (either via PyPI or from source), run:

```bash
mug <xml-file> <xsd-file> [options]
# or
python -m mug <xml-file> <xsd-file> [options]
```

**Example:**

```bash
mug requirements/2025/08/20/req_20250820T142442+0000.xml requirements-v1.xsd
```

On success, it prints:

```
OK
```

* * *

## Options

| Option | Description |
| --- | --- |
| `--xsd-version {1.0,1.1}` | Selects the XSD version. Default is **1.1**. |
| `--fail-fast` | Stop at the first validation error. |
| `--quiet` | Suppress the `OK` message when validation passes. |
| `-h`, `--help` | Show usage help. |

* * *

## Exit Codes

* **0** → Validation successful
    
* **1** → Validation failed (errors found)
    
* **2** → Input read error or missing dependency
    
* **3** → Schema read/parse error
    

* * *

## Output Format

Errors are printed in a familiar style:

```
file:line:column: LEVEL: message
```

* * *

## Development

```bash
git clone https://github.com/bynbb/mug.git
cd mug
pip install -e .

# verify CLI is available
mug --help

# sample validation
mug requirements-spec-example.xml requirements-v1.xsd
```

* * *

## Notes

* XSD 1.1 features (e.g., `xs:assert`) require `--xsd-version 1.1` (this is the default).
    
* If you see `ERROR: The 'xmlschema' package is required`, install it with `pip install xmlschema`.
    

* * *