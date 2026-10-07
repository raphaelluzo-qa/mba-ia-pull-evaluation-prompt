"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith():
    """Faz pull dos prompts do Hub e salva em YAML local."""
    print_section_header("PULL DE PROMPTS (LANGSMITH HUB)")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return False

    source_prompts = {
        "bug_to_user_story_v1": "leonanluppi/bug_to_user_story_v1",
    }

    pulled_prompts = {}

    for local_name, hub_name in source_prompts.items():
        print(f"🔽 Fazendo pull de '{hub_name}'...")
        try:
            prompt = hub.pull(hub_name)
            normalized = _normalize_chat_prompt(prompt, local_name, hub_name)
            pulled_prompts[local_name] = normalized

            local_file = Path("prompts") / f"{local_name}.yml"
            if save_yaml({local_name: normalized}, str(local_file)):
                print(f"   ✓ Salvo em {local_file}")
            else:
                print(f"   ❌ Falha ao salvar {local_file}")
                return False
        except Exception as e:
            print(f"   ❌ Erro ao fazer pull de '{hub_name}': {e}")
            return False

    raw_output = Path("prompts") / "raw_prompts.yml"
    if save_yaml(pulled_prompts, str(raw_output)):
        print(f"\n✓ Arquivo consolidado salvo em {raw_output}")
    else:
        print(f"\n❌ Falha ao salvar arquivo consolidado: {raw_output}")
        return False

    print("\n✅ Pull concluído com sucesso.")
    return True


def _normalize_chat_prompt(prompt, local_name: str, hub_name: str) -> dict:
    """
    Converte o objeto de prompt do LangChain para um formato YAML simples do desafio.
    """
    system_parts = []
    human_parts = []

    messages = getattr(prompt, "messages", None) or []

    for message in messages:
        message_type = getattr(message, "__class__", type("x", (), {})).__name__.lower()

        template = ""
        if hasattr(message, "prompt") and hasattr(message.prompt, "template"):
            template = message.prompt.template or ""
        elif hasattr(message, "template"):
            template = getattr(message, "template") or ""
        elif hasattr(message, "content"):
            template = getattr(message, "content") or ""

        if not template:
            continue

        if "system" in message_type:
            system_parts.append(template)
        elif "human" in message_type or "user" in message_type:
            human_parts.append(template)

    system_prompt = "\n\n".join(p.strip() for p in system_parts if p.strip())
    user_prompt = "\n\n".join(p.strip() for p in human_parts if p.strip())

    # Fallback caso a estrutura da serialização mude.
    if not system_prompt and hasattr(prompt, "input_variables"):
        system_prompt = (
            "Prompt importado do LangSmith Hub (serialização parcial). "
            "Revise manualmente antes de otimizar."
        )
    if not user_prompt:
        user_prompt = "{bug_report}"

    return {
        "description": f"Prompt importado de {hub_name}",
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "version": local_name.split("_")[-1],
        "source_hub_prompt": hub_name,
        "tags": ["imported", "langsmith-hub", "bug-to-user-story"],
    }


def main():
    """Função principal"""
    success = pull_prompts_from_langsmith()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
