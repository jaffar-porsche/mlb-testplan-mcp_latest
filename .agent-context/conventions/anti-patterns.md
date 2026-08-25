# Anti-Patterns

- Avoid catching bare 'except Exception' broadly around large blocks of logic instead of catching specific exception types, which can mask unrelated errors.
- Avoid embedding secrets/config defaults such as internal proxy URLs directly in source as fallback values for environment variables.
