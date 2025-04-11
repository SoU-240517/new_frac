import matplotlib.pyplot as plt
from matplotlib.widgets import Button
# 同じフォルダにある zoom_selector.py から ZoomSelector クラスをインポート
from ui.zoom_function.zoom_selector import ZoomSelector

# --- コールバック関数の例 ---
def handle_zoom_confirm(x, y, width, height):
    print(f"=== Zoom Confirmed Callback ===")
    print(f"  Rectangle: x={x:.2f}, y={y:.2f}, width={width:.2f}, height={height:.2f}")
    print(f"===============================")
    # 実際のズーム処理例（コメントアウト）
    # ax.set_xlim(x, x + width)
    # ax.set_ylim(y, y + height)
    # fig.canvas.draw_idle()

def handle_zoom_cancel():
    print(f"=== Zoom Cancelled Callback ===")
    # 必要ならキャンセル時の処理を追加

# --- matplotlibでグラフ準備 ---
fig, ax = plt.subplots()
ax.plot([0, 1, 2, 3, 4], [0, 1, 4, 9, 16], 'bo-')
ax.set_title("Drag Left Mouse Button to Draw Rectangle (ESC to cancel)")
ax.set_xlabel("X-axis")
ax.set_ylabel("Y-axis")
ax.grid(True)

# --- ZoomSelectorのインスタンス化 ---
zoom_selector = ZoomSelector(ax,
                             on_zoom_confirm=handle_zoom_confirm,
                             on_zoom_cancel=handle_zoom_cancel,
                             debug_enabled=True) # ログを見たければTrue

# --- ツール有効/無効切り替えボタンの例 ---
is_active = True

def toggle_selector(event):
    global is_active
    if is_active:
        zoom_selector.disconnect_events()
        button.label.set_text('Activate Selector')
        ax.set_title("Selector Deactivated")
        print("INFO: ZoomSelector deactivated.")
    else:
        zoom_selector.connect_events()
        button.label.set_text('Deactivate Selector')
        ax.set_title("Drag Left Mouse Button to Draw Rectangle (ESC to cancel)")
        print("INFO: ZoomSelector activated.")
    is_active = not is_active
    fig.canvas.draw_idle()

ax_button = plt.axes([0.7, 0.01, 0.2, 0.05])
button = Button(ax_button, 'Deactivate Selector')
button.on_clicked(toggle_selector)

plt.show()
