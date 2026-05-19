from app.schemas.create_novel import CreateNovelResult, FirstChapterSeed


def ensure_first_chapter(result: CreateNovelResult) -> FirstChapterSeed:
    return result.first_chapter

