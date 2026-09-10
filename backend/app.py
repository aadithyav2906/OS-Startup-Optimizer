"""
STARTUP APPLICATION OPTIMIZER
=============================

Main Flask backend for the OS DA2 project.

Provides:
    - System CPU / RAM / disk information
    - Running process information
    - Startup application detection
    - Startup application analysis
    - Optimization recommendations
    - Safe startup enable / disable operations

Frontend:
    HTML + CSS + JavaScript

Backend:
    Python + Flask + psutil

Operating System:
    Windows
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

import os
import time
import psutil

from analyzer import calculate_impact
from startup_manager import (
    get_startup_apps,
    disable_startup,
    enable_startup
)


# =========================================================
# APPLICATION CONFIGURATION
# =========================================================

app = Flask(__name__)

CORS(app)

APP_NAME = "Startup Application Optimizer"
APP_VERSION = "1.0.0"


# =========================================================
# HOME / HEALTH CHECK
# =========================================================

@app.route("/", methods=["GET"])
def home():
    """
    Basic backend health check.
    """

    return jsonify({
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "message": "Backend is running successfully."
    })


# =========================================================
# SYSTEM INFORMATION
# =========================================================

@app.route("/api/system", methods=["GET"])
def get_system_info():
    """
    Return current system resource information.

    Includes:
        CPU usage
        RAM usage
        Disk usage
        Process count
        CPU core count
    """

    try:

        # CPU percentage
        cpu_usage = psutil.cpu_percent(
            interval=0.5
        )

        # Virtual memory
        memory = psutil.virtual_memory()

        # System disk
        disk_path = os.path.abspath(os.sep)

        disk = psutil.disk_usage(
            disk_path
        )

        # Number of running processes
        process_count = len(
            psutil.pids()
        )

        # Logical CPU cores
        cpu_count = psutil.cpu_count(
            logical=True
        )

        return jsonify({
            "success": True,

            "cpu": round(
                cpu_usage,
                1
            ),

            "memory": {
                "percent": round(
                    memory.percent,
                    1
                ),

                "used_gb": round(
                    memory.used / (1024 ** 3),
                    2
                ),

                "total_gb": round(
                    memory.total / (1024 ** 3),
                    2
                ),

                "available_gb": round(
                    memory.available / (1024 ** 3),
                    2
                )
            },

            "disk": {
                "percent": round(
                    disk.percent,
                    1
                ),

                "used_gb": round(
                    disk.used / (1024 ** 3),
                    2
                ),

                "total_gb": round(
                    disk.total / (1024 ** 3),
                    2
                )
            },

            "process_count": process_count,

            "cpu_count": cpu_count
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================================================
# COLLECT RUNNING PROCESSES
# =========================================================

def collect_processes():
    """
    Collect information about currently running processes.

    Returns:
        List of process dictionaries.
    """

    processes = []

    process_objects = []

    # -----------------------------------------------------
    # First CPU measurement
    # -----------------------------------------------------

    for process in psutil.process_iter(
        [
            "pid",
            "name",
            "username",
            "status"
        ]
    ):

        try:

            # Initialize CPU measurement
            process.cpu_percent(
                interval=None
            )

            process_objects.append(
                process
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    # -----------------------------------------------------
    # Give psutil time for CPU calculation
    # -----------------------------------------------------

    time.sleep(0.3)

    # -----------------------------------------------------
    # Second CPU measurement
    # -----------------------------------------------------

    for process in process_objects:

        try:

            cpu_usage = process.cpu_percent(
                interval=None
            )

            memory_info = process.memory_info()

            memory_mb = (
                memory_info.rss /
                (1024 ** 2)
            )

            process_name = process.name()

            # Analyze process resource usage
            analysis = calculate_impact(
                cpu=cpu_usage,
                memory=memory_mb,
                running=True,
                startup_enabled=True
            )

            processes.append({

                "pid": process.pid,

                "name": process_name,

                "cpu": round(
                    cpu_usage,
                    2
                ),

                "memory": round(
                    memory_mb,
                    2
                ),

                "status": process.status(),

                "impact": analysis["impact"],

                "score": analysis["score"],

                "recommendation":
                    analysis["recommendation"]

            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    # -----------------------------------------------------
    # Sort processes by memory usage
    # -----------------------------------------------------

    processes.sort(
        key=lambda item: item["memory"],
        reverse=True
    )

    return processes


# =========================================================
# PROCESS API
# =========================================================

@app.route("/api/processes", methods=["GET"])
def get_processes():
    """
    Return currently running processes.

    Optional query:
        ?limit=50
    """

    try:

        processes = collect_processes()

        limit = request.args.get(
            "limit",
            default=50,
            type=int
        )

        # Keep the API response reasonable
        limit = max(
            1,
            min(limit, 100)
        )

        return jsonify({

            "success": True,

            "count": len(processes),

            "processes":
                processes[:limit]

        })

    except Exception as error:

        return jsonify({

            "success": False,

            "error": str(error)

        }), 500


# =========================================================
# STARTUP APPLICATION API
# =========================================================

@app.route("/api/startup", methods=["GET"])
def get_startup():
    """
    Return all detected startup applications.
    """

    try:

        applications = get_startup_apps()

        return jsonify({

            "success": True,

            "count": len(applications),

            "applications":
                applications

        })

    except Exception as error:

        return jsonify({

            "success": False,

            "error": str(error)

        }), 500


# =========================================================
# BUILD PROCESS MAP
# =========================================================

def build_process_map(processes):
    """
    Create a lookup table using executable names.

    Example:

        chrome.exe
            -> process 1
            -> process 2

        discord.exe
            -> process 3
    """

    process_map = {}

    for process in processes:

        name = str(
            process.get(
                "name",
                ""
            )
        ).lower()

        if not name:
            continue

        if name not in process_map:
            process_map[name] = []

        process_map[name].append(
            process
        )

    return process_map


# =========================================================
# ANALYZE STARTUP APPLICATIONS
# =========================================================

@app.route("/api/analyze", methods=["GET"])
def analyze_startup():
    """
    Analyze startup applications.

    For every startup application:

        1. Check whether it is running.
        2. Match it with running processes.
        3. Calculate CPU usage.
        4. Calculate memory usage.
        5. Calculate impact score.
        6. Generate recommendation.
    """

    try:

        # -------------------------------------------------
        # Get startup applications
        # -------------------------------------------------

        startup_apps = get_startup_apps()

        # -------------------------------------------------
        # Get running processes
        # -------------------------------------------------

        processes = collect_processes()

        # -------------------------------------------------
        # Build executable lookup
        # -------------------------------------------------

        process_map = build_process_map(
            processes
        )

        analyzed_apps = []

        # -------------------------------------------------
        # Analyze each startup application
        # -------------------------------------------------

        for application in startup_apps:

            executable = str(
                application.get(
                    "executable",
                    ""
                )
            ).lower()

            # Find matching running processes
            matching_processes = (
                process_map.get(
                    executable,
                    []
                )
            )

            # -------------------------------------------------
            # Calculate total CPU usage
            # -------------------------------------------------

            total_cpu = sum(

                float(
                    process.get(
                        "cpu",
                        0
                    )
                )

                for process
                in matching_processes

            )

            # -------------------------------------------------
            # Calculate total memory usage
            # -------------------------------------------------

            total_memory = sum(

                float(
                    process.get(
                        "memory",
                        0
                    )
                )

                for process
                in matching_processes

            )

            # -------------------------------------------------
            # Is the startup application running?
            # -------------------------------------------------

            is_running = (
                len(matching_processes) > 0
            )

            startup_enabled = application.get(
                "startup_enabled",
                True
            )

            # -------------------------------------------------
            # Analyze resource impact
            # -------------------------------------------------

            analysis = calculate_impact(

                cpu=total_cpu,

                memory=total_memory,

                running=is_running,

                startup_enabled=startup_enabled

            )

            # -------------------------------------------------
            # Create final result
            # -------------------------------------------------

            analyzed_apps.append({

                "name":
                    application.get(
                        "name",
                        "Unknown"
                    ),

                "command":
                    application.get(
                        "command",
                        ""
                    ),

                "executable":
                    executable,

                "source":
                    application.get(
                        "source",
                        "Unknown"
                    ),

                "type":
                    application.get(
                        "type",
                        "unknown"
                    ),

                "status":
                    application.get(
                        "status",
                        "Unknown"
                    ),

                "startup_enabled":
                    startup_enabled,

                "can_modify":
                    application.get(
                        "can_modify",
                        False
                    ),

                "running":
                    is_running,

                "cpu":
                    analysis["cpu"],

                "memory":
                    analysis["memory"],

                "cpu_score":
                    analysis["cpu_score"],

                "memory_score":
                    analysis["memory_score"],

                "score":
                    analysis["score"],

                "impact":
                    analysis["impact"],

                "optimization_score":
                    analysis[
                        "optimization_score"
                    ],

                "recommendation":
                    analysis[
                        "recommendation"
                    ]

            })

        # =================================================
        # SORT RESULTS
        # =================================================

        impact_order = {

            "High": 0,

            "Medium": 1,

            "Low": 2,

            "Not Running": 3

        }

        analyzed_apps.sort(

            key=lambda item: (

                impact_order.get(
                    item["impact"],
                    4
                ),

                -float(
                    item["score"]
                )

            )

        )

        # =================================================
        # SUMMARY
        # =================================================

        high_count = sum(

            1

            for application
            in analyzed_apps

            if application["impact"] == "High"

        )

        medium_count = sum(

            1

            for application
            in analyzed_apps

            if application["impact"] == "Medium"

        )

        low_count = sum(

            1

            for application
            in analyzed_apps

            if application["impact"] == "Low"

        )

        not_running_count = sum(

            1

            for application
            in analyzed_apps

            if application["impact"] ==
            "Not Running"

        )

        # =================================================
        # FINAL RESPONSE
        # =================================================

        return jsonify({

            "success": True,

            "summary": {

                "total":
                    len(analyzed_apps),

                "high":
                    high_count,

                "medium":
                    medium_count,

                "low":
                    low_count,

                "not_running":
                    not_running_count

            },

            "applications":
                analyzed_apps

        })

    except Exception as error:

        return jsonify({

            "success": False,

            "error": str(error)

        }), 500


# =========================================================
# OPTIMIZATION RECOMMENDATIONS
# =========================================================

@app.route(
    "/api/optimization",
    methods=["GET"]
)
def get_optimization():
    """
    Return startup applications that may benefit
    from optimization.

    Only running applications with Medium or High
    resource impact are returned.
    """

    try:

        startup_apps = get_startup_apps()

        processes = collect_processes()

        process_map = build_process_map(
            processes
        )

        candidates = []

        for application in startup_apps:

            # Only enabled startup applications
            if not application.get(
                "startup_enabled",
                True
            ):
                continue

            executable = str(
                application.get(
                    "executable",
                    ""
                )
            ).lower()

            matching_processes = (
                process_map.get(
                    executable,
                    []
                )
            )

            # Ignore applications that are not
            # currently running.
            if not matching_processes:
                continue

            total_cpu = sum(

                float(
                    process.get(
                        "cpu",
                        0
                    )
                )

                for process
                in matching_processes

            )

            total_memory = sum(

                float(
                    process.get(
                        "memory",
                        0
                    )
                )

                for process
                in matching_processes

            )

            analysis = calculate_impact(

                cpu=total_cpu,

                memory=total_memory,

                running=True,

                startup_enabled=True

            )

            # Only recommend applications that
            # have meaningful resource impact.
            if analysis["impact"] in (
                "High",
                "Medium"
            ):

                candidates.append({

                    "name":
                        application["name"],

                    "cpu":
                        analysis["cpu"],

                    "memory":
                        analysis["memory"],

                    "impact":
                        analysis["impact"],

                    "score":
                        analysis["score"],

                    "recommendation":
                        analysis["recommendation"],

                    "can_modify":
                        application.get(
                            "can_modify",
                            False
                        )

                })

        # Highest impact first
        candidates.sort(

            key=lambda item:
                item["score"],

            reverse=True

        )

        return jsonify({

            "success": True,

            "candidate_count":
                len(candidates),

            "candidates":
                candidates

        })

    except Exception as error:

        return jsonify({

            "success": False,

            "error": str(error)

        }), 500


# =========================================================
# DISABLE STARTUP APPLICATION
# =========================================================

@app.route(
    "/api/startup/disable",
    methods=["POST"]
)
def disable_startup_application():
    """
    Disable a startup application.

    Expected JSON:

        {
            "name": "Application Name"
        }
    """

    data = request.get_json(
        silent=True
    ) or {}

    name = data.get("name")

    # -----------------------------------------------------
    # Validate name
    # -----------------------------------------------------

    if not name:

        return jsonify({

            "success": False,

            "error":
                "Application name is required."

        }), 400

    if not isinstance(
        name,
        str
    ):

        return jsonify({

            "success": False,

            "error":
                "Invalid application name."

        }), 400

    name = name.strip()

    if not name:

        return jsonify({

            "success": False,

            "error":
                "Application name cannot be empty."

        }), 400

    # -----------------------------------------------------
    # Disable application
    # -----------------------------------------------------

    result = disable_startup(
        name
    )

    return jsonify(
        result
    ), (
        200
        if result.get("success")
        else 400
    )


# =========================================================
# ENABLE STARTUP APPLICATION
# =========================================================

@app.route(
    "/api/startup/enable",
    methods=["POST"]
)
def enable_startup_application():
    """
    Restore a previously disabled startup application.

    Expected JSON:

        {
            "name": "Application Name"
        }
    """

    data = request.get_json(
        silent=True
    ) or {}

    name = data.get("name")

    # -----------------------------------------------------
    # Validate name
    # -----------------------------------------------------

    if not name:

        return jsonify({

            "success": False,

            "error":
                "Application name is required."

        }), 400

    if not isinstance(
        name,
        str
    ):

        return jsonify({

            "success": False,

            "error":
                "Invalid application name."

        }), 400

    name = name.strip()

    if not name:

        return jsonify({

            "success": False,

            "error":
                "Application name cannot be empty."

        }), 400

    # -----------------------------------------------------
    # Enable application
    # -----------------------------------------------------

    result = enable_startup(
        name
    )

    return jsonify(
        result
    ), (
        200
        if result.get("success")
        else 400
    )


# =========================================================
# API ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def handle_not_found(error):

    return jsonify({

        "success": False,

        "error":
            "API endpoint not found."

    }), 404


@app.errorhandler(405)
def handle_method_not_allowed(error):

    return jsonify({

        "success": False,

        "error":
            "HTTP method not allowed."

    }), 405


@app.errorhandler(500)
def handle_internal_error(error):

    return jsonify({

        "success": False,

        "error":
            "Internal server error."

    }), 500


# =========================================================
# START FLASK SERVER
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("       STARTUP APPLICATION OPTIMIZER")
    print("=" * 60)
    print()
    print("Backend        : Flask")
    print("Monitoring     : psutil")
    print("Startup        : Windows Registry + Startup Folder")
    print("Platform       : Windows")
    print()
    print("Server:")
    print("http://127.0.0.1:5000")
    print()
    print("=" * 60)
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )