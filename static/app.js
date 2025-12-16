const API_BASE = "http://127.0.0.1:5000";

// Run when page is ready
window.addEventListener("DOMContentLoaded", () => {
    setupHandlers();
    loadExpenses();
});

function setupHandlers() {
    const expenseForm = document.getElementById("expense-form");
    const aiParseBtn = document.getElementById("ai-parse-btn");
    const aiInsightsBtn = document.getElementById("ai-insights-btn");

    if (expenseForm) {
        expenseForm.addEventListener("submit", onSubmitExpense);
    }
    if (aiParseBtn) {
        aiParseBtn.addEventListener("click", onAiParseClick);
    }
    if (aiInsightsBtn) {
        aiInsightsBtn.addEventListener("click", onAiInsightsClick);
    }
}

// ----- Load and show expenses -----

async function loadExpenses() {
    try {
        const res = await fetch(`${API_BASE}/api/expense`);
        const data = await res.json();
        const tbody = document.querySelector("#expense-table tbody");
        if (!tbody) return;

        tbody.innerHTML = "";
        data.forEach((e) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${e.date}</td>
                <td>${e.description}</td>
                <td>${e.category}</td>
                <td>${e.amount}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed to load expenses", err);
    }
}

// ----- Add expense (normal form) -----

async function onSubmitExpense(ev) {
    ev.preventDefault();

    const body = {
        date: document.getElementById("date").value,
        amount: document.getElementById("amount").value,
        category: document.getElementById("category").value,
        description: document.getElementById("description").value,
    };

    try {
        await fetch(`${API_BASE}/api/expense`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        // clear amount & description only
        document.getElementById("amount").value = "";
        document.getElementById("description").value = "";
        loadExpenses();
    } catch (err) {
        console.error("Failed to save expense", err);
    }
}

// ----- AI: parse free text into fields -----

async function onAiParseClick() {
    const textArea = document.getElementById("ai-text");
    const resultBox = document.getElementById("ai-result");

    if (!textArea || !resultBox) return;

    const text = textArea.value;
    if (!text.trim()) {
        resultBox.textContent = "Type something first.";
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/ai/parse-text`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        });
        const parsed = await res.json();
        resultBox.textContent = JSON.stringify(parsed, null, 2);

        // Fill form fields from AI suggestion
        if (parsed.amount !== undefined) {
            document.getElementById("amount").value = parsed.amount;
        }
        if (parsed.category) {
            document.getElementById("category").value = parsed.category;
        }
        if (parsed.description) {
            document.getElementById("description").value = parsed.description;
        }
    } catch (err) {
        console.error("AI parse failed", err);
        resultBox.textContent = "Error talking to AI.";
    }
}

// ----- AI: generate insights -----

async function onAiInsightsClick() {
    const box = document.getElementById("insights-box");
    if (!box) return;

    box.textContent = "Thinking...";
    try {
        const res = await fetch(`${API_BASE}/api/ai/insights`);
        const data = await res.json();
        box.textContent = data.insights || "No insights.";
    } catch (err) {
        console.error("AI insights failed", err);
        box.textContent = "Error getting AI insights.";
    }
}
