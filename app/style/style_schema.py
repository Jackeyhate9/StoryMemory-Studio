from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StyleProfileInput(BaseModel):
    style_name: str
    samples: list[str] = Field(default_factory=list)
    source_note: str = ""
    target_usage: list[str] = Field(default_factory=list)
    save_source: bool = False
    project_only: bool = True
    set_default: bool = False


class SentenceRhythmProfile(BaseModel):
    average: str = ""
    variation: str = ""
    short_sentence_ratio: str = ""
    long_sentence_ratio: str = ""


class NarrativeVoiceProfile(BaseModel):
    narrative_pov: str = ""
    tense: str = ""


class DialogueProfile(BaseModel):
    dialogue_ratio: str = ""
    dialogue_speed: str = ""
    subtext_level: str = ""
    common_dialogue_functions: list[str] = Field(default_factory=list)


class EmotionProfile(BaseModel):
    emotion_intensity: str = ""
    emotion_expression_mode: str = ""
    inner_monologue_ratio: str = ""
    restraint_level: str = ""


class PacingProfile(BaseModel):
    scene_speed: str = ""
    conflict_frequency: str = ""
    cliffhanger_frequency: str = ""
    information_release_pattern: str = ""


class ImageryProfile(BaseModel):
    sensory_focus: list[str] = Field(default_factory=list)
    visual_density: str = ""
    metaphor_density: str = ""
    action_detail_level: str = ""


class HookProfile(BaseModel):
    opening_hook_methods: list[str] = Field(default_factory=list)
    chapter_ending_hook_methods: list[str] = Field(default_factory=list)
    suspense_methods: list[str] = Field(default_factory=list)


class PlatformStyleProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    language_register: str = Field(default="", alias="register")
    common_word_types: list[str] = Field(default_factory=list)
    avoid_word_types: list[str] = Field(default_factory=list)
    platform_specific_terms: list[str] = Field(default_factory=list)


class ForbiddenImitationRule(BaseModel):
    rule: str


class ParagraphStyleProfile(BaseModel):
    average_paragraph_length: str = ""
    line_break_frequency: str = ""
    white_space_style: str = ""


class StructureStyleProfile(BaseModel):
    scene_transition_methods: list[str] = Field(default_factory=list)
    flashback_usage: str = ""
    reversal_frequency: str = ""
    foreshadowing_style: str = ""


class StyleProfileResult(BaseModel):
    style_name: str
    source_summary: str = ""
    language: str = "zh"
    target_usage: list[str] = Field(default_factory=list)
    narrative_pov: str = ""
    tense: str = ""
    sentence_length: SentenceRhythmProfile = Field(default_factory=SentenceRhythmProfile)
    paragraph_style: ParagraphStyleProfile = Field(default_factory=ParagraphStyleProfile)
    dialogue_style: DialogueProfile = Field(default_factory=DialogueProfile)
    description_style: ImageryProfile = Field(default_factory=ImageryProfile)
    emotion_style: EmotionProfile = Field(default_factory=EmotionProfile)
    pacing_style: PacingProfile = Field(default_factory=PacingProfile)
    hook_style: HookProfile = Field(default_factory=HookProfile)
    word_choice: PlatformStyleProfile = Field(default_factory=PlatformStyleProfile)
    structure_style: StructureStyleProfile = Field(default_factory=StructureStyleProfile)
    do_rules: list[str] = Field(default_factory=list)
    dont_rules: list[str] = Field(default_factory=list)
    safe_style_summary: str = ""
    forbidden_copy_rules: list[str] = Field(
        default_factory=lambda: [
            "Do not reuse exact sentences from the sample.",
            "Do not reuse unique metaphors from the sample.",
            "Do not reuse named characters, locations, or proprietary settings from the sample.",
            "Do not keep the same paragraph order or event sequence.",
            "Do not generate text that is substantially similar to the sample.",
        ]
    )


class SimilarityReport(BaseModel):
    risk_level: Literal["low", "medium", "high"] = "low"
    overlap_score: float = 0.0
    matched_phrases: list[str] = Field(default_factory=list)
    reason: str = ""
    rewrite_required: bool = False
