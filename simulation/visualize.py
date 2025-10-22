"""
可視化スクリプト

SUMO + SIONNA RT統合シミュレーションの結果を可視化します。
車両、基地局、建物の位置関係と、LoS/NLoS通信リンクを時系列で描画します。
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, List, Tuple
from fcd_parser import parse_fcd_xml, TimestepData


# シミュレーション環境のパラメータ
BASE_STATION = (500, 150)  # 基地局の座標 (X, Y)
BUILDING_CENTER = (500, 50)  # 建物の中心座標 (X, Y)
BUILDING_SIZE = (20, 20)  # 建物のサイズ (width, height)
ROAD_X_RANGE = (0, 1000)  # 道路のX範囲
ROAD_Y_RANGE = (-3.5, 3.5)  # 道路のY範囲


def load_link_quality_data(csv_path: str) -> pd.DataFrame:
    """
    リンク品質CSVデータを読み込む

    Args:
        csv_path: link_quality_results.csvのパス

    Returns:
        pandas DataFrame
    """
    try:
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load link quality CSV: {csv_path}") from e


def merge_data(timestep_data_list: List[TimestepData],
               link_quality_df: pd.DataFrame) -> pd.DataFrame:
    """
    FCDデータとリンク品質データをマージする

    Args:
        timestep_data_list: FCDパース結果のリスト
        link_quality_df: リンク品質DataFrame

    Returns:
        マージされたDataFrame (timestamp, vehicle_id, x, y, is_line_of_sight)
    """
    # FCDデータをDataFrameに変換
    fcd_records = []
    for timestep_data in timestep_data_list:
        for vehicle in timestep_data.vehicles:
            fcd_records.append({
                'timestamp': timestep_data.timestamp,
                'vehicle_id': vehicle.vehicle_id,
                'x': vehicle.x,
                'y': vehicle.y
            })
    fcd_df = pd.DataFrame(fcd_records)

    # timestampとvehicle_idをキーにマージ
    merged_df = pd.merge(
        fcd_df,
        link_quality_df[['timestamp', 'vehicle_id', 'is_line_of_sight']],
        on=['timestamp', 'vehicle_id'],
        how='left'
    )

    return merged_df


def draw_static_objects(ax: plt.Axes):
    """
    静的オブジェクト（道路、基地局、建物）を描画

    Args:
        ax: matplotlibのAxesオブジェクト
    """
    # 道路の範囲を薄いグレーで塗りつぶし
    ax.axhspan(ROAD_Y_RANGE[0], ROAD_Y_RANGE[1],
               color='lightgray', alpha=0.3, zorder=0)

    # 基地局（青色の三角マーカー）
    ax.plot(BASE_STATION[0], BASE_STATION[1],
            marker='^', color='blue', markersize=12,
            label='Base Station', zorder=10)

    # 建物（灰色の四角形）
    building_x = BUILDING_CENTER[0] - BUILDING_SIZE[0] / 2
    building_y = BUILDING_CENTER[1] - BUILDING_SIZE[1] / 2
    building_rect = patches.Rectangle(
        (building_x, building_y),
        BUILDING_SIZE[0], BUILDING_SIZE[1],
        linewidth=1, edgecolor='black', facecolor='gray',
        alpha=0.7, label='Building', zorder=5
    )
    ax.add_patch(building_rect)


def draw_dynamic_objects(ax: plt.Axes,
                         timestamp_data: pd.DataFrame):
    """
    動的オブジェクト（車両、通信リンク）を描画

    Args:
        ax: matplotlibのAxesオブジェクト
        timestamp_data: 特定のタイムステップのデータ
    """
    # 車両マーカー（黒色の丸）
    vehicle_x = timestamp_data['x'].values
    vehicle_y = timestamp_data['y'].values
    ax.scatter(vehicle_x, vehicle_y,
               color='black', s=80, marker='o',
               label='Vehicles', zorder=8)

    # 通信リンク（LoS=緑、NLoS=赤）
    for _, row in timestamp_data.iterrows():
        veh_x = row['x']
        veh_y = row['y']
        is_los = row['is_line_of_sight']

        # LoS判定による色分け
        link_color = 'green' if is_los else 'red'
        link_alpha = 0.6 if is_los else 0.4

        # 基地局から車両への直線
        ax.plot([BASE_STATION[0], veh_x],
                [BASE_STATION[1], veh_y],
                color=link_color, alpha=link_alpha,
                linewidth=1.5, zorder=3)


def create_frame(timestamp: float,
                 timestamp_data: pd.DataFrame,
                 output_path: str):
    """
    1フレームの画像を生成

    Args:
        timestamp: タイムスタンプ
        timestamp_data: そのタイムステップのデータ
        output_path: 出力ファイルパス
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # 静的オブジェクトを描画
    draw_static_objects(ax)

    # 動的オブジェクトを描画
    draw_dynamic_objects(ax, timestamp_data)

    # タイムスタンプをテキスト表示
    ax.text(0.02, 0.98, f'Time: {timestamp:.1f}s',
            transform=ax.transAxes, fontsize=14,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # 軸とグリッド設定
    ax.set_xlim(-50, ROAD_X_RANGE[1] + 50)
    ax.set_ylim(-50, 200)
    ax.set_xlabel('X [m]', fontsize=12)
    ax.set_ylabel('Y [m]', fontsize=12)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('V2I Communication Simulation', fontsize=14, fontweight='bold')

    # 凡例（重複を避けるため、最初の1つだけ）
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(),
              loc='upper right', fontsize=10)

    # 保存
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close(fig)


def generate_frames(merged_df: pd.DataFrame,
                    output_dir: str = 'frames'):
    """
    全タイムステップのフレーム画像を生成

    Args:
        merged_df: マージされたデータフレーム
        output_dir: 出力ディレクトリ
    """
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)

    # タイムスタンプごとにループ
    unique_timestamps = sorted(merged_df['timestamp'].unique())
    total_frames = len(unique_timestamps)

    print(f"Generating {total_frames} frames...")

    for i, timestamp in enumerate(unique_timestamps):
        # そのタイムステップのデータを抽出
        timestamp_data = merged_df[merged_df['timestamp'] == timestamp]

        # フレーム番号を4桁でゼロパディング
        frame_number = str(i).zfill(4)
        output_path = os.path.join(output_dir, f'frame_{frame_number}.png')

        # フレームを生成
        create_frame(timestamp, timestamp_data, output_path)

        # 進捗表示
        if (i + 1) % 10 == 0 or i == total_frames - 1:
            print(f"  Progress: {i + 1}/{total_frames} frames")

    print(f"✅ All frames saved to '{output_dir}/' directory")


def main():
    """メイン処理"""
    # ファイルパス
    fcd_file = 'output/fcd_output.xml'
    csv_file = 'output/link_quality_results.csv'
    output_dir = 'frames'

    print("=" * 60)
    print("V2I Communication Visualization")
    print("=" * 60)

    # データ読み込み
    print("\n1. Loading FCD data...")
    timestep_data_list = parse_fcd_xml(fcd_file)
    print(f"   Loaded {len(timestep_data_list)} timesteps")

    print("\n2. Loading link quality data...")
    link_quality_df = load_link_quality_data(csv_file)
    print(f"   Loaded {len(link_quality_df)} records")

    # データマージ
    print("\n3. Merging data...")
    merged_df = merge_data(timestep_data_list, link_quality_df)
    print(f"   Merged data: {len(merged_df)} records")

    # フレーム生成
    print("\n4. Generating frames...")
    generate_frames(merged_df, output_dir)

    print("\n" + "=" * 60)
    print("Visualization completed!")
    print("=" * 60)
    print(f"\nTo create an animation, run:")
    print(f"  ffmpeg -r 10 -i {output_dir}/frame_%04d.png -vcodec libx264 -pix_fmt yuv420p animation.mp4")
    print("")


if __name__ == "__main__":
    main()
