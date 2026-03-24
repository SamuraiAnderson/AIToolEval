# Bug Fix: zstd compression fails for large inputs

## Problem

When input size exceeds 4GB, `zstd_compress()` returns error code -1 instead
of producing compressed output.

## Expected Behavior

The library should handle inputs of any size correctly, including those
exceeding the 4GB (2^32 byte) boundary.

## Reproduction

1. Create a test buffer larger than 4GB
2. Call `ZSTD_compress(dst, dstCapacity, src, 5GB, compressionLevel)`
3. Observe that the function returns `ZSTD_error_srcSize_wrong`

## Constraints

- All existing tests must continue to pass
- No regression on 32-bit platforms
