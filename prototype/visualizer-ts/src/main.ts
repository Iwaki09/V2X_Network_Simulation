import './style.css';

// --- Type Definitions ---
type Vehicle = { id: number; position: [number, number]; };
type BaseStation = { id: number; position: [number, number]; };
type Assignments = { [key: string]: number };
type SimulationStep = {
  time: number;
  vehicles: Vehicle[];
  base_stations: BaseStation[];
  assignments: Assignments;
};

// --- Main Application ---
const app = document.querySelector<HTMLDivElement>('#app')!;

app.innerHTML = `
  <h1>V2X Simulation Visualizer</h1>
  <canvas id="simulationCanvas" width="1000" height="500"></canvas>
  <div class="controls">
    <button id="playPauseBtn">Play</button>
    <input type="range" id="timeSlider" min="0" value="0" />
    <span id="timeLabel">Time: 0.0s</span>
  </div>
`;

// --- Canvas and Control Elements ---
const canvas = document.getElementById('simulationCanvas') as HTMLCanvasElement;
const ctx = canvas.getContext('2d')!;
const playPauseBtn = document.getElementById('playPauseBtn') as HTMLButtonElement;
const timeSlider = document.getElementById('timeSlider') as HTMLInputElement;
const timeLabel = document.getElementById('timeLabel') as HTMLSpanElement;

let simulationData: SimulationStep[] = [];
let currentStep = 0;
let isPlaying = false;
let animationFrameId: number;

// --- Drawing Functions ---
function draw(stepData: SimulationStep) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#DDD'; // Grid color

  // Draw grid
  for (let x = 0; x < canvas.width; x += 50) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 50) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
  }

  const scale = 0.5; // Scale down simulation coordinates to fit canvas

  // Draw Base Stations
  stepData.base_stations.forEach(bs => {
    ctx.fillStyle = 'red';
    ctx.fillRect(bs.position[0] * scale - 10, bs.position[1] * scale - 10, 20, 20);
    ctx.fillStyle = 'white';
    ctx.fillText(`BS${bs.id}`, bs.position[0] * scale - 8, bs.position[1] * scale + 4);
  });

  // Draw Vehicles
  stepData.vehicles.forEach(v => {
    ctx.fillStyle = 'blue';
    ctx.beginPath();
    ctx.arc(v.position[0] * scale, v.position[1] * scale, 8, 0, 2 * Math.PI);
    ctx.fill();
    ctx.fillStyle = 'white';
    ctx.fillText(`${v.id}`, v.position[0] * scale - 3, v.position[1] * scale + 4);
  });

  // Draw Assignments
  for (const vehicleId in stepData.assignments) {
    const bsId = stepData.assignments[vehicleId];
    const vehicle = stepData.vehicles.find(v => v.id === parseInt(vehicleId));
    const baseStation = stepData.base_stations.find(bs => bs.id === bsId);

    if (vehicle && baseStation) {
      ctx.beginPath();
      ctx.moveTo(vehicle.position[0] * scale, vehicle.position[1] * scale);
      ctx.lineTo(baseStation.position[0] * scale, baseStation.position[1] * scale);
      ctx.strokeStyle = 'lime';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }
}

// --- Animation Loop ---
function gameLoop() {
    if (!isPlaying || currentStep >= simulationData.length - 1) {
        isPlaying = false;
        playPauseBtn.textContent = 'Play';
        return;
    }
    currentStep++;
    timeSlider.value = String(currentStep);
    const stepData = simulationData[currentStep];
    timeLabel.textContent = `Time: ${stepData.time.toFixed(1)}s`;
    draw(stepData);
    animationFrameId = requestAnimationFrame(gameLoop);
}

// --- Event Listeners ---
playPauseBtn.addEventListener('click', () => {
    isPlaying = !isPlaying;
    playPauseBtn.textContent = isPlaying ? 'Pause' : 'Play';
    if (isPlaying) {
        if (currentStep >= simulationData.length - 1) {
            currentStep = 0; // Restart if at the end
        }
        gameLoop();
    }
});

timeSlider.addEventListener('input', () => {
    currentStep = parseInt(timeSlider.value);
    const stepData = simulationData[currentStep];
    timeLabel.textContent = `Time: ${stepData.time.toFixed(1)}s`;
    draw(stepData);
    if (isPlaying) {
        isPlaying = false;
        playPauseBtn.textContent = 'Play';
        cancelAnimationFrame(animationFrameId);
    }
});

// --- Data Loading ---
async function loadData() {
  try {
    const response = await fetch('../simulation_log.json');
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    simulationData = await response.json();
    timeSlider.max = String(simulationData.length - 1);
    draw(simulationData[0]); // Draw initial state
  } catch (error) {
    console.error("Failed to load simulation data:", error);
    app.innerHTML = `<p style="color: red;">Failed to load simulation_log.json. Make sure you have run the python simulation first.</p>`;
  }
}

loadData();