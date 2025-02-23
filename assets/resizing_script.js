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