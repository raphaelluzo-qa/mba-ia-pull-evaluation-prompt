"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    full_prompt_name = f"{username}/{prompt_name}"

    system_prompt = prompt_data.get("system_prompt", "").strip()
    user_prompt = prompt_data.get("user_prompt", "{bug_report}").strip()
    description = prompt_data.get("description", f"Prompt otimizado: {prompt_name}")

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt),
    ])

    print(f"🚀 Publicando prompt: {full_prompt_name}")

    metadata = {
        "tags": prompt_data.get("tags", []),
        "techniques_applied": prompt_data.get("techniques_applied", []),
        "version": prompt_data.get("version"),
    }
    print(f"   Metadados locais: {metadata}")

    try:
        # Tenta assinatura mais comum com descrição e publicação pública.
        hub.push(
            full_prompt_name,
            chat_prompt,
            new_repo_is_public=True,
            new_repo_description=description,
        )
    except TypeError:
        # Fallback para versões com assinatura reduzida.
        try:
            hub.push(full_prompt_name, chat_prompt)
        except Exception as e:
            print(f"   ❌ Falha no push: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Falha no push: {e}")
        return False

    print("   ✓ Push concluído")
    print("   ⚠️  Se o prompt ficar privado, altere para público no dashboard do LangSmith.")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = ["description", "system_prompt", "user_prompt", "version"]
    for field in required_fields:
        value = prompt_data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"Campo obrigatório inválido/vazio: {field}")

    techniques = prompt_data.get("techniques_applied", [])
    if not isinstance(techniques, list) or len(techniques) < 2:
        errors.append("techniques_applied deve conter pelo menos 2 técnicas")

    if "{bug_report}" not in prompt_data.get("user_prompt", "") and "{bug_report}" not in prompt_data.get("system_prompt", ""):
        errors.append("Prompt deve usar a variável {bug_report}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    yaml_path = Path("prompts/bug_to_user_story_v2.yml")
    if not yaml_path.exists():
        print(f"❌ Arquivo não encontrado: {yaml_path}")
        print("Crie o prompt otimizado antes de executar o push.")
        return 1

    data = load_yaml(str(yaml_path))
    if not data:
        return 1

    if "bug_to_user_story_v2" in data:
        prompt_name = "bug_to_user_story_v2"
        prompt_data = data[prompt_name]
    else:
        # fallback se o YAML estiver sem chave raiz
        prompt_name = "bug_to_user_story_v2"
        prompt_data = data

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido. Corrija antes do push:")
        for error in errors:
            print(f"   - {error}")
        return 1

    success = push_prompt_to_langsmith(prompt_name, prompt_data)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
