"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def get_prompt_data():
    prompts = load_prompts(str(PROMPT_FILE))
    if "bug_to_user_story_v2" in prompts:
        return prompts["bug_to_user_story_v2"]
    return prompts


def collect_prompt_text(prompt_data: dict) -> str:
    parts = [
        str(prompt_data.get("system_prompt", "")),
        str(prompt_data.get("user_prompt", "")),
        str(prompt_data.get("description", "")),
        yaml.safe_dump(prompt_data.get("few_shot_examples", []), allow_unicode=True),
    ]
    return "\n".join(parts)

class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt_data = get_prompt_data()
        assert "system_prompt" in prompt_data
        assert isinstance(prompt_data["system_prompt"], str)
        assert prompt_data["system_prompt"].strip() != ""

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        prompt_data = get_prompt_data()
        system_prompt = prompt_data.get("system_prompt", "").lower()
        role_keywords = [
            "você é um product manager",
            "você é uma product manager",
            "assistente especializado",
            "especializado em",
        ]
        assert any(keyword in system_prompt for keyword in role_keywords)

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        prompt_data = get_prompt_data()
        full_text = collect_prompt_text(prompt_data).lower()
        assert ("markdown" in full_text) or ("como um" in full_text and "eu quero" in full_text and "para que" in full_text)

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompt_data = get_prompt_data()
        examples = prompt_data.get("few_shot_examples", [])
        full_text = collect_prompt_text(prompt_data).lower()

        has_examples_field = isinstance(examples, list) and len(examples) >= 1
        has_examples_in_text = "exemplo" in full_text and ("entrada" in full_text or "saída" in full_text)

        assert has_examples_field or has_examples_in_text

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt_data = get_prompt_data()
        full_text = collect_prompt_text(prompt_data).lower()
        assert "[todo]" not in full_text
        assert "todo:" not in full_text

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        prompt_data = get_prompt_data()
        is_valid, errors = validate_prompt_structure(prompt_data)
        techniques = prompt_data.get("techniques_applied", [])

        assert isinstance(techniques, list)
        assert len(techniques) >= 2
        assert is_valid, f"Prompt inválido pela validação estrutural: {errors}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
