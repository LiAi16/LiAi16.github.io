CLASSIC_SCENES = [
    {
        "query": "预算300元内，适合春季通勤的女士轻薄外套",
        "context": {"channel": "search", "city": "guangzhou", "season": "spring"},
        "user_profile": {
            "user_id": "classic_u_001",
            "gender": "female",
            "age_bucket": "25-34",
            "price_preference": "mid",
            "style_preference": ["commute", "minimal"],
            "recent_behaviors": ["clicked_trench_coat", "favorited_light_jacket"],
        },
    },
    {
        "query": "给我推荐适合初夏通勤的简约女士外套，预算320元内",
        "context": {"channel": "search", "city": "shenzhen", "season": "summer"},
        "user_profile": {
            "user_id": "classic_u_002",
            "gender": "female",
            "age_bucket": "25-34",
            "price_preference": "mid",
            "style_preference": ["minimal", "office"],
            "recent_behaviors": ["clicked_light_blazer", "viewed_commute_outerwear"],
        },
    },
    {
        "query": "预算350元内，适合办公室穿的女士通勤外套，风格尽量简洁",
        "context": {"channel": "search", "city": "hangzhou", "season": "spring"},
        "user_profile": {
            "user_id": "classic_u_003",
            "gender": "female",
            "age_bucket": "30-39",
            "price_preference": "mid",
            "style_preference": ["commute", "clean"],
            "recent_behaviors": ["clicked_office_jacket", "saved_minimal_outerwear"],
        },
    },
    {
        "query": "想买一件适合春秋通勤的轻薄女士外套，预算280元左右",
        "context": {"channel": "search", "city": "nanjing", "season": "spring"},
        "user_profile": {
            "user_id": "classic_u_004",
            "gender": "female",
            "age_bucket": "25-34",
            "price_preference": "mid_low",
            "style_preference": ["lightweight", "commute"],
            "recent_behaviors": ["viewed_short_jacket", "clicked_spring_outerwear"],
        },
    },
    {
        "query": "帮我找几款适合上班路上穿的女士轻便外套，预算300以内",
        "context": {"channel": "search", "city": "chengdu", "season": "spring"},
        "user_profile": {
            "user_id": "classic_u_005",
            "gender": "female",
            "age_bucket": "25-34",
            "price_preference": "mid_low",
            "style_preference": ["commute", "practical"],
            "recent_behaviors": ["clicked_basic_outerwear", "clicked_light_jacket"],
        },
    },
    {
        "query": "推荐适合南方春天办公室穿的女士通勤外套，预算350元内",
        "context": {"channel": "search", "city": "xiamen", "season": "spring"},
        "user_profile": {
            "user_id": "classic_u_006",
            "gender": "female",
            "age_bucket": "30-39",
            "price_preference": "mid",
            "style_preference": ["office", "minimal"],
            "recent_behaviors": ["viewed_office_style", "favorited_minimal_jacket"],
        },
    },
    {
        "query": "预算300元左右，想买件适合地铁通勤的女士薄外套",
        "context": {"channel": "search", "city": "wuhan", "season": "spring"},
        "user_profile": {
            "user_id": "classic_u_007",
            "gender": "female",
            "age_bucket": "20-29",
            "price_preference": "mid_low",
            "style_preference": ["lightweight", "urban_commute"],
            "recent_behaviors": ["clicked_bomber_jacket", "viewed_spring_commute"],
        },
    },
    {
        "query": "给我推荐适合工作日通勤穿的女士外套，预算不超过330元",
        "context": {"channel": "search", "city": "suzhou", "season": "spring"},
        "user_profile": {
            "user_id": "classic_u_008",
            "gender": "female",
            "age_bucket": "25-34",
            "price_preference": "mid",
            "style_preference": ["clean", "office"],
            "recent_behaviors": ["viewed_clean_style", "clicked_commute_jacket"],
        },
    },
]


LLM_HYBRID_SCENES = [
    {
        "query": "给我推荐三款适合上班通勤的女士鞋子，预算500元内，最好简约一点，并说明理由",
        "context": {"channel": "chat_assistant", "city": "shanghai", "season": "spring"},
        "user_profile": {
            "user_id": "llm_u_001",
            "gender": "female",
            "age_bucket": "25-34",
            "style_preference": ["minimal", "commute"],
            "price_preference": "mid",
        },
    },
    {
        "query": "推荐三款适合办公室穿的女士通勤鞋，预算450元内，风格基础一点，并说明推荐理由",
        "context": {"channel": "chat_assistant", "city": "beijing", "season": "spring"},
        "user_profile": {
            "user_id": "llm_u_002",
            "gender": "female",
            "age_bucket": "25-34",
            "style_preference": ["basic", "office"],
            "price_preference": "mid",
        },
    },
    {
        "query": "想买几双适合日常上班穿的简约女士鞋，预算500以内，帮我解释一下推荐逻辑",
        "context": {"channel": "chat_assistant", "city": "shenzhen", "season": "summer"},
        "user_profile": {
            "user_id": "llm_u_003",
            "gender": "female",
            "age_bucket": "20-29",
            "style_preference": ["minimal", "daily_commute"],
            "price_preference": "mid",
        },
    },
    {
        "query": "帮我挑三款适合面试和办公室穿搭的女士鞋子，预算500元内，尽量简洁大方",
        "context": {"channel": "chat_assistant", "city": "guangzhou", "season": "spring"},
        "user_profile": {
            "user_id": "llm_u_004",
            "gender": "female",
            "age_bucket": "22-30",
            "style_preference": ["clean", "formal_commute"],
            "price_preference": "mid",
        },
    },
    {
        "query": "推荐三双适合久站通勤的女士鞋子，预算500元以内，风格简约，最好说明各自特点",
        "context": {"channel": "chat_assistant", "city": "hangzhou", "season": "autumn"},
        "user_profile": {
            "user_id": "llm_u_005",
            "gender": "female",
            "age_bucket": "30-39",
            "style_preference": ["minimal", "practical"],
            "price_preference": "mid",
        },
    },
    {
        "query": "给我找几款适合商务休闲风的女士通勤鞋，预算500以内，并说明为什么适合上班穿",
        "context": {"channel": "chat_assistant", "city": "nanjing", "season": "spring"},
        "user_profile": {
            "user_id": "llm_u_006",
            "gender": "female",
            "age_bucket": "25-34",
            "style_preference": ["business_casual", "office"],
            "price_preference": "mid",
        },
    },
    {
        "query": "我想要三款基础款女士通勤鞋，预算500元以内，最好百搭一点，请附上理由",
        "context": {"channel": "chat_assistant", "city": "chengdu", "season": "spring"},
        "user_profile": {
            "user_id": "llm_u_007",
            "gender": "female",
            "age_bucket": "25-34",
            "style_preference": ["basic", "versatile"],
            "price_preference": "mid",
        },
    },
    {
        "query": "推荐三双适合春季办公室穿的女士鞋，预算500元内，简约耐看一些，并解释原因",
        "context": {"channel": "chat_assistant", "city": "wuhan", "season": "spring"},
        "user_profile": {
            "user_id": "llm_u_008",
            "gender": "female",
            "age_bucket": "25-34",
            "style_preference": ["simple", "commute"],
            "price_preference": "mid",
        },
    },
]


COMPOSITE_ENHANCED_SCENES = [
    {
        "query": "帮我推荐两款适合作为女生生日礼物的香薰，预算200元内，最好包装精致一点，并确认广州仓有货，说明推荐理由",
        "context": {"channel": "chat_assistant", "city": "guangzhou", "festival": "birthday_gift"},
        "user_profile": {
            "user_id": "comp_u_001",
            "gender": "female",
            "gift_preference": ["practical", "good_packaging"],
            "price_preference": "mid_low",
        },
    },
    {
        "query": "推荐两款适合作为闺蜜生日礼物的香薰，预算200元以内，包装要适合送礼，并确认深圳仓有货",
        "context": {"channel": "chat_assistant", "city": "shenzhen", "festival": "birthday_gift"},
        "user_profile": {
            "user_id": "comp_u_002",
            "gender": "female",
            "gift_preference": ["giftable", "good_packaging"],
            "price_preference": "mid_low",
        },
    },
    {
        "query": "帮我挑两款适合送女生朋友的香薰，预算不超过200元，优先考虑包装完整和礼物属性，并确认上海仓库存",
        "context": {"channel": "chat_assistant", "city": "shanghai", "festival": "friend_gift"},
        "user_profile": {
            "user_id": "comp_u_003",
            "gender": "female",
            "gift_preference": ["friend_gift", "good_packaging"],
            "price_preference": "mid_low",
        },
    },
    {
        "query": "给我推荐两款适合节日送礼的香薰，预算200元内，最好看起来精致一些，并查一下杭州仓是否有货",
        "context": {"channel": "chat_assistant", "city": "hangzhou", "festival": "holiday_gift"},
        "user_profile": {
            "user_id": "comp_u_004",
            "gender": "female",
            "gift_preference": ["holiday_gift", "giftable"],
            "price_preference": "mid_low",
        },
    },
    {
        "query": "推荐两款适合作为纪念日礼物的香薰，预算200以内，包装要好，顺便确认南京仓库存并说明理由",
        "context": {"channel": "chat_assistant", "city": "nanjing", "festival": "anniversary_gift"},
        "user_profile": {
            "user_id": "comp_u_005",
            "gender": "female",
            "gift_preference": ["anniversary", "good_packaging"],
            "price_preference": "mid_low",
        },
    },
    {
        "query": "帮我推荐两款适合送礼的香薰，预算200元以内，要求包装体面一点，并确认成都仓有货",
        "context": {"channel": "chat_assistant", "city": "chengdu", "festival": "gift"},
        "user_profile": {
            "user_id": "comp_u_006",
            "gender": "female",
            "gift_preference": ["giftable", "formal_gift"],
            "price_preference": "mid_low",
        },
    },
    {
        "query": "推荐两款适合女生生日送礼的香薰，预算200内，希望包装完整且香型温和，并确认武汉仓库存",
        "context": {"channel": "chat_assistant", "city": "wuhan", "festival": "birthday_gift"},
        "user_profile": {
            "user_id": "comp_u_007",
            "gender": "female",
            "gift_preference": ["birthday", "gentle_style"],
            "price_preference": "mid_low",
        },
    },
    {
        "query": "给我找两款适合作为女性礼物的香薰，预算控制在200元内，包装精致，顺便查一下厦门仓是否有货",
        "context": {"channel": "chat_assistant", "city": "xiamen", "festival": "gift"},
        "user_profile": {
            "user_id": "comp_u_008",
            "gender": "female",
            "gift_preference": ["giftable", "good_packaging"],
            "price_preference": "mid_low",
        },
    },
]
