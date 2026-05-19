PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    genre TEXT DEFAULT '',
    target_platform TEXT DEFAULT '',
    current_volume TEXT DEFAULT '',
    status TEXT DEFAULT 'active',
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    aliases_json TEXT DEFAULT '[]',
    role TEXT DEFAULT '',
    appearance TEXT DEFAULT '',
    personality TEXT DEFAULT '',
    motivation TEXT DEFAULT '',
    secrets TEXT DEFAULT '',
    abilities TEXT DEFAULT '',
    status TEXT DEFAULT 'active',
    current_location TEXT DEFAULT '',
    hard_constraints TEXT DEFAULT '',
    importance INTEGER DEFAULT 50,
    first_chapter_id INTEGER,
    last_seen_chapter_id INTEGER,
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, name),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    character_a_id INTEGER,
    character_b_id INTEGER,
    character_a_name TEXT NOT NULL,
    character_b_name TEXT NOT NULL,
    relationship_type TEXT DEFAULT '',
    status TEXT DEFAULT '',
    description TEXT DEFAULT '',
    evidence TEXT DEFAULT '',
    chapter_id INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS world_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    category TEXT DEFAULT '',
    rule_text TEXT NOT NULL,
    rigidity TEXT DEFAULT 'hard',
    source TEXT DEFAULT '',
    chapter_id INTEGER,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT DEFAULT '',
    description TEXT DEFAULT '',
    rules TEXT DEFAULT '',
    connected_locations_json TEXT DEFAULT '[]',
    first_chapter_id INTEGER,
    metadata_json TEXT DEFAULT '{}',
    UNIQUE(project_id, name),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT DEFAULT '',
    description TEXT DEFAULT '',
    leader TEXT DEFAULT '',
    allies_json TEXT DEFAULT '[]',
    enemies_json TEXT DEFAULT '[]',
    status TEXT DEFAULT '',
    UNIQUE(project_id, name),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT DEFAULT '',
    description TEXT DEFAULT '',
    owner TEXT DEFAULT '',
    location TEXT DEFAULT '',
    status TEXT DEFAULT '',
    constraints TEXT DEFAULT '',
    first_chapter_id INTEGER,
    UNIQUE(project_id, name),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS abilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    owner TEXT DEFAULT '',
    system TEXT DEFAULT '',
    description TEXT DEFAULT '',
    limitations TEXT DEFAULT '',
    cost TEXT DEFAULT '',
    level TEXT DEFAULT '',
    UNIQUE(project_id, name, owner),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,
    volume TEXT DEFAULT '',
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    outline TEXT DEFAULT '',
    status TEXT DEFAULT 'draft',
    word_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, chapter_number),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chapter_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_id INTEGER NOT NULL UNIQUE,
    short_summary TEXT DEFAULT '',
    detailed_summary TEXT DEFAULT '',
    key_characters_json TEXT DEFAULT '[]',
    key_locations_json TEXT DEFAULT '[]',
    plot_threads_json TEXT DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chapter_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_id INTEGER NOT NULL,
    fact_type TEXT DEFAULT '',
    subject TEXT DEFAULT '',
    predicate TEXT DEFAULT '',
    object TEXT DEFAULT '',
    fact_text TEXT NOT NULL,
    certainty REAL DEFAULT 1.0,
    source_quote TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS plot_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    thread_type TEXT DEFAULT '',
    status TEXT DEFAULT 'open',
    summary TEXT DEFAULT '',
    related_characters_json TEXT DEFAULT '[]',
    first_chapter_id INTEGER,
    last_chapter_id INTEGER,
    UNIQUE(project_id, name),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS foreshadows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    first_chapter_id INTEGER,
    related_characters_json TEXT DEFAULT '[]',
    related_items_json TEXT DEFAULT '[]',
    related_thread TEXT DEFAULT '',
    status TEXT DEFAULT 'unresolved',
    expected_resolution_chapter INTEGER,
    resolution_method TEXT DEFAULT '',
    last_mentioned_chapter_id INTEGER,
    risk_note TEXT DEFAULT '',
    evidence TEXT DEFAULT '',
    UNIQUE(project_id, name),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS timeline_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_id INTEGER,
    story_time TEXT DEFAULT '',
    sort_key TEXT DEFAULT '',
    event_text TEXT NOT NULL,
    location TEXT DEFAULT '',
    characters_json TEXT DEFAULT '[]',
    duration TEXT DEFAULT '',
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS style_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    platform TEXT DEFAULT '',
    pov TEXT DEFAULT '',
    sentence_length TEXT DEFAULT '',
    dialogue_ratio TEXT DEFAULT '',
    description_ratio TEXT DEFAULT '',
    inner_monologue_ratio TEXT DEFAULT '',
    high_point_density TEXT DEFAULT '',
    common_patterns_json TEXT DEFAULT '[]',
    banned_expressions_json TEXT DEFAULT '[]',
    pacing TEXT DEFAULT '',
    sample_text TEXT DEFAULT '',
    profile_json TEXT DEFAULT '{}',
    is_default INTEGER DEFAULT 0,
    UNIQUE(project_id, name),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS style_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    style_profile_id INTEGER,
    sample_title TEXT DEFAULT '',
    sample_text_hash TEXT NOT NULL,
    sample_excerpt_safe TEXT DEFAULT '',
    sample_text TEXT,
    sample_length INTEGER DEFAULT 0,
    source_note TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(style_profile_id) REFERENCES style_profiles(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS forbidden_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    rule_text TEXT NOT NULL,
    category TEXT DEFAULT '',
    severity TEXT DEFAULT 'critical',
    source TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS unresolved_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    related_thread TEXT DEFAULT '',
    related_characters_json TEXT DEFAULT '[]',
    first_chapter_id INTEGER,
    status TEXT DEFAULT 'open',
    priority TEXT DEFAULT 'medium',
    notes TEXT DEFAULT '',
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS memory_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    source_id INTEGER,
    chunk_type TEXT DEFAULT '',
    title TEXT DEFAULT '',
    content TEXT NOT NULL,
    keywords_json TEXT DEFAULT '[]',
    embedding_json TEXT,
    importance INTEGER DEFAULT 50,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_id INTEGER,
    operation TEXT NOT NULL,
    provider TEXT DEFAULT '',
    model TEXT DEFAULT '',
    prompt_hash TEXT DEFAULT '',
    prompt_preview TEXT DEFAULT '',
    response_preview TEXT DEFAULT '',
    structured_json TEXT DEFAULT '{}',
    status TEXT DEFAULT 'success',
    error TEXT DEFAULT '',
    module_name TEXT DEFAULT '',
    input_summary TEXT DEFAULT '',
    output_json TEXT DEFAULT '{}',
    user_action TEXT DEFAULT '',
    applied_to_chapter INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quality_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_id INTEGER,
    report_type TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    risk_level TEXT DEFAULT 'low',
    report_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS adaptation_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_id INTEGER,
    adaptation_type TEXT NOT NULL,
    output_json TEXT DEFAULT '{}',
    output_markdown TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS platform_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name TEXT NOT NULL UNIQUE,
    profile_json TEXT NOT NULL,
    is_builtin INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS character_arcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    chapter_id INTEGER,
    current_goal TEXT DEFAULT '',
    psychological_state TEXT DEFAULT '',
    relationship_state_json TEXT DEFAULT '[]',
    ability_state_json TEXT DEFAULT '[]',
    moral_position TEXT DEFAULT '',
    emotional_progress TEXT DEFAULT '',
    arc_stage TEXT DEFAULT '',
    key_behavior TEXT DEFAULT '',
    contradiction_risk TEXT DEFAULT 'low',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS character_presence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    chapter_id INTEGER,
    presence_type TEXT DEFAULT 'scene',
    importance INTEGER DEFAULT 50,
    mentioned_only INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS edit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    row_id INTEGER,
    action TEXT NOT NULL,
    before_json TEXT DEFAULT '{}',
    after_json TEXT DEFAULT '{}',
    note TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chapters_project_number ON chapters(project_id, chapter_number);
CREATE INDEX IF NOT EXISTS idx_facts_project_chapter ON chapter_facts(project_id, chapter_id);
CREATE INDEX IF NOT EXISTS idx_chunks_project_type ON memory_chunks(project_id, chunk_type);
CREATE INDEX IF NOT EXISTS idx_timeline_project_sort ON timeline_events(project_id, sort_key);
CREATE INDEX IF NOT EXISTS idx_quality_project_chapter ON quality_reports(project_id, chapter_id);
CREATE INDEX IF NOT EXISTS idx_adapt_project_chapter ON adaptation_outputs(project_id, chapter_id);
CREATE INDEX IF NOT EXISTS idx_arc_project_character ON character_arcs(project_id, character_id);
CREATE INDEX IF NOT EXISTS idx_edit_logs_project_table ON edit_logs(project_id, table_name, row_id);
