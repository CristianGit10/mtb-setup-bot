"""Constantes de estado para el ConversationHandler."""

# Modo
MODE_TIRES = "tires"
MODE_SUSPENSION = "suspension"
MODE_FULL = "full"
MODE_DIAGNOSTIC = "diagnostic"

# Estados (enteros para ConversationHandler)
(
    MENU,
    USE_PROFILE,
    WEIGHT,
    DISCIPLINE,
    BIKE_TYPE,
    TERRAIN,
    FRONT_WIDTH,
    FRONT_TUBELESS,
    FRONT_TUBELESS_HELP,
    FRONT_INSERT,
    REAR_WIDTH,
    REAR_TUBELESS,
    REAR_TUBELESS_HELP,
    REAR_INSERT,
    FORK_TRAVEL,
    FORK_BRAND,
    SHOCK_TYPE,
    RIDING_STYLE,
    DIAG_SYMPTOM,
) = range(19)
