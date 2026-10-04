const API = "http://127.0.0.1:8000", $ = id => document.getElementById(id);
const CATS = ["food", "rent", "transport", "shopping", "bills", "entertainment"];
const show = msg => $("status").textContent = msg;
const notify = msg => Notification.permission === "granted" && new Notification("Financial alert", { body: msg });
const call = async (path, body) => {
  try {
    const r = await fetch(API + path, body && { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return await r.json();
  } catch { show("Cannot reach the backend. Start the server and refresh."); throw new Error("backend down"); }
};

async function load() {
  const s = await call(`/summary?income=${$("income").value || 0}`), b = s.budget;
    $("budget").innerHTML = `<b>Total spent: ₹${s.total}</b>` + (b
    ? `<br>This month, needs ₹${b.needs_spent} (plan ₹${b.plan.needs}) · wants ₹${b.wants_spent} (plan ₹${b.plan.wants}) · savings ₹${b.savings} (plan ₹${b.plan.savings})`
      + (b.savings < b.plan.savings ? `<div class='alert'>⚠ Savings are below your planned ₹${b.plan.savings}.</div>` : "") : "");
  if (b && b.savings < b.plan.savings) notify(`Savings are below your planned ₹${b.plan.savings}.`);
  const h = s.behavior;
  $("behavior").innerHTML = h
    ? `<b>Spending behavior</b><br>Top category: ${h.top_category} (${h.top_share}%) · Busiest day: ${h.busiest_day} · Biggest: ${h.biggest} · Average: ₹${h.average_expense}`
      + (h.month_trend_percent === null ? "" : ` · Month-over-month: ${h.month_trend_percent}%`)
      + (h.recurring.length ? `<br>Recurring: ${h.recurring.join(", ")}` : "")
    : "";
  Plotly.newPlot("cat", [{ type: "pie", labels: Object.keys(s.by_category), values: Object.values(s.by_category) }], { title: "By category", width: 400, height: 300 });
    Plotly.newPlot("month", [{ type: "bar", x: Object.keys(s.by_month), y: Object.values(s.by_month) }], { title: "By month", width: 400, height: 300, xaxis: { type: "category" } });
  $("recent").innerHTML = s.recent.map(r => `<li>${r.description}: ₹${r.amount} <select onchange="fixCat(${r.id}, this.value)">${CATS.map(c => `<option ${c === r.category ? "selected" : ""}>${c}</option>`).join("")}</select></li>`).join("");
  $("goals").innerHTML = (await call("/goals")).map(g => { const p = Math.min(100, Math.round(100 * g.saved / g.target)); return `<div class="goal"><div>${g.name}: ₹${g.saved} / ₹${g.target} (${p}%)</div><div class="bar"><div style="width:${p}%"></div></div><button onclick="fund(${g.id})">+ Add money</button></div>`; }).join("");
}

$("add").onclick = async () => {
  const r = await call("/expenses", { description: $("desc").value, amount: $("amt").value });
  $("alerts").innerHTML = r.alert ? `<div class="alert">⚠ ${r.alert}</div>` : "";
  r.alert && notify(r.alert);
  $("desc").value = $("amt").value = "";
  load();
};
$("gadd").onclick = async () => { await call("/goals", { name: $("gname").value, target: $("gtarget").value }); load(); };
$("refresh").onclick = load;
$("insights").onclick = async () => {
  $("insightbox").textContent = "Thinking...";
  $("insightbox").innerHTML = marked.parse((await call(`/insights?income=${$("income").value || 0}`)).insights);
};
$("retrain").onclick = async () => { const r = await call("/retrain", {}); show(`Model retrained on ${r.samples} samples, accuracy ${r.cv_accuracy}`); };
$("backup").onclick = async () => show("Backup saved: " + (await call("/backup", {})).saved);
$("csv").onchange = async e => {
  const r = await call("/import", { csv: await e.target.files[0].text() });
  show(`Imported ${r.imported} transactions`);
  e.target.value = "";
  load();
};
window.fund = async id => { const a = prompt("Amount to add (₹)"); if (a) { await call(`/goals/${id}/add`, { amount: a }); load(); } };
window.fixCat = async (id, category) => { await call(`/expenses/${id}/category`, { category }); load(); };

Notification.requestPermission();
load().catch(() => {});