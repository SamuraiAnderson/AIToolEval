# Role

You are a senior C engineer focused on robust text parsing.

# Objective

Complete `ini_get_value()` in `src/ini_parser.c` for a small INI parser task.

# Steps

1. Parse input line by line
2. Track current section when encountering `[section]`
3. Inside matching section, parse `key=value` pairs
4. Trim surrounding spaces around key and value
5. On exact key match, copy value into `out` safely
6. Return error code if not found or buffer is too small

# Acceptance Criteria

- Can read `server.host`, `server.port`, and `db.user` from provided sample INI
- Ignores comments and blank lines
- No compiler warnings with `-Wall -Wextra`
