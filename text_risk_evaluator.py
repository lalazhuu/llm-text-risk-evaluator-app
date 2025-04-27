import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein
import statistics

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    print("正在下载 VADER 词典用于情感分析...")
    nltk.download('vader_lexicon')

class TextRiskEvaluator:

    def __init__(self, category_baselines=None):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.category_baselines = category_baselines if category_baselines else {}

        self.exaggeration_keywords = {
            "惊艳", "完美", "令人难以置信", "难以置信", "革命性", "必备", "神器", "全能",
            "游戏规则改变者", "无瑕", "史上最佳", "终极", "奇迹", "无与伦比", "轰动", "绝对", "效果惊人",
            "amazing", "perfect", "incredible", "unbelievable", "revolutionary",
            "must-have", "game-changer", "flawless", "best ever", "ultimate",
            "miracle", "unparalleled", "sensational", "absolutely", "stunning", "fantastic"
        }
        self.vague_keywords = {
             "好", "不错", "很棒", "极好", "有效", "高质量", "优秀", "卓越", "显著", "轻松", "智能",
             "方便", "强大", "全面",
             "great", "nice", "good", "wonderful", "fantastic", "effective", "easy", "smart",
             "high-quality", "excellent", "superb", "significant", "powerful", "comprehensive"
        }
        self.suspicious_claim_keywords = {
            "能量", "量子", "保证", "运势", "风水", "磁疗", "红外线",
            "宇宙", "奇迹", "根治", "特效", "永恒"
        }

        self.dimension_weights = {
            "exaggeration_sentiment": 0.35,
            "consistency_factuality": 0.30,
            "originality_anomaly": 0.15,
            "vagueness_detail": 0.20,
        }
        self.sentiment_deviation_threshold = 0.3
        self.exaggeration_freq_threshold = 0.015
        self.similarity_threshold = 0.8
        self.vagueness_ratio_threshold = 0.08
        self.suspicious_keywords_threshold = 2
        self.min_numbers_electronics = 3

    def _assess_sentiment_exaggeration(self, item_text, category=None):
        risk_score = 0.0
        labels = []
        sentiment = None

        try:
            sentiment = self.sentiment_analyzer.polarity_scores(item_text)['compound']
        except Exception as e:
            print(f"情感分析时出错: {e}")
            labels.append("情感分析失败")
            sentiment = 0.0

        baseline_sentiment = None
        if category and category in self.category_baselines:
            baseline_sentiment = self.category_baselines[category].get('avg_sentiment')
            if baseline_sentiment is not None and sentiment is not None:
                if sentiment > baseline_sentiment + self.sentiment_deviation_threshold:
                    risk_score += 0.3
                    labels.append(f"情感得分 ({sentiment:.2f}) 显著高于类别平均值 ({baseline_sentiment:.2f})")
            elif sentiment is not None and sentiment > 0.90:
                 risk_score += 0.2
                 labels.append(f"情感得分 ({sentiment:.2f}) 极度正向。")
        elif sentiment is not None and sentiment > 0.90:
            risk_score += 0.2
            labels.append(f"情感得分 ({sentiment:.2f}) 极度正向。")

        words = re.findall(r'\b\w+\b', item_text.lower())
        if not words:
             dim_risk = min(1.0, risk_score)
             return dim_risk, labels, sentiment

        exaggeration_count = sum(1 for word in words if word in self.exaggeration_keywords)
        exaggeration_freq = exaggeration_count / len(words)

        if exaggeration_freq > self.exaggeration_freq_threshold :
            risk_score += 0.8
            labels.append(f"【高风险】检测到高频率 ({exaggeration_freq:.2%}) 的过度宣传关键词 ({exaggeration_count}个)。")
        elif exaggeration_count >= 3:
             risk_score += 0.6
             labels.append(f"【中高风险】检测到多个 ({exaggeration_count}个) 过度宣传关键词。")
        elif exaggeration_count >= 1:
             risk_score += 0.3
             labels.append(f"【中风险】检测到少量 ({exaggeration_count}个) 过度宣传关键词。")


        dim_risk = min(1.0, risk_score)
        return dim_risk, labels, sentiment

    def _assess_consistency(self, item_text, item_metadata):
        risk_score = 0.0
        labels = []
        consistency_penalty = 0

        if not item_metadata:
            return 0.1, ["元数据缺失，无法进行详细一致性检查"]

        text_prices = re.findall(r'[$€£¥]\s?(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)', item_text)
        metadata_price = item_metadata.get('price')
        if text_prices and metadata_price is not None:
            try:
                text_price_val = float(text_prices[0].replace(',', ''))
                if abs(text_price_val - metadata_price) > max(metadata_price * 0.1, 50):
                    risk_score = max(risk_score, 0.9)
                    consistency_penalty = 1
                    labels.append(f"【高风险】文本价格 ('{text_prices[0]}') 与元数据价格 ({metadata_price}) 严重不符。")
            except ValueError:
                labels.append("无法解析文本中找到的价格以进行比较。")

        metadata_specs = item_metadata.get('specs', {})
        metadata_speed = metadata_specs.get('read_speed_mbps')
        text_speeds = re.findall(r'(\d{3,})\s?MB/s', item_text, re.IGNORECASE)
        if text_speeds and metadata_speed is not None:
            try:
                text_speed_val = int(text_speeds[0])
                if abs(text_speed_val - metadata_speed) > metadata_speed * 0.2:
                    risk_score = max(risk_score, 0.9)
                    consistency_penalty = 1
                    labels.append(f"【高风险】文本宣称速度 ({text_speed_val}MB/s) 与元数据规格 ({metadata_speed}MB/s) 严重不符。")
            except ValueError:
                 labels.append("无法解析文本中找到的速度值。")

        if consistency_penalty == 0:
            metadata_color = metadata_specs.get('color')
            if metadata_color and metadata_color.lower() not in item_text.lower():
                risk_score += 0.15
                labels.append(f"元数据中的颜色 ('{metadata_color}') 在描述中未提及。")

            metadata_battery = metadata_specs.get('battery_life_hours')
            if metadata_battery:
                 text_hours = re.findall(r'(\d{1,2})\s?(?:小时|hours)', item_text)
                 found_match = False
                 for h in text_hours:
                     if abs(int(h) - metadata_battery) <= 2:
                         found_match = True
                         break
                 if not found_match:
                     risk_score += 0.2
                     labels.append(f"文本中提及的续航时间与元数据 ({metadata_battery}小时) 不符或未明确提及。")

        suspicious_count = 0
        words_lower = item_text.lower()
        for keyword in self.suspicious_claim_keywords:
            if keyword in words_lower:
                 suspicious_count += 1
        category = item_metadata.get('category', '').lower()
        price = metadata_price if metadata_price is not None else 0
        if suspicious_count >= self.suspicious_keywords_threshold and (price > 500 or category == 'accessories'):
            risk_score += 0.5
            labels.append(f"文本包含多个可疑或无法验证的声明关键词 ({suspicious_count}个)，结合价格/类别判断风险较高。")
        elif suspicious_count > 0:
             risk_score += 0.1
             labels.append(f"文本包含少量可疑声明关键词 ({suspicious_count}个)。")


        dim_risk = min(1.0, risk_score)
        return dim_risk, labels

    def _assess_originality_anomaly(self, item_text, historical_texts, similar_item_texts, category=None):
        risk_score = 0.0
        labels = []
        text_length = len(item_text.split())

        if similar_item_texts:
            corpus = [item_text] + similar_item_texts
            try:
                vectorizer = TfidfVectorizer(stop_words='english')
                tfidf_matrix = vectorizer.fit_transform(corpus)
                cosine_sims = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
                avg_similarity = cosine_sims.mean() if cosine_sims.size > 0 else 0
                if avg_similarity > self.similarity_threshold:
                    risk_score += 0.6
                    labels.append(f"与相似物品的平均相似度过高 ({avg_similarity:.2f})，可能是模板化文本。")
                elif avg_similarity > self.similarity_threshold * 0.7:
                    risk_score += 0.2
                    labels.append(f"与相似物品的平均相似度较高 ({avg_similarity:.2f})。")
            except ValueError as e:
                 print(f"TF-IDF 计算错误: {e}")
                 labels.append("由于文本特性，无法计算相似度。")

        if historical_texts:
            last_historical_text = historical_texts[-1]
            edit_dist = Levenshtein.distance(item_text, last_historical_text)
            max_len = max(len(item_text), len(last_historical_text))
            normalized_distance = edit_dist / max_len if max_len > 0 else 0
            if max_len > 30 and 0 < normalized_distance < 0.10:
                risk_score += 0.15
                labels.append(f"与上一版本相比改动较小 (距离: {normalized_distance:.2%})。")

        if category and category in self.category_baselines:
            baseline_length = self.category_baselines[category].get('avg_length')
            if baseline_length and baseline_length > 0:
                length_ratio = text_length / baseline_length
                if length_ratio < 0.2 or length_ratio > 5.0:
                    risk_score += 0.2
                    labels.append(f"文本长度 ({text_length} 词) 与类别平均长度 ({baseline_length} 词) 相比异常。")

        dim_risk = min(1.0, risk_score)
        return dim_risk, labels

    def _assess_vagueness(self, item_text, category=None):
        risk_score = 0.0
        labels = []

        words = re.findall(r'\b\w+\b', item_text.lower())
        if not words: return 0.0, ["文本为空或不包含标准单词。"]

        vague_count = sum(1 for word in words if word in self.vague_keywords)
        vagueness_ratio = vague_count / len(words)

        if vagueness_ratio > self.vagueness_ratio_threshold:
            risk_score += 0.7
            labels.append(f"【中高风险】检测到高比例 ({vagueness_ratio:.2%}) 的模糊关键词 ({vague_count}个)。")
        elif vague_count >= 3:
            risk_score += 0.4
            labels.append(f"【中风险】检测到多个 ({vague_count}个) 模糊关键词。")
        elif vague_count >= 1:
            risk_score += 0.15
            labels.append(f"检测到少量 ({vague_count}个) 模糊关键词。")

        numbers_found = re.findall(r'\b\d+(?:\.\d+)?\b', item_text)
        num_digits = len(numbers_found)
        expected_digits = self.min_numbers_electronics if category and category.lower() in ['electronics', 'computers', 'hardware'] else 1

        if num_digits < expected_digits:
             risk_score += 0.5
             labels.append(f"【中风险】对于 {category or '该'} 类别，文本中包含的具体数值信息过少 ({num_digits}个，预期至少 {expected_digits}个)。")

        dim_risk = min(1.0, risk_score)
        return dim_risk, labels

    def assess(self, item_text, item_metadata=None, historical_texts=None, similar_item_texts=None):
        if not item_text:
            return {'overall_score': 0, 'dimension_risks': {}, 'risk_labels': ["输入文本为空。"], 'raw_sentiment': None}

        category = item_metadata.get('category') if item_metadata else None
        historical_texts = historical_texts or []
        similar_item_texts = similar_item_texts or []

        risk_senti, labels_senti, raw_sentiment = self._assess_sentiment_exaggeration(item_text, category)
        risk_cons, labels_cons = self._assess_consistency(item_text, item_metadata)
        risk_orig, labels_orig = self._assess_originality_anomaly(item_text, historical_texts, similar_item_texts, category)
        risk_vague, labels_vague = self._assess_vagueness(item_text, category)

        dimension_risks = {
            "exaggeration_sentiment": risk_senti,
            "consistency_factuality": risk_cons,
            "originality_anomaly": risk_orig,
            "vagueness_detail": risk_vague,
        }

        total_weighted_risk = sum(dimension_risks[dim] * self.dimension_weights[dim]
                                  for dim in dimension_risks)

        max_score = 10
        overall_score = max(0, max_score - total_weighted_risk * max_score)

        all_labels = labels_senti + labels_cons + labels_orig + labels_vague
        labeled_risks = []
        for label in all_labels:
             if "【高风险】" in label or "【中高风险】" in label:
                 labeled_risks.append(label)
             elif "【中风险】" in label:
                 labeled_risks.append(label)
             elif label:
                 labeled_risks.append(f"【低风险提示】{label}" if "【" not in label else label)


        return {
            'overall_score': round(overall_score, 1),
            'dimension_risks': {k: round(v, 2) for k, v in dimension_risks.items()},
            'risk_labels': labeled_risks,
            'raw_sentiment': round(raw_sentiment, 3) if raw_sentiment is not None else None
        }

if __name__ == "__main__":
    baselines = {
        "Electronics": {"avg_sentiment": 0.4, "avg_length": 120},
        "Books": {"avg_sentiment": 0.6, "avg_length": 200},
        "Apparel": {"avg_sentiment": 0.3, "avg_length": 80},
        "Accessories": {"avg_sentiment": 0.2, "avg_length": 50}
    }
    evaluator = TextRiskEvaluator(category_baselines=baselines)
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
    print("--- 再次优化后评分机制测试 ---")
    for product in PRODUCT_SOURCE_DATA:
        print(f"\n--- 评估物品: {product['name']} ---")
        assessment = evaluator.assess(
            item_text=product.get("item_text", ""),
            item_metadata=product.get("item_metadata"),
            historical_texts=product.get("historical_texts"),
            similar_item_texts=product.get("similar_item_texts")
        )
        print(f"  综合评分: {assessment['overall_score']}/10")
        print(f"  维度风险: {assessment['dimension_risks']}")
        print(f"  风险标签:")
        if assessment['risk_labels']:
            for label in assessment['risk_labels']:
                print(f"    - {label}")
        else:
            print("    - 无")