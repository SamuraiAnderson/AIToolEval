# Role

You are a C systems programming expert specializing in compression libraries.

# Task

Fix a bug in the facebook/zstd library where compression fails when the input
size exceeds 4GB (2^32 bytes).

# Context

The `ZSTD_compress()` function uses a 32-bit integer for the source size
parameter, which causes an overflow for inputs larger than 4GB. The function
returns `ZSTD_error_srcSize_wrong` instead of compressed data.

# Steps

1. Locate the size handling code in the compression path
2. Identify where 32-bit integer types are used for size parameters
3. Update the types to support 64-bit sizes
4. Ensure backward compatibility with existing callers
5. Verify that 32-bit platform builds are not broken

# Acceptance Criteria

- Compression succeeds for inputs larger than 4GB
- All existing unit tests pass
- No new compiler warnings
