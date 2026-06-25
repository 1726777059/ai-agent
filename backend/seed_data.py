"""
一次性脚本：把现有压缩笔记导入 flashcard_bank + 生成初始题目
运行：python seed_data.py
"""

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY or "")


def seed():
    # ─── Python Phase 1 闪卡 ───
    cards = [
        # Python串讲2
        {"phase":"Python","chapter":"基础语法","title":"五大容器","content":"⭐ 五大容器 ▸ 5种存多个元素的数据类型：str, list, tuple, set, dict\n▸ 区分三维度：符号, 是否可变, 元素限制\n▸ 底层：list动态数组, tuple静态数组, set/dict哈希表","tags":["python","容器","list","dict"]},
        {"phase":"Python","chapter":"基础语法","title":"字符串 str","content":"⭐ 字符串 str ▸ '', \"\", \"\"\"\"\"\"  ▸ 元素=字符  ▸ 不可变\n▸ 正负索引 ▸ 底层数组O(1), 不是链表\n▸ split切, join拼, strip去空格, replace换, find查(-1), index查(报错)","tags":["python","字符串","str"]},
        {"phase":"Python","chapter":"基础语法","title":"列表 list","content":"⭐ 列表 list ▸ [] ▸ 元素=任意 ▸ 可变 ▸ 底层动态数组\n▸ 增：append尾加, insert插入, extend批加\n▸ 删：pop弹出, remove按值删, clear清空\n▸ Java对照: ArrayList","tags":["python","list","列表"]},
        {"phase":"Python","chapter":"基础语法","title":"字典 dict","content":"⭐ 字典 dict ▸ {k:v} ▸ 可变 ▸ key不可变, value任意 ▸ 底层哈希表\n▸ d[key]取, .get(key,默认)安全取 ▸ .keys(), .values(), .items()\n▸ Java对照: HashMap","tags":["python","dict","字典"]},
        {"phase":"Python","chapter":"基础语法","title":"推导式","content":"⭐ 推导式 ▸ for循环表达式写法, 一行生成容器\n▸ 三种内置：列表[x for x in seq], 集合{x for x in seq}, 字典{k:v for k,v in seq}\n▸ 带条件：[x for x in range(10) if x % 2 == 0]\n▸ Java对照: Stream map().toList()","tags":["python","推导式","列表推导式"]},
        # Python串讲4
        {"phase":"Python","chapter":"NumPy","title":"向量化","content":"⭐ 向量化 ▸ a+b a*b a**2 np.sqrt(a) 全逐元素，告别for循环\n▸ 布尔索引: a[a>3] 直接筛选\n▸ Java对照: int[]+Stream，但NumPy是C底层并行更快","tags":["numpy","向量化","布尔索引"]},
        {"phase":"Python","chapter":"NumPy","title":"ndarray","content":"⭐ ndarray ▸ 连续内存+同类型+C底层循环 ▸ 比Python list快10-100倍\n▸ 创建: np.array() zeros ones arange linspace random.randint randn\n▸ 形状: .shape .reshape() .flatten() .T","tags":["numpy","ndarray"]},
        {"phase":"Python","chapter":"Pandas","title":"DataFrame操作","content":"⭐ DataFrame操作 ▸ 查看: .head() .describe() .info() .dtypes\n▸ 选列: df[\"col\"] df[[\"c1\",\"c2\"]] ▸ 选行: loc[]标签 iloc[]位置\n▸ 筛选: df[df[\"col\"]>100] ▸ 排序: sort_values(\"col\", ascending=False)","tags":["pandas","dataframe"]},
        {"phase":"Python","chapter":"Pandas","title":"分组聚合","content":"⭐ 分组聚合 ▸ df.groupby(\"city\")[\"sales\"].sum() 单列单函数\n▸ 多列分组+多函数: .groupby([c1,c2]).agg({\"col\":\"mean\", \"col2\":\"max\"})\n▸ Java对照: SQL GROUP BY / Stream.collect(groupingBy)","tags":["pandas","groupby","分组聚合"]},
        {"phase":"Python","chapter":"Pandas","title":"透视表","content":"⭐ 透视表 ▸ pd.pivot_table(df, values, index, columns, aggfunc)\n▸ index=行分组，columns=列分组，values=被聚合，aggfunc=聚合函数\n▸ Java对照: SQL PIVOT，行列交叉统计","tags":["pandas","透视表","pivot_table"]},
        # Python串讲5
        {"phase":"Python","chapter":"Pandas","title":"三种空值","content":"⭐ 三种空值 ▸ None(Python) np.nan(NumPy) pd.NA(pandas) ▸ pandas自动转换\n▸ NaN 不等于自己 ▸ 不能用 == 判空，必须用 isna()","tags":["pandas","空值","NaN"]},
        {"phase":"Python","chapter":"Pandas","title":"判空三连","content":"⭐ 判空三连 ▸ isna()/isnull() 是否空 ▸ notna()/notnull() 是否非空\n▸ 全表布尔: df.isna() ▸ 每列空值数: .isna().sum()\n▸ 占比: .isna().sum() / len(df) * 100","tags":["pandas","isna","空值检测"]},
        {"phase":"Python","chapter":"Pandas","title":"fillna填充","content":"⭐ fillna填充 ▸ 填0(粗暴) ▸ 填均值 .fillna(df['age'].mean())\n▸ ffill 前向(用上一行) ▸ bfill 后向(用下一行)\n▸ 时序数据首选 ffill/bfill，分类数据用众数\n▸ df.fillna(0)=全表填充 ▸ df[\"age\"].fillna(...)=单列填充","tags":["pandas","fillna","缺失值"]},
        {"phase":"Python","chapter":"Pandas","title":"RFM三维度","content":"⭐ RFM三维度 ▸ R=Recency 最近购买距今 ▸ F=Frequency 交易次数\n▸ M=Monetary 消费金额 ▸ 用于客户价值分层\n▸ RFM五步 ▸ 删全空 → 算R/F/M → pd.cut分箱打分 → 加权合并 → 客户分层","tags":["pandas","RFM","客户分层"]},
    ]

    print(f"Inserting {len(cards)} flashcards...")
    for c in cards:
        sb.table("flashcard_bank").insert(c).execute()

    # 生成初始 mastery_scores（全设50）
    for c in cards:
        sb.table("mastery_scores").insert({
            "flashcard_id": None,  # will update later if needed
            "knowledge_point": c["title"],
            "phase": c["phase"],
            "score": 50,
        }).execute()

    # ─── 生成初始题目 ───
    questions = [
        {"knowledge_point":"向量化","type":"true_false","difficulty":1,"question":"NumPy 的 a[a>3] 是布尔索引，可以直接筛选数组中满足条件的值。","options":["✅ 对","❌ 错"],"correct_index":0,"explanation":"NumPy 布尔索引直接筛选值，返回满足条件的元素。"},
        {"knowledge_point":"向量化","type":"true_false","difficulty":1,"question":"NumPy 的 a+b 是两个数组的逐元素相加，和 Python list 的 +（拼接）行为相同。","options":["✅ 对","❌ 错"],"correct_index":1,"explanation":"list 的 + 是拼接，NumPy 的 + 是逐元素相加，行为完全不同。"},
        {"knowledge_point":"三种空值","type":"true_false","difficulty":1,"question":"np.nan == np.nan 的结果是 True。","options":["✅ 对","❌ 错"],"correct_index":1,"explanation":"NaN 不等于任何值包括自己，必须用 isna() 判空。"},
        {"knowledge_point":"判空三连","type":"true_false","difficulty":1,"question":".isna() 和 .isnull() 在 pandas 中作用相同，都可以检测空值。","options":["✅ 对","❌ 错"],"correct_index":0,"explanation":"isna() 和 isnull() 是同一个方法的两个别名。"},
        {"knowledge_point":"fillna填充","type":"single_choice","difficulty":1,"question":"df.fillna(0) 会填充 DataFrame 中的哪些列？","options":["A) 只填第一列","B) 填所有列","C) 只填数值列","D) 都不填"],"correct_index":1,"explanation":"df.fillna(0) 作用在全表，所有列的空值都被填 0。"},
        {"knowledge_point":"fillna填充","type":"true_false","difficulty":1,"question":"df['age'].fillna(df['age'].mean()) 只会填充 age 这一列的缺失值。","options":["✅ 对","❌ 错"],"correct_index":0,"explanation":"指定了列名 'age'，所以只填充这一列。"},
        {"knowledge_point":"dropna删除","type":"true_false","difficulty":1,"question":"df.dropna(how='any') 删除的是所有列都为空的行。","options":["✅ 对","❌ 错"],"correct_index":1,"explanation":"how='any' 是任一列为空就删；how='all' 才是所有列都为空才删。"},
        {"knowledge_point":"DataFrame操作","type":"single_choice","difficulty":1,"question":"df[df['score']>80] 返回的是什么？","options":["A) 返回 score 列中大于80的值","B) 返回 score>80 的行","C) 返回 True/False 列表","D) 报错"],"correct_index":1,"explanation":"布尔索引在 DataFrame 上按行筛选，返回满足条件的整行。"},
        {"knowledge_point":"分组聚合","type":"single_choice","difficulty":2,"question":"对 df 按 city 分组统计 sales 总和，正确写法是？","options":["A) df.groupby('city').sum('sales')","B) df.groupby('city')['sales'].sum()","C) df.group('city').sum('sales')","D) df.sum().groupby('city','sales')"],"correct_index":1,"explanation":"先 groupby 分组，再选列，最后聚合函数。"},
        {"knowledge_point":"RFM三维度","type":"single_choice","difficulty":2,"question":"RFM 分析中，R 代表什么？","options":["A) Revenue 收入","B) Recency 最近一次购买距今","C) Retention 留存率","D) Rating 评分"],"correct_index":1,"explanation":"R=Recency 最近购买距今天数，越小说明客户越活跃。"},
    ]

    print(f"Inserting {len(questions)} quiz questions...")
    for q in questions:
        sb.table("quiz_questions").insert(q).execute()

    print("✅ Seed data inserted successfully!")


if __name__ == "__main__":
    seed()
