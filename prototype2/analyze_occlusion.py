#!/usr/bin/env python3
"""
Building Occlusion Analysis Tool
"""
import numpy as np
import matplotlib.pyplot as plt
import json

def point_to_line_distance(point, line_start, line_end):
    """点から線分への最短距離を計算"""
    x0, y0 = point
    x1, y1 = line_start  
    x2, y2 = line_end
    
    # 線分の方向ベクトル
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        # 線分が点の場合
        return np.sqrt((x0 - x1)**2 + (y0 - y1)**2)
    
    # パラメータt（0-1で線分上の点を表す）
    t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)))
    
    # 線分上の最近点
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    # 距離を返す
    return np.sqrt((x0 - closest_x)**2 + (y0 - closest_y)**2)

def line_intersects_rectangle(line_start, line_end, rect_center, rect_size):
    """線分が矩形と交差するかを判定"""
    x1, y1 = line_start
    x2, y2 = line_end
    cx, cy = rect_center[:2]  # x, y座標のみ使用
    w, h = rect_size[:2]  # width, heightのみ使用
    
    # 矩形の境界
    left = cx - w/2
    right = cx + w/2
    top = cy - h/2
    bottom = cy + h/2
    
    # 線分が矩形の境界と交差するかをチェック
    # Liang-Barsky clipping algorithm の簡易版
    
    dx = x2 - x1
    dy = y2 - y1
    
    # 線分の方向に応じてチェック
    t_min = 0.0
    t_max = 1.0
    
    # X方向の境界
    if dx != 0:
        t1 = (left - x1) / dx
        t2 = (right - x1) / dx
        if dx < 0:
            t1, t2 = t2, t1
        t_min = max(t_min, t1)
        t_max = min(t_max, t2)
    elif x1 < left or x1 > right:
        return False
    
    # Y方向の境界
    if dy != 0:
        t1 = (top - y1) / dy
        t2 = (bottom - y1) / dy
        if dy < 0:
            t1, t2 = t2, t1
        t_min = max(t_min, t1)
        t_max = min(t_max, t2)
    elif y1 < top or y1 > bottom:
        return False
    
    return t_min <= t_max

def analyze_building_occlusion():
    """建物による遮蔽効果を分析"""
    
    print("=== Building Occlusion Analysis ===")
    print()
    
    # シナリオ設定
    vehicles_config = [
        {"id": "vehicle_1", "pos": [60, 90], "vel": [6, 0]},
        {"id": "vehicle_2", "pos": [180, 160], "vel": [-4, 0]},
        {"id": "vehicle_3", "pos": [110, 60], "vel": [0, 5]},
        {"id": "vehicle_4", "pos": [190, 200], "vel": [0, -4]},
    ]
    
    base_stations = [
        {"id": "bs_1", "pos": [80, 80]},
        {"id": "bs_2", "pos": [220, 180]}
    ]
    
    building = {"pos": [150, 120, 0], "size": [50, 30, 25]}
    
    print(f"Building: center={building['pos'][:2]}, size={building['size'][:2]}")
    print(f"Building boundaries: x=[{building['pos'][0] - building['size'][0]/2}, {building['pos'][0] + building['size'][0]/2}], y=[{building['pos'][1] - building['size'][1]/2}, {building['pos'][1] + building['size'][1]/2}]")
    print()
    
    occlusion_events = []
    
    # 各時刻での遮蔽チェック
    for step in range(0, 20, 5):  # 5ステップごとに確認
        time = step * 1.0
        print(f"Time Step {step} (t={time}s):")
        
        # 車両位置を計算
        vehicle_positions = {}
        for v_config in vehicles_config:
            x = v_config["pos"][0] + v_config["vel"][0] * time
            y = v_config["pos"][1] + v_config["vel"][1] * time
            x = max(10, min(290, x))
            y = max(10, min(290, y))
            vehicle_positions[v_config["id"]] = [x, y]
        
        # 各車両-基地局ペアの遮蔽をチェック
        for v_id, v_pos in vehicle_positions.items():
            for bs in base_stations:
                bs_pos = bs["pos"]
                
                # 車両-基地局間の直線が建物と交差するかチェック
                is_occluded = line_intersects_rectangle(
                    v_pos, bs_pos, building["pos"], building["size"]
                )
                
                # 距離計算
                distance = np.sqrt((v_pos[0] - bs_pos[0])**2 + (v_pos[1] - bs_pos[1])**2)
                
                status = "🚫 OCCLUDED" if is_occluded else "✅ Clear"
                print(f"  {v_id} [{v_pos[0]:.1f}, {v_pos[1]:.1f}] -> {bs['id']} [{bs_pos[0]}, {bs_pos[1]}]: {distance:.1f}m {status}")
                
                if is_occluded:
                    occlusion_events.append({
                        "time": time,
                        "vehicle": v_id,
                        "base_station": bs["id"],
                        "distance": distance,
                        "vehicle_pos": v_pos,
                        "bs_pos": bs_pos
                    })
        
        print()
    
    # 遮蔽イベントの要約
    print("=== Occlusion Events Summary ===")
    if occlusion_events:
        for event in occlusion_events:
            print(f"t={event['time']:.1f}s: {event['vehicle']} -> {event['base_station']} (occluded, {event['distance']:.1f}m)")
    else:
        print("⚠️  No occlusion events detected!")
        print("This suggests building occlusion may not be properly implemented in the simulation.")
    
    print()
    
    # 理論的な遮蔽パスロス増加を計算
    print("=== Expected Occlusion Path Loss Impact ===")
    print("Building material: concrete")
    print("Expected additional path loss: 10-20 dB")
    print("Non-occluded vs occluded links should show significant difference")
    
    return occlusion_events

def create_visualization():
    """遮蔽状況の可視化"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # 建物
    building_pos = [150, 120]
    building_size = [50, 30]
    rect = plt.Rectangle(
        (building_pos[0] - building_size[0]/2, building_pos[1] - building_size[1]/2),
        building_size[0], building_size[1],
        facecolor='brown', alpha=0.7, label='Building'
    )
    ax.add_patch(rect)
    
    # 基地局
    bs_positions = [[80, 80], [220, 180]]
    for i, pos in enumerate(bs_positions):
        ax.plot(pos[0], pos[1], 'rs', markersize=12, label=f'BS_{i+1}' if i == 0 else "")
    
    # 車両軌道を描画
    vehicles_config = [
        {"id": "vehicle_1", "pos": [60, 90], "vel": [6, 0], "color": "blue"},
        {"id": "vehicle_2", "pos": [180, 160], "vel": [-4, 0], "color": "green"},
        {"id": "vehicle_3", "pos": [110, 60], "vel": [0, 5], "color": "orange"},
        {"id": "vehicle_4", "pos": [190, 200], "vel": [0, -4], "color": "purple"},
    ]
    
    for v_config in vehicles_config:
        start_x, start_y = v_config["pos"]
        end_x = start_x + v_config["vel"][0] * 19  # 19秒後
        end_y = start_y + v_config["vel"][1] * 19
        
        # 境界内に制限
        end_x = max(10, min(290, end_x))
        end_y = max(10, min(290, end_y))
        
        ax.plot([start_x, end_x], [start_y, end_y], 
                color=v_config["color"], linewidth=2, 
                label=v_config["id"], alpha=0.7)
        
        # 開始位置にマーカー
        ax.plot(start_x, start_y, 'o', color=v_config["color"], markersize=8)
    
    # 潜在的な遮蔽ライン（vehicle_3 -> bs_2の例）
    ax.plot([110, 220], [60, 180], 'r--', alpha=0.5, linewidth=1, label='Potential occlusion line')
    
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 300)
    ax.set_xlabel('X Position (m)')
    ax.set_ylabel('Y Position (m)')
    ax.set_title('V2X Scenario: Building Occlusion Analysis')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('visualization/occlusion_analysis.png', dpi=150, bbox_inches='tight')
    print("✅ Visualization saved to visualization/occlusion_analysis.png")

if __name__ == "__main__":
    occlusion_events = analyze_building_occlusion()
    create_visualization()