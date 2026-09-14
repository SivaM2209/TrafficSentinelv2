const API_URL = window.location.origin;

const $ = (selector) => document.querySelector(selector);

let vehicles = [];

/* =========================
   FETCH VEHICLES FROM BACKEND
   ========================= */

async function fetchVehicles() {
  try {
    const response = await fetch(`${API_URL}/vehicles/`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    vehicles = await response.json();

    console.log("Vehicles received from backend:", vehicles);

    updateDashboard();
    renderActivity();

  } catch (error) {
    console.error("Backend connection failed:", error);

    $("#activityBody").innerHTML = `
      <tr>
        <td colspan="5" style="color:#ff5f6d;">
          Cannot connect to FastAPI backend.
          Make sure Uvicorn is running on http://127.0.0.1:8000
        </td>
      </tr>
    `;
  }
}


/* =========================
   DASHBOARD STATISTICS
   ========================= */

function updateDashboard() {
  const uniqueVehicles = new Set(
    vehicles.map(vehicle => vehicle.vehicle_id)
  );

  $("#totalVehicles").textContent = uniqueVehicles.size;

  $("#activeCameras").textContent = "03 / 03";

  if (uniqueVehicles.size === 0) {
    $("#trafficDensity").textContent = "0%";
  } else {
    const density = Math.min(uniqueVehicles.size * 10, 100);
    $("#trafficDensity").textContent = `${density}%`;
  }

  $("#activeAlerts").textContent = "00";
}


/* =========================
   CAMERA
   ========================= */

function renderActivity() {

  if (vehicles.length === 0) {
    $("#activityBody").innerHTML = `
      <tr>
        <td colspan="5">No vehicles detected.</td>
      </tr>
    `;
    return;
  }

  $("#activityBody").innerHTML = vehicles.map(vehicle => `
    <tr>

      <td>${vehicle.vehicle_id}</td>

      <td>${vehicle.camera_id}</td>

      <td>${vehicle.timestamp}</td>

      <td>${vehicle.vehicle_type}</td>

      <td>
        <span class="status detected">
          Detected
        </span>
      </td>

    </tr>
  `).join("");

  $("#lastUpdated").textContent = "just now";
}


/* =========================
   VEHICLE SEARCH
   ========================= */

function showJourney(vehicleId) {

  const normalized = vehicleId.trim().toUpperCase();

  if (!normalized) {
    $("#journeyResult").innerHTML = `
      <div class="empty-state">
        <div class="search-icon">×</div>
        <strong>Enter a vehicle ID</strong>
        <span>Example: V-1001</span>
      </div>
    `;
    return;
  }

  const matches = vehicles.filter(
    vehicle =>
      vehicle.vehicle_id.toUpperCase() === normalized
  );

  if (matches.length === 0) {

    $("#journeyResult").innerHTML = `
      <div class="empty-state">
        <div class="search-icon">×</div>

        <strong>
          Vehicle ${normalized} not found
        </strong>

        <span>
          Try V-1001, V-1002 or V-1003
        </span>

      </div>
    `;

    return;
  }

  $("#journeyResult").innerHTML = `
    <div class="journey-head">

      <strong>${normalized}</strong>

      <span>
        ${matches.length} checkpoint(s)
      </span>

    </div>

    <div class="journey-track">

      ${matches.map(vehicle => `
        <div class="stop">

          <i></i>

          <b>${vehicle.camera_id}</b>

          <small>${vehicle.timestamp}</small>

        </div>
      `).join("")}

    </div>
  `;
}


/* =========================
   CLOCK
   ========================= */

function updateClock() {

  const now = new Date();

  $("#clock").textContent =
    now.toLocaleTimeString("en-IN", {
      hour12: false
    });
}


/* =========================
   BUTTONS
   ========================= */

$("#vehicleSearchForm").addEventListener(
  "submit",
  (event) => {

    event.preventDefault();

    showJourney(
      $("#vehicleId").value
    );

  }
);


$("#refreshCameras").addEventListener(
  "click",
  fetchVehicles
);


$("#refreshActivity").addEventListener(
  "click",
  fetchVehicles
);
/* =========================
   VIDEO UPLOAD
   ========================= */

async function uploadVideo(cameraId) {

  const fileInput = $(`#videoUpload${cameraId}`);
  const uploadButton = $(`#uploadButton${cameraId}`);

  const file = fileInput.files[0];

  if (!file) {
    return;
  }

  const formData = new FormData();

  formData.append(
    "file",
    file
  );

  uploadButton.disabled = true;
  uploadButton.textContent = "Uploading...";

  try {

    const response = await fetch(
      `${API_URL}/upload-video/${cameraId}`,
      {
        method: "POST",
        body: formData
      }
    );

    const result = await response.json();

    if (!response.ok || result.error) {
      throw new Error(
        result.error || "Upload failed."
      );
    }

    alert(
      `Camera ${cameraId}: Video uploaded successfully!`
    );
    const video = $(`#trafficVideo${cameraId}`);

video.src = `${API_URL}/processed-video/${cameraId}`;

video.load();

video.play().catch(error => {
  console.log(
    "Autoplay prevented:",
    error
  );
});

    console.log(
      "Upload result:",
      result
    );

  } catch (error) {

    console.error(
      "Video upload failed:",
      error
    );

    alert(
      `Camera ${cameraId}: Upload failed.`
    );

  } finally {

    uploadButton.disabled = false;
    uploadButton.textContent = "Upload Video";

  }
}


/* Upload buttons open file picker */

$("#uploadButton1").addEventListener(
  "click",
  () => {
    $("#videoUpload1").click();
  }
);

$("#uploadButton2").addEventListener(
  "click",
  () => {
    $("#videoUpload2").click();
  }
);

$("#uploadButton3").addEventListener(
  "click",
  () => {
    $("#videoUpload3").click();
  }
);


/* Automatically upload selected video */

$("#videoUpload1").addEventListener(
  "change",
  () => uploadVideo(1)
);

$("#videoUpload2").addEventListener(
  "change",
  () => uploadVideo(2)
);

$("#videoUpload3").addEventListener(
  "change",
  () => uploadVideo(3)
);


/* =========================
   START APPLICATION
   ========================= */

updateClock();

setInterval(
  updateClock,
  1000
);

fetchVehicles();