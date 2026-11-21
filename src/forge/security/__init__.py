"""Security package initialization."""

from forge.security.hashes import (
    canonical_json_dumps,
    compute_audit_hash,
    hash_arguments,
    hash_bytes,
    hash_file,
    hash_string,
)
from forge.security.paths import (
    PathSecurityError,
    canonicalize_path,
    ensure_within_workspace,
    validate_safe_filename,
)
from forge.security.secrets import redact_sensitive_text, sanitize_dict_for_logging
from forge.security.subprocesses import (
    SubprocessResult,
    SubprocessSecurityError,
    run_safe_subprocess,
    sanitize_environment,
    terminate_process_tree,
)
from forge.security.validation import (
    ValidationSecurityError,
    validate_data_against_schema,
    validate_identifier,
    validate_json_schema_definition,
)

__all__ = [
    "PathSecurityError",
    "SubprocessSecurityError",
    "ValidationSecurityError",
    "canonicalize_path",
    "ensure_within_workspace",
    "validate_safe_filename",
    "hash_bytes",
    "hash_string",
    "hash_file",
    "canonical_json_dumps",
    "hash_arguments",
    "compute_audit_hash",
    "SubprocessResult",
    "sanitize_environment",
    "terminate_process_tree",
    "run_safe_subprocess",
    "redact_sensitive_text",
    "sanitize_dict_for_logging",
    "validate_identifier",
    "validate_json_schema_definition",
    "validate_data_against_schema",
]
