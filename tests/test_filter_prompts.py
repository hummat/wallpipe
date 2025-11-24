from filter import build_clip_prompts


def test_build_clip_prompts_general():
    prompts = build_clip_prompts(["car"], context="general")
    assert any("photo of car" in p for p in prompts)
    assert any("illustration of car" in p for p in prompts)
    assert any("render of car" in p for p in prompts)


def test_build_clip_prompts_nsfw():
    prompts = build_clip_prompts(["nude"], context="nsfw")
    assert any("explicit photo of nude" in p for p in prompts)
    assert any("pornographic image of nude" in p for p in prompts)
    assert any("nude photo of nude" in p for p in prompts)


def test_build_clip_prompts_empty():
    assert build_clip_prompts([], context="general") == []
