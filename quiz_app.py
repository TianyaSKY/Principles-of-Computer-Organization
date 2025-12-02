import tkinter as tk
from tkinter import messagebox
import json

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("计算机组成原理刷题系统 v2.0")
        self.root.geometry("900x700") # 加大窗口尺寸，防止内容展示不全

        # --- 数据初始化 ---
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.user_answer_var = tk.StringVar()
        
        # 记录每道题的状态列表：None=未答, 'correct'=正确, 'wrong'=错误
        self.question_status = [] 

        # --- 加载数据 ---
        self.load_data()

        # --- 界面布局 ---
        self.setup_ui()

        # --- 启动 ---
        if self.questions:
            self.show_question()
        else:
            messagebox.showerror("错误", "题库加载失败或为空！")

    def load_data(self):
        """读取JSON文件并初始化状态列表"""
        try:
            with open("questions.json", "r", encoding="utf-8") as f:
                self.questions = json.load(f)
                # 初始化状态列表，长度与题目数量一致，初始全为 None
                self.question_status = [None] * len(self.questions)
        except FileNotFoundError:
            self.questions = []
            messagebox.showerror("错误", "找不到 questions.json 文件，请确保它和程序在同一目录下。")
        except Exception as e:
            self.questions = []
            messagebox.showerror("错误", f"读取文件出错: {e}")

    def setup_ui(self):
        """构建主界面"""
        # 1. 顶部功能区 (状态 + 预览按钮)
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=20, pady=10)

        self.status_label = tk.Label(top_frame, text="", font=("微软雅黑", 10))
        self.status_label.pack(side="left")

        btn_preview = tk.Button(top_frame, text="📅 题目概览 / 跳转", command=self.open_question_board, bg="#2196F3", fg="white", font=("微软雅黑", 10, "bold"))
        btn_preview.pack(side="right")

        # --- 中间主要内容区 (用于控制整体边距) ---
        main_content = tk.Frame(self.root)
        main_content.pack(fill="both", expand=True, padx=40, pady=10)

        # 2. 题型标签 (固定在左上角)
        self.type_label = tk.Label(main_content, text="", font=("微软雅黑", 12, "bold"), fg="#1976D2")
        self.type_label.pack(anchor="w", pady=(0, 5))

        # 3. 题目文本显示区域 (左对齐，自动换行)
        self.question_label = tk.Label(
            main_content, 
            text="", 
            font=("微软雅黑", 14), 
            wraplength=820,  # 增加换行宽度
            justify="left"   # 文本左对齐
        )
        self.question_label.pack(anchor="w", fill="x", pady=(0, 20))

        # 4. 选项区域 (动态内容)
        self.options_frame = tk.Frame(main_content)
        self.options_frame.pack(fill="both", expand=True)

        # 5. 反馈信息区域
        self.feedback_label = tk.Label(self.root, text="", font=("微软雅黑", 12))
        self.feedback_label.pack(pady=5)

        # 6. 底部控制按钮
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=20)

        self.prev_btn = tk.Button(bottom_frame, text="< 上一题", command=self.prev_question, width=12, font=("微软雅黑", 10))
        self.prev_btn.pack(side="left", padx=10)

        self.submit_btn = tk.Button(bottom_frame, text="提交答案", command=self.check_answer, bg="#4CAF50", fg="white", width=12, font=("微软雅黑", 10, "bold"))
        self.submit_btn.pack(side="left", padx=10)

        self.next_btn = tk.Button(bottom_frame, text="下一题 >", command=self.next_question, width=12, font=("微软雅黑", 10))
        self.next_btn.pack(side="left", padx=10)

    def show_question(self):
        """核心逻辑：渲染当前题目"""
        q_data = self.questions[self.current_index]
        
        # 1. 更新顶部状态栏
        answered_count = sum(1 for s in self.question_status if s is not None)
        self.status_label.config(text=f"当前第 {self.current_index + 1} 题 / 共 {len(self.questions)} 题 | 累计得分: {self.score} | 已完成: {answered_count}")
        
        # 2. 显示题目类型 (左上角)
        q_type_map = {"single_choice": "选择题", "true_false": "判断题", "fill_in": "填空题"}
        q_type_cn = q_type_map.get(q_data['type'], "题目")
        self.type_label.config(text=f"【{q_type_cn}】")

        # 3. 显示题目内容 (仅显示题干)
        self.question_label.config(text=q_data['question'])
        
        # 4. 清空旧选项
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        self.user_answer_var.set("")
        self.feedback_label.config(text="")

        # 5. 检查当前题目的历史状态（是否做过）
        status = self.question_status[self.current_index]
        is_answered = status is not None

        # 6. 渲染选项
        if q_data['type'] in ["single_choice", "true_false"]:
            for option in q_data['options']:
                # 智能提取选项值 (例如 "A. 内容" -> "A")
                val = option
                if "." in option:
                    val = option.split(".")[0].strip()
                elif "(" in option:  # 处理 (T) 这种格式
                    try:
                        val = option.split("(")[1].split(")")[0].strip()
                    except:
                        val = option[0] # 兜底

                rb = tk.Radiobutton(self.options_frame, text=option, variable=self.user_answer_var, value=val, font=("微软雅黑", 12), anchor="w")
                rb.pack(fill="x", pady=5)
                
                # 如果做过，禁用选项
                if is_answered:
                    rb.config(state="disabled")
                    
        elif q_data['type'] == "fill_in":
            entry = tk.Entry(self.options_frame, textvariable=self.user_answer_var, font=("微软雅黑", 12))
            entry.pack(pady=10, fill="x") # 填空框拉长
            if is_answered:
                entry.config(state="disabled")
        
        # 7. 恢复界面状态（根据是否做过）
        if is_answered:
            self.submit_btn.config(state="disabled", text="已作答", bg="gray")
            if status == 'correct':
                self.feedback_label.config(text="✅ 回答正确", fg="green")
            else:
                self.feedback_label.config(text=f"❌ 回答错误。正确答案是: {q_data['answer']}", fg="red")
        else:
            self.submit_btn.config(state="normal", text="提交答案", bg="#4CAF50")
            
        # 8. 控制翻页按钮可用性
        self.prev_btn.config(state="normal" if self.current_index > 0 else "disabled")
        self.next_btn.config(state="normal" if self.current_index < len(self.questions) - 1 else "disabled")

    def check_answer(self):
        """验证答案逻辑"""
        user_ans = self.user_answer_var.get().strip()
        
        if not user_ans:
            messagebox.showwarning("提示", "请先输入或选择一个答案！")
            return
            
        q_data = self.questions[self.current_index]
        correct_ans = str(q_data['answer']).strip()
        
        # 简单的大小写不敏感比对
        is_correct = user_ans.upper() == correct_ans.upper()
        
        if is_correct:
            self.score += 10
            self.question_status[self.current_index] = 'correct'
            self.feedback_label.config(text="✅ 回答正确！+10分", fg="green")
        else:
            self.question_status[self.current_index] = 'wrong'
            self.feedback_label.config(text=f"❌ 回答错误。\n正确答案是: {correct_ans}", fg="red")
            
        # 提交后刷新页面以锁定状态
        self.show_question()

    def prev_question(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()

    def next_question(self):
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.show_question()

    def open_question_board(self):
        """打开题目预览/跳转窗口"""
        board = tk.Toplevel(self.root)
        board.title("题目概览 (点击题号跳转)")
        board.geometry("650x450")
        
        # 使用 Canvas + Scrollbar 实现滚动，防止题目太多显示不全
        canvas = tk.Canvas(board)
        scrollbar = tk.Scrollbar(board, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- 图例说明 ---
        legend_frame = tk.Frame(scroll_frame)
        legend_frame.pack(fill="x", pady=10, padx=10)
        tk.Label(legend_frame, text="图例说明: ").pack(side="left")
        tk.Label(legend_frame, text=" ⬜ 未作答 ", bg="#f0f0f0", relief="solid", bd=1).pack(side="left", padx=5)
        tk.Label(legend_frame, text=" 🟩 正确 ", bg="#90EE90", relief="solid", bd=1).pack(side="left", padx=5)
        tk.Label(legend_frame, text=" 🟥 错误 ", bg="#FFB6C1", relief="solid", bd=1).pack(side="left", padx=5)
        tk.Label(legend_frame, text=" 🟦 当前题 ", bg="#2196F3", fg="white", relief="solid", bd=1).pack(side="left", padx=5)

        # --- 题目网格 ---
        grid_frame = tk.Frame(scroll_frame)
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = 10 # 每行显示10个题号
        for i, status in enumerate(self.question_status):
            # 确定颜色
            bg_color = "#f0f0f0" # 默认灰白
            fg_color = "black"
            
            if i == self.current_index:
                bg_color = "#2196F3" # 当前题目高亮蓝
                fg_color = "white"
            elif status == 'correct':
                bg_color = "#90EE90" # 浅绿
            elif status == 'wrong':
                bg_color = "#FFB6C1" # 浅红
            
            btn = tk.Button(grid_frame, text=f"{i+1}", bg=bg_color, fg=fg_color, width=4, height=2,
                            command=lambda idx=i: self.jump_and_close(board, idx))
            btn.grid(row=i//columns, column=i%columns, padx=3, pady=3)

    def jump_and_close(self, window, index):
        """跳转并关闭预览窗口"""
        self.current_index = index
        self.show_question()
        window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()