import sys
import os
import math
import random
import time
from PyQt6.QtCore import QTimer, Qt, QUrl, QPoint
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QPainter, QColor, QImage, QPixmap, QCursor, QTransform, QPen, QPainterPath

class CombinedGlitchSimulation(QMainWindow):
    def __init__(self):
        super().__init__()
        
        screen = QApplication.primaryScreen()
        size = screen.size()
        self.width = size.width()
        self.height = size.height()
        
        self.screenshot = screen.grabWindow(0).toImage()
        self.buffer_image = QImage(self.screenshot)
        
        self.setGeometry(0, 0, self.width, self.height)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow)
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.unsetCursor() 
        
        self.mouse_pos = QPoint(self.width // 2, self.height // 2)
        self.mouse_history = []
        
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
            
        original_pixmap = QPixmap(os.path.join(base_path, "xbutton.png"))
        self.target_size = 24
        
        self.mouse_pixmap = original_pixmap.scaled(self.target_size, self.target_size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation) if not original_pixmap.isNull() else QPixmap()
        
        self.iteration = 0
        self.current_mode = 0  
        self.total_modes = 8  
        
        self.active_scribbles = []
        
        self.speed_x = -18
        self.speed_y = -18
        self.mode1_offset_x = 0
        self.mode1_offset_y = 0
        
        from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        
        sound_file = os.path.abspath(os.path.join(base_path, "background.mp3"))
        if os.path.exists(sound_file):
            self.player.setSource(QUrl.fromLocalFile(sound_file))
            self.player.setLoops(QMediaPlayer.Loops.Infinite)
            self.audio_output.setVolume(1.0)
            self.player.play()
        
        self.mode_durations = [20000, 20000, 20000, 20000, 20000, 20000, 20000, 20000]
        
        self.mode_timer = QTimer(self)
        self.mode_timer.timeout.connect(self.switch_mode)
        self.mode_timer.start(self.mode_durations[0])

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.apply_visual_effects)
        self.timer.start(16)

        self.clear_timer = QTimer(self)
        self.clear_timer.timeout.connect(self.clear_old_history)
        self.clear_timer.start(20000)

        self.shutdown_timer = QTimer(self)
        self.shutdown_timer.setSingleShot(True)
        self.shutdown_timer.timeout.connect(self.close_application)
        self.shutdown_timer.start(sum(self.mode_durations))
        
        self.raise_()
        self.activateWindow()

    def close_application(self):
        self.audio_output.setVolume(0.0)
        self.player.stop()
        QApplication.quit()

    def unmute_audio(self):
        self.audio_output.setVolume(1.0)

    def clear_old_history(self):
        if len(self.mouse_history) > 80:
            self.mouse_history = self.mouse_history[-40:]

    def switch_mode(self):
        self.audio_output.setVolume(0.0)
        if self.current_mode == self.total_modes - 1:
            self.close_application()
            return

        self.current_mode = (self.current_mode + 1) % self.total_modes
        self.buffer_image = QImage(self.screenshot)
        self.mouse_history.clear()  
        self.active_scribbles.clear()
        self.iteration = 0
        
        self.mode1_offset_x = 0
        self.mode1_offset_y = 0
        
        self.mode_timer.start(self.mode_durations[self.current_mode])
        
        audio_map = {0: 0, 1: 20000, 2: 40000, 3: 60000, 4: 80000, 5: 100000, 6: 120000, 7: 140000}
        self.player.setPosition(audio_map.get(self.current_mode, 0))
        QTimer.singleShot(150, self.unmute_audio)

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position().toPoint()
        
        if self.current_mode != 2 and self.iteration % 2 == 0:
            self.mouse_history.append(QCursor.pos())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_N:
            if self.current_mode == self.total_modes - 1: 
                self.close_application()
            else: 
                self.switch_mode()

    def apply_visual_effects(self):
        self.iteration += 1

        curr_pos = QCursor.pos()
        QCursor.setPos(curr_pos.x() + random.randint(-5, 5), curr_pos.y() + random.randint(-5, 5))

        if self.current_mode in [0, 1, 3, 5, 6, 7]:
            base = self.buffer_image.copy()
        else:
            base = self.screenshot.copy()

        if self.iteration % 2 == 0 and self.current_mode not in [0, 2]:
            painter_mod = QPainter(base)
            painter_mod.setCompositionMode(QPainter.CompositionMode.CompositionMode_Difference)
            for _ in range(12):  
                inv_color = QColor(random.choice([0, 255]), random.choice([0, 255]), random.choice([0, 255]))
                painter_mod.fillRect(
                    random.randint(0, self.width), random.randint(0, self.height),
                    random.randint(300, 800), random.randint(50, 400),
                    inv_color
                )
            painter_mod.end()

        temp_image = QImage(self.width, self.height, QImage.Format.Format_ARGB32)
        painter = QPainter(temp_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.current_mode not in [0, 2]:
            painter.setOpacity(0.65)
            painter.drawImage(random.randint(-10, 10), random.randint(-10, 10), self.buffer_image)
            painter.setOpacity(1.0)

        if self.current_mode == 0:
            painter.drawImage(0, 0, base)
            num_slices = 15
            slice_h = self.height // num_slices
            for i in range(num_slices):
                if i % 2 == 0:
                    y_pos = i * slice_h
                    shift_amount = int(math.sin(self.iteration * 0.2 + i) * 15)
                    painter.drawImage(shift_amount, y_pos, base, 0, y_pos, self.width, slice_h)
            
            if self.iteration % 4 == 0:
                painter.setOpacity(0.15)
                for _ in range(3):
                    painter.fillRect(0, random.randint(0, self.height), self.width, random.randint(2, 8), QColor(0, 255, 150))
                painter.setOpacity(1.0)

        elif self.current_mode == 1:
            painter.drawImage(0, 0, base)
            for _ in range(40):
                bx = random.randint(0, self.width - 400)
                by = random.randint(0, self.height - 100)
                painter.drawImage(bx + random.randint(-120, 120), by, base, bx, by, random.randint(200, 600), random.randint(20, 80))

        elif self.current_mode == 2:
            self.mode1_offset_x = (self.mode1_offset_x + self.speed_x) % self.width
            self.mode1_offset_y = (self.mode1_offset_y + self.speed_y) % self.height
            
            if self.iteration % 2 == 0:
                local_m = self.mapFromGlobal(QCursor.pos())
                self.mouse_history.append(local_m)

            updated_history = []
            for pos in self.mouse_history:
                new_pos = pos + QPoint(self.speed_x, self.speed_y)
                nx = new_pos.x() % self.width
                ny = new_pos.y() % self.height
                updated_history.append(QPoint(nx, ny))
            self.mouse_history = updated_history

            wave_image = QImage(self.width, self.height, QImage.Format.Format_ARGB32)
            wave_painter = QPainter(wave_image)
            num_lines = 70
            line_h = self.height // num_lines
            for i in range(num_lines):
                y = i * line_h
                wave_shift = int(math.sin((self.iteration * 0.4) + (i * 0.6)) * 75)
                wave_painter.drawImage(wave_shift, y, base, 0, y, self.width, line_h)
            wave_painter.end()
            
            painter.drawImage(self.mode1_offset_x, self.mode1_offset_y, wave_image)
            painter.drawImage(self.mode1_offset_x - self.width, self.mode1_offset_y, wave_image)
            painter.drawImage(self.mode1_offset_x, self.mode1_offset_y - self.height, wave_image)
            painter.drawImage(self.mode1_offset_x - self.width, self.mode1_offset_y - self.height, wave_image)

        elif self.current_mode == 3:
            painter.drawImage(0, 0, base)
            if self.iteration % 8 == 0:
                painter.setOpacity(0.3)
                painter.drawImage(0, 0, self.screenshot)
                painter.setOpacity(1.0)

            for _ in range(60):
                rx = random.randint(0, self.width - 250)
                rw = random.randint(100, 400)
                painter.drawImage(rx, random.randint(40, 100), base, rx, 0, rw, self.height - 100)

        elif self.current_mode == 4:
            painter.save()
            shift = int(45 + math.sin(self.iteration * 0.5) * 50)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            painter.drawImage(shift, 0, base)
            painter.drawImage(-shift, 0, base)
            painter.restore()

        elif self.current_mode == 5:
            painter.drawImage(0, 0, base)
            if self.iteration % 8 == 0 and len(self.active_scribbles) < 25:
                start_x = random.randint(int(self.width * 0.05), int(self.width * 0.95))
                start_y = random.randint(int(self.height * 0.05), int(self.height * 0.95))
                self.active_scribbles.append({
                    "points": [QPoint(start_x, start_y)],
                    "dx": random.choice([-25, 25]) * random.randint(1, 4),
                    "dy": random.randint(-20, 20),
                    "steps": random.randint(30, 60)
                })

            for scribble in self.active_scribbles:
                if scribble["steps"] > 0 and len(scribble["points"]) > 0:
                    last_pt = scribble["points"][-1]
                    new_x = last_pt.x() + scribble["dx"] + random.randint(-35, 35)
                    new_y = last_pt.y() + scribble["dy"] + random.randint(-35, 35)
                    scribble["points"].append(QPoint(new_x, new_y))
                    scribble["steps"] -= 1

            painter.save()
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Xor)
            for scribble in self.active_scribbles:
                if len(scribble["points"]) < 2:
                    continue
                path = QPainterPath()
                first_pt = scribble["points"][0]
                path.moveTo(float(first_pt.x()), float(first_pt.y()))
                for pt in scribble["points"][1:]:
                    path.lineTo(float(pt.x()), float(pt.y()))
                
                painter.setPen(QPen(QColor(255, 255, 255, 255), 8))  
                painter.drawPath(path)
            painter.restore()

        elif self.current_mode == 6:
            painter.drawImage(0, 0, base)
            painter.save()
            zoom = 1.08
            zw, zh = int(self.width * zoom), int(self.height * zoom)
            dx, dy = (self.width - zw) // 2, (self.height - zh) // 2
            
            t = QTransform()
            t.translate(self.width//2, self.height//2)
            t.rotate(math.sin(self.iteration * 0.18) * 18)
            t.translate(-self.width//2, -self.height//2)
            painter.setTransform(t)
            
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Difference)
            painter.drawImage(dx, dy, base, 0, 0, self.width, self.height)
            painter.restore()

        elif self.current_mode == 7:
            painter.drawImage(0, 0, base)
            for _ in range(30):  
                col_w = random.randint(200, 600)
                col_x = random.randint(0, self.width - col_w)
                painter.drawImage(col_x, random.randint(-120, 120), base, col_x, 0, col_w, self.height)
                
                row_h = random.randint(150, 450)
                row_y = random.randint(0, self.height - row_h)
                painter.drawImage(random.randint(-120, 120), row_y, base, 0, row_y, self.width, row_h)

        painter.end()
        self.buffer_image = temp_image
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.current_mode in [0, 1, 3, 5, 6, 7]:
            shx = random.randint(-55, 55)
            shy = random.randint(-55, 55)
        elif self.current_mode == 2:
            shx, shy = 0, 0  
        else:
            shx = random.randint(-35, 35) if self.iteration % 2 == 0 else 0
            shy = random.randint(-35, 35) if self.iteration % 2 == 0 else 0
            
        painter.drawImage(shx, shy, self.buffer_image)
        
        if self.mouse_pixmap.isNull(): return
        offset = self.target_size // 2

        dupe_layer = QImage(self.width, self.height, QImage.Format.Format_ARGB32)
        dupe_layer.fill(Qt.GlobalColor.transparent)
        
        layer_painter = QPainter(dupe_layer)
        layer_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for old_pos_data in self.mouse_history:
            if self.current_mode == 2:
                draw_x, draw_y = old_pos_data.x() - offset, old_pos_data.y() - offset
            else:
                old_local = self.mapFromGlobal(old_pos_data)
                draw_x, draw_y = old_local.x() - offset, old_local.y() - offset
            layer_painter.drawPixmap(draw_x, draw_y, self.mouse_pixmap)
        layer_painter.end()

        glitched_dupe_layer = QImage(self.width, self.height, QImage.Format.Format_ARGB32)
        glitched_dupe_layer.fill(Qt.GlobalColor.transparent)
        gd_painter = QPainter(glitched_dupe_layer)
        gd_painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.current_mode == 0: 
            num_slices = 20
            slice_h = self.height // num_slices
            for i in range(num_slices):
                y_pos = i * slice_h
                shift = int(math.sin(self.iteration * 0.3 + i) * 25) if i % 2 == 0 else 0
                gd_painter.drawImage(shift, y_pos, dupe_layer, 0, y_pos, self.width, slice_h)
        elif self.current_mode == 2:
            gd_painter.drawImage(0, 0, dupe_layer)
            gd_painter.drawImage(-15, 0, dupe_layer)
            gd_painter.drawImage(15, 0, dupe_layer)
        elif self.current_mode in [1, 7]: 
            gd_painter.drawImage(random.randint(-20, 20), random.randint(-20, 20), dupe_layer)
        elif self.current_mode == 3: 
            for _ in range(15):
                rx = random.randint(0, self.width - 100)
                gd_painter.drawImage(rx, random.randint(10, 30), dupe_layer, rx, 0, 100, self.height)
        elif self.current_mode == 4: 
            gd_painter.setOpacity(0.7)
            gd_painter.drawImage(15, 0, dupe_layer)
            gd_painter.drawImage(-15, 0, dupe_layer)
        else: 
            gd_painter.drawImage(0, 0, dupe_layer)
            
        if self.iteration % 2 == 0:
            gd_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
            random_color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 180)
            gd_painter.fillRect(glitched_dupe_layer.rect(), random_color)
            
        gd_painter.end()

        painter.drawImage(0, 0, glitched_dupe_layer)

        local_mouse = self.mapFromGlobal(QCursor.pos())
        painter.drawPixmap(local_mouse.x() - offset, local_mouse.y() - offset, self.mouse_pixmap)

def main():
    app = QApplication(sys.argv)
    window = CombinedGlitchSimulation()
    window.showFullScreen()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()