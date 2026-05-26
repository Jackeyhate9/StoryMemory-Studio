from app.llm.output_cleaner import clean_model_output


def test_cleaner_removes_closed_think_block():
    text = "<think>I need to plan this.</think>\n正文第一句。"
    assert clean_model_output(text) == "正文第一句。"


def test_cleaner_removes_unclosed_think_block_and_keeps_prose():
    text = """<think>
1. Analyze User Input:
- Ending Hook: Let's use a seal.
*(Opening)* 这是草稿提示，不应保留。
磨玉盆里的水已经浑成乳白色。改松岩搁下青铜尺，指尖在粗麻布上蹭去残留的玉粉。沈青梧站在柜台后，没有立刻问价。"""
    cleaned = clean_model_output(text)
    assert "<think>" not in cleaned
    assert "Analyze User Input" not in cleaned
    assert "Let's" not in cleaned
    assert "Opening" not in cleaned
    assert cleaned.startswith("磨玉盆里的水已经浑成乳白色。")


def test_cleaner_removes_bulleted_english_planning_lines():
    text = """正文第一段。
    - I'll distribute these naturally. Ending hook: specific sound/object.
    - *Jade Details:* Included 水磨 and 鱼鳞背; I'll add more detail.
    - Let's write carefully.
        - Check ending hook.
    (Opening) 账房的窗纸糊得严实。"""
    cleaned = clean_model_output(text)
    assert "I'll" not in cleaned
    assert "Let's" not in cleaned
    assert "Jade Details" not in cleaned
    assert "Check ending hook" not in cleaned
    assert "(Opening)" not in cleaned
    assert "账房的窗纸糊得严实。" in cleaned


def test_cleaner_cuts_editor_appendix_after_valid_prose():
    text = """改松岩看着剪报边缘的小字，半晌没动。

“碎玉可补，旧债难清。”

*Added content:*
堂屋的角门吱呀一声，this is an editor note.
*   End on specific object: clipping.
*Final Polish:*
Need to connect to Ch1."""
    cleaned = clean_model_output(text)
    assert "Added content" not in cleaned
    assert "Final Polish" not in cleaned
    assert "Need to" not in cleaned
    assert cleaned.endswith("“碎玉可补，旧债难清。”")


def test_cleaner_cuts_word_count_check_appendix():
    text = """门轴再次转动，风灌进来，吹得账册的缺页翻动了一角。

*Word Count Check*
- around 1200 Chinese chars
- no English please"""
    cleaned = clean_model_output(text)
    assert "Word Count Check" not in cleaned
    assert "around 1200" not in cleaned
    assert cleaned.endswith("门轴再次转动，风灌进来，吹得账册的缺页翻动了一角。")
