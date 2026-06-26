"""
一次性脚本：把压缩笔记导入 flashcard_bank + 生成初始题目
运行：python seed_data.py

v2: content 字段改为 JSON {front, back, blanks}
"""
import json
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY or "")


def seed():
    # ─── Python Phase 闪卡（content 为 JSON 格式）───
    cards = [
        {
            "phase": "Python", "chapter": "基础语法", "title": "五大容器",
            "tags": ["python", "容器", "list", "dict"],
            "content": json.dumps({
                "front": "⭐ **___(1)___** ▸ 5种存多个元素的数据类型：___(2)___, list, tuple, set, dict\n▸ 区分三维度：___(3)___, 是否可变, ___(4)___\n▸ 底层：list动态数组, tuple静态数组, set/dict哈希表",
                "back": "⭐ **五大容器** ▸ 5种存多个元素的数据类型：str, list, tuple, set, dict\n▸ 区分三维度：符号, 是否可变, 元素限制\n▸ 底层：list动态数组, tuple静态数组, set/dict哈希表",
                "blanks": [
                    {"pos": 1, "answer": "五大容器", "options": ["五大容器", "四大金刚", "六大件", "三大数据结构"]},
                    {"pos": 2, "answer": "str", "options": ["str", "int", "float", "bool"]},
                    {"pos": 3, "answer": "符号", "options": ["符号", "类型", "长度", "索引"]},
                    {"pos": 4, "answer": "元素限制", "options": ["元素限制", "大小限制", "类型限制", "长度限制"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "基础语法", "title": "字符串 str",
            "tags": ["python", "字符串", "str"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ '', \"\", \"\"\"\"\"\"  ▸ 元素=字符  ▸ ___(2)___\n▸ 正负索引 ▸ 底层数组O(1), 不是链表\n▸ ___(3)___切, join拼, strip去空格, replace换, find查(-1), index查(报错)",
                "back": "⭐ 字符串 str ▸ '', \"\", \"\"\"\"\"\"  ▸ 元素=字符  ▸ 不可变\n▸ 正负索引 ▸ 底层数组O(1), 不是链表\n▸ split切, join拼, strip去空格, replace换, find查(-1), index查(报错)",
                "blanks": [
                    {"pos": 1, "answer": "字符串 str", "options": ["字符串 str", "列表 list", "元组 tuple", "字典 dict"]},
                    {"pos": 2, "answer": "不可变", "options": ["不可变", "可变", "可哈希", "可排序"]},
                    {"pos": 3, "answer": "split", "options": ["split", "slice", "cut", "divide"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "基础语法", "title": "列表 list",
            "tags": ["python", "list", "列表"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ [] ▸ 元素=任意 ▸ 可变 ▸ 底层___(2)___\n▸ 增：append尾加, insert插入, extend批加\n▸ 删：pop弹出, remove按值删, clear清空\n▸ Java对照: ArrayList",
                "back": "⭐ 列表 list ▸ [] ▸ 元素=任意 ▸ 可变 ▸ 底层动态数组\n▸ 增：append尾加, insert插入, extend批加\n▸ 删：pop弹出, remove按值删, clear清空\n▸ Java对照: ArrayList",
                "blanks": [
                    {"pos": 1, "answer": "列表 list", "options": ["列表 list", "元组 tuple", "集合 set", "字典 dict"]},
                    {"pos": 2, "answer": "动态数组", "options": ["动态数组", "链表", "哈希表", "二叉树"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "基础语法", "title": "字典 dict",
            "tags": ["python", "dict", "字典"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ {k:v} ▸ 可变 ▸ key不可变, value任意 ▸ 底层___(2)___\n▸ d[key]取, .get(key,默认)安全取 ▸ .keys(), .values(), .items()\n▸ Java对照: HashMap",
                "back": "⭐ 字典 dict ▸ {k:v} ▸ 可变 ▸ key不可变, value任意 ▸ 底层哈希表\n▸ d[key]取, .get(key,默认)安全取 ▸ .keys(), .values(), .items()\n▸ Java对照: HashMap",
                "blanks": [
                    {"pos": 1, "answer": "字典 dict", "options": ["字典 dict", "列表 list", "集合 set", "元组 tuple"]},
                    {"pos": 2, "answer": "哈希表", "options": ["哈希表", "动态数组", "链表", "红黑树"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "基础语法", "title": "推导式",
            "tags": ["python", "推导式", "列表推导式"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ for循环表达式写法, 一行生成容器\n▸ 三种内置：列表[x for x in seq], 集合{x for x in seq}, 字典{k:v for k,v in seq}\n▸ 带条件：[x for x in range(10) if x % 2 == 0]\n▸ Java对照: Stream ___(2)___",
                "back": "⭐ 推导式 ▸ for循环表达式写法, 一行生成容器\n▸ 三种内置：列表[x for x in seq], 集合{x for x in seq}, 字典{k:v for k,v in seq}\n▸ 带条件：[x for x in range(10) if x % 2 == 0]\n▸ Java对照: Stream map().toList()",
                "blanks": [
                    {"pos": 1, "answer": "推导式", "options": ["推导式", "生成器", "迭代器", "装饰器"]},
                    {"pos": 2, "answer": "map().toList()", "options": ["map().toList()", "filter().collect()", "forEach()", "reduce()"]},
                ]
            }, ensure_ascii=False)
        },
        # NumPy
        {
            "phase": "Python", "chapter": "NumPy", "title": "向量化",
            "tags": ["numpy", "向量化", "布尔索引"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ a+b a*b a**2 np.sqrt(a) 全逐元素，告别for循环\n▸ ___(2)___: a[a>3] 直接筛选\n▸ Java对照: int[]+Stream，但NumPy是C底层并行更快",
                "back": "⭐ 向量化 ▸ a+b a*b a**2 np.sqrt(a) 全逐元素，告别for循环\n▸ 布尔索引: a[a>3] 直接筛选\n▸ Java对照: int[]+Stream，但NumPy是C底层并行更快",
                "blanks": [
                    {"pos": 1, "answer": "向量化", "options": ["向量化", "标量化", "序列化", "并行化"]},
                    {"pos": 2, "answer": "布尔索引", "options": ["布尔索引", "条件筛选", "逻辑索引", "掩码选择"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "NumPy", "title": "ndarray",
            "tags": ["numpy", "ndarray"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ 连续内存+同类型+C底层循环 ▸ 比Python list快___(2)___倍\n▸ 创建: np.array() zeros ones arange linspace random.randint randn\n▸ 形状: .shape .reshape() .flatten() .T",
                "back": "⭐ ndarray ▸ 连续内存+同类型+C底层循环 ▸ 比Python list快10-100倍\n▸ 创建: np.array() zeros ones arange linspace random.randint randn\n▸ 形状: .shape .reshape() .flatten() .T",
                "blanks": [
                    {"pos": 1, "answer": "ndarray", "options": ["ndarray", "list", "Series", "DataFrame"]},
                    {"pos": 2, "answer": "10-100", "options": ["10-100", "2-5", "100-1000", "500+"]},
                ]
            }, ensure_ascii=False)
        },
        # Pandas
        {
            "phase": "Python", "chapter": "Pandas", "title": "DataFrame操作",
            "tags": ["pandas", "dataframe"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ 查看: .head() .describe() .info() .dtypes\n▸ 选列: df[\"col\"] df[[\"c1\",\"c2\"]] ▸ 选行: ___(2)___[]标签 iloc[]位置\n▸ 筛选: df[df[\"col\"]>100] ▸ 排序: sort_values(\"col\", ascending=False)",
                "back": "⭐ DataFrame操作 ▸ 查看: .head() .describe() .info() .dtypes\n▸ 选列: df[\"col\"] df[[\"c1\",\"c2\"]] ▸ 选行: loc[]标签 iloc[]位置\n▸ 筛选: df[df[\"col\"]>100] ▸ 排序: sort_values(\"col\", ascending=False)",
                "blanks": [
                    {"pos": 1, "answer": "DataFrame操作", "options": ["DataFrame操作", "Series操作", "ndarray操作", "Panel操作"]},
                    {"pos": 2, "answer": "loc", "options": ["loc", "at", "row", "idx"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "Pandas", "title": "分组聚合",
            "tags": ["pandas", "groupby", "分组聚合"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ df.groupby(\"city\")[\"sales\"].sum() 单列单函数\n▸ 多列分组+多函数: .groupby([c1,c2]).agg({\"col\":\"mean\", \"col2\":\"max\"})\n▸ Java对照: SQL ___(2)___ / Stream.collect(groupingBy)",
                "back": "⭐ 分组聚合 ▸ df.groupby(\"city\")[\"sales\"].sum() 单列单函数\n▸ 多列分组+多函数: .groupby([c1,c2]).agg({\"col\":\"mean\", \"col2\":\"max\"})\n▸ Java对照: SQL GROUP BY / Stream.collect(groupingBy)",
                "blanks": [
                    {"pos": 1, "answer": "分组聚合", "options": ["分组聚合", "透视表", "合并连接", "重塑变形"]},
                    {"pos": 2, "answer": "GROUP BY", "options": ["GROUP BY", "ORDER BY", "JOIN", "WHERE"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "Pandas", "title": "透视表",
            "tags": ["pandas", "透视表", "pivot_table"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ pd.pivot_table(df, values, ___(2)___, columns, aggfunc)\n▸ index=行分组，columns=列分组，values=被聚合，aggfunc=聚合函数\n▸ Java对照: SQL PIVOT，行列交叉统计",
                "back": "⭐ 透视表 ▸ pd.pivot_table(df, values, index, columns, aggfunc)\n▸ index=行分组，columns=列分组，values=被聚合，aggfunc=聚合函数\n▸ Java对照: SQL PIVOT，行列交叉统计",
                "blanks": [
                    {"pos": 1, "answer": "透视表", "options": ["透视表", "交叉表", "分组表", "汇总表"]},
                    {"pos": 2, "answer": "index", "options": ["index", "rows", "group", "by"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "Pandas", "title": "三种空值",
            "tags": ["pandas", "空值", "NaN"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ None(Python) np.nan(NumPy) pd.NA(pandas) ▸ pandas自动转换\n▸ NaN 不等于自己 ▸ 不能用 ___(2)___ 判空，必须用 isna()",
                "back": "⭐ 三种空值 ▸ None(Python) np.nan(NumPy) pd.NA(pandas) ▸ pandas自动转换\n▸ NaN 不等于自己 ▸ 不能用 == 判空，必须用 isna()",
                "blanks": [
                    {"pos": 1, "answer": "三种空值", "options": ["三种空值", "缺失值处理", "空值检测", "NaN类型"]},
                    {"pos": 2, "answer": "==", "options": ["==", "is null", "empty()", "isnan()"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "Pandas", "title": "判空三连",
            "tags": ["pandas", "isna", "空值检测"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ isna()/isnull() 是否空 ▸ notna()/notnull() 是否非空\n▸ 全表布尔: df.isna() ▸ 每列空值数: .isna().___(2)___()\n▸ 占比: .isna().sum() / len(df) * 100",
                "back": "⭐ 判空三连 ▸ isna()/isnull() 是否空 ▸ notna()/notnull() 是否非空\n▸ 全表布尔: df.isna() ▸ 每列空值数: .isna().sum()\n▸ 占比: .isna().sum() / len(df) * 100",
                "blanks": [
                    {"pos": 1, "answer": "判空三连", "options": ["判空三连", "空值检测", "三剑客", "缺失值三法"]},
                    {"pos": 2, "answer": "sum", "options": ["sum", "count", "size", "len"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "Pandas", "title": "fillna填充",
            "tags": ["pandas", "fillna", "缺失值"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ 填0(粗暴) ▸ 填均值 .fillna(df['age'].mean())\n▸ ___(2)___ 前向(用上一行) ▸ bfill 后向(用下一行)\n▸ 时序数据首选 ffill/bfill，分类数据用众数",
                "back": "⭐ fillna填充 ▸ 填0(粗暴) ▸ 填均值 .fillna(df['age'].mean())\n▸ ffill 前向(用上一行) ▸ bfill 后向(用下一行)\n▸ 时序数据首选 ffill/bfill，分类数据用众数",
                "blanks": [
                    {"pos": 1, "answer": "fillna填充", "options": ["fillna填充", "dropna删除", "插值法", "替换法"]},
                    {"pos": 2, "answer": "ffill", "options": ["ffill", "bfill", "pfill", "nfill"]},
                ]
            }, ensure_ascii=False)
        },
        {
            "phase": "Python", "chapter": "Pandas", "title": "RFM三维度",
            "tags": ["pandas", "RFM", "客户分层"],
            "content": json.dumps({
                "front": "⭐ ___(1)___ ▸ R=___(2)___ 最近购买距今 ▸ F=Frequency 交易次数\n▸ M=Monetary 消费金额 ▸ 用于客户价值分层",
                "back": "⭐ RFM三维度 ▸ R=Recency 最近购买距今 ▸ F=Frequency 交易次数\n▸ M=Monetary 消费金额 ▸ 用于客户价值分层",
                "blanks": [
                    {"pos": 1, "answer": "RFM三维度", "options": ["RFM三维度", "KNN分类", "K-Means聚类", "AARRR模型"]},
                    {"pos": 2, "answer": "Recency", "options": ["Recency", "Revenue", "Retention", "Rating"]},
                ]
            }, ensure_ascii=False)
        },
    ]

    print(f"Inserting {len(cards)} flashcards...")
    for c in cards:
        sb.table("flashcard_bank").insert(c).execute()

    # 生成初始 mastery_scores（全设50）
    for c in cards:
        sb.table("mastery_scores").insert({
            "knowledge_point": c["title"],
            "phase": c["phase"],
            "score": 50,
        }).execute()

    # ─── 生成初始题目 ───
    questions = [
        {"knowledge_point":"向量化","type":"true_false","difficulty":1,"question":"NumPy 的 a[a>3] 是布尔索引，可以直接筛选数组中满足条件的值。","options":json.dumps(["✅ 对","❌ 错"]),"correct_index":0,"explanation":"NumPy 布尔索引直接筛选值，返回满足条件的元素。"},
        {"knowledge_point":"向量化","type":"true_false","difficulty":1,"question":"NumPy 的 a+b 是两个数组的逐元素相加，和 Python list 的 +（拼接）行为相同。","options":json.dumps(["✅ 对","❌ 错"]),"correct_index":1,"explanation":"list 的 + 是拼接，NumPy 的 + 是逐元素相加，行为完全不同。"},
        {"knowledge_point":"三种空值","type":"true_false","difficulty":1,"question":"np.nan == np.nan 的结果是 True。","options":json.dumps(["✅ 对","❌ 错"]),"correct_index":1,"explanation":"NaN 不等于任何值包括自己，必须用 isna() 判空。"},
        {"knowledge_point":"判空三连","type":"true_false","difficulty":1,"question":".isna() 和 .isnull() 在 pandas 中作用相同，都可以检测空值。","options":json.dumps(["✅ 对","❌ 错"]),"correct_index":0,"explanation":"isna() 和 isnull() 是同一个方法的两个别名。"},
        {"knowledge_point":"fillna填充","type":"single_choice","difficulty":1,"question":"df.fillna(0) 会填充 DataFrame 中的哪些列？","options":json.dumps(["A) 只填第一列","B) 填所有列","C) 只填数值列","D) 都不填"]),"correct_index":1,"explanation":"df.fillna(0) 作用在全表，所有列的空值都被填 0。"},
        {"knowledge_point":"fillna填充","type":"true_false","difficulty":1,"question":"df['age'].fillna(df['age'].mean()) 只会填充 age 这一列的缺失值。","options":json.dumps(["✅ 对","❌ 错"]),"correct_index":0,"explanation":"指定了列名 'age'，所以只填充这一列。"},
        {"knowledge_point":"dropna删除","type":"true_false","difficulty":1,"question":"df.dropna(how='any') 删除的是所有列都为空的行。","options":json.dumps(["✅ 对","❌ 错"]),"correct_index":1,"explanation":"how='any' 是任一列为空就删；how='all' 才是所有列都为空才删。"},
        {"knowledge_point":"DataFrame操作","type":"single_choice","difficulty":1,"question":"df[df['score']>80] 返回的是什么？","options":json.dumps(["A) 返回 score 列中大于80的值","B) 返回 score>80 的行","C) 返回 True/False 列表","D) 报错"]),"correct_index":1,"explanation":"布尔索引在 DataFrame 上按行筛选，返回满足条件的整行。"},
        {"knowledge_point":"分组聚合","type":"single_choice","difficulty":2,"question":"对 df 按 city 分组统计 sales 总和，正确写法是？","options":json.dumps(["A) df.groupby('city').sum('sales')","B) df.groupby('city')['sales'].sum()","C) df.group('city').sum('sales')","D) df.sum().groupby('city','sales')"]),"correct_index":1,"explanation":"先 groupby 分组，再选列，最后聚合函数。"},
        {"knowledge_point":"RFM三维度","type":"single_choice","difficulty":2,"question":"RFM 分析中，R 代表什么？","options":json.dumps(["A) Revenue 收入","B) Recency 最近一次购买距今","C) Retention 留存率","D) Rating 评分"]),"correct_index":1,"explanation":"R=Recency 最近购买距今天数，越小说明客户越活跃。"},
    ]

    print(f"Inserting {len(questions)} quiz questions...")
    for q in questions:
        sb.table("quiz_questions").insert(q).execute()

    # 初始化积分记录
    sb.table("user_points").insert({
        "total_points": 0,
        "current_streak": 0,
        "max_streak": 0,
        "multiplier": 1.0,
    }).execute()

    print("✅ Seed data inserted successfully!")


if __name__ == "__main__":
    seed()
