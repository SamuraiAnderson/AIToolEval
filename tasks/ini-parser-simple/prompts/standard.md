# Code Generation: C INI Parser

## Task

Implement a simple INI parser in C by completing `ini_get_value()` in `src/ini_parser.c`.

## Requirements

- Support section headers like `[server]`
- Support key-value pairs like `host = localhost` and `port=8080`
- Ignore empty lines and lines starting with `;` or `#`
- Match section and key names exactly
- Write value to output buffer and return `0` on success
- Return non-zero when section/key is not found or arguments are invalid

## Constraints

- Keep implementation in C11
- Do not change function signature in `ini_parser.h`
- Keep code simple and readable
