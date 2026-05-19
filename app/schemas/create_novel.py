from typing import Any, Literal

from pydantic import BaseModel, Field


class NovelSeedInput(BaseModel):
    mode: Literal["minimal", "pro"] = "minimal"
    title: str
    genre: str = ""
    platform: str = ""
    target_reader: str = ""
    expected_word_count: int = 0
    chapter_word_count: int = 2500
    premise: str = ""
    protagonist: str = ""
    protagonist_goal: str = ""
    selling_points: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    expected_chapters: int = 100
    style_reference: str = ""
    core_conflict: str = ""
    story_highlights: str = ""
    major_characters: str = ""
    world_setting: str = ""
    ability_system: str = ""
    organizations: str = ""
    opening_event: str = ""
    first_volume_climax: str = ""
    midpoint_twist: str = ""
    ending_direction: str = ""
    hard_rules: list[str] = Field(default_factory=list)


class ProjectSeed(BaseModel):
    title: str
    genre: str = ""
    platform: str = ""
    target_reader: str = ""
    expected_chapters: int = 0
    chapter_word_count: int = 0
    logline: str = ""
    core_selling_points: list[str] = Field(default_factory=list)


class WorldRuleSeed(BaseModel):
    category: str = ""
    rule_text: str
    rigidity: str = "hard"
    source: str = "create_novel_wizard"


class CharacterSeed(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    role: str = ""
    appearance: str = ""
    personality: str = ""
    motivation: str = ""
    secrets: str = ""
    abilities: str = ""
    status: str = "active"
    current_location: str = ""
    hard_constraints: str = ""


class RelationshipSeed(BaseModel):
    character_a: str
    character_b: str
    relationship_type: str = ""
    status: str = ""
    description: str = ""
    evidence: str = "create_novel_wizard"


class LocationSeed(BaseModel):
    name: str
    type: str = ""
    description: str = ""
    rules: str = ""
    connected_locations: list[str] = Field(default_factory=list)


class OrganizationSeed(BaseModel):
    name: str
    type: str = ""
    description: str = ""
    leader: str = ""
    allies: list[str] = Field(default_factory=list)
    enemies: list[str] = Field(default_factory=list)
    status: str = ""


class AbilitySeed(BaseModel):
    name: str
    owner: str = ""
    system: str = ""
    description: str = ""
    limitations: str = ""
    cost: str = ""
    level: str = ""


class ItemSeed(BaseModel):
    name: str
    type: str = ""
    description: str = ""
    owner: str = ""
    location: str = ""
    status: str = ""
    constraints: str = ""


class PlotThreadSeed(BaseModel):
    name: str
    thread_type: str = ""
    status: str = "open"
    summary: str = ""
    related_characters: list[str] = Field(default_factory=list)


class ForeshadowSeed(BaseModel):
    name: str
    related_characters: list[str] = Field(default_factory=list)
    related_items: list[str] = Field(default_factory=list)
    related_thread: str = ""
    status: str = "unresolved"
    expected_resolution_chapter: int | None = None
    resolution_method: str = ""
    risk_note: str = ""
    evidence: str = "create_novel_wizard"


class TimelineEventSeed(BaseModel):
    story_time: str = ""
    sort_key: str = ""
    event_text: str
    location: str = ""
    characters: list[str] = Field(default_factory=list)
    duration: str = ""
    confidence: float = 1.0


class StyleProfileSeed(BaseModel):
    name: str = "默认文风"
    platform: str = ""
    pov: str = ""
    sentence_length: str = ""
    dialogue_ratio: str = ""
    description_ratio: str = ""
    inner_monologue_ratio: str = ""
    high_point_density: str = ""
    common_patterns: list[str] = Field(default_factory=list)
    banned_expressions: list[str] = Field(default_factory=list)
    pacing: str = ""
    sample_text: str = ""
    profile: dict[str, Any] = Field(default_factory=dict)


class ForbiddenRuleSeed(BaseModel):
    rule_text: str
    category: str = ""
    severity: str = "critical"
    source: str = "create_novel_wizard"


class UnresolvedQuestionSeed(BaseModel):
    question: str
    related_thread: str = ""
    related_characters: list[str] = Field(default_factory=list)
    status: str = "open"
    priority: str = "medium"
    notes: str = ""


class ChapterOutlineSeed(BaseModel):
    chapter_number: int
    title: str
    chapter_goal: str = ""
    main_conflict: str = ""
    characters: list[str] = Field(default_factory=list)
    key_events: list[str] = Field(default_factory=list)
    new_information: list[str] = Field(default_factory=list)
    foreshadows: list[str] = Field(default_factory=list)
    ending_hook: str = ""
    memory_facts: list[str] = Field(default_factory=list)


class FirstChapterSeed(BaseModel):
    title: str
    content: str
    summary: str = ""
    facts: list[str] = Field(default_factory=list)


class CreateNovelResult(BaseModel):
    project: ProjectSeed
    world_rules: list[WorldRuleSeed] = Field(default_factory=list)
    characters: list[CharacterSeed] = Field(default_factory=list)
    relationships: list[RelationshipSeed] = Field(default_factory=list)
    locations: list[LocationSeed] = Field(default_factory=list)
    organizations: list[OrganizationSeed] = Field(default_factory=list)
    abilities: list[AbilitySeed] = Field(default_factory=list)
    items: list[ItemSeed] = Field(default_factory=list)
    plot_threads: list[PlotThreadSeed] = Field(default_factory=list)
    foreshadows: list[ForeshadowSeed] = Field(default_factory=list)
    timeline_events: list[TimelineEventSeed] = Field(default_factory=list)
    style_profile: StyleProfileSeed = Field(default_factory=StyleProfileSeed)
    forbidden_rules: list[ForbiddenRuleSeed] = Field(default_factory=list)
    unresolved_questions: list[UnresolvedQuestionSeed] = Field(default_factory=list)
    volume_outline: list[str] = Field(default_factory=list)
    chapter_outlines: list[ChapterOutlineSeed] = Field(default_factory=list)
    first_chapter: FirstChapterSeed

