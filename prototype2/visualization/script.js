// --- Type Definitions (for clarity, not strict enforcement in JS) ---
// type Vehicle = { id: string; position: [number, number]; };
// type BaseStation = { id: string; position: [number, number]; };
// type Building = { id: string; position: [number, number]; size: [number, number]; };
// type PathLoss = { source: string; target: string; value: number; };
// type VisualizationStep = {
//   time: number;
//   world_size: [number, number];
//   vehicles: Vehicle[];
//   base_stations: BaseStation[];
//   buildings: Building[];
//   path_losses: PathLoss[];
// };

// --- Canvas and Control Elements ---
const canvas = document.getElementById('simulationCanvas') as HTMLCanvasElement;
const ctx = canvas.getContext('2d')!;
const playPauseBtn = document.getElementById('playPauseBtn') as HTMLButtonElement;
const timeSlider = document.getElementById('timeSlider') as HTMLInputElement;
const timeLabel = document.getElementById('timeLabel') as HTMLSpanElement;

let visualizationData = [];
let currentStep = 0;
let isPlaying = false;
let animationFrameId;

// --- Configuration ---
const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 800;
canvas.width = CANVAS_WIDTH;
canvas.height = CANVAS_HEIGHT;

const PADDING = 50; // Padding around the simulation area
let scaleX = 1;
let scaleY = 1;
let offsetX = 0;
let offsetY = 0;

// --- Drawing Functions ---
function draw(stepData) {
    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Calculate scaling and offset based on world_size
    const worldWidth = stepData.world_size[0];
    const worldHeight = stepData.world_size[1];

    scaleX = (CANVAS_WIDTH - 2 * PADDING) / worldWidth;
    scaleY = (CANVAS_HEIGHT - 2 * PADDING) / worldHeight;
    
    // Use the smaller scale to maintain aspect ratio and fit within canvas
    const scale = Math.min(scaleX, scaleY);

    // Center the simulation in the canvas
    offsetX = PADDING + (CANVAS_WIDTH - 2 * PADDING - worldWidth * scale) / 2;
    offsetY = PADDING + (CANVAS_HEIGHT - 2 * PADDING - worldHeight * scale) / 2;

    // Draw background grid (optional, for context)
    ctx.strokeStyle = '#EEE';
    ctx.lineWidth = 0.5;
    for (let x = 0; x <= worldWidth; x += 20) {
        ctx.beginPath();
        ctx.moveTo(offsetX + x * scale, offsetY);
        ctx.lineTo(offsetX + x * scale, offsetY + worldHeight * scale);
        ctx.stroke();
    }
    for (let y = 0; y <= worldHeight; y += 20) {
        ctx.beginPath();
        ctx.moveTo(offsetX, offsetY + y * scale);
        ctx.lineTo(offsetX + worldWidth * scale, offsetY + y * scale);
        ctx.stroke();
    }

    // Draw Buildings
    stepData.buildings.forEach(b => {
        ctx.fillStyle = '#8B4513'; // SaddleBrown
        const x = offsetX + b.position[0] * scale;
        const y = offsetY + b.position[1] * scale;
        const width = b.size[0] * scale;
        const height = b.size[1] * scale;
        ctx.fillRect(x, y, width, height);
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, width, height);
        ctx.fillStyle = 'white';
        ctx.fillText(b.id, x + 5, y + 15);
    });

    // Draw Base Stations
    stepData.base_stations.forEach(bs => {
        ctx.fillStyle = 'red';
        const x = offsetX + bs.position[0] * scale;
        const y = offsetY + bs.position[1] * scale;
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillStyle = 'white';
        ctx.fillText(bs.id, x - 8, y + 4);
    });

    // Draw Vehicles
    stepData.vehicles.forEach(v => {
        ctx.fillStyle = 'blue';
        const x = offsetX + v.position[0] * scale;
        const y = offsetY + v.position[1] * scale;
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillStyle = 'white';
        ctx.fillText(v.id, x - 5, y + 4);
    });

    // Draw Path Loss Links
    stepData.path_losses.forEach(pl => {
        const vehicle = stepData.vehicles.find(v => v.id === pl.source);
        const baseStation = stepData.base_stations.find(bs => bs.id === pl.target);

        if (vehicle && baseStation) {
            ctx.beginPath();
            ctx.moveTo(offsetX + vehicle.position[0] * scale, offsetY + vehicle.position[1] * scale);
            ctx.lineTo(offsetX + baseStation.position[0] * scale, offsetY + baseStation.position[1] * scale);
            
            // Color based on path loss (example: green for low, red for high)
            // Normalize path loss to a 0-1 range for color interpolation
            const minPL = 70; // Example min path loss
            const maxPL = 100; // Example max path loss
            const normalizedPL = Math.max(0, Math.min(1, (pl.value - minPL) / (maxPL - minPL)));
            
            // Interpolate between green (low PL) and red (high PL)
            const r = Math.floor(255 * normalizedPL);
            const g = Math.floor(255 * (1 - normalizedPL));
            ctx.strokeStyle = `rgb(${r},${g},0)`;
            ctx.lineWidth = 2;
            ctx.stroke();

            // Display path loss value near the link (optional)
            const midX = (offsetX + vehicle.position[0] * scale + offsetX + baseStation.position[0] * scale) / 2;
            const midY = (offsetY + vehicle.position[1] * scale + offsetY + baseStation.position[1] * scale) / 2;
            ctx.fillStyle = 'black';
            ctx.font = '10px Arial';
            ctx.fillText(pl.value.toFixed(1) + 'dB', midX + 5, midY - 5);
        }
    });
}

// --- Animation Loop ---
function gameLoop() {
    if (!isPlaying || currentStep >= visualizationData.length - 1) {
        isPlaying = false;
        playPauseBtn.textContent = 'Play';
        return;
    }
    currentStep++;
    timeSlider.value = String(currentStep);
    const stepData = visualizationData[currentStep];
    timeLabel.textContent = `Time: ${stepData.time}`;
    draw(stepData);
    animationFrameId = requestAnimationFrame(gameLoop);
}

// --- Event Listeners ---
playPauseBtn.addEventListener('click', () => {
    isPlaying = !isPlaying;
    playPauseBtn.textContent = isPlaying ? 'Pause' : 'Play';
    if (isPlaying) {
        if (currentStep >= visualizationData.length - 1) {
            currentStep = 0; // Restart if at the end
        }
        gameLoop();
    }
});

timeSlider.addEventListener('input', () => {
    currentStep = parseInt(timeSlider.value);
    const stepData = visualizationData[currentStep];
    timeLabel.textContent = `Time: ${stepData.time}`;
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
    const response = await fetch('data.json');
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    visualizationData = await response.json();
    timeSlider.max = String(visualizationData.length - 1);
    draw(visualizationData[0]); // Draw initial state
  } catch (error) {
    console.error("Failed to load visualization data:", error);
    document.querySelector('.container').innerHTML = `<p style="color: red;">Failed to load data.json. Make sure you have run prepare_data.py.</p>`;
  }
}

loadData();
