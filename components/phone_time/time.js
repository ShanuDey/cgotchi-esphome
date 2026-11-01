const status = document.getElementById("s");
const z = (n) => String(n).padStart(2, "0");
const d = new Date();
const t =
  d.getFullYear() +
  "-" +
  z(d.getMonth() + 1) +
  "-" +
  z(d.getDate()) +
  " " +
  z(d.getHours()) +
  ":" +
  z(d.getMinutes()) +
  ":" +
  z(d.getSeconds());

fetch("/text/Set%20Time/set?value=" + encodeURIComponent(t), { method: "POST" })
  .then((r) => {
    status.textContent = r.ok ? "Time set: " + t : "Failed (" + r.status + ")";
    if (r.ok)
      setTimeout(() => {
        location.href = "/";
      }, 1200);
  })
  .catch(() => {
    status.textContent = "Could not reach the device";
  });
