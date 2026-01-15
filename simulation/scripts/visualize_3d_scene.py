"""
3D Scene Visualization for Corner Intersection Scenario

論文用の3D地物モデル画像を生成するスクリプト
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from pathlib import Path
import sys

# プロジェクトルートをPYTHONPATHに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scenarios.corner_intersection import CornerIntersectionConfig


def create_box_vertices(center, size):
    """
    箱の頂点を生成

    Args:
        center: [x, y, z] 中心座標
        size: [width, depth, height] サイズ

    Returns:
        vertices: 8つの頂点座標のリスト
    """
    cx, cy, cz = center
    w, d, h = size

    # 8つの頂点
    vertices = [
        [cx - w/2, cy - d/2, cz],      # 0: 左下前
        [cx + w/2, cy - d/2, cz],      # 1: 右下前
        [cx + w/2, cy + d/2, cz],      # 2: 右上前
        [cx - w/2, cy + d/2, cz],      # 3: 左上前
        [cx - w/2, cy - d/2, cz + h],  # 4: 左下奥
        [cx + w/2, cy - d/2, cz + h],  # 5: 右下奥
        [cx + w/2, cy + d/2, cz + h],  # 6: 右上奥
        [cx - w/2, cy + d/2, cz + h],  # 7: 左上奥
    ]

    return np.array(vertices)


def create_box_faces(vertices):
    """
    箱の面を生成

    Args:
        vertices: 8つの頂点座標

    Returns:
        faces: 6つの面（各面は4つの頂点インデックス）
    """
    faces = [
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # 底面（前）
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # 底面（後）
        [vertices[0], vertices[3], vertices[7], vertices[4]],  # 左側面
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # 右側面
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # 下面
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # 上面
    ]

    return faces


def get_base_stations(config):
    """設定から基地局リストを取得（単一/複数に対応）"""
    if hasattr(config, "base_stations") and config.base_stations:
        return config.base_stations
    if hasattr(config, "base_station") and config.base_station:
        return [config.base_station]
    return []


def plot_3d_scene(config, view='isometric', save_path=None, show_labels=True, show_grid=True):
    """
    3Dシーンをプロット

    Args:
        config: シナリオ設定
        view: カメラ視点 ('isometric', 'top', 'side', 'front')
        save_path: 保存先パス（Noneの場合は表示のみ）
        show_labels: ラベルを表示するか
        show_grid: グリッドを表示するか
    """
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # 建物を描画
    building_color = '#8B4513'  # 茶色
    building_alpha = 0.7

    base_stations = get_base_stations(config)
    label_xy_offset = 18.0
    label_z_offset = 8.0
    bs_label_z_offset = 6.0
    bs_avoid_radius = 120.0

    for building in config.buildings:
        vertices = create_box_vertices(building.center, building.size)
        faces = create_box_faces(vertices)

        # 3D Collectionとして追加
        collection = Poly3DCollection(faces, alpha=building_alpha,
                                     facecolor=building_color,
                                     edgecolor='black', linewidth=1)
        ax.add_collection3d(collection)

        # ラベル（建物の上、さらに高い位置に配置）
        if show_labels:
            cx, cy, cz = building.center
            _, _, h = building.size
            offset_vec = np.array([cx, cy], dtype=float)
            if base_stations:
                bs_positions = np.array([bs.position[:2] for bs in base_stations], dtype=float)
                deltas = offset_vec - bs_positions
                dists = np.hypot(deltas[:, 0], deltas[:, 1])
                nearest_idx = int(np.argmin(dists))
                if dists[nearest_idx] < bs_avoid_radius:
                    offset_vec = deltas[nearest_idx]

            norm = np.hypot(offset_vec[0], offset_vec[1])
            if norm == 0:
                offset_x, offset_y = 0.0, label_xy_offset
            else:
                offset_x = label_xy_offset * offset_vec[0] / norm
                offset_y = label_xy_offset * offset_vec[1] / norm
            ax.text(cx + offset_x, cy + offset_y, cz + h + label_z_offset, building.id,
                   fontsize=10, ha='center', va='bottom', fontweight='bold', zorder=100,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='black'))

    # 基地局を描画
    for bs in base_stations:
        ax.scatter([bs.position[0]], [bs.position[1]], [bs.position[2]],
                  c='red', marker='^', s=300,
                  edgecolors='black', linewidths=2, zorder=10)

        # 基地局の支柱を描画
        ax.plot([bs.position[0], bs.position[0]],
                [bs.position[1], bs.position[1]],
                [0, bs.position[2]],
                'r--', linewidth=2, alpha=0.6)

        # ラベル（白背景付きで見やすく）
        if show_labels:
            label = getattr(bs, "id", "BS")
            ax.text(bs.position[0], bs.position[1], bs.position[2] + bs_label_z_offset,
                   label, fontsize=12, ha='center', va='bottom',
                   fontweight='bold', color='red', zorder=100,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9, edgecolor='red'))

    # 道路を描画（平面）
    road_width = 7.0  # 2車線
    road_color = '#555555'
    road_alpha = 0.3

    # 東西道路（X軸）
    road_x = np.array([[-200, -road_width/2, 0],
                       [200, -road_width/2, 0],
                       [200, road_width/2, 0],
                       [-200, road_width/2, 0]])
    ax.add_collection3d(Poly3DCollection([road_x], alpha=road_alpha,
                                        facecolor=road_color, edgecolor='white'))

    # 南北道路（Y軸）
    road_y = np.array([[-road_width/2, -200, 0],
                       [road_width/2, -200, 0],
                       [road_width/2, 200, 0],
                       [-road_width/2, 200, 0]])
    ax.add_collection3d(Poly3DCollection([road_y], alpha=road_alpha,
                                        facecolor=road_color, edgecolor='white'))

    # 座標軸とラベル
    ax.set_xlabel('X [m]', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y [m]', fontsize=12, fontweight='bold')
    ax.set_zlabel('Z [m]', fontsize=12, fontweight='bold')

    # 軸範囲を設定
    ax.set_xlim(-150, 150)
    ax.set_ylim(-150, 150)
    ax.set_zlim(0, 50)

    # グリッド
    if show_grid:
        ax.grid(True, alpha=0.3)

    # 視点を設定
    if view == 'isometric':
        ax.view_init(elev=25, azim=45)
    elif view == 'isometric_sw':
        ax.view_init(elev=25, azim=-135)
    elif view == 'isometric_se':
        ax.view_init(elev=25, azim=-45)
    elif view == 'isometric_nw':
        ax.view_init(elev=25, azim=135)
    elif view == 'top':
        ax.view_init(elev=90, azim=0)
    elif view == 'side':
        ax.view_init(elev=0, azim=0)
    elif view == 'front':
        ax.view_init(elev=0, azim=90)
    else:
        ax.view_init(elev=25, azim=45)

    # アスペクト比を均等に
    ax.set_box_aspect([1, 1, 0.5])

    # 保存または表示
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"✅ Saved: {save_path}")
    else:
        plt.show()

    plt.close()


def plot_2d_top_view(config, save_path=None, show_labels=True):
    """
    2D上面図をプロット（よりクリーンな論文用図）

    Args:
        config: シナリオ設定
        save_path: 保存先パス
        show_labels: ラベルを表示するか
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    # 建物を描画（矩形）
    building_color = '#8B4513'

    for building in config.buildings:
        cx, cy, _ = building.center
        w, d, _ = building.size

        # 矩形を描画
        rect = plt.Rectangle((cx - w/2, cy - d/2), w, d,
                            facecolor=building_color, edgecolor='black',
                            linewidth=2, alpha=0.7)
        ax.add_patch(rect)

        # ラベル
        if show_labels:
            ax.text(cx, cy, building.id, fontsize=11, ha='center',
                   va='center', fontweight='bold', color='white')

    # 基地局を描画
    base_stations = get_base_stations(config)
    for bs in base_stations:
        ax.scatter([bs.position[0]], [bs.position[1]],
                  c='red', marker='^', s=400,
                  edgecolors='black', linewidths=2, zorder=10)

        if show_labels:
            label = getattr(bs, "id", "BS")
            ax.text(bs.position[0], bs.position[1] - 10, label,
                   fontsize=12, ha='center', va='top',
                   fontweight='bold', color='red',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9, edgecolor='red'))

    # 道路を描画
    road_width = 7.0
    road_color = '#555555'

    # 東西道路
    ax.add_patch(plt.Rectangle((-200, -road_width/2), 400, road_width,
                              facecolor=road_color, alpha=0.3))

    # 南北道路
    ax.add_patch(plt.Rectangle((-road_width/2, -200), road_width, 400,
                              facecolor=road_color, alpha=0.3))

    # 中央線を描画
    ax.plot([-200, 200], [0, 0], 'w--', linewidth=1, alpha=0.5)
    ax.plot([0, 0], [-200, 200], 'w--', linewidth=1, alpha=0.5)

    # 軸設定
    ax.set_xlim(-150, 150)
    ax.set_ylim(-150, 150)
    ax.set_xlabel('X [m]', fontsize=14, fontweight='bold')
    ax.set_ylabel('Y [m]', fontsize=14, fontweight='bold')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')

    # 方位を示す矢印
    arrow_len = 30
    arrow_props = dict(arrowstyle='->', lw=2, color='black')
    ax.annotate('', xy=(120, 120), xytext=(120-arrow_len, 120),
               arrowprops=arrow_props)
    ax.text(120-arrow_len/2, 125, 'E', fontsize=12, ha='center', fontweight='bold')
    ax.annotate('', xy=(120, 120), xytext=(120, 120-arrow_len),
               arrowprops=arrow_props)
    ax.text(125, 120-arrow_len/2, 'N', fontsize=12, va='center', fontweight='bold')

    # 保存または表示
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"✅ Saved: {save_path}")
    else:
        plt.show()

    plt.close()


def main():
    """メイン関数"""
    print("🎨 3D Scene Visualization for Corner Intersection")
    print("=" * 60)

    # シナリオ設定を読み込み
    config = CornerIntersectionConfig()

    # 出力ディレクトリを作成
    output_dir = config.figures_output_dir / "3d_scene"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📊 Generating 3D visualizations...")
    print(f"Output directory: {output_dir}")

    # 複数の視点から画像を生成
    views = [
        ('isometric', 'Isometric NE (斜め視点・北東から)'),
        ('isometric_sw', 'Isometric SW (斜め視点・南西から)'),
        ('isometric_se', 'Isometric SE (斜め視点・南東から)'),
        ('isometric_nw', 'Isometric NW (斜め視点・北西から)'),
        ('top', 'Top (上面図)'),
        ('side', 'Side (横視点)'),
        ('front', 'Front (正面視点)'),
    ]

    print(f"\n🎬 Generating 3D views...")
    for view_name, view_desc in views:
        save_path = output_dir / f"scene_3d_{view_name}.png"
        print(f"  - {view_desc}...", end=' ')
        plot_3d_scene(config, view=view_name, save_path=save_path)

    # 2D上面図も生成
    print(f"\n🗺️  Generating 2D top view...")
    save_path_2d = output_dir / "scene_2d_top.png"
    print(f"  - 2D Top View...", end=' ')
    plot_2d_top_view(config, save_path=save_path_2d)

    print(f"\n" + "=" * 60)
    print(f"✅ All visualizations generated successfully!")
    print(f"📁 Output directory: {output_dir}")
    print(f"\n📸 Generated files:")
    for file in sorted(output_dir.glob("*.png")):
        print(f"  - {file.name}")


if __name__ == "__main__":
    main()
