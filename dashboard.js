const CATS = ["food", "rent", "transport", "shopping", "bills", "entertainment"];
const API = "http://127.0.0.1:8000", $ = id => document.getElementById(id);
const call = (path, body) => fetch(API + path, body && { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(r => r.json());

async function load() {
  const s = await call(`/summary?income=${$("income").value || 0}`), b = s.budget;
  $("budget").innerHTML = `<b>Total spent: ₹${s.total}</b>` + (b
    ? `<br>Needs ₹${b.needs_spent} (plan ₹${b.plan.needs}) · Wants ₹${b.wants_spent} (plan ₹${b.plan.wants}) · Savings ₹${b.savings} (plan ₹${b.plan.savings})`
      + (b.savings < b.plan.savings ? "<div class='alert'>⚠ Savings are below the 20% target.</div>" : "") : "");
  Plotly.newPlot("cat", [{ type: "pie", labels: Object.keys(s.by_category), values: Object.values(s.by_category) }], { title: "By category", width: 400, height: 300 });
  Plotly.newPlot("month", [{ type: "bar", x: Object.keys(s.by_month), y: Object.values(s.by_month) }], { title: "By month", width: 400, height: 300 });
  $("recent").innerHTML = s.recent.map(r => `<li>${r.description}: ₹${r.amount} (${r.category})</li>`).join("");
  $("goals").innerHTML = (await call("/goals")).map(g =>
    `<p>${g.name}: ₹${g.saved} / ₹${g.target} (${Math.round(100 * g.saved / g.target)}%) <button onclick="fund(${g.id})">+ Add money</button></p>`).join("");
      if (b && b.savings < b.plan.savings) notify("Savings are below the 20% target.");
}

$("add").onclick = async () => {
  const r = await call("/expenses", { description: $("desc").value, amount: $("amt").value });
  $("alerts").innerHTML = r.alert ? `<div class="alert">⚠ ${r.alert}</div>` : "";
  $("desc").value = $("amt").value = "";
 r.alert && notify(r.alert);
  load();
  
};
$("gadd").onclick = async () => { await call("/goals", { name: $("gname").value, target: $("gtarget").value }); load(); };
window.fund = async id => { const a = prompt("Amount to add (₹)"); if (a) { await call(`/goals/${id}/add`, { amount: a }); load(); } };
$("refresh").onclick = load;
load();
const notify = msg => Notification.permission === "granted" && new Notification("Financial alert", { body: msg });
Notification.requestPermission();
const show = msg => $("status").textContent = msg;
window.fixCat = async (id, category) => { await call(`/expenses/${id}/category`, { category }); load(); };
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