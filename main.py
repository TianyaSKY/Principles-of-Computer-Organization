import sys
import json
import sqlite3  # [新增] 导入sqlite3
import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QRadioButton, 
                               QLineEdit, QButtonGroup, QMessageBox, QScrollArea, 
                               QDialog, QGridLayout, QFrame, QFileDialog)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QKeyEvent

class QuizApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("计算机组成原理刷题系统 v4.0 (数据库版)")
        self.resize(1000, 700)

        # --- 数据初始化 ---
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.question_status = [] 
        self.user_answers_log = {} 
        self.block_key_jump = False
        
        # 字体设置
        self.font_title = QFont("Microsoft YaHei", 12, QFont.Bold)
        self.font_text = QFont("Microsoft YaHei", 12)
        self.font_option = QFont("Microsoft YaHei", 11)

        # --- 加载数据 ---
        self.load_data()

        # --- 界面布局初始化 ---
        self.setup_ui()

        # --- 启动 ---
        if self.questions:
            self.show_question()
        else:
            QMessageBox.critical(self, "错误", "题库加载失败！请确保 'quiz.db' 文件存在。")

    def load_data(self):
        """[修改] 从 SQLite 数据库读取题目"""
        try:
            # 连接数据库
            conn = sqlite3.connect("quiz.db")
            cursor = conn.cursor()
            
            # 查询所有题目
            cursor.execute("SELECT id, type, question, options, answer FROM questions ORDER BY id")
            rows = cursor.fetchall()
            
            self.questions = []
            
            for row in rows:
                # 数据库取出的 options 是 JSON 字符串，需要转回 Python 列表
                options_list = json.loads(row[3]) if row[3] else []
                
                # 构造字典，保持与原有逻辑兼容
                q_data = {
                    "id": row[0],
                    "type": row[1],
                    "question": row[2],
                    "options": options_list,
                    "answer": row[4]
                }
                self.questions.append(q_data)
                
            conn.close()
            
            # 初始化状态列表
            self.question_status = [None] * len(self.questions)
            
            if not self.questions:
                raise ValueError("数据库中没有题目数据")

        except sqlite3.Error as e:
            self.questions = []
            QMessageBox.critical(self, "数据库错误", f"无法读取数据库: {e}\n请先运行 init_db.py")
        except Exception as e:
            self.questions = []
            QMessageBox.critical(self, "错误", f"加载数据出错: {e}")

    def setup_ui(self):
        """构建主界面 UI (保持不变)"""
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主垂直布局
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(30, 20, 30, 20)
        self.main_layout.setSpacing(15)

        # 1. 顶部栏 (状态 + 导出按钮 + 跳转按钮)
        top_layout = QHBoxLayout()
        
        self.status_label = QLabel("加载中...")
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        self.status_label.setStyleSheet("color: #555;")
        
        # 导出按钮
        self.btn_export = QPushButton("📂 导出错题报告")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; 
                color: white; 
                border-radius: 5px; 
                padding: 8px 15px; 
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.btn_export.clicked.connect(self.export_error_report)

        # 概览按钮
        self.btn_preview = QPushButton("📅 题目概览 / 跳转")
        self.btn_preview.setCursor(Qt.PointingHandCursor)
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; 
                color: white; 
                border-radius: 5px; 
                padding: 8px 15px; 
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.btn_preview.clicked.connect(self.open_question_board)

        top_layout.addWidget(self.status_label)
        top_layout.addStretch() 
        top_layout.addWidget(self.btn_export)
        top_layout.addWidget(self.btn_preview)
        
        self.main_layout.addLayout(top_layout)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.main_layout.addWidget(line)

        # 2. 题目类型标签
        self.type_label = QLabel("")
        self.type_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.type_label.setStyleSheet("color: #1976D2; margin-top: 10px;")
        self.main_layout.addWidget(self.type_label)

        # 3. 题目内容
        self.question_label = QLabel("")
        self.question_label.setFont(self.font_title)
        self.question_label.setWordWrap(True)
        self.question_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.question_label.setStyleSheet("padding-bottom: 10px;")
        
        question_scroll = QScrollArea()
        question_scroll.setWidgetResizable(True)
        question_scroll.setWidget(self.question_label)
        question_scroll.setFrameShape(QFrame.NoFrame)
        question_scroll.setFixedHeight(120)
        
        self.main_layout.addWidget(question_scroll)

        # 4. 选项区域
        self.options_widget = QWidget()
        self.options_layout = QVBoxLayout(self.options_widget)
        self.options_layout.setContentsMargins(10, 0, 0, 0)
        self.options_layout.setAlignment(Qt.AlignTop)
        
        self.options_scroll = QScrollArea()
        self.options_scroll.setWidgetResizable(True)
        self.options_scroll.setWidget(self.options_widget)
        self.options_scroll.setFrameShape(QFrame.NoFrame)
        
        self.main_layout.addWidget(self.options_scroll)

        # 5. 反馈区域
        self.feedback_label = QLabel("")
        self.feedback_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setFixedHeight(40)
        self.main_layout.addWidget(self.feedback_label)

        # 6. 底部按钮
        bottom_layout = QHBoxLayout()
        
        self.btn_prev = QPushButton("< 上一题")
        self.btn_submit = QPushButton("提交答案")
        self.btn_next = QPushButton("下一题 >")

        btn_style = """
            QPushButton {
                background-color: #f0f0f0; 
                border: 1px solid #ccc; 
                border-radius: 5px; 
                padding: 10px 20px;
                font-family: "Microsoft YaHei";
                font-size: 14px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:disabled { color: #999; background-color: #f9f9f9; }
        """
        submit_style = """
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                border-radius: 5px; 
                padding: 10px 20px;
                font-family: "Microsoft YaHei";
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; color: #666; }
        """

        self.btn_prev.setStyleSheet(btn_style)
        self.btn_next.setStyleSheet(btn_style)
        self.btn_submit.setStyleSheet(submit_style)
        self.btn_submit.setCursor(Qt.PointingHandCursor)

        self.btn_prev.clicked.connect(self.prev_question)
        self.btn_next.clicked.connect(self.next_question)
        self.btn_submit.clicked.connect(self.check_answer)

        bottom_layout.addWidget(self.btn_prev)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_submit)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_next)

        self.main_layout.addLayout(bottom_layout)

        # 变量存储
        self.current_button_group = None 
        self.input_field = None 

    def show_question(self):
        """渲染题目逻辑"""
        q_data = self.questions[self.current_index]
        
        # 更新顶部状态
        answered_count = sum(1 for s in self.question_status if s is not None)
        self.status_label.setText(f"当前第 {self.current_index + 1} 题 / 共 {len(self.questions)} 题   |   得分: {self.score}   |   已完成: {answered_count}")

        # 显示题型
        q_type_map = {
            "single_choice": "选择题", 
            "true_false": "判断题", 
            "fill_in": "填空题",
            "fill_in_the_blank": "填空题" # 兼容旧数据
        }
        self.type_label.setText(f"【{q_type_map.get(q_data['type'], '题目')}】")

        # 显示题目
        self.question_label.setText(q_data['question'])

        # 清空旧控件
        self.clear_layout(self.options_layout)
        self.current_button_group = None
        self.input_field = None
        self.feedback_label.setText("")

        # 检查状态
        status = self.question_status[self.current_index]
        is_answered = status is not None

        # 渲染选项
        if q_data['type'] in ["single_choice", "true_false"]:
            self.current_button_group = QButtonGroup(self)
            
            for idx, option in enumerate(q_data['options']):
                val = option
                if "." in option:
                    val = option.split(".")[0].strip()
                elif "(" in option:
                    try:
                        val = option.split("(")[1].split(")")[0].strip()
                    except:
                        val = option[0]

                rb = QRadioButton(option)
                rb.setFont(self.font_option)
                rb.setProperty("value", val)
                rb.setStyleSheet("padding: 5px;")
                
                self.options_layout.addWidget(rb)
                self.current_button_group.addButton(rb, idx)
                
                if is_answered:
                    rb.setEnabled(False)
                    user_val = self.user_answers_log.get(self.current_index)
                    if user_val and str(val).upper() == str(user_val).upper():
                        rb.setChecked(True)
            
            self.options_layout.addStretch()

        elif q_data['type'] in ["fill_in", "fill_in_the_blank"]:
            self.input_field = QLineEdit()
            self.input_field.setFont(self.font_text)
            self.input_field.setPlaceholderText("请输入答案...")
            self.input_field.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px;")
            self.options_layout.addWidget(self.input_field)
            self.options_layout.addStretch()

            if is_answered:
                self.input_field.setEnabled(False)
                # 恢复填空题的显示
                user_val = self.user_answers_log.get(self.current_index, "")
                self.input_field.setText(user_val)
            else:
                self.input_field.setFocus()
                self.input_field.returnPressed.connect(self.check_answer)

        # 恢复状态
        if is_answered:
            self.btn_submit.setText("已作答")
            self.btn_submit.setEnabled(False)
            if status == 'correct':
                self.feedback_label.setText("✅ 回答正确")
                self.feedback_label.setStyleSheet("color: green;")
            else:
                self.feedback_label.setText(f"❌ 回答错误。正确答案是: {q_data['answer']}")
                self.feedback_label.setStyleSheet("color: red;")
        else:
            self.btn_submit.setText("提交答案")
            self.btn_submit.setEnabled(True)

        self.btn_prev.setEnabled(self.current_index > 0)
        self.btn_next.setEnabled(self.current_index < len(self.questions) - 1)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self.block_key_jump:
                return
            if self.btn_submit.isEnabled():
                if not (self.input_field and self.input_field.hasFocus()):
                    self.check_answer()
            elif self.btn_next.isEnabled():
                self.next_question()
            return

        if self.btn_submit.isEnabled():
            q_data = self.questions[self.current_index]
            target_val = None

            if q_data['type'] == "single_choice":
                if key == Qt.Key_A: target_val = "A"
                elif key == Qt.Key_B: target_val = "B"
                elif key == Qt.Key_C: target_val = "C"
                elif key == Qt.Key_D: target_val = "D"

            elif q_data['type'] == "true_false":
                if key == Qt.Key_T: target_val = "T"
                elif key == Qt.Key_F: target_val = "F"
            
            if target_val and self.current_button_group:
                for btn in self.current_button_group.buttons():
                    if str(btn.property("value")).upper() == target_val:
                        btn.setChecked(True)
                        btn.setFocus()
                        break

        super().keyPressEvent(event)

    def check_answer(self):
        user_ans = ""
        q_data = self.questions[self.current_index]

        if q_data['type'] in ["single_choice", "true_false"]:
            checked_btn = self.current_button_group.checkedButton()
            if not checked_btn:
                QMessageBox.warning(self, "提示", "请先选择一个选项！")
                return
            user_ans = checked_btn.property("value")
        
        elif q_data['type'] in ["fill_in", "fill_in_the_blank"]:
            user_ans = self.input_field.text().strip()
            if not user_ans:
                QMessageBox.warning(self, "提示", "请输入答案！")
                return

        # 记录用户的原始答案
        self.user_answers_log[self.current_index] = user_ans

        correct_ans = str(q_data['answer']).strip()
        is_correct = user_ans.upper() == correct_ans.upper()

        if is_correct:
            self.score += 10
            self.question_status[self.current_index] = 'correct'
            self.feedback_label.setText("✅ 回答正确！+10分")
            self.feedback_label.setStyleSheet("color: green;")
        else:
            self.question_status[self.current_index] = 'wrong'
            self.feedback_label.setText(f"❌ 回答错误。正确答案是: {correct_ans}")
            self.feedback_label.setStyleSheet("color: red;")
        self.block_key_jump = True
        QTimer.singleShot(500, lambda: setattr(self, 'block_key_jump', False))
        self.show_question()

    def prev_question(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()

    def next_question(self):
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.show_question()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def open_question_board(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("题目概览 (点击题号跳转)")
        dialog.resize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("图例:"))
        
        def create_legend(text, color, fg="black"):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"background-color: {color}; color: {fg}; border: 1px solid #ccc; padding: 2px 5px;")
            return lbl

        legend_layout.addWidget(create_legend("未作答", "#f0f0f0"))
        legend_layout.addWidget(create_legend("正确", "#90EE90"))
        legend_layout.addWidget(create_legend("错误", "#FFB6C1"))
        legend_layout.addWidget(create_legend("当前题", "#2196F3", "white"))
        legend_layout.addStretch()
        
        layout.addLayout(legend_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        grid = QGridLayout(content_widget)
        grid.setSpacing(5)
        
        cols = 10
        for i, status in enumerate(self.question_status):
            btn = QPushButton(str(i + 1))
            btn.setFixedSize(50, 35)
            
            bg_color = "#f0f0f0"
            fg_color = "black"
            border = "1px solid #ccc"
            
            if i == self.current_index:
                bg_color = "#2196F3"
                fg_color = "white"
                border = "1px solid #1976D2"
            elif status == 'correct':
                bg_color = "#90EE90"
            elif status == 'wrong':
                bg_color = "#FFB6C1"
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {fg_color};
                    border: {border};
                    border-radius: 3px;
                }}
                QPushButton:hover {{ filter: brightness(90%); }}
            """)
            
            btn.clicked.connect(lambda checked=False, idx=i: [self.jump_to(idx), dialog.close()])
            
            grid.addWidget(btn, i // cols, i % cols)
            
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        dialog.exec()

    def jump_to(self, index):
        self.current_index = index
        self.show_question()

    def export_error_report(self):
        """导出错题报告逻辑"""
        wrong_indices = [i for i, status in enumerate(self.question_status) if status == 'wrong']
        
        if not wrong_indices:
            QMessageBox.information(self, "棒棒哒", "目前没有错题！\n请继续加油或检查是否还未开始答题。")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"错题本_{timestamp}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(self, "保存错题报告", default_filename, "Text Files (*.txt);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"=== 计算机组成原理错题报告 ===\n")
                    f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"错题数量: {len(wrong_indices)}\n")
                    f.write("=" * 30 + "\n\n")

                    for idx in wrong_indices:
                        q = self.questions[idx]
                        user_ans = self.user_answers_log.get(idx, "未记录")
                        
                        f.write(f"【第 {idx + 1} 题】 ({q['type']})\n")
                        f.write(f"题目: {q['question']}\n")
                        
                        if q['type'] in ["single_choice", "true_false"]:
                            f.write("选项:\n")
                            for opt in q['options']:
                                f.write(f"  {opt}\n")
                        
                        f.write(f"❌ 你的答案: {user_ans}\n")
                        f.write(f"✅ 正确答案: {q['answer']}\n")
                        f.write("-" * 30 + "\n\n")
                        
                QMessageBox.information(self, "成功", f"错题报告已保存至:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"保存文件时出错:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow { background-color: white; }
        QScrollArea { background-color: transparent; border: none; }
        QRadioButton { spacing: 8px; }
        QRadioButton::indicator { width: 16px; height: 16px; }
    """)
    window = QuizApp()
    window.show()
    sys.exit(app.exec())