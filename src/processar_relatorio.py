import os
import json
from api import ler_pdf, gerar_json_estruturado, combinar_json, inserir_dados_no_banco

# 🔧 Logger visível pela interface do Streamlit
def logger_visual(msg):
    try:
        with open("log_streamlit.txt", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
        print(msg)  # 👈 Força print no terminal (para Streamlit local)
    except Exception as e:
        print(f"[Logger erro]: {e}")



def processar_relatorio(
    caminho_pdf: str,
    usar_json_salvo: bool = False,
    caminho_json_salvo: str = "saida_gemini3.json",
    callback_progresso=None,
    num_partes: int = 15
):
    print("✅ Entrou na função processar_relatorio")
    logger_visual("✅ Entrou na função processar_relatorio")

    def atualizar_progresso(p, mensagem=None):
        if callback_progresso:
            try:
                callback_progresso(p)
            except Exception as cb_erro:
                logger_visual(f"[ERRO no callback_progresso]: {cb_erro}")

        try:
            with open("progresso.json", "w") as f:
                json.dump({
                    "progresso": p,
                    "mensagem": mensagem or ""
                }, f)
            if mensagem:
                logger_visual(f"[{p}%] {mensagem}")
        except Exception as e:
            logger_visual(f"[ERRO ao salvar progresso.json]: {e}")

    # Limpa o log no início
    try:
        if os.path.exists("log_streamlit.txt"):
            os.remove("log_streamlit.txt")
        logger_visual("🚀 Iniciando processamento do relatório...")
    except Exception as e:
        print(f"[ERRO ao limpar log inicial]: {e}")

    try:
        if usar_json_salvo and os.path.exists(caminho_json_salvo):
            logger_visual("📂 Usando JSON salvo.")
            with open(caminho_json_salvo, "r", encoding="utf-8") as f:
                dados_json = json.load(f)
        else:
            texto = ler_pdf(caminho_pdf)
            tamanho = len(texto)
            divisao = min(num_partes, tamanho)
            decimo = tamanho // divisao
            partes = [texto[i * decimo: (i + 1) * decimo] for i in range(divisao - 1)]
            partes.append(texto[(divisao - 1) * decimo:])

            dados_partes = []
            for i, parte in enumerate(partes, 1):
                msg = f"Processando parte {i}/{divisao} com Gemini..."
                print(msg)
                logger_visual(msg)
                try:
                    dados = gerar_json_estruturado(parte)
                    dados_partes.append(dados)
                except Exception as e:
                    erro = f"❌ Erro ao processar parte {i}: {e}"
                    print(erro)
                    logger_visual(erro)

                progresso = int(i / divisao * 100)
                atualizar_progresso(progresso, mensagem=msg)

            dados_json = combinar_json(*dados_partes)
            logger_visual("✅ Partes combinadas com sucesso.")

        logger_visual("💾 Inserindo dados no banco...")
        inserir_dados_no_banco(dados_json)

        msg_final = "✅ Dados inseridos com sucesso no banco morro_verde.db!"
        print(msg_final)
        logger_visual(msg_final)
        atualizar_progresso(100, mensagem=msg_final)

    except Exception as erro_geral:
        msg_erro = f"[ERRO GERAL]: {erro_geral}"
        print(msg_erro)
        logger_visual(msg_erro)
        raise erro_geral  # Propaga o erro para ser mostrado no app
