"""
Startup Application Optimizer
--------------------------------
Resource analysis and recommendation engine.

This module:
    - Calculates CPU impact
    - Calculates memory impact
    - Generates an overall impact score
    - Classifies applications as Low / Medium / High
    - Generates recommendations

This is a project-defined heuristic, not a Windows performance rating.
"""


# =========================================================
# THRESHOLDS
# =========================================================

CPU_LOW = 2.0
CPU_MEDIUM = 5.0
CPU_HIGH = 10.0

MEMORY_LOW = 150.0
MEMORY_MEDIUM = 300.0
MEMORY_HIGH = 500.0


# =========================================================
# SAFE NUMBER CONVERSION
# =========================================================

def safe_float(value):
    """Convert a value to float safely."""

    try:
        number = float(value)

        if number < 0:
            return 0.0

        return number

    except (TypeError, ValueError):
        return 0.0


# =========================================================
# CPU IMPACT
# =========================================================

def calculate_cpu_score(cpu):
    """
    Calculate CPU impact from 0-50.

    CPU usage:
        < 2%       -> Very low
        2-5%       -> Low
        5-10%      -> Medium
        >= 10%     -> High
    """

    cpu = safe_float(cpu)

    if cpu >= CPU_HIGH:
        return 50

    if cpu >= CPU_MEDIUM:
        # 25 - 50
        return round(
            25 + (
                (cpu - CPU_MEDIUM) /
                (CPU_HIGH - CPU_MEDIUM)
            ) * 25
        )

    if cpu >= CPU_LOW:
        # 10 - 25
        return round(
            10 + (
                (cpu - CPU_LOW) /
                (CPU_MEDIUM - CPU_LOW)
            ) * 15
        )

    # 0 - 10
    return round(
        (cpu / CPU_LOW) * 10
    )


# =========================================================
# MEMORY IMPACT
# =========================================================

def calculate_memory_score(memory):
    """
    Calculate memory impact from 0-50.

    Memory is measured in MB.
    """

    memory = safe_float(memory)

    if memory >= MEMORY_HIGH:
        return 50

    if memory >= MEMORY_MEDIUM:
        return round(
            25 + (
                (memory - MEMORY_MEDIUM) /
                (MEMORY_HIGH - MEMORY_MEDIUM)
            ) * 25
        )

    if memory >= MEMORY_LOW:
        return round(
            10 + (
                (memory - MEMORY_LOW) /
                (MEMORY_MEDIUM - MEMORY_LOW)
            ) * 15
        )

    return round(
        (memory / MEMORY_LOW) * 10
    )


# =========================================================
# IMPACT LEVEL
# =========================================================

def get_impact_level(score):
    """
    Convert 0-100 score into Low / Medium / High.
    """

    if score >= 60:
        return "High"

    if score >= 30:
        return "Medium"

    return "Low"


# =========================================================
# RECOMMENDATION
# =========================================================

def get_recommendation(
    cpu,
    memory,
    impact,
    running=True,
    startup_enabled=True
):
    """
    Generate a human-readable recommendation.
    """

    cpu = safe_float(cpu)
    memory = safe_float(memory)

    if not startup_enabled:

        return (
            "Startup is currently disabled for this "
            "application."
        )

    if not running:

        return (
            "This application is configured for startup "
            "but is not currently running. Current resource "
            "usage cannot be measured."
        )

    if impact == "High":

        return (
            "High resource impact detected. Consider "
            "disabling startup if this application is not "
            "required immediately after login."
        )

    if impact == "Medium":

        return (
            "Moderate resource impact detected. Disabling "
            "startup is optional if you do not need this "
            "application immediately."
        )

    return (
        "Low resource impact detected. Keeping startup "
        "enabled is reasonable."
    )


# =========================================================
# MAIN ANALYSIS
# =========================================================

def calculate_impact(
    cpu=0,
    memory=0,
    running=True,
    startup_enabled=True
):
    """
    Analyze CPU and memory usage.

    Returns a dictionary containing all analysis results.
    """

    cpu = safe_float(cpu)
    memory = safe_float(memory)

    # If application is not running, current resource
    # usage cannot represent its actual impact.
    if not running:

        return {
            "cpu": 0,
            "memory": 0,
            "cpu_score": 0,
            "memory_score": 0,
            "score": 0,
            "impact": "Not Running",
            "optimization_score": None,
            "recommendation": get_recommendation(
                cpu,
                memory,
                "Low",
                running=False,
                startup_enabled=startup_enabled
            )
        }

    cpu_score = calculate_cpu_score(cpu)

    memory_score = calculate_memory_score(memory)

    total_score = min(
        100,
        cpu_score + memory_score
    )

    impact = get_impact_level(
        total_score
    )

    recommendation = get_recommendation(
        cpu,
        memory,
        impact,
        running=True,
        startup_enabled=startup_enabled
    )

    # Optimization score:
    # Low impact = better optimization score.
    optimization_score = max(
        0,
        min(
            100,
            100 - total_score
        )
    )

    return {
        "cpu": round(cpu, 2),
        "memory": round(memory, 2),
        "cpu_score": cpu_score,
        "memory_score": memory_score,
        "score": total_score,
        "impact": impact,
        "optimization_score": optimization_score,
        "recommendation": recommendation
    }


# =========================================================
# ANALYZE MULTIPLE APPLICATIONS
# =========================================================

def analyze_applications(applications):
    """
    Analyze multiple application dictionaries.

    Example input:

        [
            {
                "name": "Discord",
                "cpu": 5.5,
                "memory": 300,
                "running": True
            }
        ]
    """

    results = []

    for application in applications:

        analysis = calculate_impact(
            cpu=application.get(
                "cpu",
                0
            ),
            memory=application.get(
                "memory",
                0
            ),
            running=application.get(
                "running",
                True
            ),
            startup_enabled=application.get(
                "startup_enabled",
                True
            )
        )

        results.append({
            **application,
            **analysis
        })

    return results