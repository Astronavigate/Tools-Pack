import os
import sys
import threading
import time
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog

# Set system theme and color scheme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def resource_path(relative_path):
    """
    获取资源文件路径，支持 PyInstaller 单文件打包环境
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller 临时路径
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ThemedDialog(ctk.CTkToplevel):
    """自定义弹窗，适配CTK主题（无透明效果）"""

    def __init__(self, parent, title, message, dialog_type="info"):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x200")
        self.resizable(False, False)

        # 设置窗口图标
        icon_path = resource_path("IFPLogo.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # 设置背景颜色为当前主题中CTkFrame的fg_color
        self.configure(fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

        # 图标和标题区域
        icon_text = "✔️" if dialog_type == "info" else "❌"
        title_frame = ctk.CTkFrame(self, height=50, corner_radius=8)
        title_frame.pack(fill="x", pady=(15, 10), padx=15)

        title_label = ctk.CTkLabel(
            title_frame, text=f"{icon_text} {title}", font=("Helvetica", 18, "bold")
        )
        title_label.pack(padx=10, pady=10)

        # 消息文本区域
        message_label = ctk.CTkLabel(
            self, text=message, wraplength=380, font=("Helvetica", 13)
        )
        message_label.pack(padx=15, pady=10)

        # 关闭按钮
        close_btn = ctk.CTkButton(self, text="OK", command=self.destroy, width=96, height=32)
        close_btn.pack(pady=20)

        # 居中
        self.center_window(parent)
        self.lift()
        self.attributes("-topmost", True)

    def center_window(self, parent):
        """将弹窗居中于主窗口"""
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f"+{x}+{y}")


class IconConverter:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("IconFlux Professional")
        self.app.geometry("640x380")
        self.file_path = None
        self.conversion_running = False
        self.current_progress = 0

        # 设置窗口图标
        icon_path = resource_path("IFPLogo.ico")
        if os.path.exists(icon_path):
            self.app.iconbitmap(icon_path)

        self.setup_ui()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self.app)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(
            main_frame,
            text="IconFlux Professional Converter",
            font=("Helvetica", 22, "bold")
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            main_frame,
            text=("Convert images to ICO/ICNS with multiple resolutions\n"
                  "Generates stretched square and proportional icons for Windows & macOS"),
            wraplength=600,
            font=("Helvetica", 12)
        ).pack(pady=(20, 15))

        self.file_label = ctk.CTkLabel(main_frame, text="Selected file: None", font=("Helvetica", 12))
        self.file_label.pack(pady=(0, 10))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=10)

        self.select_btn = ctk.CTkButton(
            button_frame, text="Select Image", command=self.select_file, width=128, height=32, font=("Helvetica", 14)
        )
        self.select_btn.pack(side="left", padx=10)

        self.generate_btn = ctk.CTkButton(
            button_frame, text="Generate Icons", command=self.initiate_conversion,
            width=128, height=32, font=("Helvetica", 14), state="disabled"
        )
        self.generate_btn.pack(side="left", padx=10)

        self.progress_bar = ctk.CTkProgressBar(main_frame, width=600)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()

        self.status_label = ctk.CTkLabel(
            main_frame, text="Ready", text_color="gray70", font=("Helvetica", 16, "bold")
        )
        self.status_label.pack(pady=(10, 15))

        ctk.CTkLabel(
            main_frame,
            text="After conversion, files will be saved in a corresponding [filename]_icons folder\nVersion 2.2.1 (11B0006Tz)\t© 2025 Ravon Industries. All rights reserved.",
            font=("Helvetica", 10),
            text_color="gray50"
        ).pack(side="bottom", pady=10)

        self.center_window()

    def select_file(self):
        path = filedialog.askopenfilename(
            title="Select an Image File",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff"), ("All Files", "*.*")]
        )
        if path:
            self.file_path = path
            self.file_label.configure(text=f"Selected file: {self.file_path}")
            self.generate_btn.configure(state="normal")
            self.status_label.configure(text="Ready")

    def initiate_conversion(self):
        if self.conversion_running or not self.file_path:
            return
        self.conversion_running = True
        self.generate_btn.configure(state="disabled")
        self.select_btn.configure(state="disabled")
        self.status_label.configure(text="0%")
        self.current_progress = 0
        self.progress_bar.pack(pady=10)
        threading.Thread(target=self.process_image, args=(self.file_path,), daemon=True).start()

    def process_image(self, file_path):
        try:
            with Image.open(file_path) as img:
                output_dir = self.create_output_dir(file_path)
                target_widths = [8, 16, 32, 64, 128, 256, 512, 1024]
                self.total_tasks = (len(target_widths) * 2 * 2) + 2
                self.completed_tasks = 0

                for width in target_widths:
                    square_img = self.stretch_to_square(img, width)
                    self.generate_ico(square_img, output_dir, f"square_{width}x{width}")
                    self.generate_icns(square_img, output_dir, f"square_{width}x{width}")
                    self.update_progress(2)

                for width in target_widths:
                    prop_img = self.proportional_resize(img, width)
                    self.generate_ico(prop_img, output_dir, f"proportional_{width}x{prop_img.size[1]}")
                    self.generate_icns(prop_img, output_dir, f"proportional_{width}x{prop_img.size[1]}")
                    self.update_progress(2)

                if img.size[0] <= 256 and img.size[1] <= 256:
                    self.generate_ico(img, output_dir, "original")
                if img.size[0] > 1024 or img.size[1] > 1024:
                    self.save_original_as_custom_icns(img, output_dir, "original")
                else:
                    self.generate_icns(img, output_dir, "original")
                self.update_progress(2)

                self.show_completion(output_dir)
        except Exception as e:
            self.show_error(str(e))
        finally:
            self.conversion_running = False
            self.app.after(0, lambda: (
                self.generate_btn.configure(state="normal"),
                self.select_btn.configure(state="normal"))
            )

    def create_output_dir(self, file_path):
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(os.path.dirname(file_path), f"{base_name}_icons")
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def stretch_to_square(self, img, target_size):
        return img.resize((target_size, target_size), Image.Resampling.LANCZOS)

    def proportional_resize(self, img, target_width):
        orig_w, orig_h = img.size
        ratio = target_width / orig_w
        target_height = int(orig_h * ratio)
        return img.resize((target_width, target_height), Image.Resampling.LANCZOS)

    def generate_ico(self, img, output_dir, name_suffix):
        if img.size[0] > 256 or img.size[1] > 256:
            return
        output_path = os.path.join(output_dir, f"{name_suffix}.ico")
        img.convert("RGBA").save(output_path, format="ICO", sizes=[img.size])

    def generate_icns(self, img, output_dir, name_suffix):
        output_path = os.path.join(output_dir, f"{name_suffix}.icns")
        img.convert("RGBA").save(output_path, format="ICNS")

    def save_original_as_custom_icns(self, img, output_dir, name_suffix):
        output_path = os.path.join(output_dir, f"{name_suffix}.icns")
        img.convert("RGBA").save(output_path, format="PNG")

    def update_progress(self, tasks_completed):
        self.completed_tasks += tasks_completed
        new_progress = self.completed_tasks / self.total_tasks
        self.animate_progress(self.current_progress, new_progress, duration=200)
        self.current_progress = new_progress

    def animate_progress(self, start, end, duration=200):
        steps = max(int(duration / 20), 1)
        delta = (end - start) / steps

        def step(count, current):
            new_val = current + delta
            self.progress_bar.set(new_val)
            percent = int(new_val * 100)
            self.status_label.configure(text=f"{percent}%")
            if count < steps:
                self.app.after(20, lambda: step(count + 1, new_val))
        step(0, start)

    def show_completion(self, output_dir):
        time.sleep(0.3)
        self.app.after(0, lambda: ThemedDialog(
            parent=self.app,
            title="Conversion Complete",
            message=f"All icons have been generated and saved in:\n{output_dir}",
            dialog_type="info"
        ))

    def show_error(self, message):
        self.app.after(0, lambda: ThemedDialog(
            parent=self.app,
            title="Conversion Error",
            message=f"An error occurred during conversion:\n{message}",
            dialog_type="error"
        ))

    def run(self):
        self.app.mainloop()

    def center_window(self):
        self.app.update_idletasks()
        screen_width = self.app.winfo_screenwidth()
        screen_height = self.app.winfo_screenheight()
        x = (screen_width - self.app.winfo_width()) // 2
        y = (screen_height - self.app.winfo_height()) // 2
        self.app.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    converter = IconConverter()
    converter.run()
