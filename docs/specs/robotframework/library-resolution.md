# Library Resolution

## Stage

**Planned** (Stage 09)

## Goal

Resolve Python libraries imported in `.robot` files and extract keywords, arguments, and documentation.

## Approaches

1. **Static analysis**: read the library Python file, extract function names and docstrings through AST
2. **libdoc**: use `robot.libdoc` to generate structured documentation
3. **Cache**: store libspec (keyword definitions) in disk cache

## Implementation Strategy

- Start with basic static analysis for pure Python libraries
- Use libdoc as fallback for complex libraries
- Disk cache with mtime invalidation

## Challenges

- Libraries may be dynamic (keywords generated at runtime)
- Libraries may have wrappers/decorators that hide the real signature
- Libraries may be Java or .NET through remote library

## Notes

- Full library resolution is complex and will be incremental
- Initial MVP supports only local and BuiltIn keywords
- Known libraries (BuiltIn, Collections, etc.) may have initial manual specs
