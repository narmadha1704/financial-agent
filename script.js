const API_URL = "http://127.0.0.1:8000/chat";
const $ = id => document.getElementById(id);
const history = [];

const addMsg = (text, who) => {
  const div = Object.assign(document.createElement("div"), { className: `msg ${who}`, textContent: text });
  $("messages").append(div);
  $("messages").scrollTop = $("messages").scrollHeight;
  return div;
};

addMsg("Hi! I'm your financial planning assistant. How can I help?", "bot");

$("form").onsubmit = async e => {
  e.preventDefault();
  const message = $("input").value.trim();
  if (!message) return;
  addMsg(message, "user");
  $("input").value = "";
  const loading = addMsg("Thinking", "bot");
  loading.classList.add("typing");
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history, income: $("income").value }),
    });
    const { reply, intent } = await res.json();
    loading.innerHTML = marked.parse(reply) + (intent ? `<small>Topic: ${intent}</small>` : "");
    history.push({ role: "user", text: message }, { role: "model", text: reply });
  } catch {
    loading.textContent = "(Demo mode: backend not connected yet) You asked: " + message;
  } finally {
    loading.classList.remove("typing");
  }
};

$("clear").onclick = () => {
  history.length = 0;
  $("messages").innerHTML = "";
  addMsg("Chat cleared. How can I help?", "bot");
};

let chart;
$("draw").onclick = () => {
  const [income, needs, wants] = ["income", "needs", "wants"].map(id => +$(id).value || 0);
  chart?.destroy();
  chart = new Chart($("chart"), {
    type: "doughnut",
    data: { labels: ["Needs", "Wants", "Savings"],
      datasets: [{ data: [needs, wants, Math.max(income - needs - wants, 0)], backgroundColor: ["#1a73e8", "#fbbc04", "#34a853"] }] },
  });
};

$("ask").onclick = () => {
  $("input").value = `My income is ₹${$("income").value}, needs ₹${$("needs").value}, wants ₹${$("wants").value}. How can I improve my budget?`;
  $("form").requestSubmit();
};

$("grow").onclick = async () => {
  const box = $("growth");
  if (!$("sip").value) return box.textContent = "Enter your monthly savings first.";
  if (typeof Plotly === "undefined") return box.textContent = "Plotly did not load. Check the script line in index.html.";
  const [monthly, rate, years] = ["sip", "rate", "years"].map(id => $(id).value);
  box.textContent = "Loading...";
  try {
    const r = await fetch(`http://127.0.0.1:8000/projection?monthly=${monthly}&rate=${rate}&years=${years}`);
    if (!r.ok) throw new Error(`Server error ${r.status}`);
    const d = await r.json();
    box.textContent = "";
    Plotly.newPlot("growth", [
      { x: d.years, y: d.invested, name: "Invested" },
      { x: d.years, y: d.value, name: "Value" },
    ], { margin: { t: 10, l: 55, r: 10, b: 40 }, xaxis: { title: "Years" }, yaxis: { title: "₹" },
         legend: { orientation: "h" }, width: 250, height: 260 });
  } catch (e) { box.textContent = `Could not load the chart: ${e.message}. Is the server running?`; }
};