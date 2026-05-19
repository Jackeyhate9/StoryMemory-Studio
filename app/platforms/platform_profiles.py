from __future__ import annotations

from app.platforms.platform_schema import PlatformProfile


BUILTIN_PROFILES: dict[str, PlatformProfile] = {
    "番茄小说": PlatformProfile(platform_name="番茄小说", chapter_opening="开头快，前 300 字进入冲突", pacing="强冲突，高频爽点，少铺垫", dialogue="直接，有信息量", description="少大段设定说明，多动作推进", ending_hook="每章结尾要有明确钩子", avoid=["慢热", "长篇世界观解释", "过度文艺化"], best_for=["都市爽文", "悬疑反转", "重生逆袭", "短剧化故事"]),
    "起点中文网": PlatformProfile(platform_name="起点中文网", chapter_opening="允许一定铺垫，但需明确目标和升级路径", pacing="主线成长、体系感、阶段性收益", dialogue="兼顾信息和人物气质", description="世界观可展开但要服务冲突", ending_hook="章节结尾推进目标或体系升级", avoid=["无目标闲聊", "体系混乱"], best_for=["玄幻", "仙侠", "科幻", "历史"]),
    "晋江文学城": PlatformProfile(platform_name="晋江文学城", chapter_opening="人物关系和情绪张力优先", pacing="情绪推进、关系变化、人物弧光", dialogue="有潜台词，避免直白说教", description="细腻但不拖沓", ending_hook="关系选择或情绪悬念", avoid=["粗暴爽点", "人物工具化"], best_for=["言情", "纯爱", "情绪流", "群像"]),
    "七猫": PlatformProfile(platform_name="七猫", chapter_opening="清晰、直给、快速建立期待", pacing="节奏稳定，冲突密集", dialogue="通俗易懂", description="画面明确", ending_hook="明确反转或未解问题", avoid=["晦涩表达", "过慢铺垫"], best_for=["都市", "悬疑", "女频情感"]),
    "短剧": PlatformProfile(platform_name="短剧", chapter_opening="前三秒有冲突或强视觉动作", pacing="每场一个冲突，每集一个反转", dialogue="短句、强情绪、可表演", description="动作和场景可拍摄", ending_hook="强反转卡点", avoid=["内心独白过长", "不可拍摄设定"], best_for=["复仇", "逆袭", "悬疑", "情感拉扯"]),
    "漫画分镜": PlatformProfile(platform_name="漫画分镜", chapter_opening="视觉钩子优先", pacing="按格推进，动作和表情清晰", dialogue="短对白，留画面空间", description="转为镜头、构图、动作", ending_hook="最后一格有视觉冲击", avoid=["大段旁白", "抽象心理"], best_for=["奇幻", "悬疑", "恋爱", "动作"]),
    "小红书推文": PlatformProfile(platform_name="小红书推文", chapter_opening="标题党但不欺骗，前三行给看点", pacing="短段落、强情绪、强卖点", dialogue="可摘金句", description="少设定，多情绪和反转", ending_hook="评论区互动或追更钩子", avoid=["长段正文", "复杂设定"], best_for=["推书", "剧情解说", "人物安利"]),
    "AI 视频分镜": PlatformProfile(platform_name="AI 视频分镜", chapter_opening="强画面、明确主体和环境", pacing="镜头连续，动作可视化", dialogue="少对白，多画面提示", description="光影、镜头、运动清晰", ending_hook="最后镜头形成悬念", avoid=["抽象概念", "不可视化心理"], best_for=["短视频", "预告片", "AI 漫剧"]),
}


def get_platform_profile(platform: str) -> PlatformProfile:
    return BUILTIN_PROFILES.get(platform) or BUILTIN_PROFILES["番茄小说"]
