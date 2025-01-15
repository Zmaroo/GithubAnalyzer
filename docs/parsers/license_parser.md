# License Parser

## Overview

Parser for software license files.

## Features

- License type detection
- Copyright extraction
- Holder identification
- Year validation

## Usage

```python
from GithubAnalyzer.services.core.parsers import LicenseParser

parser = LicenseParser()
result = parser.parse_file("LICENSE")
```
