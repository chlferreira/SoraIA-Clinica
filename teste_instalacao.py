import sys
import os

print(f"Versão do Python: {sys.version}")
print(f"Executável: {sys.executable}")

try:
    from genai import Client
    from dotenv import load_dotenv
    print("Sucesso! Biblioteca carregada.")
except ImportError as e:
    print(f"\nERRO DE IMPORTAÇÃO: {e}")
    print("\nPastas que o Python está vasculhando:")
    for path in sys.path:
        print(f"- {path}")
    sys.exit()

# ... (resto do seu código da SoraIA aqui abaixo)