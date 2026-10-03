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
  const loading = addMsg("Thinking...", "bot");
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });
    const { reply } = await res.json();
    loading.innerHTML = marked.parse(reply);
    history.push({ role: "user", text: message }, { role: "model", text: reply });
  } catch {
    loading.textContent = "(Demo mode: backend not connected yet) You asked: " + message;
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