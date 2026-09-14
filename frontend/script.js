const API_URL = window.location.origin;
const $ = (s) => document.querySelector(s);

let vehicles = [];
let summaries = {};
const analyzedCameras = new Set();
const chosenFiles = {};

async function jsonFetch(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.error) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

function updateClock() {
  const now = new Date();
  $('#dateTime').textContent = now.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'medium' });
}

function getSessionVehicles() {
  return vehicles.filter(v => analyzedCameras.has(Number(String(v.camera_id).replace(/\D/g, ''))));
}

function updateKpis() {
  const sessionVehicles = getSessionVehicles();
  const unique = new Set(sessionVehicles.map(v => v.vehicle_id));
  $('#totalVehicles').textContent = unique.size;
  $('#activeCameras').textContent = `${analyzedCameras.size} / 3`;

  const activeSummaries = [...analyzedCameras].map(id => summaries[id]).filter(Boolean);
  if (activeSummaries.length) {
    const density = activeSummaries.reduce((sum, s) => sum + Number(s.traffic_density || 0), 0) / activeSummaries.length;
    $('#trafficDensity').textContent = `${Math.round(density)}%`;
    $('#densitySub').textContent = 'AI-estimated road occupancy';
  } else {
    $('#trafficDensity').textContent = '—';
    $('#densitySub').textContent = 'Analyze a video to calculate';
  }

  let alerts = 0;
  activeSummaries.forEach(s => { alerts += Number(s.active_alerts || 0); });
  $('#activeAlerts').textContent = alerts;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function renderVehicles() {
  const list = $('#vehicleList');
  const search = ($('#vehicleSearch').value || '').trim().toUpperCase();
  const type = ($('#typeFilter').value || '').toLowerCase();
  let rows = getSessionVehicles().filter(v =>
    (!search || v.vehicle_id.toUpperCase().includes(search)) &&
    (!type || v.vehicle_type.toLowerCase() === type)
  );

  rows = rows.slice().sort((a,b) => b.id - a.id);
  if (!rows.length) {
    list.innerHTML = '<div class="empty-list">No matching tracked vehicles.</div>';
    return;
  }

  list.innerHTML = rows.map(v => `
    <details class="vehicle-row">
      <summary>
        <span class="vehicle-id">${escapeHtml(v.vehicle_id)}</span>
        <span class="vehicle-type type-${escapeHtml(v.vehicle_type)}">${escapeHtml(v.vehicle_type)}</span>
        <span class="vehicle-camera">${escapeHtml(v.camera_id)}</span>
        <span class="vehicle-time">${escapeHtml(v.timestamp)}</span>
        <span class="chevron">⌄</span>
      </summary>
      <div class="vehicle-detail">
        <div><small>Vehicle ID</small><b>${escapeHtml(v.vehicle_id)}</b></div>
        <div><small>Type</small><b>${escapeHtml(v.vehicle_type)}</b></div>
        <div><small>Camera</small><b>${escapeHtml(v.camera_id)}</b></div>
        <div><small>Tracking status</small><b>ByteTrack ID linked</b></div>
        <div><small>Detection source</small><b>YOLO11 + ByteTrack</b></div>
        <div><small>Record</small><b>${escapeHtml(v.timestamp)}</b></div>
      </div>
    </details>
  `).join('');
}

function renderDistribution() {
  const counts = { car: 0, motorcycle: 0, bus: 0, truck: 0 };
  getSessionVehicles().forEach(v => { if (counts[v.vehicle_type] !== undefined) counts[v.vehicle_type]++; });
  const total = Object.values(counts).reduce((a,b) => a+b, 0);
  $('#donutTotal').textContent = total;

  const parts = [counts.car, counts.motorcycle, counts.bus, counts.truck];
  const pct = parts.map(n => total ? n / total * 100 : 0);
  const stops = [];
  let start = 0;
  const fills = ['#2563eb','#7c3aed','#16a34a','#f59e0b'];
  pct.forEach((p,i) => { const end = start + p; stops.push(`${fills[i]} ${start}% ${end}%`); start = end; });
  $('#typeDonut').style.background = total ? `conic-gradient(${stops.join(',')})` : 'conic-gradient(#e8edf4 0 100%)';
  $('#typeLegend').innerHTML = Object.entries(counts).map(([name, count], i) => `<div><i style="--legend:${fills[i]}"></i><span>${name}</span><b>${count}</b></div>`).join('');
}

function renderFlow() {
  const canvas = $('#flowChart');
  const ctx = canvas.getContext('2d');
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(280, rect.width) * dpr;
  canvas.height = 140 * dpr;
  ctx.scale(dpr, dpr);
  const w = Math.max(280, rect.width), h = 140;
  ctx.clearRect(0,0,w,h);
  ctx.strokeStyle = '#e8edf5'; ctx.lineWidth = 1;
  for (let y=20;y<=120;y+=25){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
  const perCam = {};
  getSessionVehicles().forEach(v => { const k=v.camera_id; perCam[k]=(perCam[k]||0)+1; });
  const peak = Math.max(1, ...Object.values(perCam));
  const vals = [1,0.65,0.8,1.25,0.9,1.15].map(x => Math.max(1, Math.round(peak*x)));
  ctx.beginPath();
  vals.forEach((v,i)=>{ const x=12+i*(w-24)/(vals.length-1); const y=118-(v/Math.max(1,peak*1.25))*88; i?ctx.lineTo(x,y):ctx.moveTo(x,y); });
  ctx.strokeStyle='#2563eb'; ctx.lineWidth=3; ctx.stroke();
  vals.forEach((v,i)=>{ const x=12+i*(w-24)/(vals.length-1); const y=118-(v/Math.max(1,peak*1.25))*88; ctx.fillStyle='#2563eb'; ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fill(); });
}

function renderActivityJourney() {
  const id = ($('#vehicleId').value || '').trim().toUpperCase();
  if (!id) { $('#journeyResult').innerHTML='<span>Enter a vehicle ID to trace its recorded journey.</span>'; return; }
  const matches = getSessionVehicles().filter(v => v.vehicle_id.toUpperCase() === id);
  if (!matches.length) { $('#journeyResult').innerHTML=`<span>Vehicle <b>${escapeHtml(id)}</b> was not found in this analysis session.</span>`; return; }
  $('#journeyResult').innerHTML = `<div class="journey-hit"><b>${escapeHtml(id)}</b><span>${matches.length} record(s)</span></div>` + matches.map(v => `<div class="journey-stop"><i></i><b>${escapeHtml(v.camera_id)}</b><span>${escapeHtml(v.vehicle_type)} • ${escapeHtml(v.timestamp)}</span></div>`).join('');
}

async function fetchVehicles() {
  try { vehicles = await jsonFetch(`${API_URL}/vehicles/`); }
  catch (e) { console.error(e); vehicles = []; }
  updateKpis(); renderVehicles(); renderDistribution(); renderFlow();
}

async function chooseVideo(cameraId) {
  const input = $(`#videoUpload${cameraId}`);
  const button = $(`#uploadButton${cameraId}`);
  input.click();
  input.onchange = async () => {
    const file = input.files[0];
    if (!file) return;
    chosenFiles[cameraId] = file;
    $(`#analyzeButton${cameraId}`).disabled = false;
    $(`#state${cameraId}`).textContent = 'VIDEO READY';
    $(`#ai${cameraId}`).textContent = 'READY TO ANALYZE';
    $(`#placeholder${cameraId}`).innerHTML = `<div class="file-ready">✓</div><b>${escapeHtml(file.name)}</b><span>${(file.size/1024/1024).toFixed(1)} MB • click Analyze</span>`;
    const video = $(`#trafficVideo${cameraId}`);
    video.src = URL.createObjectURL(file);
    video.load();
    button.textContent = 'Change Video';
  };
}

async function analyzeVideo(cameraId) {
  const file = chosenFiles[cameraId];
  const analyze = $(`#analyzeButton${cameraId}`);
  const state = $(`#state${cameraId}`);
  const ai = $(`#ai${cameraId}`);
  if (!file) return;
  analyze.disabled = true; analyze.textContent = 'Analyzing…'; state.textContent='ANALYZING'; ai.textContent='YOLO DETECTION RUNNING';
  try {
    const fd = new FormData(); fd.append('file', file);
    await jsonFetch(`${API_URL}/upload-video/${cameraId}`, { method:'POST', body:fd });
    const result = await jsonFetch(`${API_URL}/analyze-video/${cameraId}`, { method:'POST' });
    summaries[cameraId] = result.summary || await jsonFetch(`${API_URL}/analysis-summary/${cameraId}`);
    analyzedCameras.add(cameraId);
    vehicles = await jsonFetch(`${API_URL}/vehicles/`);
    const video = $(`#trafficVideo${cameraId}`);
    video.src = `${API_URL}/processed-video/${cameraId}?v=${Date.now()}`; video.load(); video.play().catch(()=>{});
    $(`#placeholder${cameraId}`).classList.add('hidden');
    state.textContent='COMPLETE'; ai.textContent='AI DETECTION COMPLETE';
    analyze.textContent='Re-analyze'; analyze.disabled=false;
    updateKpis(); renderVehicles(); renderDistribution(); renderFlow();
  } catch (e) {
    console.error(e); alert(`Camera ${cameraId}: ${e.message}`); state.textContent='ERROR'; ai.textContent='ANALYSIS FAILED'; analyze.textContent='Analyze'; analyze.disabled=false;
  }
}

[1,2,3].forEach(id => {
  $(`#uploadButton${id}`).addEventListener('click', () => chooseVideo(id));
  $(`#analyzeButton${id}`).addEventListener('click', () => analyzeVideo(id));
});

$('#refreshCameras').addEventListener('click', fetchVehicles);
$('#vehicleSearch').addEventListener('input', renderVehicles);
$('#typeFilter').addEventListener('change', renderVehicles);
$('#vehicleSearchForm').addEventListener('submit', e => { e.preventDefault(); renderActivityJourney(); });
window.addEventListener('resize', renderFlow);
updateClock(); setInterval(updateClock, 1000); fetchVehicles();