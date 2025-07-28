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
        // 基地局の正確な位置を取得
        const container = document.querySelector('.canvas-container');
        const containerRect = container.getBoundingClientRect();
        const baseStationElement = document.querySelector('.base-station');
        const baseStationRect = baseStationElement.getBoundingClientRect();
        
        const baseStationX = baseStationRect.left - containerRect.left + 30;
        const baseStationY = baseStationRect.top - containerRect.top + 50;
        
        const communicationRange = 500;
        let activeConnections = 0;
        
        // 基地局と車両間の通信（常に表示）
        this.vehicles.forEach(vehicle => {
            const isBlocked = this.isLineBlocked(
                baseStationX, baseStationY,
                vehicle.currentX + 40, vehicle.currentY + 20
            );
            this.updateCommunicationLink(
                baseStationX, baseStationY,
                vehicle.currentX + 40, vehicle.currentY + 20,
                isBlocked, `bs-${vehicle.id}`
            );
            if (!isBlocked) activeConnections++;
        });
        
        // 車両間の通信（常に表示）
        for (let i = 0; i < this.vehicles.length; i++) {
            for (let j = i + 1; j < this.vehicles.length; j++) {
                const vehicle1 = this.vehicles[i];
                const vehicle2 = this.vehicles[j];
                
                const distance = this.calculateDistance(
                    vehicle1.currentX + 40, vehicle1.currentY + 20,
                    vehicle2.currentX + 40, vehicle2.currentY + 20
                );
                
                if (distance < communicationRange) {
                    const isBlocked = this.isLineBlocked(
                        vehicle1.currentX + 40, vehicle1.currentY + 20,
                        vehicle2.currentX + 40, vehicle2.currentY + 20
                    );
                    this.updateCommunicationLink(
                        vehicle1.currentX + 40, vehicle1.currentY + 20,
                        vehicle2.currentX + 40, vehicle2.currentY + 20,
                        isBlocked, `${vehicle1.id}-${vehicle2.id}`
                    );
                    if (!isBlocked) activeConnections++;
                }
            }
        }
        
        this.updateCommunicationStatus(activeConnections);
    }
    
    calculateDistance(x1, y1, x2, y2) {
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    }
    
    isLineBlocked(x1, y1, x2, y2) {
        // 建物の正確な位置を取得
        const container = document.querySelector('.canvas-container');
        const containerRect = container.getBoundingClientRect();
        const buildingElement = document.querySelector('.building');
        const buildingRect = buildingElement.getBoundingClientRect();
        
        const buildingX = buildingRect.left - containerRect.left;
        const buildingY = buildingRect.top - containerRect.top;
        const buildingWidth = buildingRect.width;
        const buildingHeight = buildingRect.height;
        
        // 線分と矩形の交差判定
        return this.lineIntersectsRect(
            x1, y1, x2, y2,
            buildingX, buildingY, buildingWidth, buildingHeight
        );
    }
    
    lineIntersectsRect(x1, y1, x2, y2, rectX, rectY, rectW, rectH) {
        // 線分が矩形と交差するかどうかを判定
        const rectRight = rectX + rectW;
        const rectBottom = rectY + rectH;
        
        // 線分の両端が矩形の同じ側にある場合は交差しない
        if ((x1 < rectX && x2 < rectX) || (x1 > rectRight && x2 > rectRight) ||
            (y1 < rectY && y2 < rectY) || (y1 > rectBottom && y2 > rectBottom)) {
            return false;
        }
        
        // より詳細な交差判定
        return this.lineSegmentIntersectsRectangle(x1, y1, x2, y2, rectX, rectY, rectW, rectH);
    }
    
    lineSegmentIntersectsRectangle(x1, y1, x2, y2, rectX, rectY, rectW, rectH) {
        const rectRight = rectX + rectW;
        const rectBottom = rectY + rectH;
        
        // 矩形の4つの辺との交差をチェック
        return this.lineSegmentsIntersect(x1, y1, x2, y2, rectX, rectY, rectRight, rectY) ||
               this.lineSegmentsIntersect(x1, y1, x2, y2, rectRight, rectY, rectRight, rectBottom) ||
               this.lineSegmentsIntersect(x1, y1, x2, y2, rectRight, rectBottom, rectX, rectBottom) ||
               this.lineSegmentsIntersect(x1, y1, x2, y2, rectX, rectBottom, rectX, rectY);
    }
    
    lineSegmentsIntersect(x1, y1, x2, y2, x3, y3, x4, y4) {
        const denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
        if (denom === 0) return false;
        
        const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
        const u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom;
        
        return t >= 0 && t <= 1 && u >= 0 && u <= 1;
    }
    
    updateCommunicationLink(x1, y1, x2, y2, isBlocked, id) {
        const container = document.querySelector('.canvas-container');
        let line = document.getElementById(`link-${id}`);
        
        if (!line) {
            line = document.createElement('div');
            line.className = 'communication-link';
            line.id = `link-${id}`;
            line.style.position = 'absolute';
            line.style.height = '2px';
            line.style.opacity = '0.8';
            line.style.zIndex = '3';
            line.style.pointerEvents = 'none';
            container.appendChild(line);
        }
        
        line.style.backgroundColor = isBlocked ? '#ff0000' : '#00ff00';
        
        const deltaX = x2 - x1;
        const deltaY = y2 - y1;
        const length = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
        
        line.style.width = length + 'px';
        line.style.left = x1 + 'px';
        line.style.top = y1 + 'px';
        line.style.transform = `rotate(${angle}deg)`;
        line.style.transformOrigin = '0 0';
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