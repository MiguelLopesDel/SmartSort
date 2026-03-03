import os

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

from smartsort.utils.logger import logger


def treinar_modelo_local(dados_treino, caminho_modelo="models/modelo_classificador.joblib"):
    """
    Treina um modelo simples de ML (Random Forest) para classificação local.
    dados_treino: Lista de tuplos (texto, categoria)
    """
    if not dados_treino:
        logger.warning("Nenhum dado de treino fornecido. A ignorar treino.")
        return

    logger.info("A treinar o modelo local de Machine Learning...")

    textos = [d[0] for d in dados_treino]
    categorias = [d[1] for d in dados_treino]

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("clf", RandomForestClassifier(n_estimators=100)),
        ]
    )

    pipeline.fit(textos, categorias)

    os.makedirs(os.path.dirname(caminho_modelo), exist_ok=True)
    joblib.dump(pipeline, caminho_modelo)
    logger.info(f"Modelo treinado e guardado em: [green]{caminho_modelo}[/green]")
