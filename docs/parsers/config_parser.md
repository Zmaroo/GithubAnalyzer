# Config Parser

## Overview

Parser implementation for configuration files (yaml, json, toml, ini).

## Features

- Multi-format support
- Schema validation
- Error recovery
- Metadata extraction

## Usage

```python
from GithubAnalyzer.services.core.parsers import ConfigParser

parser = ConfigParser()
result = parser.parse_file("config.yaml")
```
