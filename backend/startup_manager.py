"""
STARTUP APPLICATION OPTIMIZER
=============================

Windows Startup Application Manager

Responsibilities:
    - Detect Windows startup applications
    - Read startup entries from Windows Registry
    - Read the user's Startup Folder
    - Ignore non-application files such as desktop.ini
    - Identify executable files
    - Safely disable supported startup applications
    - Backup startup configuration before disabling
    - Restore disabled applications

Safety:
    - Current-user Registry entries can be modified.
    - System-wide Registry entries are read-only.
    - Startup Folder entries are currently read-only.
"""

import os
import re
import winreg
from pathlib import Path


# =========================================================
# WINDOWS REGISTRY PATHS
# =========================================================

HKCU_RUN_PATH = (
    r"Software\Microsoft\Windows\CurrentVersion\Run"
)

HKLM_RUN_PATH = (
    r"Software\Microsoft\Windows\CurrentVersion\Run"
)

DISABLED_PATH = (
    r"Software\StartupApplicationOptimizer\Disabled"
)


# =========================================================
# FILES THAT ARE NOT APPLICATIONS
# =========================================================

IGNORED_FILES = {
    "desktop.ini"
}


# =========================================================
# COMMAND CLEANING
# =========================================================

def clean_command(command):
    """
    Extract the most likely executable path from
    a Windows startup command.

    Examples:

        "C:\\Program Files\\App\\app.exe" --background

        becomes:

        C:\\Program Files\\App\\app.exe
    """

    if not command:
        return ""

    command = os.path.expandvars(
        str(command).strip()
    )

    # -----------------------------------------------------
    # Quoted executable
    # -----------------------------------------------------

    if command.startswith('"'):

        match = re.match(
            r'"([^"]+)"',
            command
        )

        if match:
            return match.group(1)


    # -----------------------------------------------------
    # Unquoted executable
    # -----------------------------------------------------

    match = re.search(
        r'([A-Za-z]:\\[^"]*?\.exe)',
        command,
        re.IGNORECASE
    )

    if match:
        return match.group(1)


    # -----------------------------------------------------
    # If no EXE was found
    # -----------------------------------------------------

    first_part = command.split()[0]

    return first_part


# =========================================================
# GET EXECUTABLE NAME
# =========================================================

def get_executable_name(command):
    """
    Return only the executable filename.

    Example:

        C:\\Program Files\\Microsoft\\OneDrive\\OneDrive.exe

    becomes:

        onedrive.exe
    """

    executable = clean_command(
        command
    )

    if not executable:
        return ""

    filename = os.path.basename(
        executable
    )

    # -----------------------------------------------------
    # Do not treat shortcut files as executables
    # -----------------------------------------------------

    if filename.lower().endswith(".lnk"):
        return ""

    # -----------------------------------------------------
    # Only return actual executable names
    # -----------------------------------------------------

    if filename.lower().endswith(".exe"):
        return filename.lower()

    return ""


# =========================================================
# DETERMINE ENTRY TYPE
# =========================================================

def get_entry_type(command):
    """
    Determine whether a startup entry is:

        executable
        shortcut
        other
    """

    if not command:
        return "unknown"

    cleaned = clean_command(
        command
    )

    lower = cleaned.lower()

    if lower.endswith(".exe"):
        return "executable"

    if lower.endswith(".lnk"):
        return "shortcut"

    return "other"


# =========================================================
# READ REGISTRY STARTUP ENTRIES
# =========================================================

def read_registry_startup(
    hive,
    registry_path,
    source_name,
    can_modify=False
):
    """
    Read startup applications from a Windows Registry key.
    """

    applications = []

    try:

        with winreg.OpenKey(
            hive,
            registry_path,
            0,
            winreg.KEY_READ
        ) as key:

            value_count = (
                winreg.QueryInfoKey(key)[1]
            )

            for index in range(
                value_count
            ):

                try:

                    name, command, value_type = (
                        winreg.EnumValue(
                            key,
                            index
                        )
                    )

                    # Ignore empty values
                    if not name:
                        continue

                    if command is None:
                        continue

                    command = str(
                        command
                    ).strip()

                    if not command:
                        continue

                    executable = (
                        get_executable_name(
                            command
                        )
                    )

                    entry_type = (
                        get_entry_type(
                            command
                        )
                    )

                    applications.append({

                        "name":
                            str(name),

                        "command":
                            command,

                        "executable":
                            executable,

                        "source":
                            source_name,

                        "type":
                            "registry",

                        "entry_type":
                            entry_type,

                        "status":
                            "Enabled",

                        "startup_enabled":
                            True,

                        "can_modify":
                            can_modify

                    })

                except (
                    OSError,
                    ValueError
                ):

                    continue

    except (
        FileNotFoundError,
        PermissionError,
        OSError
    ):

        pass

    return applications


# =========================================================
# CURRENT USER REGISTRY
# =========================================================

def get_user_registry_apps():
    """
    Get startup applications configured for
    the current Windows user.

    These entries can be modified by the optimizer.
    """

    return read_registry_startup(

        winreg.HKEY_CURRENT_USER,

        HKCU_RUN_PATH,

        "Registry (Current User)",

        can_modify=True

    )


# =========================================================
# SYSTEM REGISTRY
# =========================================================

def get_system_registry_apps():
    """
    Get system-wide startup applications.

    These are READ ONLY in our application.

    We do not modify HKLM entries because changing
    them can require administrator privileges and can
    affect every user on the computer.
    """

    return read_registry_startup(

        winreg.HKEY_LOCAL_MACHINE,

        HKLM_RUN_PATH,

        "Registry (System)",

        can_modify=False

    )


# =========================================================
# STARTUP FOLDER
# =========================================================

def get_startup_folder_apps():
    """
    Detect applications/shortcuts in the current user's
    Windows Startup folder.

    desktop.ini is ignored because it is a Windows
    configuration file, not a startup application.
    """

    applications = []

    appdata = os.environ.get(
        "APPDATA"
    )

    if not appdata:
        return applications


    startup_folder = (

        Path(appdata)

        / "Microsoft"

        / "Windows"

        / "Start Menu"

        / "Programs"

        / "Startup"

    )


    if not startup_folder.exists():
        return applications


    try:

        for item in startup_folder.iterdir():

            # -------------------------------------------------
            # Ignore directories
            # -------------------------------------------------

            if not item.is_file():
                continue


            # -------------------------------------------------
            # Ignore desktop.ini
            # -------------------------------------------------

            if item.name.lower() in IGNORED_FILES:
                continue


            # -------------------------------------------------
            # Determine type
            # -------------------------------------------------

            suffix = item.suffix.lower()


            if suffix == ".lnk":

                entry_type = "shortcut"

            elif suffix == ".exe":

                entry_type = "executable"

            else:

                entry_type = "other"


            # -------------------------------------------------
            # Only consider common startup file types
            # -------------------------------------------------

            if suffix not in (
                ".lnk",
                ".exe",
                ".bat",
                ".cmd",
                ".vbs"
            ):

                continue


            # -------------------------------------------------
            # For .lnk files we cannot directly use the
            # shortcut filename as the process executable.
            # It will therefore be shown as a startup
            # shortcut but not incorrectly matched to a
            # running process.
            # -------------------------------------------------

            executable = ""

            if suffix == ".exe":

                executable = (
                    item.name.lower()
                )


            applications.append({

                "name":
                    item.stem,

                "command":
                    str(item),

                "executable":
                    executable,

                "source":
                    "Startup Folder",

                "type":
                    "folder",

                "entry_type":
                    entry_type,

                "status":
                    "Enabled",

                "startup_enabled":
                    True,

                "can_modify":
                    False

            })

    except (
        PermissionError,
        OSError
    ):

        pass


    return applications


# =========================================================
# DISABLED BACKUP ENTRIES
# =========================================================

def get_disabled_startup_apps():
    """
    Return startup applications that were disabled
    using this optimizer.

    Original startup commands are stored in:

        HKCU\\Software\\StartupApplicationOptimizer\\Disabled
    """

    applications = []

    try:

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            DISABLED_PATH,
            0,
            winreg.KEY_READ
        ) as key:

            value_count = (
                winreg.QueryInfoKey(key)[1]
            )

            for index in range(
                value_count
            ):

                try:

                    name, command, value_type = (
                        winreg.EnumValue(
                            key,
                            index
                        )
                    )

                    if not name:
                        continue

                    if command is None:
                        continue

                    command = str(
                        command
                    ).strip()

                    if not command:
                        continue

                    applications.append({

                        "name":
                            str(name),

                        "command":
                            command,

                        "executable":
                            get_executable_name(
                                command
                            ),

                        "source":
                            "Optimizer Backup",

                        "type":
                            "disabled",

                        "entry_type":
                            get_entry_type(
                                command
                            ),

                        "status":
                            "Disabled",

                        "startup_enabled":
                            False,

                        "can_modify":
                            True

                    })

                except (
                    OSError,
                    ValueError
                ):

                    continue

    except (
        FileNotFoundError,
        PermissionError,
        OSError
    ):

        pass

    return applications


# =========================================================
# GET ALL STARTUP APPLICATIONS
# =========================================================

def get_startup_apps():
    """
    Return all startup applications detected on Windows.

    Sources:

        1. Current-user Registry
        2. System Registry
        3. Startup Folder
        4. Optimizer disabled backup

    Non-application files such as desktop.ini are excluded.
    """

    applications = []

    # -----------------------------------------------------
    # Current user registry
    # -----------------------------------------------------

    applications.extend(
        get_user_registry_apps()
    )

    # -----------------------------------------------------
    # System registry
    # -----------------------------------------------------

    applications.extend(
        get_system_registry_apps()
    )

    # -----------------------------------------------------
    # Startup folder
    # -----------------------------------------------------

    applications.extend(
        get_startup_folder_apps()
    )

    # -----------------------------------------------------
    # Disabled applications
    # -----------------------------------------------------

    applications.extend(
        get_disabled_startup_apps()
    )


    # -----------------------------------------------------
    # Remove duplicates
    # -----------------------------------------------------

    unique = {}

    for application in applications:

        name = str(
            application.get(
                "name",
                ""
            )
        ).strip().lower()

        source = str(
            application.get(
                "source",
                ""
            )
        ).strip().lower()

        command = str(
            application.get(
                "command",
                ""
            )
        ).strip().lower()

        if not name:
            continue

        # Use source + name + command to avoid
        # accidentally merging different startup entries.
        key = (
            source,
            name,
            command
        )

        unique[key] = application


    return list(
        unique.values()
    )


# =========================================================
# FIND CURRENT USER STARTUP APPLICATION
# =========================================================

def find_user_startup_app(name):
    """
    Find an application in the current user's
    Registry startup key.

    Only HKCU entries are eligible for modification.
    """

    if not name:
        return None


    try:

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            HKCU_RUN_PATH,
            0,
            winreg.KEY_READ
        ) as key:

            value_count = (
                winreg.QueryInfoKey(key)[1]
            )

            for index in range(
                value_count
            ):

                try:

                    value_name, command, value_type = (
                        winreg.EnumValue(
                            key,
                            index
                        )
                    )

                    if (
                        str(value_name).lower()
                        ==
                        str(name).lower()
                    ):

                        return {

                            "name":
                                value_name,

                            "command":
                                command,

                            "type":
                                value_type

                        }

                except OSError:

                    continue

    except (
        FileNotFoundError,
        PermissionError,
        OSError
    ):

        pass


    return None


# =========================================================
# DISABLE STARTUP APPLICATION
# =========================================================

def disable_startup(name):
    """
    Disable a current-user startup application.

    Steps:

        1. Find Registry entry.
        2. Back up original command.
        3. Remove active startup entry.
        4. Return success message.
    """

    application = find_user_startup_app(
        name
    )


    if not application:

        return {

            "success": False,

            "message":
                (
                    "This application cannot be disabled "
                    "by the optimizer. Only current-user "
                    "Registry startup entries are supported."
                )

        }


    try:

        # -------------------------------------------------
        # Create backup location
        # -------------------------------------------------

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            DISABLED_PATH
        ) as backup_key:

            winreg.SetValueEx(

                backup_key,

                application["name"],

                0,

                winreg.REG_SZ,

                str(
                    application["command"]
                )

            )


        # -------------------------------------------------
        # Remove active startup entry
        # -------------------------------------------------

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            HKCU_RUN_PATH,
            0,
            winreg.KEY_SET_VALUE
        ) as startup_key:

            winreg.DeleteValue(
                startup_key,
                application["name"]
            )


        return {

            "success": True,

            "message":
                (
                    f"{application['name']} has been "
                    "removed from Windows startup."
                ),

            "name":
                application["name"]

        }


    except PermissionError:

        return {

            "success": False,

            "message":
                (
                    "Permission denied while modifying "
                    "Windows startup configuration."
                )

        }


    except OSError as error:

        return {

            "success": False,

            "message":
                f"Windows Registry error: {error}"

        }


# =========================================================
# ENABLE STARTUP APPLICATION
# =========================================================

def enable_startup(name):
    """
    Restore a previously disabled startup application.

    Steps:

        1. Read backup command.
        2. Restore it to HKCU Run.
        3. Delete backup.
    """

    if not name:

        return {

            "success": False,

            "message":
                "Application name is required."

        }


    try:

        # -------------------------------------------------
        # Read backup
        # -------------------------------------------------

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            DISABLED_PATH,
            0,
            winreg.KEY_READ
        ) as backup_key:

            command, value_type = (
                winreg.QueryValueEx(
                    backup_key,
                    name
                )
            )


        # -------------------------------------------------
        # Restore startup entry
        # -------------------------------------------------

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            HKCU_RUN_PATH
        ) as startup_key:

            winreg.SetValueEx(

                startup_key,

                name,

                0,

                winreg.REG_SZ,

                str(command)

            )


        # -------------------------------------------------
        # Remove backup
        # -------------------------------------------------

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            DISABLED_PATH,
            0,
            winreg.KEY_SET_VALUE
        ) as backup_key:

            winreg.DeleteValue(
                backup_key,
                name
            )


        return {

            "success": True,

            "message":
                (
                    f"{name} has been restored to "
                    "Windows startup."
                ),

            "name":
                name

        }


    except FileNotFoundError:

        return {

            "success": False,

            "message":
                (
                    f"No disabled backup was found "
                    f"for {name}."
                )

        }


    except PermissionError:

        return {

            "success": False,

            "message":
                (
                    "Permission denied while modifying "
                    "Windows startup configuration."
                )

        }


    except OSError as error:

        return {

            "success": False,

            "message":
                f"Windows Registry error: {error}"

        }


# =========================================================
# CHECK WHETHER APPLICATION IS ENABLED
# =========================================================

def is_startup_enabled(name):
    """
    Check whether an application currently exists
    in the current user's Run registry.
    """

    application = find_user_startup_app(
        name
    )

    return application is not None


# =========================================================
# GET STARTUP SUMMARY
# =========================================================

def get_startup_summary():
    """
    Return a simple summary for the dashboard.
    """

    applications = get_startup_apps()

    enabled = sum(

        1

        for application in applications

        if application.get(
            "startup_enabled",
            False
        )

    )

    disabled = sum(

        1

        for application in applications

        if not application.get(
            "startup_enabled",
            True
        )

    )

    modifiable = sum(

        1

        for application in applications

        if application.get(
            "can_modify",
            False
        )

    )

    return {

        "total": len(
            applications
        ),

        "enabled": enabled,

        "disabled": disabled,

        "modifiable": modifiable

    }