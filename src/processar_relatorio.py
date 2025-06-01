import os
import json
from api import ler_pdf, gerar_json_estruturado, combinar_json, inserir_dados_no_banco

def processar_relatorio(
    caminho_pdf: str,
    usar_json_salvo: bool = False,
    caminho_json_salvo: str = "saida_gemini3.json",
    callback_progresso=None,
    num_partes: int = 15  # Novo parâmetro para controlar quantas divisões fazer
):
    def atualizar_progresso(p):
        if callback_progresso:
            callback_progresso(p)

    # Caso esteja reaproveitando um JSON salvo
    if usar_json_salvo and os.path.exists(caminho_json_salvo):
        with open(caminho_json_salvo, "r", encoding="utf-8") as f:
            dados_json = json.load(f)
    else:
        texto = ler_pdf(caminho_pdf)
        tamanho = len(texto)
        divisao = min(num_partes, tamanho)  # Evita dividir mais do que o necessário
        decimo = tamanho // divisao
        partes = [texto[i * decimo: (i + 1) * decimo] for i in range(divisao - 1)]
        partes.append(texto[(divisao - 1) * decimo:])

        dados_partes = []
        for i, parte in enumerate(partes, 1):
            print(f"Processando parte {i}/{divisao} com Gemini...")
            try:
                dados = gerar_json_estruturado(parte)
                dados_partes.append(dados)
            except Exception as e:
                print(f"Erro ao processar parte {i}: {e}")

            progresso = int(i / divisao * 100)
            atualizar_progresso(progresso)

        dados_json = combinar_json(*dados_partes)

    # Insere os dados extraídos no banco
    inserir_dados_no_banco(dados_json)
    print("✅ Dados inseridos com sucesso no banco morro_verde.db!")
    atualizar_progresso(100)
