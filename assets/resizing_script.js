if (!window.dash_clientside) {
  window.dash_clientside = {};
}
window.dash_clientside.clientside = {
  resize: function(value) {
    console.log("resizing..."); // for testing
    setTimeout(function() {
      window.dispatchEvent(new Event("resize"));
      console.log("fired resize");
    }, 500);
    return null;
  }
};


window.addEventListener("beforeunload", function (e) {
    // You can send a request to save data via fetch or XMLHttpRequest
    navigator.sendBeacon("/save-on-refresh", JSON.stringify({ data: "Save this data" }));
});


// function waitForElement(id, callback, retries = 10, delay = 300) {
//     const el = document.getElementById(id);
//     if (el) {
//         callback(el);
//     } else if (retries > 0) {
//         setTimeout(() => waitForElement(id, callback, retries - 1, delay), delay);
//     } else {
//         console.error(`Element with id '${id}' not found after multiple attempts.`);
//     }
// }
//
// window.onload = function () {
//     waitForElement("start-btn", function (btn) {
//         btn.onclick = function () {
//             if (typeof introJs === "function") {
//                 introJs().start();
//             } else {
//                 console.error("Intro.js is not loaded.");
//             }
//         };
//     });
// };
