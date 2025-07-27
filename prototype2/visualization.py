"""
V2X Simulation Visualization Tool
6台の車両シナリオ用
"""

import json
import os
from typing import Dict, Any, List

class V2XVisualizer:
    """V2Xシミュレーション用ビジュアライザー"""
    
    def __init__(self):
        self.world_size = [300, 300]
        
    def convert_results_to_visualization(self, results_file: str, output_file: str = "visualization/data.json"):
        """シミュレーション結果をvisualization形式に変換"""
        
        try:
            # Load simulation results
            with open(results_file, 'r') as f:
                simulation_data = json.load(f)
            
            visualization_data = []
            
            for step_data in simulation_data["simulation_data"]:
                frame = {
                    "time": step_data["time_step"],
                    "world_size": self.world_size,
                    "vehicles": [],
                    "base_stations": [
                        {
                            "id": "bs_1",
                            "position": [80, 80]
                        },
                        {
                            "id": "bs_2", 
                            "position": [220, 180]
                        }
                    ],
                    "buildings": [
                        {
                            "id": "building_1",
                            "position": [150, 120],
                            "size": [60, 40, 25]
                        }
                    ],
                    "path_losses": []
                }
                
                # Add vehicles with current positions
                for vehicle_id, position in step_data["vehicle_positions"].items():
                    frame["vehicles"].append({
                        "id": vehicle_id,
                        "position": [position[0], position[1]]  # x, y only for 2D visualization
                    })
                
                # Add path loss data
                for pair in step_data["path_loss_pairs"]:
                    frame["path_losses"].append({
                        "source": pair["source"],
                        "target": pair["target"],
                        "value": pair["path_loss_db"]
                    })
                
                visualization_data.append(frame)
            
            # Save visualization data
            os.makedirs("visualization", exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(visualization_data, f, indent=2)
            
            print(f"✅ Visualization data saved to {output_file}")
            
            # Print summary statistics
            self._print_visualization_summary(visualization_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to convert results: {e}")
            return False
    
    def _print_visualization_summary(self, data: List[Dict[str, Any]]):
        """ビジュアライゼーションデータのサマリーを表示"""
        if not data:
            return
        
        print(f"\n=== Visualization Data Summary ===")
        print(f"Time steps: {len(data)}")
        print(f"Vehicles: {len(data[0]['vehicles'])}")
        print(f"Base stations: {len(data[0]['base_stations'])}")
        print(f"Buildings: {len(data[0]['buildings'])}")
        
        # Analyze path loss variations
        print(f"\n=== Vehicle Movement Analysis ===")
        for vehicle in data[0]['vehicles']:
            vehicle_id = vehicle['id']
            positions = []
            
            for frame in data:
                for v in frame['vehicles']:
                    if v['id'] == vehicle_id:
                        positions.append(v['position'])
                        break
            
            if len(positions) >= 2:
                start_pos = positions[0]
                end_pos = positions[-1]
                distance_moved = ((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)**0.5
                print(f"{vehicle_id}: [{start_pos[0]:.1f}, {start_pos[1]:.1f}] → [{end_pos[0]:.1f}, {end_pos[1]:.1f}] (moved {distance_moved:.1f}m)")
        
        # Path loss analysis
        print(f"\n=== Path Loss Variation Analysis ===")
        path_loss_stats = {}
        
        for frame in data:
            for loss_data in frame['path_losses']:
                pair_key = f"{loss_data['source']}-{loss_data['target']}"
                if pair_key not in path_loss_stats:
                    path_loss_stats[pair_key] = []
                path_loss_stats[pair_key].append(loss_data['value'])
        
        for pair, losses in path_loss_stats.items():
            if losses:
                min_loss = min(losses)
                max_loss = max(losses)
                variation = max_loss - min_loss
                print(f"{pair}: {min_loss:.1f} - {max_loss:.1f} dB (variation: {variation:.1f} dB)")
    
    def create_html_visualization(self, data_file: str = "visualization/data.json"):
        """HTMLビジュアライゼーションファイルを作成"""
        
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V2X Simulation Visualization</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .controls {
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .time-info {
            margin-bottom: 10px;
            font-weight: bold;
        }
        .simulation-canvas {
            border: 2px solid #333;
            background-color: #e8f4f8;
            cursor: pointer;
        }
        .stats-panel {
            margin-top: 20px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .stats-section {
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
        }
        .path-loss-item {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }
        .high-loss {
            background-color: #ffebee;
            padding: 2px 4px;
            border-radius: 3px;
        }
        .low-loss {
            background-color: #e8f5e8;
            padding: 2px 4px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚗 V2X Network Simulation</h1>
        <div class="time-info" id="timeInfo">Time: 0s | Step: 1/20</div>
        
        <div class="controls">
            <button id="playBtn">▶️ Play</button>
            <button id="pauseBtn">⏸️ Pause</button>
            <button id="resetBtn">🔄 Reset</button>
            <label for="speedSlider">Speed: </label>
            <input type="range" id="speedSlider" min="0.5" max="3" value="1" step="0.1">
            <span id="speedLabel">1.0x</span>
            <button id="toggleViewBtn">📊 Graph View</button>
        </div>
        
        <div id="visualizationContainer">
            <canvas id="simulationCanvas" class="simulation-canvas" width="800" height="600"></canvas>
            <canvas id="networkCanvas" class="simulation-canvas" width="800" height="600" style="display: none;"></canvas>
        </div>
        
        <div class="stats-panel">
            <div class="stats-section">
                <h3>📊 Path Loss Statistics</h3>
                <div id="pathLossStats"></div>
            </div>
            <div class="stats-section">
                <h3>🚗 Vehicle Information</h3>
                <div id="vehicleInfo"></div>
            </div>
        </div>
    </div>

    <script>
        let simulationData = [];
        let currentFrame = 0;
        let isPlaying = false;
        let animationSpeed = 1.0;
        let lastTime = 0;
        let isNetworkView = false;

        const canvas = document.getElementById('simulationCanvas');
        const ctx = canvas.getContext('2d');
        const networkCanvas = document.getElementById('networkCanvas');
        const networkCtx = networkCanvas.getContext('2d');
        const timeInfo = document.getElementById('timeInfo');
        const pathLossStats = document.getElementById('pathLossStats');
        const vehicleInfo = document.getElementById('vehicleInfo');
        
        // Load simulation data
        fetch('data.json')
            .then(response => response.json())
            .then(data => {
                simulationData = data;
                currentFrame = 0;
                drawFrame();
                drawNetworkGraph();
                updateStats();
            })
            .catch(error => {
                console.error('Error loading data:', error);
                // Fallback: show sample frame
                showSampleFrame();
            });

        function showSampleFrame() {
            // Sample data for testing
            simulationData = [{
                time: 0,
                world_size: [300, 300],
                vehicles: [
                    {id: "vehicle_1", position: [50, 50]},
                    {id: "vehicle_2", position: [100, 100]},
                    {id: "vehicle_3", position: [150, 80]},
                    {id: "vehicle_4", position: [200, 150]},
                    {id: "vehicle_5", position: [80, 200]},
                    {id: "vehicle_6", position: [180, 30]}
                ],
                base_stations: [
                    {id: "bs_1", position: [80, 80]},
                    {id: "bs_2", position: [220, 180]}
                ],
                buildings: [
                    {id: "building_1", position: [150, 120], size: [60, 40, 25]}
                ],
                path_losses: []
            }];
            drawFrame();
        }

        function drawFrame() {
            if (simulationData.length === 0) return;
            
            const frame = simulationData[currentFrame];
            const worldSize = frame.world_size || [300, 300];
            
            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Scale factors
            const scaleX = canvas.width / worldSize[0];
            const scaleY = canvas.height / worldSize[1];
            
            // Draw buildings
            ctx.fillStyle = '#8B4513';
            frame.buildings?.forEach(building => {
                const x = building.position[0] * scaleX;
                const y = building.position[1] * scaleY;
                const w = building.size[0] * scaleX;
                const h = building.size[1] * scaleY;
                ctx.fillRect(x - w/2, y - h/2, w, h);
                
                // Building label
                ctx.fillStyle = 'white';
                ctx.font = '12px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(building.id, x, y);
                ctx.fillStyle = '#8B4513';
            });
            
            // Draw base stations
            ctx.fillStyle = '#FF6B6B';
            frame.base_stations?.forEach(bs => {
                const x = bs.position[0] * scaleX;
                const y = bs.position[1] * scaleY;
                
                // Draw tower
                ctx.fillRect(x - 8, y - 8, 16, 16);
                
                // Draw antenna
                ctx.strokeStyle = '#FF6B6B';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(x, y - 8);
                ctx.lineTo(x, y - 25);
                ctx.stroke();
                
                // Label
                ctx.fillStyle = 'black';
                ctx.font = '12px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(bs.id, x, y + 25);
            });
            
            // Draw vehicles
            const colors = ['#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'];
            frame.vehicles?.forEach((vehicle, index) => {
                const x = vehicle.position[0] * scaleX;
                const y = vehicle.position[1] * scaleY;
                
                ctx.fillStyle = colors[index % colors.length];
                ctx.fillRect(x - 6, y - 6, 12, 12);
                
                // Vehicle label
                ctx.fillStyle = 'black';
                ctx.font = '10px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(vehicle.id.replace('vehicle_', 'V'), x, y - 10);
            });
            
            // Update time info
            timeInfo.textContent = `Time: ${frame.time}s | Step: ${currentFrame + 1}/${simulationData.length}`;
        }

        function drawNetworkGraph() {
            if (simulationData.length === 0) return;
            
            const frame = simulationData[currentFrame];
            
            // Clear canvas
            networkCtx.clearRect(0, 0, networkCanvas.width, networkCanvas.height);
            
            // Network layout parameters
            const centerX = networkCanvas.width / 2;
            const centerY = networkCanvas.height / 2;
            const radius = 200;
            
            // Calculate node positions
            const allNodes = [...frame.vehicles, ...frame.base_stations];
            const nodePositions = {};
            
            allNodes.forEach((node, index) => {
                const angle = (2 * Math.PI * index) / allNodes.length;
                nodePositions[node.id] = {
                    x: centerX + radius * Math.cos(angle),
                    y: centerY + radius * Math.sin(angle),
                    type: frame.vehicles.find(v => v.id === node.id) ? 'vehicle' : 'base_station'
                };
            });
            
            // Draw edges (connections with path loss)
            frame.path_losses?.forEach(loss => {
                const source = nodePositions[loss.source];
                const target = nodePositions[loss.target];
                
                if (source && target) {
                    // Color based on path loss value
                    const pathLoss = loss.value;
                    let edgeColor;
                    let lineWidth;
                    
                    if (pathLoss < 80) {
                        edgeColor = '#00ff00'; // Green for good signal
                        lineWidth = 4;
                    } else if (pathLoss < 100) {
                        edgeColor = '#ffaa00'; // Orange for medium signal
                        lineWidth = 3;
                    } else if (pathLoss < 120) {
                        edgeColor = '#ff4444'; // Red for poor signal
                        lineWidth = 2;
                    } else {
                        edgeColor = '#888888'; // Gray for very poor/no signal
                        lineWidth = 1;
                    }
                    
                    // Draw connection line
                    networkCtx.strokeStyle = edgeColor;
                    networkCtx.lineWidth = lineWidth;
                    networkCtx.beginPath();
                    networkCtx.moveTo(source.x, source.y);
                    networkCtx.lineTo(target.x, target.y);
                    networkCtx.stroke();
                    
                    // Draw path loss value on edge
                    const midX = (source.x + target.x) / 2;
                    const midY = (source.y + target.y) / 2;
                    
                    networkCtx.fillStyle = '#000000';
                    networkCtx.font = '12px Arial';
                    networkCtx.textAlign = 'center';
                    networkCtx.fillRect(midX - 20, midY - 8, 40, 16);
                    networkCtx.fillStyle = '#ffffff';
                    networkCtx.fillText(pathLoss.toFixed(1) + 'dB', midX, midY + 4);
                }
            });
            
            // Draw nodes
            Object.entries(nodePositions).forEach(([nodeId, pos]) => {
                // Node circle
                if (pos.type === 'vehicle') {
                    networkCtx.fillStyle = '#4ECDC4';
                    networkCtx.strokeStyle = '#333333';
                } else {
                    networkCtx.fillStyle = '#FF6B6B';
                    networkCtx.strokeStyle = '#333333';
                }
                
                networkCtx.lineWidth = 2;
                networkCtx.beginPath();
                networkCtx.arc(pos.x, pos.y, 25, 0, 2 * Math.PI);
                networkCtx.fill();
                networkCtx.stroke();
                
                // Node label
                networkCtx.fillStyle = '#000000';
                networkCtx.font = 'bold 12px Arial';
                networkCtx.textAlign = 'center';
                networkCtx.fillText(nodeId.replace('vehicle_', 'V').replace('bs_', 'BS'), pos.x, pos.y + 4);
            });
            
            // Legend
            networkCtx.fillStyle = '#000000';
            networkCtx.font = '14px Arial';
            networkCtx.textAlign = 'left';
            networkCtx.fillText('Network Graph Legend:', 20, 30);
            
            // Vehicle legend
            networkCtx.fillStyle = '#4ECDC4';
            networkCtx.beginPath();
            networkCtx.arc(30, 55, 10, 0, 2 * Math.PI);
            networkCtx.fill();
            networkCtx.fillStyle = '#000000';
            networkCtx.fillText('Vehicles', 50, 60);
            
            // Base station legend
            networkCtx.fillStyle = '#FF6B6B';
            networkCtx.beginPath();
            networkCtx.arc(30, 80, 10, 0, 2 * Math.PI);
            networkCtx.fill();
            networkCtx.fillStyle = '#000000';
            networkCtx.fillText('Base Stations', 50, 85);
            
            // Edge legend
            const legendY = 110;
            networkCtx.strokeStyle = '#00ff00';
            networkCtx.lineWidth = 4;
            networkCtx.beginPath();
            networkCtx.moveTo(20, legendY);
            networkCtx.lineTo(40, legendY);
            networkCtx.stroke();
            networkCtx.fillText('Good Signal (<80dB)', 50, legendY + 5);
            
            networkCtx.strokeStyle = '#ffaa00';
            networkCtx.lineWidth = 3;
            networkCtx.beginPath();
            networkCtx.moveTo(20, legendY + 25);
            networkCtx.lineTo(40, legendY + 25);
            networkCtx.stroke();
            networkCtx.fillText('Medium Signal (80-100dB)', 50, legendY + 30);
            
            networkCtx.strokeStyle = '#ff4444';
            networkCtx.lineWidth = 2;
            networkCtx.beginPath();
            networkCtx.moveTo(20, legendY + 50);
            networkCtx.lineTo(40, legendY + 50);
            networkCtx.stroke();
            networkCtx.fillText('Poor Signal (100-120dB)', 50, legendY + 55);
            
            networkCtx.strokeStyle = '#888888';
            networkCtx.lineWidth = 1;
            networkCtx.beginPath();
            networkCtx.moveTo(20, legendY + 75);
            networkCtx.lineTo(40, legendY + 75);
            networkCtx.stroke();
            networkCtx.fillText('Very Poor Signal (>120dB)', 50, legendY + 80);
        }

        function updateStats() {
            if (simulationData.length === 0) return;
            
            const frame = simulationData[currentFrame];
            
            // Update path loss stats
            let pathLossHTML = '';
            frame.path_losses?.forEach(loss => {
                const lossClass = loss.value > 100 ? 'high-loss' : 'low-loss';
                pathLossHTML += `
                    <div class="path-loss-item">
                        <span>${loss.source} → ${loss.target}</span>
                        <span class="${lossClass}">${loss.value.toFixed(1)} dB</span>
                    </div>
                `;
            });
            pathLossStats.innerHTML = pathLossHTML;
            
            // Update vehicle info
            let vehicleHTML = '';
            frame.vehicles?.forEach(vehicle => {
                vehicleHTML += `
                    <div>
                        <strong>${vehicle.id}:</strong> 
                        [${vehicle.position[0].toFixed(1)}, ${vehicle.position[1].toFixed(1)}]
                    </div>
                `;
            });
            vehicleInfo.innerHTML = vehicleHTML;
        }

        function animate(timestamp) {
            if (isPlaying && timestamp - lastTime > (1000 / animationSpeed)) {
                currentFrame = (currentFrame + 1) % simulationData.length;
                drawFrame();
                drawNetworkGraph();
                updateStats();
                lastTime = timestamp;
            }
            requestAnimationFrame(animate);
        }

        // Controls
        document.getElementById('playBtn').onclick = () => {
            isPlaying = true;
            lastTime = performance.now();
        };
        
        document.getElementById('pauseBtn').onclick = () => {
            isPlaying = false;
        };
        
        document.getElementById('resetBtn').onclick = () => {
            currentFrame = 0;
            isPlaying = false;
            drawFrame();
            drawNetworkGraph();
            updateStats();
        };
        
        document.getElementById('toggleViewBtn').onclick = () => {
            isNetworkView = !isNetworkView;
            const simCanvas = document.getElementById('simulationCanvas');
            const netCanvas = document.getElementById('networkCanvas');
            const toggleBtn = document.getElementById('toggleViewBtn');
            
            if (isNetworkView) {
                simCanvas.style.display = 'none';
                netCanvas.style.display = 'block';
                toggleBtn.textContent = '🗺️ Map View';
            } else {
                simCanvas.style.display = 'block';
                netCanvas.style.display = 'none';
                toggleBtn.textContent = '📊 Graph View';
            }
        };
        
        document.getElementById('speedSlider').oninput = (e) => {
            animationSpeed = parseFloat(e.target.value);
            document.getElementById('speedLabel').textContent = `${animationSpeed.toFixed(1)}x`;
        };

        // Start animation loop
        requestAnimationFrame(animate);
    </script>
</body>
</html>"""
        
        try:
            os.makedirs("visualization", exist_ok=True)
            with open("visualization/index.html", 'w') as f:
                f.write(html_content)
            print("✅ HTML visualization created: visualization/index.html")
        except Exception as e:
            print(f"❌ Failed to create HTML visualization: {e}")

def main():
    """メイン関数"""
    visualizer = V2XVisualizer()
    
    # Convert simulation results to visualization format
    success = visualizer.convert_results_to_visualization(
        "output/simulation_results.json",
        "visualization/data.json"
    )
    
    if success:
        # Create HTML visualization
        visualizer.create_html_visualization()
        print("\n✅ V2X visualization ready!")
        print("📁 Open visualization/index.html in your browser to view the simulation")
    else:
        print("\n❌ Failed to create visualization")

if __name__ == "__main__":
    main()