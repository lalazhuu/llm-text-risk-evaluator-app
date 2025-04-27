import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QSplitter, QPushButton,
    QGroupBox, QFormLayout, QFrame, QTextEdit, QMessageBox,
    QSizePolicy
)
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QBrush, QPen, QFont
from PyQt6.QtCore import Qt, QSize

try:
    from text_risk_evaluator import TextRiskEvaluator
except ImportError:
    print("错误：找不到 text_risk_evaluator.py。请确保它与 main_app.py 在同一目录下。")
    class TextRiskEvaluator:
        def __init__(self, *args, **kwargs): pass
        def assess(self, *args, **kwargs):
            print("警告：TextRiskEvaluator 未能加载，将使用虚拟数据。")
            return {
                'overall_score': 0,
                'dimension_risks': {},
                'risk_labels': ["评估器加载失败"],
                'raw_sentiment': 0.0
            }

PRODUCT_SOURCE_DATA = [
    {
        "name": "智能降噪耳机 Pro",
        "item_text": "采用最新主动降噪技术，有效隔绝环境噪音，提供沉浸式纯净音频体验。人体工学设计，佩戴舒适。单次充电可提供长达20小时的播放时间。支持蓝牙5.2快速连接。",
        "item_metadata": {"category": "Electronics", "price": 899.00, "specs": {"color": "星空灰", "battery_life_hours": 20, "bluetooth": "5.2"}},
        "historical_texts": ["新款降噪耳机，提供沉浸式体验，续航20小时。"],
        "similar_item_texts": [
            "体验极致降噪，享受音乐本真。XX品牌耳机，续航18小时。",
            "高性能无线耳机，智能降噪，舒适佩戴。",
            "专注于音质，主动降噪耳机，电池耐用。"
        ]
    },
    {
        "name": "“全能王”家用清洁机器人 X1",
        "item_text": "革命性的家庭清洁解决方案！这款全能王机器人简直是完美！能轻松搞定地毯、地板等所有地面。智能路径规划，覆盖无死角。绝对是现代家庭的必备神器！效果惊人！",
        "item_metadata": {"category": "Electronics", "price": 2599.00, "specs": {"function": "扫拖一体", "navigation": "LDS激光导航"}},
        "historical_texts": ["新型扫地机器人，智能规划路径。"],
        "similar_item_texts": [
            "智能扫拖机器人，解放双手，高效清洁。",
            "XX扫地机，激光导航，弓字形清扫。",
            "家用全自动清洁器，适用于多种地面。"
        ]
    },
    {
        "name": "神秘量子能量手环",
        "item_text": "快来佩戴这款独一无二的神秘量子能量手环，即刻感受源自宇宙深处的强大能量！它能显著改善您的健康状况，提升个人运势，带来难以置信的好运！效果保证，无与伦比！全球限量发售，机会难得！",
        "item_metadata": {"category": "Accessories", "price": 1999.00, "specs": {"material": "未知特殊材质"}},
        "historical_texts": ["能量手环，改善健康。"],
        "similar_item_texts": [
            "健康磁力手链，促进血液循环。",
            "平衡能量项链，带来身心和谐。",
            "稀有宝石手串，据说有特殊功效。"
        ]
    },
    {
        "name": "经典款纯棉T恤 (多色)",
        "item_text": "基础款男士圆领T恤。选用100%优质长绒棉，面料柔软亲肤，吸湿透气性好，穿着舒适。经典合身版型，不易变形。提供黑色、白色、灰色、藏青色等多种颜色选择。尺码范围：S-XXL。",
        "item_metadata": {"category": "Apparel", "price": 79.00, "specs": {"material": "100%棉", "neck_style": "圆领", "colors": ["黑", "白", "灰", "藏青"], "sizes": ["S", "M", "L", "XL", "XXL"]}},
        "historical_texts": ["纯棉T恤，多色可选。"],
        "similar_item_texts": [
            "夏季男士纯色T恤，舒适透气。",
            "基础款棉质上衣，适合日常穿着。",
            "圆领短袖T恤，简约百搭。"
        ]
    },
     {
        "name": "超高速SSD固态硬盘 1TB",
        "item_text": "体验闪电般的启动速度和文件传输！这款固态硬盘读取速度高达惊人的 5000MB/s。采用最新 NVMe 协议，性能卓越。容量1TB，足够存储大量游戏和文件。仅售 $599!",
        "item_metadata": {"category": "Electronics", "price": 799.00, "specs": {"capacity_gb": 1000, "interface": "NVMe PCIe 4.0", "read_speed_mbps": 3500}},
        "historical_texts": ["1TB NVMe SSD, 高速读写。"],
        "similar_item_texts": [
            "大容量固态硬盘，提升电脑性能。",
            "NVMe SSD，速度快，稳定性好。",
            "1TB 存储硬盘，适用于游戏和工作站。"
        ]
    }
]

def create_risk_icon(level):
    size = 16
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if level == "low":
        color = QColor("#2ECC71")
    elif level == "medium":
        color = QColor("#F39C12")
    elif level == "high":
        color = QColor("#E74C3C")
    else:
        color = QColor("gray")

    painter.setBrush(QBrush(color))
    painter.setPen(QPen(Qt.GlobalColor.darkGray, 1))
    margin = 2
    painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)
    painter.end()
    return QIcon(pixmap)

def map_score_to_level(score):
    if score >= 7.5:
        return "low"
    elif score >= 4.5:
        return "medium"
    else:
        return "high"

def format_dimension_risk(dim_risk_score):
    risk_scale_10 = round(dim_risk_score * 10)
    if risk_scale_10 <= 3:
        level_text = "低风险"
    elif risk_scale_10 <= 6:
        level_text = "中等风险"
    else:
        level_text = "高风险"
    return f"{level_text} ({risk_scale_10}/10)"


class RiskAssessmentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文本可信度与风险评估（集成版）")
        self.setGeometry(100, 100, 950, 650)

        category_baselines = {
            "Electronics": {"avg_sentiment": 0.4, "avg_length": 120},
            "Books": {"avg_sentiment": 0.6, "avg_length": 200},
            "Apparel": {"avg_sentiment": 0.3, "avg_length": 80},
            "Accessories": {"avg_sentiment": 0.2, "avg_length": 50}
        }
        self.evaluator = TextRiskEvaluator(category_baselines=category_baselines)
        self.processed_data = []
        self.load_and_assess_data()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget::item { padding: 5px; }")
        self.list_widget.currentItemChanged.connect(self.display_item_details)
        self.splitter.addWidget(self.list_widget)

        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setSpacing(5)
        self.detail_layout.setContentsMargins(10, 10, 10, 10)

        self.detail_widget.setStyleSheet("""
            QLabel { margin-bottom: 2px; }
            QGroupBox {
                margin-top: 4px;
                margin-bottom: 4px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px 0 3px;
                left: 10px;
            }
            """)
        self.splitter.addWidget(self.detail_widget)

        self.splitter.setSizes([350, 600])

        self.item_name_label = QLabel("请选择一个物品查看详情")
        font = self.item_name_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.item_name_label.setFont(font)
        self.item_name_label.setWordWrap(True)
        self.detail_layout.addWidget(self.item_name_label)

        self.item_description_label = QTextEdit()
        self.item_description_label.setReadOnly(True)
        self.item_description_label.setMaximumHeight(120)
        self.item_description_label.setFont(QFont("SimSun", 10))
        self.detail_layout.addWidget(QLabel("物品描述:"))
        self.detail_layout.addWidget(self.item_description_label)

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        self.detail_layout.addWidget(line1)

        assessment_group = QGroupBox("文本可信度与风险评估")
        assessment_layout = QVBoxLayout(assessment_group)
        self.detail_layout.addWidget(assessment_group)

        overall_layout = QHBoxLayout()
        self.overall_risk_label = QLabel("风险等级: -")
        self.score_label = QLabel("可信度评分: - / 10")
        font_bold = self.overall_risk_label.font()
        font_bold.setBold(True)
        self.overall_risk_label.setFont(font_bold)
        self.score_label.setFont(font_bold)
        self.overall_risk_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.score_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        overall_layout.addWidget(self.overall_risk_label)
        overall_layout.addStretch()
        overall_layout.addWidget(self.score_label)
        assessment_layout.addLayout(overall_layout)

        self.dimension_group = QGroupBox("维度风险剖析:")
        self.dimension_layout = QFormLayout(self.dimension_group)
        self.dimension_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.dimension_layout.setHorizontalSpacing(20)
        assessment_layout.addWidget(self.dimension_group)

        self.tags_group = QGroupBox("具体风险标签:")
        self.tags_layout = QVBoxLayout(self.tags_group)
        assessment_layout.addWidget(self.tags_group)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        self.detail_layout.addSpacing(5)
        self.detail_layout.addWidget(line2)
        self.detail_layout.addSpacing(5)

        feedback_group = QGroupBox("评估反馈")
        feedback_layout = QHBoxLayout(feedback_group)
        self.detail_layout.addWidget(feedback_group)

        self.accurate_button = QPushButton("评估准确 👍")
        self.inaccurate_button = QPushButton("评估不准 👎")
        self.report_button = QPushButton("进一步报告可疑文本")

        button_min_width = 130
        self.accurate_button.setMinimumWidth(button_min_width)
        self.inaccurate_button.setMinimumWidth(button_min_width)

        self.accurate_button.clicked.connect(self.feedback_accurate)
        self.inaccurate_button.clicked.connect(self.feedback_inaccurate)
        self.report_button.clicked.connect(self.report_suspicious)

        feedback_layout.addWidget(self.accurate_button)
        feedback_layout.addWidget(self.inaccurate_button)
        feedback_layout.addStretch()
        feedback_layout.addWidget(self.report_button)

        self.detail_layout.addStretch(1)

        self.populate_list()

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def load_and_assess_data(self):
        print("正在加载和评估产品数据...")
        self.processed_data = []
        for index, source_item in enumerate(PRODUCT_SOURCE_DATA):
            print(f"  评估物品: {source_item['name']}")
            try:
                assessment_result = self.evaluator.assess(
                    item_text=source_item.get("item_text", ""),
                    item_metadata=source_item.get("item_metadata"),
                    historical_texts=source_item.get("historical_texts"),
                    similar_item_texts=source_item.get("similar_item_texts")
                )

                processed_item = source_item.copy()
                processed_item['assessment'] = assessment_result
                processed_item['risk_level'] = map_score_to_level(assessment_result['overall_score'])

                if assessment_result['risk_labels']:
                     processed_item['tooltip'] = f"评分 {assessment_result['overall_score']}/10 | 主要风险: {assessment_result['risk_labels'][0]}"
                else:
                    processed_item['tooltip'] = f"评分 {assessment_result['overall_score']}/10 | 无明显风险标签"

                self.processed_data.append(processed_item)

            except Exception as e:
                print(f"错误：评估物品 '{source_item['name']}' 时出错: {e}")
                processed_item = source_item.copy()
                processed_item['assessment'] = {'overall_score': 0, 'dimension_risks': {}, 'risk_labels': [f'评估出错: {e}'], 'raw_sentiment': None}
                processed_item['risk_level'] = 'high'
                processed_item['tooltip'] = '评估过程中发生错误'
                self.processed_data.append(processed_item)

        print("数据评估完成。")


    def populate_list(self):
        self.list_widget.clear()
        if not self.processed_data:
             error_item = QListWidgetItem("未能加载或评估产品数据")
             error_item.setIcon(create_risk_icon('high'))
             self.list_widget.addItem(error_item)
             error_item.setFlags(error_item.flags() & ~Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsSelectable)
             return

        for index, item_data in enumerate(self.processed_data):
            list_item = QListWidgetItem()
            list_item.setText(item_data["name"])
            list_item.setIcon(create_risk_icon(item_data.get("risk_level", "unknown")))
            list_item.setToolTip(item_data.get("tooltip", "无提示信息"))
            list_item.setData(Qt.ItemDataRole.UserRole, index)
            self.list_widget.addItem(list_item)

    def display_item_details(self, current_item, previous_item):
        if not current_item or current_item.data(Qt.ItemDataRole.UserRole) is None:
            self.item_name_label.setText("请选择一个物品查看详情")
            self.item_description_label.setText("")
            self.overall_risk_label.setText("风险等级: -")
            self.overall_risk_label.setStyleSheet("color: black;")
            self.score_label.setText("可信度评分: - / 10")
            self._clear_layout(self.dimension_layout)
            self._clear_layout(self.tags_layout)
            return

        item_index = current_item.data(Qt.ItemDataRole.UserRole)
        if item_index < 0 or item_index >= len(self.processed_data):
             print(f"错误：无效的物品索引 {item_index}")
             return

        item_data = self.processed_data[item_index]
        assessment = item_data.get('assessment')

        self.item_name_label.setText(item_data["name"])
        self.item_description_label.setText(item_data.get("item_text", "无描述信息"))

        if not assessment:
             self.overall_risk_label.setText("风险等级: 评估数据缺失")
             self.overall_risk_label.setStyleSheet("color: red;")
             self.score_label.setText("可信度评分: - / 10")
             self._clear_layout(self.dimension_layout)
             self._clear_layout(self.tags_layout)
             error_label = QLabel("- 无法加载评估详情")
             error_label.setStyleSheet("color: red;")
             self.tags_layout.addWidget(error_label)
             return

        risk_level = item_data.get("risk_level", "unknown")
        risk_text = {
            "low": "低风险", "medium": "中等风险", "high": "高风险"
        }.get(risk_level, "未知")
        color_map = {"low": "green", "medium": "orange", "high": "red"}
        self.overall_risk_label.setStyleSheet(f"QLabel {{ color: {color_map.get(risk_level, 'black')}; }}")
        self.overall_risk_label.setText(f"风险等级: {risk_text}")
        self.score_label.setText(f"可信度评分: {assessment.get('overall_score', '-')} / 10")

        self._clear_layout(self.dimension_layout)
        dimension_risks_display = {
            "exaggeration_sentiment": "过度宣传与情感偏见",
            "consistency_factuality": "信息一致性与事实核验",
            "originality_anomaly": "文本原创性与异常模式",
            "vagueness_detail": "细节缺乏与模糊性",
        }
        for dim_key, dim_value in assessment.get('dimension_risks', {}).items():
             display_name = dimension_risks_display.get(dim_key, dim_key)
             formatted_value = format_dimension_risk(dim_value)
             label_widget = QLabel(f"{display_name}:")
             value_widget = QLabel(formatted_value)
             value_widget.setWordWrap(True)
             self.dimension_layout.addRow(label_widget, value_widget)

        self._clear_layout(self.tags_layout)
        risk_labels = assessment.get('risk_labels', [])
        if risk_labels:
            for tag in risk_labels:
                tag_layout = QHBoxLayout()
                tag_layout.setContentsMargins(0, 0, 0, 0)
                tag_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

                icon_label = QLabel("\u26A0\ufe0f")
                icon_label.setStyleSheet("color: orange; font-size: 14px; margin-right: 5px;")
                icon_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
                tag_layout.addWidget(icon_label, 0)

                tag_text_label = QLabel(tag)
                tag_text_label.setWordWrap(True)
                tag_text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                tag_layout.addWidget(tag_text_label, 1)

                container_widget = QWidget()
                container_widget.setLayout(tag_layout)
                self.tags_layout.addWidget(container_widget)

        else:
             ok_label = QLabel("\u2705 无特定风险标签")
             ok_label.setStyleSheet("color: green;")
             self.tags_layout.addWidget(ok_label)


    def _clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._clear_layout(sub_layout)


    def feedback_accurate(self):
        current_item = self.list_widget.currentItem()
        if current_item and current_item.data(Qt.ItemDataRole.UserRole) is not None:
            item_index = current_item.data(Qt.ItemDataRole.UserRole)
            item_name = self.processed_data[item_index]['name']
            QMessageBox.information(self, "反馈已记录", f"感谢反馈！已记录您认为对 '{item_name}' 的评估是准确的 👍。")
            print(f"用户反馈: 对 '{item_name}' 的评估准确 👍")
        else:
            QMessageBox.warning(self, "操作无效", "请先在左侧列表中选择一个物品。")

    def feedback_inaccurate(self):
        current_item = self.list_widget.currentItem()
        if current_item and current_item.data(Qt.ItemDataRole.UserRole) is not None:
            item_index = current_item.data(Qt.ItemDataRole.UserRole)
            item_name = self.processed_data[item_index]['name']
            QMessageBox.information(self, "反馈已记录", f"感谢反馈！已记录您认为对 '{item_name}' 的评估不准确 👎。我们会参考此信息改进模型。")
            print(f"用户反馈: 对 '{item_name}' 的评估不准确 👎")
        else:
             QMessageBox.warning(self, "操作无效", "请先在左侧列表中选择一个物品。")

    def report_suspicious(self):
        current_item = self.list_widget.currentItem()
        if current_item and current_item.data(Qt.ItemDataRole.UserRole) is not None:
            item_index = current_item.data(Qt.ItemDataRole.UserRole)
            item_name = self.processed_data[item_index]['name']
            QMessageBox.information(self, "报告已提交", f"感谢您的警惕！我们已收到您对 '{item_name}' 文本可疑性的报告，将进行进一步核查。")
            print(f"用户报告: 认为 '{item_name}' 的文本可疑")
        else:
             QMessageBox.warning(self, "操作无效", "请先在左侧列表中选择一个物品。")

if __name__ == "__main__":
    try:
        if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
             QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
             QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except Exception as e:
        print(f"设置 High DPI 属性时出错 (可能 PyQt 版本不支持或属性名更改): {e}")

    app = QApplication(sys.argv)

    window = RiskAssessmentApp()
    window.show()
    sys.exit(app.exec())