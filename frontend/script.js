/*
=========================================================
STARTUP APPLICATION OPTIMIZER
Frontend JavaScript
=========================================================
*/


// =======================================================
// CONFIGURATION
// =======================================================

const API_BASE = "http://127.0.0.1:5000";


// =======================================================
// GLOBAL STATE
// =======================================================

let startupApplications = [];

let processData = [];

let currentSystem = null;

let resourceChart = null;

let cpuChart = null;

let memoryChart = null;

let pendingAction = null;


// =======================================================
// DOM HELPER
// =======================================================

function $(id) {
    return document.getElementById(id);
}


// =======================================================
// NUMBER FORMAT
// =======================================================

function formatNumber(value, decimals = 1) {

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toFixed(decimals);
}


// =======================================================
// API REQUEST
// =======================================================

async function apiRequest(
    endpoint,
    options = {}
) {

    const response = await fetch(
        `${API_BASE}${endpoint}`,
        {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        }
    );

    let data;

    try {

        data = await response.json();

    } catch {

        throw new Error(
            "Invalid response from backend."
        );

    }


    if (!response.ok) {

        throw new Error(
            data.error ||
            data.message ||
            `Request failed (${response.status})`
        );

    }


    return data;
}


// =======================================================
// BACKEND CONNECTION
// =======================================================

async function checkBackend() {

    const dot = $("connectionDot");

    const text = $("connectionText");


    try {

        await apiRequest("/");

        dot.classList.add("connected");

        text.textContent =
            "Backend connected";


    } catch {

        dot.classList.remove("connected");

        text.textContent =
            "Backend offline";

    }

}


// =======================================================
// PAGE NAVIGATION
// =======================================================

function setupNavigation() {

    document.querySelectorAll(
        ".nav-item"
    ).forEach(button => {

        button.addEventListener(
            "click",
            () => {

                showPage(
                    button.dataset.page
                );

            }
        );

    });


    document.querySelectorAll(
        "[data-page]"
    ).forEach(button => {

        if (
            button.classList.contains(
                "nav-item"
            )
        ) {
            return;
        }


        button.addEventListener(
            "click",
            () => {

                showPage(
                    button.dataset.page
                );

            }
        );

    });

}


// =======================================================
// SHOW PAGE
// =======================================================

function showPage(pageId) {

    document.querySelectorAll(
        ".page"
    ).forEach(page => {

        page.classList.remove(
            "active"
        );

    });


    const page = $(pageId);

    if (page) {

        page.classList.add(
            "active"
        );

    }


    document.querySelectorAll(
        ".nav-item"
    ).forEach(button => {

        button.classList.toggle(
            "active",
            button.dataset.page === pageId
        );

    });


    const titles = {

        dashboard:
            "System Dashboard",

        startup:
            "Startup Applications",

        analytics:
            "System Analytics",

        optimizer:
            "Startup Optimizer",

        reports:
            "Optimization Report",

        about:
            "About the Project"

    };


    $("pageTitle").textContent =
        titles[pageId] ||
        "System Dashboard";


    if (pageId === "startup") {

        renderStartupTable();

    }


    if (pageId === "analytics") {

        loadProcesses();

    }


    if (pageId === "optimizer") {

        if (
            startupApplications.length === 0
        ) {
            loadStartupAnalysis();
        }

    }


    if (pageId === "reports") {

        updateReport();

    }

}


// =======================================================
// SYSTEM DATA
// =======================================================

async function loadSystemData() {

    try {

        const data =
            await apiRequest(
                "/api/system"
            );


        currentSystem = data;


        updateSystemCards(
            data
        );


        updateAnalyticsValues(
            data
        );


        updateReport();


        updateLastScan();


        $("connectionDot")
            .classList.add(
                "connected"
            );

        $("connectionText")
            .textContent =
                "Backend connected";


    } catch (error) {

        showToast(
            "Connection Error",
            error.message,
            "error"
        );

    }

}


// =======================================================
// UPDATE SYSTEM CARDS
// =======================================================

function updateSystemCards(data) {

    const cpu =
        Number(data.cpu) || 0;

    const memory =
        Number(
            data.memory?.percent
        ) || 0;


    $("cpuValue").textContent =
        `${formatNumber(cpu)}%`;

    $("memoryValue").textContent =
        `${formatNumber(memory)}%`;

    $("startupValue").textContent =
        startupApplications.length ||
        "—";

    $("processValue").textContent =
        data.process_count ?? "—";


    $("cpuBar").style.width =
        `${Math.min(cpu, 100)}%`;

    $("memoryBar").style.width =
        `${Math.min(memory, 100)}%`;


    updateResourceStatus(
        "cpuStatus",
        cpu
    );

    updateResourceStatus(
        "memoryStatus",
        memory
    );


    $("healthCpu").textContent =
        `${formatNumber(cpu)}%`;

    $("healthMemory").textContent =
        `${formatNumber(memory)}%`;

    $("healthStartup").textContent =
        startupApplications.length ||
        "—";

    $("healthProcesses").textContent =
        data.process_count ?? "—";


    calculateHealth(
        cpu,
        memory
    );

}


// =======================================================
// RESOURCE STATUS
// =======================================================

function updateResourceStatus(
    elementId,
    value
) {

    const element =
        $(elementId);


    let status = "Normal";


    if (value >= 85) {

        status = "Critical";

    } else if (value >= 70) {

        status = "High";

    } else if (value >= 50) {

        status = "Moderate";

    }


    element.textContent =
        status;

}


// =======================================================
// SYSTEM HEALTH
// =======================================================

function calculateHealth(
    cpu,
    memory
) {

    /*
        CPU:
            0%  = best
            100% = worst

        Memory:
            0%  = best
            100% = worst

        Weighted:
            CPU    40%
            Memory 60%
    */

    const cpuHealth =
        100 - Math.min(
            cpu,
            100
        );

    const memoryHealth =
        100 - Math.min(
            memory,
            100
        );


    let score = Math.round(

        cpuHealth * 0.4 +

        memoryHealth * 0.6

    );


    score = Math.max(
        0,
        Math.min(
            100,
            score
        )
    );


    $("healthScore").textContent =
        score;


    $("healthCircle").style.setProperty(
        "--score",
        `${score * 3.6}deg`
    );


    let status = "Excellent";


    if (score < 40) {

        status = "High Load";

    } else if (score < 60) {

        status = "Needs Attention";

    } else if (score < 80) {

        status = "Good";

    }


    $("healthBadge").textContent =
        status;


    $("healthBadge").className =
        "status-badge " +
        getStatusClass(score);

}


// =======================================================
// STATUS CLASS
// =======================================================

function getStatusClass(score) {

    if (score >= 80) {
        return "success";
    }

    if (score >= 60) {
        return "warning";
    }

    return "danger";
}


// =======================================================
// LOAD STARTUP ANALYSIS
// =======================================================

async function loadStartupAnalysis() {

    try {

        setStartupLoading();

        const data =
            await apiRequest(
                "/api/analyze"
            );


        startupApplications =
            data.applications || [];


        updateStartupSummary(
            data.summary
        );


        renderStartupTable();


        $("startupValue").textContent =
            startupApplications.length;


        $("healthStartup").textContent =
            startupApplications.length;


        updateReport();


    } catch (error) {

        $("startupTableBody").innerHTML = `

            <tr>
                <td
                    colspan="8"
                    class="error-cell"
                >
                    Unable to load startup applications.
                    <br>
                    ${escapeHtml(error.message)}
                </td>
            </tr>

        `;


        showToast(
            "Startup Analysis Failed",
            error.message,
            "error"
        );

    }

}


// =======================================================
// STARTUP LOADING
// =======================================================

function setStartupLoading() {

    $("startupTableBody").innerHTML = `

        <tr>
            <td
                colspan="8"
                class="loading-cell"
            >
                <div class="spinner"></div>
                Scanning startup applications...
            </td>
        </tr>

    `;

}


// =======================================================
// UPDATE STARTUP SUMMARY
// =======================================================

function updateStartupSummary(
    summary
) {

    if (!summary) {
        return;
    }


    $("totalStartup").textContent =
        summary.total ?? 0;

    $("highStartup").textContent =
        summary.high ?? 0;

    $("mediumStartup").textContent =
        summary.medium ?? 0;

    $("lowStartup").textContent =
        summary.low ?? 0;

    $("notRunningStartup").textContent =
        summary.not_running ?? 0;


    $("optimizerHigh").textContent =
        summary.high ?? 0;

    $("optimizerMedium").textContent =
        summary.medium ?? 0;


    updateReportSummary(
        summary
    );

}


// =======================================================
// RENDER STARTUP TABLE
// =======================================================

function renderStartupTable() {

    const tbody =
        $("startupTableBody");


    if (
        !startupApplications ||
        startupApplications.length === 0
    ) {

        tbody.innerHTML = `

            <tr>
                <td
                    colspan="8"
                    class="empty-cell"
                >
                    No startup applications found.
                </td>
            </tr>

        `;

        return;

    }


    const search =
        $("startupSearch")
            .value
            .toLowerCase()
            .trim();


    const filter =
        $("impactFilter")
            .value;


    const sort =
        $("sortSelect")
            .value;


    let applications =
        startupApplications.filter(
            app => {

                const matchesSearch =
                    !search ||
                    app.name
                        .toLowerCase()
                        .includes(search);


                const matchesFilter =
                    filter === "all" ||
                    app.impact === filter;


                return (
                    matchesSearch &&
                    matchesFilter
                );

            }
        );


    // -----------------------------------------------------
    // SORT
    // -----------------------------------------------------

    applications.sort(
        (a, b) => {

            if (sort === "name") {

                return a.name.localeCompare(
                    b.name
                );

            }


            if (sort === "cpu") {

                return (
                    Number(b.cpu || 0) -
                    Number(a.cpu || 0)
                );

            }


            if (sort === "memory") {

                return (
                    Number(b.memory || 0) -
                    Number(a.memory || 0)
                );

            }


            const order = {

                High: 0,

                Medium: 1,

                Low: 2,

                "Not Running": 3

            };


            return (
                (order[a.impact] ?? 4) -
                (order[b.impact] ?? 4)
            );

        }
    );


    if (applications.length === 0) {

        tbody.innerHTML = `

            <tr>
                <td
                    colspan="8"
                    class="empty-cell"
                >
                    No applications match
                    your filters.
                </td>
            </tr>

        `;

        return;

    }


    tbody.innerHTML =
        applications.map(
            createStartupRow
        ).join("");

}


// =======================================================
// CREATE STARTUP ROW
// =======================================================

function createStartupRow(app) {

    const impactClass =
        getImpactClass(
            app.impact
        );


    const runningText =
        app.running
            ? "Running"
            : "Not running";


    const runningClass =
        app.running
            ? "running"
            : "not-running";


    const cpuText =
        app.running
            ? `${formatNumber(app.cpu)}%`
            : "—";


    const memoryText =
        app.running
            ? `${formatNumber(app.memory)} MB`
            : "—";


    let action = `

        <span class="protected">
            Protected
        </span>

    `;


    if (
        app.can_modify &&
        app.startup_enabled
    ) {

        action = `

            <button
                class="table-action disable"
                data-action="disable"
                data-name="${escapeAttribute(app.name)}"
            >
                Disable
            </button>

        `;

    }


    if (
        app.can_modify &&
        !app.startup_enabled
    ) {

        action = `

            <button
                class="table-action enable"
                data-action="enable"
                data-name="${escapeAttribute(app.name)}"
            >
                Enable
            </button>

        `;

    }


    return `

        <tr>

            <td>

                <div class="application-cell">

                    <div class="app-avatar">
                        ${getAppIcon(app.name)}
                    </div>

                    <div>

                        <strong>
                            ${escapeHtml(app.name)}
                        </strong>

                        <small>
                            ${escapeHtml(
                                app.executable ||
                                app.entry_type ||
                                "Startup entry"
                            )}
                        </small>

                    </div>

                </div>

            </td>


            <td>

                <span class="source-badge">
                    ${escapeHtml(
                        app.source || "Unknown"
                    )}
                </span>

            </td>


            <td>

                <span class="status-pill enabled">
                    ${escapeHtml(
                        app.status || "Unknown"
                    )}
                </span>

            </td>


            <td>

                <span
                    class="running-status ${runningClass}"
                >
                    <span></span>
                    ${runningText}
                </span>

            </td>


            <td>
                <strong>
                    ${cpuText}
                </strong>
            </td>


            <td>
                <strong>
                    ${memoryText}
                </strong>
            </td>


            <td>

                <span
                    class="impact-badge ${impactClass}"
                    title="${escapeAttribute(
                        app.recommendation || ""
                    )}"
                >
                    ${escapeHtml(
                        app.impact
                    )}
                </span>

            </td>


            <td>
                ${action}
            </td>

        </tr>

    `;

}


// =======================================================
// IMPACT CLASS
// =======================================================

function getImpactClass(
    impact
) {

    switch (impact) {

        case "High":
            return "high";

        case "Medium":
            return "medium";

        case "Low":
            return "low";

        default:
            return "not-running";

    }

}


// =======================================================
// APPLICATION ICON
// =======================================================

function getAppIcon(name) {

    const value =
        String(name)
            .toLowerCase();


    if (value.includes("edge")) {
        return "E";
    }

    if (value.includes("opera")) {
        return "O";
    }

    if (value.includes("one drive") ||
        value.includes("onedrive")) {
        return "☁";
    }

    if (value.includes("grammarly")) {
        return "G";
    }

    if (value.includes("blue")) {
        return "B";
    }

    if (value.includes("winzip")) {
        return "W";
    }

    if (value.includes("security")) {
        return "✓";
    }

    if (value.includes("realtek") ||
        value.includes("rtk")) {
        return "R";
    }

    return "●";

}


// =======================================================
// STARTUP TABLE ACTIONS
// =======================================================

function setupStartupActions() {

    $("startupTableBody")
        .addEventListener(
            "click",
            event => {

                const button =
                    event.target.closest(
                        "[data-action]"
                    );


                if (!button) {
                    return;
                }


                const action =
                    button.dataset.action;


                const name =
                    button.dataset.name;


                if (action === "disable") {

                    openDisableModal(
                        name
                    );

                }


                if (action === "enable") {

                    enableStartup(
                        name
                    );

                }

            }
        );

}


// =======================================================
// DISABLE MODAL
// =======================================================

function openDisableModal(
    name
) {

    pendingAction = {
        action: "disable",
        name: name
    };


    $("modalTitle").textContent =
        "Disable Startup?";


    $("modalMessage").textContent =
        `${name} will no longer launch automatically when Windows starts. The original configuration will be backed up so it can be restored later.`;


    $("modalConfirm").textContent =
        "Disable Startup";


    $("modalConfirm").className =
        "danger-button";


    $("modalOverlay")
        .classList.add(
            "show"
        );

}


// =======================================================
// CONFIRM ACTION
// =======================================================

async function confirmModalAction() {

    if (!pendingAction) {
        return;
    }


    const {
        action,
        name
    } = pendingAction;


    closeModal();


    if (action === "disable") {

        await disableStartup(
            name
        );

    }

}


// =======================================================
// CLOSE MODAL
// =======================================================

function closeModal() {

    $("modalOverlay")
        .classList.remove(
            "show"
        );


    pendingAction = null;

}


// =======================================================
// DISABLE STARTUP
// =======================================================

async function disableStartup(
    name
) {

    try {

        const data =
            await apiRequest(
                "/api/startup/disable",
                {
                    method: "POST",

                    body: JSON.stringify({
                        name: name
                    })
                }
            );


        showToast(
            "Startup Disabled",
            data.message ||
                `${name} was disabled.`,
            "success"
        );


        await loadStartupAnalysis();


    } catch (error) {

        showToast(
            "Unable to Disable",
            error.message,
            "error"
        );

    }

}


// =======================================================
// ENABLE STARTUP
// =======================================================

async function enableStartup(
    name
) {

    try {

        const data =
            await apiRequest(
                "/api/startup/enable",
                {
                    method: "POST",

                    body: JSON.stringify({
                        name: name
                    })
                }
            );


        showToast(
            "Startup Enabled",
            data.message ||
                `${name} was enabled.`,
            "success"
        );


        await loadStartupAnalysis();


    } catch (error) {

        showToast(
            "Unable to Enable",
            error.message,
            "error"
        );

    }

}


// =======================================================
// LOAD PROCESSES
// =======================================================

async function loadProcesses() {

    try {

        const data =
            await apiRequest(
                "/api/processes?limit=10"
            );


        processData =
            data.processes || [];


        renderProcesses(
            processData
        );


    } catch (error) {

        $("processList").innerHTML = `

            <div class="empty-state">
                Unable to load processes.
                <br>
                ${escapeHtml(error.message)}
            </div>

        `;

    }

}


// =======================================================
// RENDER PROCESSES
// =======================================================

function renderProcesses(
    processes
) {

    if (
        !processes ||
        processes.length === 0
    ) {

        $("processList").innerHTML = `

            <div class="empty-state">
                No processes available.
            </div>

        `;

        return;

    }


    $("processList").innerHTML =
        processes.map(
            (process, index) => {

                const maxMemory =
                    Math.max(
                        ...processes.map(
                            item =>
                                Number(
                                    item.memory
                                ) || 0
                        )
                    );


                const memory =
                    Number(
                        process.memory
                    ) || 0;


                const percentage =
                    maxMemory > 0
                        ? (
                            memory /
                            maxMemory
                        ) * 100
                        : 0;


                return `

                    <div class="process-item">

                        <div class="process-rank">
                            ${index + 1}
                        </div>


                        <div class="process-info">

                            <strong>
                                ${escapeHtml(
                                    process.name
                                )}
                            </strong>

                            <small>
                                PID ${process.pid}
                            </small>

                        </div>


                        <div class="process-resource">

                            <div class="resource-label">

                                <span>
                                    Memory
                                </span>

                                <strong>
                                    ${formatNumber(
                                        memory
                                    )} MB
                                </strong>

                            </div>


                            <div class="mini-progress">

                                <div
                                    style="width:${percentage}%"
                                ></div>

                            </div>

                        </div>


                        <div class="process-cpu">

                            <strong>
                                ${formatNumber(
                                    process.cpu
                                )}%
                            </strong>

                            <small>
                                CPU
                            </small>

                        </div>

                    </div>

                `;

            }
        ).join("");

}


// =======================================================
// ANALYTICS VALUES
// =======================================================

function updateAnalyticsValues(
    data
) {

    if (!data) {
        return;
    }


    $("analyticsCpu").textContent =
        `${formatNumber(data.cpu)}%`;


    $("analyticsMemory").textContent =
        `${formatNumber(
            data.memory?.percent
        )}%`;

}


// =======================================================
// CHARTS
// =======================================================

function initializeCharts() {

    const labels = [];

    const cpuData = [];

    const memoryData = [];


    for (
        let i = 0;
        i < 20;
        i++
    ) {

        labels.push("");

        cpuData.push(null);

        memoryData.push(null);

    }


    const resourceCanvas =
        $("resourceChart");


    if (resourceCanvas) {

        resourceChart =
            new Chart(
                resourceCanvas,
                {
                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {
                                label: "CPU %",

                                data: cpuData,

                                tension: 0.4,

                                borderWidth: 2,

                                pointRadius: 0
                            },

                            {
                                label: "Memory %",

                                data: memoryData,

                                tension: 0.4,

                                borderWidth: 2,

                                pointRadius: 0
                            }

                        ]

                    },

                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        interaction: {
                            intersect: false,
                            mode: "index"
                        },

                        plugins: {

                            legend: {
                                position: "bottom"
                            }

                        },

                        scales: {

                            y: {

                                min: 0,

                                max: 100,

                                ticks: {
                                    callback:
                                        value =>
                                            `${value}%`
                                }

                            },

                            x: {
                                display: false
                            }

                        }

                    }

                }
            );

    }


    createSmallCharts();

}


// =======================================================
// SMALL CHARTS
// =======================================================

function createSmallCharts() {

    const cpuCanvas =
        $("cpuChart");


    if (cpuCanvas) {

        cpuChart =
            new Chart(
                cpuCanvas,
                {
                    type: "line",

                    data: {

                        labels:
                            Array(20).fill(""),

                        datasets: [

                            {
                                label:
                                    "CPU Usage",

                                data:
                                    Array(20).fill(null),

                                tension:
                                    0.4,

                                borderWidth:
                                    2,

                                pointRadius:
                                    0

                            }

                        ]

                    },

                    options: chartOptions()

                }
            );

    }


    const memoryCanvas =
        $("memoryChart");


    if (memoryCanvas) {

        memoryChart =
            new Chart(
                memoryCanvas,
                {
                    type: "line",

                    data: {

                        labels:
                            Array(20).fill(""),

                        datasets: [

                            {
                                label:
                                    "Memory Usage",

                                data:
                                    Array(20).fill(null),

                                tension:
                                    0.4,

                                borderWidth:
                                    2,

                                pointRadius:
                                    0

                            }

                        ]

                    },

                    options: chartOptions()

                }
            );

    }

}


// =======================================================
// CHART OPTIONS
// =======================================================

function chartOptions() {

    return {

        responsive: true,

        maintainAspectRatio: false,

        plugins: {

            legend: {
                display: false
            }

        },

        scales: {

            y: {

                min: 0,

                max: 100,

                ticks: {

                    callback:
                        value =>
                            `${value}%`

                }

            },

            x: {
                display: false
            }

        }

    };

}


// =======================================================
// UPDATE CHARTS
// =======================================================

function updateCharts() {

    if (!currentSystem) {
        return;
    }


    const cpu =
        Number(
            currentSystem.cpu
        ) || 0;


    const memory =
        Number(
            currentSystem.memory?.percent
        ) || 0;


    if (resourceChart) {

        resourceChart.data.datasets[0]
            .data.shift();

        resourceChart.data.datasets[0]
            .data.push(cpu);


        resourceChart.data.datasets[1]
            .data.shift();

        resourceChart.data.datasets[1]
            .data.push(memory);


        resourceChart.update(
            "none"
        );

    }


    if (cpuChart) {

        cpuChart.data.datasets[0]
            .data.shift();

        cpuChart.data.datasets[0]
            .data.push(cpu);

        cpuChart.update(
            "none"
        );

    }


    if (memoryChart) {

        memoryChart.data.datasets[0]
            .data.shift();

        memoryChart.data.datasets[0]
            .data.push(memory);

        memoryChart.update(
            "none"
        );

    }

}


// =======================================================
// OPTIMIZATION SCAN
// =======================================================

async function runOptimizationScan() {

    const button =
        $("optimizationScanButton");


    button.disabled = true;

    button.innerHTML =
        `<span class="spinner-small"></span> Scanning...`;


    try {

        await loadStartupAnalysis();


        const data =
            await apiRequest(
                "/api/optimization"
            );


        const candidates =
            data.candidates || [];


        renderRecommendations(
            candidates
        );


        calculateOptimizationScore(
            candidates
        );


        showToast(
            "Scan Complete",
            `${candidates.length} optimization candidate(s) found.`,
            "success"
        );


    } catch (error) {

        showToast(
            "Optimization Failed",
            error.message,
            "error"
        );

    } finally {

        button.disabled = false;

        button.innerHTML =
            "⚡ Scan for Optimization";

    }

}


// =======================================================
// CALCULATE OPTIMIZATION SCORE
// =======================================================

function calculateOptimizationScore(
    candidates
) {

    let score = 100;


    candidates.forEach(
        candidate => {

            const impact =
                Number(
                    candidate.score
                ) || 0;


            score -= (
                impact * 0.25
            );

        }
    );


    score = Math.round(
        Math.max(
            0,
            Math.min(
                100,
                score
            )
        )
    );


    $("optimizationScore")
        .textContent = score;


    $("optimizationCircle")
        .style.setProperty(
            "--score",
            `${score * 3.6}deg`
        );


    $("optimizerHigh")
        .textContent =
            candidates.filter(
                item =>
                    item.impact === "High"
            ).length;


    $("optimizerMedium")
        .textContent =
            candidates.filter(
                item =>
                    item.impact === "Medium"
            ).length;


    let title =
        "Excellent startup configuration";


    let description =
        "Your currently running startup applications have low resource impact.";


    if (score < 80) {

        title =
            "Some optimization is possible";


        description =
            "A few startup applications are consuming meaningful system resources.";

    }


    if (score < 60) {

        title =
            "Startup needs attention";


        description =
            "Several startup applications have significant resource impact.";

    }


    $("optimizationTitle")
        .textContent =
            title;


    $("optimizationDescription")
        .textContent =
            description;

}


// =======================================================
// RENDER RECOMMENDATIONS
// =======================================================

function renderRecommendations(
    candidates
) {

    const container =
        $("recommendationGrid");


    if (
        !candidates ||
        candidates.length === 0
    ) {

        container.innerHTML = `

            <div class="empty-state panel">

                <div class="empty-icon">
                    ✓
                </div>

                <h3>
                    No immediate optimization
                    candidates
                </h3>

                <p>
                    No currently running startup
                    applications have medium or high
                    resource impact.
                </p>

            </div>

        `;

        return;

    }


    container.innerHTML =
        candidates.map(
            candidate => {

                const impactClass =
                    getImpactClass(
                        candidate.impact
                    );


                const app =
                    startupApplications.find(
                        item =>
                            item.name ===
                            candidate.name
                    );


                const canModify =
                    candidate.can_modify &&
                    app?.can_modify;


                return `

                    <div class="recommendation-card">

                        <div class="recommendation-top">

                            <div class="recommendation-app">

                                <div class="app-avatar large">
                                    ${getAppIcon(
                                        candidate.name
                                    )}
                                </div>

                                <div>

                                    <strong>
                                        ${escapeHtml(
                                            candidate.name
                                        )}
                                    </strong>

                                    <small>
                                        Startup Application
                                    </small>

                                </div>

                            </div>


                            <span
                                class="impact-badge ${impactClass}"
                            >
                                ${escapeHtml(
                                    candidate.impact
                                )}
                            </span>

                        </div>


                        <div class="recommendation-metrics">

                            <div>

                                <span>
                                    CPU
                                </span>

                                <strong>
                                    ${formatNumber(
                                        candidate.cpu
                                    )}%
                                </strong>

                            </div>


                            <div>

                                <span>
                                    Memory
                                </span>

                                <strong>
                                    ${formatNumber(
                                        candidate.memory
                                    )} MB
                                </strong>

                            </div>


                            <div>

                                <span>
                                    Impact Score
                                </span>

                                <strong>
                                    ${candidate.score}/100
                                </strong>

                            </div>

                        </div>


                        <p class="recommendation-text">

                            ${escapeHtml(
                                candidate.recommendation
                            )}

                        </p>


                        ${
                            canModify
                                ? `

                                    <button
                                        class="recommendation-button"
                                        data-recommend-disable="${escapeAttribute(
                                            candidate.name
                                        )}"
                                    >
                                        Disable Startup
                                    </button>

                                `
                                : `

                                    <div class="protected-message">
                                        System-managed entry —
                                        read only
                                    </div>

                                `
                        }

                    </div>

                `;

            }
        ).join("");

}


// =======================================================
// RECOMMENDATION ACTIONS
// =======================================================

function setupRecommendationActions() {

    $("recommendationGrid")
        .addEventListener(
            "click",
            event => {

                const button =
                    event.target.closest(
                        "[data-recommend-disable]"
                    );


                if (!button) {
                    return;
                }


                const name =
                    button.dataset
                        .recommendDisable;


                openDisableModal(
                    name
                );

            }
        );

}


// =======================================================
// REPORT
// =======================================================

function updateReport() {

    const now =
        new Date();


    $("reportDate").textContent =
        formatDateTime(now);


    if (!currentSystem) {
        return;
    }


    $("reportCpu").textContent =
        `${formatNumber(
            currentSystem.cpu
        )}%`;


    $("reportMemory").textContent =
        `${formatNumber(
            currentSystem.memory?.percent
        )}%`;


    $("reportProcesses").textContent =
        currentSystem.process_count ??
        "—";


    $("reportStartup").textContent =
        startupApplications.length ||
        "—";


    const summary =
        calculateLocalSummary();


    updateReportSummary(
        summary
    );


    renderReportRecommendations();

}


// =======================================================
// LOCAL SUMMARY
// =======================================================

function calculateLocalSummary() {

    return {

        total:
            startupApplications.length,

        high:
            startupApplications.filter(
                app =>
                    app.impact === "High"
            ).length,

        medium:
            startupApplications.filter(
                app =>
                    app.impact === "Medium"
            ).length,

        low:
            startupApplications.filter(
                app =>
                    app.impact === "Low"
            ).length,

        not_running:
            startupApplications.filter(
                app =>
                    app.impact ===
                    "Not Running"
            ).length

    };

}


// =======================================================
// REPORT SUMMARY
// =======================================================

function updateReportSummary(
    summary
) {

    if (!summary) {
        return;
    }


    $("reportHigh").textContent =
        summary.high ?? 0;

    $("reportMedium").textContent =
        summary.medium ?? 0;

    $("reportLow").textContent =
        summary.low ?? 0;

    $("reportNotRunning").textContent =
        summary.not_running ?? 0;

}


// =======================================================
// REPORT RECOMMENDATIONS
// =======================================================

function renderReportRecommendations() {

    const high =
        startupApplications.filter(
            app =>
                app.impact === "High"
        );


    const medium =
        startupApplications.filter(
            app =>
                app.impact === "Medium"
        );


    let items = [
        ...high,
        ...medium
    ];


    items = items.slice(
        0,
        5
    );


    if (items.length === 0) {

        $("reportRecommendations")
            .innerHTML = `

                <div class="report-success">
                    ✓ No high or medium impact
                    startup applications are currently
                    running.
                </div>

            `;

        return;

    }


    $("reportRecommendations")
        .innerHTML =
            items.map(
                app => `

                    <div class="report-recommendation">

                        <strong>
                            ${escapeHtml(
                                app.name
                            )}
                        </strong>

                        <span>
                            ${escapeHtml(
                                app.impact
                            )} impact —
                            ${formatNumber(
                                app.cpu
                            )}% CPU,
                            ${formatNumber(
                                app.memory
                            )} MB RAM
                        </span>

                    </div>

                `
            ).join("");

}


// =======================================================
// PRINT REPORT
// =======================================================

function printReport() {

    updateReport();

    window.print();

}


// =======================================================
// LAST SCAN
// =======================================================

function updateLastScan() {

    $("lastScan").textContent =
        new Date().toLocaleTimeString(
            [],
            {
                hour: "2-digit",
                minute: "2-digit"
            }
        );

}


// =======================================================
// DATE FORMAT
// =======================================================

function formatDateTime(
    date
) {

    return date.toLocaleString(
        [],
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );

}


// =======================================================
// TOAST
// =======================================================

function showToast(
    title,
    message,
    type = "success"
) {

    const toast =
        $("toast");


    $("toastTitle").textContent =
        title;


    $("toastMessage").textContent =
        message;


    $("toastIcon").textContent =
        type === "error"
            ? "!"
            : "✓";


    toast.className =
        `toast show ${type}`;


    clearTimeout(
        window.toastTimer
    );


    window.toastTimer =
        setTimeout(
            () => {

                toast.classList.remove(
                    "show"
                );

            },
            4000
        );

}


// =======================================================
// HTML ESCAPING
// =======================================================

function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}


function escapeAttribute(
    value
) {

    return escapeHtml(
        value
    );

}


// =======================================================
// SEARCH / FILTER
// =======================================================

function setupFilters() {

    $("startupSearch")
        .addEventListener(
            "input",
            renderStartupTable
        );


    $("impactFilter")
        .addEventListener(
            "change",
            renderStartupTable
        );


    $("sortSelect")
        .addEventListener(
            "change",
            renderStartupTable
        );

}


// =======================================================
// EVENT LISTENERS
// =======================================================

function setupEvents() {

    $("scanButton")
        .addEventListener(
            "click",
            async () => {

                $("scanButton").disabled =
                    true;

                $("scanButton").innerHTML =
                    `<span class="spinner-small"></span> Analyzing...`;


                await Promise.all([
                    loadSystemData(),
                    loadStartupAnalysis()
                ]);


                $("scanButton").disabled =
                    false;

                $("scanButton").innerHTML =
                    "<span>⌕</span> Analyze System";


                showToast(
                    "Analysis Complete",
                    "System and startup applications have been analyzed.",
                    "success"
                );

            }
        );


    $("refreshButton")
        .addEventListener(
            "click",
            refreshAll
        );


    $("startupRefreshButton")
        .addEventListener(
            "click",
            loadStartupAnalysis
        );


    $("processRefreshButton")
        .addEventListener(
            "click",
            loadProcesses
        );


    $("optimizationScanButton")
        .addEventListener(
            "click",
            runOptimizationScan
        );


    $("printReportButton")
        .addEventListener(
            "click",
            printReport
        );


    $("modalClose")
        .addEventListener(
            "click",
            closeModal
        );


    $("modalCancel")
        .addEventListener(
            "click",
            closeModal
        );


    $("modalConfirm")
        .addEventListener(
            "click",
            confirmModalAction
        );


    $("modalOverlay")
        .addEventListener(
            "click",
            event => {

                if (
                    event.target ===
                    $("modalOverlay")
                ) {

                    closeModal();

                }

            }
        );

}


// =======================================================
// REFRESH ALL
// =======================================================

async function refreshAll() {

    await Promise.all([
        loadSystemData(),
        loadStartupAnalysis()
    ]);

    updateCharts();

    await loadProcesses();

    showToast(
        "Refreshed",
        "System information has been updated.",
        "success"
    );

}


// =======================================================
// AUTOMATIC MONITORING
// =======================================================

async function automaticMonitoring() {

    try {

        await loadSystemData();

        updateCharts();

    } catch {

        // Ignore temporary monitoring errors.

    }

}


// =======================================================
// INITIALIZE APPLICATION
// =======================================================

async function initializeApp() {

    console.log(
        "Startup Application Optimizer"
    );

    setupNavigation();

    setupStartupActions();

    setupRecommendationActions();

    setupFilters();

    setupEvents();

    initializeCharts();


    await checkBackend();


    await Promise.all([
        loadSystemData(),
        loadStartupAnalysis()
    ]);


    await loadProcesses();


    updateCharts();


    // Refresh system metrics every 5 seconds.
    setInterval(
        automaticMonitoring,
        5000
    );


    // Recheck backend periodically.
    setInterval(
        checkBackend,
        10000
    );

}


// =======================================================
// START
// =======================================================

document.addEventListener(
    "DOMContentLoaded",
    initializeApp
);