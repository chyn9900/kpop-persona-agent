"""페르소나 카드(persona/artist_card.yaml) 구조 검증.

왜 필요한가: 카드는 시스템 프롬프트·평가 정답의 원본이라, 필드가 빠지거나
형식이 깨지면 뒤 단계가 조용히 잘못 돌아간다. 가장 먼저 잡아야 할 오류다.
"""

from pathlib import Path

import yaml

CARD_PATH = Path(__file__).resolve().parents[1] / "persona" / "artist_card.yaml"


def load_card() -> dict:
    with CARD_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_card_has_required_sections():
    card = load_card()
    for key in ["meta", "group", "speaker", "speech_style", "forbidden", "timeline", "fan_memory"]:
        assert key in card, f"카드에 '{key}' 섹션이 없다"


def test_exactly_one_speaker_member():
    # 챗봇은 멤버 한 명으로만 말해야 한다 (일관성 측정 단위)
    members = load_card()["group"]["members"]
    speakers = [m for m in members if m.get("is_speaker")]
    assert len(speakers) == 1
    assert speakers[0]["name"] == load_card()["speaker"]["name"]


def test_persona_statements_are_first_person_sentences():
    # "나는 ~다." 형식: judge가 문장 단위로 위반을 묻기 위한 규약
    statements = load_card()["speaker"]["persona_statements"]
    assert len(statements) >= 10
    for s in statements:
        assert s.startswith("나는 "), f"1인칭으로 시작해야 함: {s}"
        assert s.endswith("다."), f"'다.'로 끝나야 함: {s}"


def test_fan_memory_store_and_block_lists_do_not_overlap():
    fm = load_card()["fan_memory"]
    assert fm["store"] and fm["do_not_store"]
    assert not set(fm["store"]) & set(fm["do_not_store"])
