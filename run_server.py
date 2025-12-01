
"""
Script para iniciar o servidor FastAPI.
Ajusta o path para permitir imports corretos.
"""

import sys
import os

# Adiciona o diretório raiz ao path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Importa e executa o servidor
if __name__ == "__main__":
    import uvicorn
    from backend.server import app
    
    print("=" * 60)
    print("Sistema de Controle Fuzzy para Data Center")
    print("=" * 60)
    print(f"Servidor iniciando em http://localhost:8000")
    print(f"Documentação da API: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

