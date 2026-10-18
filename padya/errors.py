"""Typed, classified errors (§26.8 fault model). Every failure fails closed."""


class PadyaError(Exception):
    """Base class; `code` is a stable machine-readable classification."""

    code = "padya_error"


class ContractError(PadyaError):
    """Cleaner data contract violated (§29.5)."""

    code = "contract_violation"


class OffsetError(PadyaError):
    """An offset is out of range, unsorted or not grapheme-safe (INV-2, OFF-10)."""

    code = "offset_invalid"


class RegistryError(PadyaError):
    """Metre registry failed to compile (§25, T25)."""

    code = "registry_invalid"


class ConfigError(PadyaError):
    """Configuration is missing, malformed or requests an unavailable feature."""

    code = "config_invalid"


class ValidationError(PadyaError):
    """Output failed pre-write validation (§24.1); nothing is written."""

    code = "output_invalid"


class NotImplementedFeature(PadyaError):
    """A target CLI option or stage exists in the spec but not in this build (§47.3)."""

    code = "not_implemented"
