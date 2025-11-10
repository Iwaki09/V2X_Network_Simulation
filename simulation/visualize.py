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
               link_quality_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    FCDデータとリンク品質データをマージする

    Args:
        timestep_data_list: FCDパース結果のリスト
        link_quality_df: リンク品質DataFrame

    Returns:
        Tuple[v2i_merged_df, v2v_links_df]
        - v2i_merged_df: V2Iリンク用マージデータ (timestamp, vehicle_id, x, y, is_line_of_sight)
        - v2v_links_df: V2Vリンク用データ (timestamp, tx_id, rx_id, is_line_of_sight)
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

    # V2Iリンクを抽出（link_type == 'V2I'）
    v2i_df = link_quality_df[link_quality_df['link_type'] == 'V2I'].copy()
    v2i_df['vehicle_id'] = v2i_df['rx_id']  # rx_idをvehicle_idとして扱う

    # V2Iリンク: timestampとvehicle_idをキーにマージ
    v2i_merged_df = pd.merge(
        fcd_df,
        v2i_df[['timestamp', 'vehicle_id', 'is_line_of_sight']],
        on=['timestamp', 'vehicle_id'],
        how='left'
    )

    # V2Vリンクを抽出（link_type == 'V2V'）
    v2v_links_df = link_quality_df[link_quality_df['link_type'] == 'V2V'][
        ['timestamp', 'tx_id', 'rx_id', 'is_line_of_sight']
    ].copy()

    return v2i_merged_df, v2v_links_df


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
                         timestamp_data: pd.DataFrame,
                         v2v_links: pd.DataFrame,
                         vehicle_positions: Dict[str, Tuple[float, float]]):
    """
    動的オブジェクト（車両、通信リンク）を描画

    Args:
        ax: matplotlibのAxesオブジェクト
        timestamp_data: 特定のタイムステップのV2Iデータ
        v2v_links: 特定のタイムステップのV2Vリンクデータ
        vehicle_positions: 車両ID -> (x, y) の辞書
    """
    # 車両マーカー（黒色の丸）
    vehicle_x = timestamp_data['x'].values
    vehicle_y = timestamp_data['y'].values
    ax.scatter(vehicle_x, vehicle_y,
               color='black', s=80, marker='o',
               label='Vehicles', zorder=8)

    # V2I通信リンク（基地局-車両、LoS=緑、NLoS=赤）
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
                linewidth=1.5, zorder=3, label='V2I LoS' if is_los else 'V2I NLoS')

    # V2V通信リンク（車両間、LoS=青、NLoS=オレンジ）
    for _, row in v2v_links.iterrows():
        tx_id = row['tx_id']
        rx_id = row['rx_id']
        is_los = row['is_line_of_sight']

        # 両端の車両位置を取得
        if tx_id in vehicle_positions and rx_id in vehicle_positions:
            tx_x, tx_y = vehicle_positions[tx_id]
            rx_x, rx_y = vehicle_positions[rx_id]

            # LoS判定による色分け（V2Vは青系）
            link_color = 'cyan' if is_los else 'orange'
            link_alpha = 0.4 if is_los else 0.3

            # 車両間の直線
            ax.plot([tx_x, rx_x],
                    [tx_y, rx_y],
                    color=link_color, alpha=link_alpha,
                    linewidth=1.0, linestyle='--', zorder=2, label='V2V LoS' if is_los else 'V2V NLoS')


def create_frame(timestamp: float,
                 timestamp_data: pd.DataFrame,
                 v2v_links: pd.DataFrame,
                 vehicle_positions: Dict[str, Tuple[float, float]],
                 output_path: str):
    """
    1フレームの画像を生成

    Args:
        timestamp: タイムスタンプ
        timestamp_data: そのタイムステップのV2Iデータ
        v2v_links: そのタイムステップのV2Vリンクデータ
        vehicle_positions: 車両ID -> (x, y) の辞書
        output_path: 出力ファイルパス
    """
    # figsizeを調整して、最終的な画像サイズが2で割り切れるようにする
    fig, ax = plt.subplots(figsize=(14, 6))

    # 静的オブジェクトを描画
    draw_static_objects(ax)

    # 動的オブジェクトを描画
    draw_dynamic_objects(ax, timestamp_data, v2v_links, vehicle_positions)

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
    ax.set_title('V2X Communication Simulation (V2I + V2V)', fontsize=14, fontweight='bold')

    # 凡例（重複を避けるため、最初の1つだけ）
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(),
              loc='upper right', fontsize=10)

    # 保存（DPI=100で1400x600ピクセル、両方とも2で割り切れる）
    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close(fig)


def generate_frames(v2i_merged_df: pd.DataFrame,
                    v2v_links_df: pd.DataFrame,
                    output_dir: str = 'frames'):
    """
    全タイムステップのフレーム画像を生成

    Args:
        v2i_merged_df: V2Iリンク用マージデータ
        v2v_links_df: V2Vリンク用データ
        output_dir: 出力ディレクトリ
    """
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)

    # タイムスタンプごとにループ
    unique_timestamps = sorted(v2i_merged_df['timestamp'].unique())
    total_frames = len(unique_timestamps)

    print(f"Generating {total_frames} frames...")

    for i, timestamp in enumerate(unique_timestamps):
        # そのタイムステップのV2Iデータを抽出
        timestamp_data = v2i_merged_df[v2i_merged_df['timestamp'] == timestamp]

        # そのタイムステップのV2Vリンクを抽出
        v2v_links = v2v_links_df[v2v_links_df['timestamp'] == timestamp]

        # 車両位置の辞書を作成
        vehicle_positions = {
            row['vehicle_id']: (row['x'], row['y'])
            for _, row in timestamp_data.iterrows()
        }

        # フレーム番号を4桁でゼロパディング
        frame_number = str(i).zfill(4)
        output_path = os.path.join(output_dir, f'frame_{frame_number}.png')

        # フレームを生成
        create_frame(timestamp, timestamp_data, v2v_links, vehicle_positions, output_path)

        # 進捗表示
        if (i + 1) % 10 == 0 or i == total_frames - 1:
            print(f"  Progress: {i + 1}/{total_frames} frames")

    print(f"✅ All frames saved to '{output_dir}/' directory")


def main():
    """メイン処理"""
    # ファイルパス
    fcd_file = 'output/fcd/fcd_output.xml'
    csv_file = 'output/raytracing/link_quality_results.csv'
    output_dir = 'output/visualizations/frames'

    print("=" * 60)
    print("V2X Communication Visualization (V2I + V2V)")
    print("=" * 60)

    # データ読み込み
    print("\n1. Loading FCD data...")
    timestep_data_list = parse_fcd_xml(fcd_file)
    print(f"   Loaded {len(timestep_data_list)} timesteps")

    print("\n2. Loading link quality data...")
    link_quality_df = load_link_quality_data(csv_file)
    print(f"   Loaded {len(link_quality_df)} records")
    v2i_count = len(link_quality_df[link_quality_df['link_type'] == 'V2I'])
    v2v_count = len(link_quality_df[link_quality_df['link_type'] == 'V2V'])
    print(f"   - V2I links: {v2i_count}")
    print(f"   - V2V links: {v2v_count}")

    # データマージ
    print("\n3. Merging data...")
    v2i_merged_df, v2v_links_df = merge_data(timestep_data_list, link_quality_df)
    print(f"   - V2I merged records: {len(v2i_merged_df)}")
    print(f"   - V2V link records: {len(v2v_links_df)}")

    # フレーム生成
    print("\n4. Generating frames...")
    generate_frames(v2i_merged_df, v2v_links_df, output_dir)

    print("\n" + "=" * 60)
    print("Visualization completed!")
    print("=" * 60)
    print(f"\nTo create an animation, run:")
    print(f"  ffmpeg -r 10 -i {output_dir}/frame_%04d.png -vcodec libx264 -pix_fmt yuv420p animation.mp4")
    print("")


if __name__ == "__main__":
    main()
