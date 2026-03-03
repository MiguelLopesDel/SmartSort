import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline



dados_treino = [
    "fatura de eletricidade mensalidade conta energia luz",
    "recibo do supermercado compras alimentação",
    "pagamento do iva impostos",
    "declaração de IRS finanças",
    "extrato bancário despesas",
    "relatório de contas anuais da empresa lucros",
    "curriculum vitae experiência profissional",
    "ata da reunião de direção",
    "projeto de arquitetura especificações",
    "fotos da viagem férias praia familia",
    "exames médicos saúde clinica",
    "receita médica farmácia"
]

categorias_alvo = [
    "Financas",
    "Financas",
    "Financas",
    "Financas",
    "Financas",
    "Trabalho",
    "Trabalho",
    "Trabalho",
    "Trabalho",
    "Pessoal",
    "Saude",
    "Saude"
]

def treinar():
    print("A treinar o modelo local de Machine Learning...")


    modelo = make_pipeline(TfidfVectorizer(), MultinomialNB())
    

    modelo.fit(dados_treino, categorias_alvo)
    

    caminho_modelo = "models/modelo_classificador.joblib"
    joblib.dump(modelo, caminho_modelo)
    print(f"Modelo treinado e guardado em: {caminho_modelo}")

if __name__ == "__main__":
    treinar()