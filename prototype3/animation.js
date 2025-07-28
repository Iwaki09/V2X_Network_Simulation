class VehicleSimulation {
    constructor() {
        this.vehicles = [
            {
                id: 'vehicle1',
                element: document.getElementById('vehicle1'),
                startX: 1200,
                startY: 180,
                targetX: 50,
                targetY: 180,
                currentX: 1200,
                currentY: 180,
                speed: 2,
                direction: -1
            },
            {
                id: 'vehicle2',
                element: document.getElementById('vehicle2'),
                startX: 800,
                startY: 180,
                targetX: 50,
                targetY: 180,
                currentX: 800,
                currentY: 180,
                speed: 2,
                direction: -1
            },
            {
                id: 'vehicle3',
                element: document.getElementById('vehicle3'),
                startX: 50,
                startY: 300,
                targetX: 1200,
                targetY: 300,
                currentX: 50,
                currentY: 300,
                speed: 2,
                direction: 1
            },
            {
                id: 'vehicle4',
                element: document.getElementById('vehicle4'),
                startX: 350,
                startY: 300,
                targetX: 1200,
                targetY: 300,
                currentX: 350,
                currentY: 300,
                speed: 2,
                direction: 1
            }
        ];
        
        this.isRunning = false;
        this.animationId = null;
        
        this.initializeVehicles();
    }
    
    initializeVehicles() {
        this.vehicles.forEach(vehicle => {
            vehicle.element.style.left = vehicle.currentX + 'px';
            vehicle.element.style.top = vehicle.currentY + 'px';
            
            // 上側車線（vehicle1, vehicle2）は左向き、下側車線（vehicle3, vehicle4）は右向き
            if (vehicle.id === 'vehicle1' || vehicle.id === 'vehicle2') {
                vehicle.element.style.transform = 'scaleX(-1)';
            } else {
                vehicle.element.style.transform = 'scaleX(1)';
            }
        });
        
        this.updateStatus('準備完了 - 4台の車両が配置されました');
    }
    
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.updateStatus('シミュレーション実行中...');
        this.animate();
    }
    
    stop() {
        this.isRunning = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.updateStatus('シミュレーション停止');
    }
    
    reset() {
        this.stop();
        
        this.vehicles.forEach(vehicle => {
            vehicle.currentX = vehicle.startX;
            vehicle.currentY = vehicle.startY;
            vehicle.element.style.left = vehicle.currentX + 'px';
            vehicle.element.style.top = vehicle.currentY + 'px';
        });
        
        this.updateStatus('リセット完了');
    }
    
    animate() {
        if (!this.isRunning) return;
        
        this.vehicles.forEach(vehicle => {
            // 上側車線（vehicle1, vehicle2）は左向きに移動
            if (vehicle.id === 'vehicle1' || vehicle.id === 'vehicle2') {
                vehicle.currentX -= vehicle.speed;
                if (vehicle.currentX < vehicle.targetX) {
                    vehicle.currentX = vehicle.startX;
                }
            }
            // 下側車線（vehicle3, vehicle4）は右向きに移動
            else {
                vehicle.currentX += vehicle.speed;
                if (vehicle.currentX > vehicle.targetX) {
                    vehicle.currentX = vehicle.startX;
                }
            }
            
            vehicle.element.style.left = vehicle.currentX + 'px';
        });
        
        this.simulateV2XCommunication();
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    simulateV2XCommunication() {
        const communicationDistance = 200;
        let activeConnections = 0;
        
        for (let i = 0; i < this.vehicles.length; i++) {
            for (let j = i + 1; j < this.vehicles.length; j++) {
                const vehicle1 = this.vehicles[i];
                const vehicle2 = this.vehicles[j];
                
                const distance = Math.sqrt(
                    Math.pow(vehicle1.currentX - vehicle2.currentX, 2) +
                    Math.pow(vehicle1.currentY - vehicle2.currentY, 2)
                );
                
                if (distance < communicationDistance) {
                    activeConnections++;
                    this.showCommunicationEffect(vehicle1, vehicle2);
                }
            }
        }
        
        this.updateCommunicationStatus(activeConnections);
    }
    
    showCommunicationEffect(vehicle1, vehicle2) {
        const existingLine = document.querySelector(`#line-${vehicle1.id}-${vehicle2.id}`);
        if (existingLine) {
            existingLine.remove();
        }
        
        const container = document.querySelector('.canvas-container');
        const line = document.createElement('div');
        line.id = `line-${vehicle1.id}-${vehicle2.id}`;
        line.style.position = 'absolute';
        line.style.height = '2px';
        line.style.backgroundColor = '#00ff00';
        line.style.opacity = '0.7';
        line.style.zIndex = '3';
        line.style.pointerEvents = 'none';
        
        const deltaX = vehicle2.currentX - vehicle1.currentX;
        const deltaY = vehicle2.currentY - vehicle1.currentY;
        const length = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
        
        line.style.width = length + 'px';
        line.style.left = (vehicle1.currentX + 40) + 'px';
        line.style.top = (vehicle1.currentY + 20) + 'px';
        line.style.transform = `rotate(${angle}deg)`;
        line.style.transformOrigin = '0 0';
        
        container.appendChild(line);
        
        setTimeout(() => {
            if (line.parentNode) {
                line.remove();
            }
        }, 100);
    }
    
    updateCommunicationStatus(connections) {
        const now = new Date().toLocaleTimeString();
        this.updateStatus(`実行中 - V2X通信: ${connections}接続 (${now})`);
    }
    
    updateStatus(message) {
        const statusElement = document.getElementById('status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }
}

let simulation;

function startAnimation() {
    if (!simulation) {
        simulation = new VehicleSimulation();
    }
    simulation.start();
}

function stopAnimation() {
    if (simulation) {
        simulation.stop();
    }
}

function resetAnimation() {
    if (simulation) {
        simulation.reset();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    simulation = new VehicleSimulation();
});