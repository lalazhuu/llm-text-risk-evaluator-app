import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QSplitter, QPushButton,
    QGroupBox, QFormLayout, QFrame, QTextEdit
)
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QBrush, QPen, QFont
from PyQt6.QtCore import Qt, QSize

MOCK_DATA = [
    {
        "name": "智能降噪耳机 Pro",
        "risk_level": "low",
        "score": 8,
        "tooltip": "文本可信度较高",
        "dimensions": {
            "过度宣传与情感偏见": "低风险 (2/10)",
            "信息一致性与事实核验": "低风险 (1/10)",
            "文本原创性与异常模式": "低风险 (2/10)",
            "细节缺乏与模糊性": "低风险 (1/10)"
        },
        "tags": ["描述与规格基本一致"],
        "description": "采用最新降噪技术，提供沉浸式音频体验。电池续航20小时。"
    },
    {
        "name": "“全能”家用清洁机器人 X1",
        "risk_level": "medium",
        "score": 6,
        "tooltip": "文本可能存在过度宣传",
        "dimensions": {
            "过度宣传与情感偏见": "高风险 (7/10)",
            "信息一致性与事实核验": "低风险 (2/10)",
            "文本原创性与异常模式": "中等风险 (5/10)",
            "细节缺乏与模糊性": "中等风险 (4/10)"
        },
        "tags": ["检测到多个极端积极词汇", "与同类产品描述相似度较高"],
        "description": "革命性的清洁方案！轻松搞定所有地面，智能路径规划，简直完美！"
    },
    {
        "name": "神秘能量手环",
        "risk_level": "high",
        "score": 3,
        "tooltip": "文本风险较高，请谨慎判断",
        "dimensions": {
            "过度宣传与情感偏见": "高风险 (8/10)",
            "信息一致性与事实核验": "高风险 (7/10)",
            "文本原创性与异常模式": "低风险 (3/10)",
            "细节缺乏与模糊性": "高风险 (9/10)"
        },
        "tags": ["描述与已知信息存在冲突", "关键功能描述模糊", "缺乏可验证细节"],
        "description": "佩戴即刻感受宇宙能量！改善健康，提升运势，效果惊人！全球限量。"
    },
    {
        "name": "经典款纯棉T恤",
        "risk_level": "low",
        "score": 9,
        "tooltip": "文本可信度很高",
         "dimensions": {
            "过度宣传与情感偏见": "低风险 (1/10)",
            "信息一致性与事实核验": "低风险 (0/10)",
            "文本原创性与异常模式": "低风险 (1/10)",
            "细节缺乏与模糊性": "低风险 (0/10)"
        },
        "tags": ["描述清晰具体"],
        "description": "100%纯棉材质，舒适透气。经典圆领设计，多种颜色可选。尺码 S-XXL。"
    }
]

def create_risk_icon(level):
    size = 16
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if level == "low":
        color = QColor("green")
    elif level == "medium":
        color = QColor("orange")
    elif level == "high":
        color = QColor("red")
    else:
        color = QColor("gray")

    painter.setBrush(QBrush(color))
    painter.setPen(QPen(Qt.GlobalColor.darkGray, 1))
    margin = 2
    painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)
    painter.end()
    return QIcon(pixmap)

class RiskAssessmentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文本可信度与风险评估")
        self.setGeometry(100, 100, 900, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self.display_item_details)
        self.splitter.addWidget(self.list_widget)

        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.splitter.addWidget(self.detail_widget)

        self.splitter.setSizes([300, 600])

        self.item_name_label = QLabel("请选择一个物品查看详情")
        font = self.item_name_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.item_name_label.setFont(font)
        self.detail_layout.addWidget(self.item_name_label)

        self.item_description_label = QTextEdit()
        self.item_description_label.setReadOnly(True)
        self.item_description_label.setMaximumHeight(100)
        self.detail_layout.addWidget(QLabel("物品描述:"))
        self.detail_layout.addWidget(self.item_description_label)

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        self.detail_layout.addWidget(line1)

        assessment_group = QGroupBox("文本可信度与风险评估")
        assessment_layout = QVBoxLayout(assessment_group)
        self.detail_layout.addWidget(assessment_group)

        self.overall_risk_label = QLabel("风险等级: -")
        self.score_label = QLabel("可信度评分: - / 10")
        assessment_layout.addWidget(self.overall_risk_label)
        assessment_layout.addWidget(self.score_label)

        self.dimension_group = QGroupBox("维度风险剖析:")
        self.dimension_layout = QFormLayout(self.dimension_group)
        assessment_layout.addWidget(self.dimension_group)

        self.tags_group = QGroupBox("具体风险标签:")
        self.tags_layout = QVBoxLayout(self.tags_group)
        assessment_layout.addWidget(self.tags_group)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        self.detail_layout.addWidget(line2)

        feedback_group = QGroupBox("评估反馈")
        feedback_layout = QHBoxLayout(feedback_group)
        self.detail_layout.addWidget(feedback_group)

        self.accurate_button = QPushButton("评估准确 👍")
        self.inaccurate_button = QPushButton("评估不准 👎")
        self.report_button = QPushButton("报告可疑文本")

        self.accurate_button.clicked.connect(self.feedback_accurate)
        self.inaccurate_button.clicked.connect(self.feedback_inaccurate)
        self.report_button.clicked.connect(self.report_suspicious)

        feedback_layout.addWidget(self.accurate_button)
        feedback_layout.addWidget(self.inaccurate_button)
        feedback_layout.addStretch()
        feedback_layout.addWidget(self.report_button)

        self.detail_layout.addStretch()

        self.populate_list()

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def populate_list(self):
        self.list_widget.clear()
        for index, item_data in enumerate(MOCK_DATA):
            list_item = QListWidgetItem()
            list_item.setText(item_data["name"])
            list_item.setIcon(create_risk_icon(item_data["risk_level"]))
            list_item.setToolTip(item_data["tooltip"])
            list_item.setData(Qt.ItemDataRole.UserRole, index)
            self.list_widget.addItem(list_item)

    def display_item_details(self, current_item, previous_item):
        if not current_item:
            self.item_name_label.setText("请选择一个物品查看详情")
            self.item_description_label.setText("")
            self.overall_risk_label.setText("风险等级: -")
            self.score_label.setText("可信度评分: - / 10")
            while self.dimension_layout.count():
                child = self.dimension_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            while self.tags_layout.count():
                 child = self.tags_layout.takeAt(0)
                 if child.widget():
                    child.widget().deleteLater()
            return

        item_index = current_item.data(Qt.ItemDataRole.UserRole)
        item_data = MOCK_DATA[item_index]

        self.item_name_label.setText(item_data["name"])
        self.item_description_label.setText(item_data.get("description", "N/A"))

        risk_text = {
            "low": "低风险", "medium": "中等风险", "high": "高风险"
        }.get(item_data["risk_level"], "未知")
        self.overall_risk_label.setText(f"风险等级: {risk_text}")
        self.score_label.setText(f"可信度评分: {item_data['score']} / 10")

        while self.dimension_layout.count():
            child = self.dimension_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        for dim_name, dim_value in item_data["dimensions"].items():
            self.dimension_layout.addRow(QLabel(f"{dim_name}:"), QLabel(dim_value))

        while self.tags_layout.count():
             child = self.tags_layout.takeAt(0)
             if child.widget():
                child.widget().deleteLater()
        if item_data["tags"]:
            for tag in item_data["tags"]:
                tag_label = QLabel(f"- {tag}")
                self.tags_layout.addWidget(tag_label)
        else:
             self.tags_layout.addWidget(QLabel("- 无特定风险标签"))


    def feedback_accurate(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            item_index = current_item.data(Qt.ItemDataRole.UserRole)
            item_name = MOCK_DATA[item_index]['name']
            print(f"用户反馈: 对 '{item_name}' 的评估准确 👍")
        else:
            print("用户反馈: (未选择物品)")

    def feedback_inaccurate(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            item_index = current_item.data(Qt.ItemDataRole.UserRole)
            item_name = MOCK_DATA[item_index]['name']
            print(f"用户反馈: 对 '{item_name}' 的评估不准确 👎")
        else:
            print("用户反馈: (未选择物品)")

    def report_suspicious(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            item_index = current_item.data(Qt.ItemDataRole.UserRole)
            item_name = MOCK_DATA[item_index]['name']
            print(f"用户报告: 认为 '{item_name}' 的文本可疑 (即使系统未标记高风险)")
        else:
             print("用户报告: (未选择物品)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RiskAssessmentApp()
    window.show()
    sys.exit(app.exec())