document.addEventListener("DOMContentLoaded", function () {
  var calendarEl = document.getElementById("calendar");
  var modal = document.getElementById("sessionModal");
  var closeBtn = document.getElementById("closeModal");
  var modalContent = document.getElementById("modalContent");

  // Fetch events from API
  fetch("/api/sessions")
    .then((response) => response.json())
    .then((events) => {
      var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: "timeGridWeek",
        events: events,
        eventClick: function (info) {
          // Build modal HTML
          let activities = info.event.extendedProps.activities;
          let html = `<h3>${info.event.title}</h3>`;
          if (activities && activities.length) {
            html += "<ul>";
            activities.forEach((a) => {
              html += `<li><b>${a.name}</b>: ${a.detail} (${a.duration} min)</li>`;
            });
            html += "</ul>";
          } else {
            html += "<p>No activities recorded.</p>";
          }
          modalContent.innerHTML = html;
          modal.style.display = "flex";
        },
      });
      calendar.render();
    });

  // Close modal when X clicked or backdrop clicked
  closeBtn.onclick = function () {
    modal.style.display = "none";
  };
  modal.onclick = function (e) {
    if (e.target === modal) modal.style.display = "none";
  };
});
