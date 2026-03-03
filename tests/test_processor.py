import os
import shutil
import pytest
from smartsort.core.engine import FileProcessor


@pytest.fixture
def mock_config():
    return {
        "directories_to_watch": ["test_downloads"],
        "destination_base_folder": "test_destination",
        "ai_classification": {
            "enabled": False
        },
        "fallback_rules": {
            "pdf": "Documentos_Teste",
            "jpg": "Imagens_Teste",
            "txt": "Textos_Teste"
        }
    }

@pytest.fixture
def setup_teardown_folders():

    os.makedirs("test_downloads", exist_ok=True)
    os.makedirs("test_destination", exist_ok=True)
    yield

    if os.path.exists("test_downloads"):
        shutil.rmtree("test_downloads")
    if os.path.exists("test_destination"):
        shutil.rmtree("test_destination")

def test_fallback_classification(mock_config):
    processor = FileProcessor(mock_config)
    assert processor.classify_file("fake_path.pdf", "meu_arq.pdf") == "Documentos_Teste"
    assert processor.classify_file("fake_path.jpg", "foto_ferias.jpg") == "Imagens_Teste"
    assert processor.classify_file("fake_path.xyz", "desconhecido.xyz") == "Outros"

def test_process_file_integration(mock_config, setup_teardown_folders):
    processor = FileProcessor(mock_config)
    test_file_path = os.path.join("test_downloads", "nota_urgente.txt")
    with open(test_file_path, "w") as f:
        f.write("Isto é um teste.")
        
    processor.process_file(test_file_path)
    
    assert not os.path.exists(test_file_path)
    expected_dest_dir = os.path.join("test_destination", "Textos_Teste")
    assert os.path.exists(expected_dest_dir)
    assert os.path.exists(os.path.join(expected_dest_dir, "nota_urgente.txt"))

def test_temp_file_ignore(mock_config, setup_teardown_folders):
    processor = FileProcessor(mock_config)
    temp_file = os.path.join("test_downloads", "fatura.pdf.crdownload")
    with open(temp_file, "w") as f:
        f.write("Incompleto")
        
    processor.process_file(temp_file)
    assert os.path.exists(temp_file)



def test_security_path_traversal(mock_config):

    processor = FileProcessor(mock_config)
    
    malicious_ai_output = "../../etc/passwd"
    safe_output = processor.sanitize_category(malicious_ai_output)
    

    assert safe_output == "etcpasswd"
    assert "/" not in safe_output
    assert "." not in safe_output

    another_attack = "/root/Pasta Maliciosa!"
    assert processor.sanitize_category(another_attack) == "rootPasta Maliciosa"

def test_safety_prevent_overwrite(mock_config, setup_teardown_folders):


    processor = FileProcessor(mock_config)
    

    dest_dir = os.path.join("test_destination", "Textos_Teste")
    os.makedirs(dest_dir, exist_ok=True)
    existing_file = os.path.join(dest_dir, "importante.txt")
    with open(existing_file, "w") as f:
        f.write("DADOS ANTIGOS")
        

    new_file = os.path.join("test_downloads", "importante.txt")
    with open(new_file, "w") as f:
        f.write("DADOS NOVOS")
        

    processor.process_file(new_file)
    

    assert os.path.exists(existing_file)
    with open(existing_file, "r") as f:
        assert f.read() == "DADOS ANTIGOS"
        

    files_in_dest = os.listdir(dest_dir)
    assert len(files_in_dest) == 2

def test_ai_classification_mock(setup_teardown_folders):

    config_com_ia = {
        "destination_base_folder": "test_destination",
        "ai_classification": {
            "enabled": True,
            "mode": "zero_shot",
            "categorias_disponiveis": ["Segurança", "Perigo"]
        },
        "fallback_rules": {}
    }
    
    processor = FileProcessor(config_com_ia)
    

    def mock_classifier(text, categories):

        return {'labels': ['Seguranca_IA'], 'scores': [0.99]}
        
    processor.zero_shot_classifier = mock_classifier
    
    test_file_path = os.path.join("test_downloads", "doc_ia.txt")
    with open(test_file_path, "w") as f:
        f.write("Testando a rede neural!")
        
    processor.process_file(test_file_path)
    

    expected_dest_dir = os.path.join("test_destination", "Seguranca_IA")
    assert os.path.exists(expected_dest_dir)
    assert os.path.exists(os.path.join(expected_dest_dir, "doc_ia.txt"))

def test_process_existing_files(mock_config, setup_teardown_folders):
    processor = FileProcessor(mock_config)
    

    regular_file = os.path.join("test_downloads", "documento.pdf")
    with open(regular_file, "w") as f:
        f.write("Conteudo pdf fake")
        

    hidden_file = os.path.join("test_downloads", ".gitkeep")
    with open(hidden_file, "w") as f:
        f.write("")
        

    sub_dir = os.path.join("test_downloads", "subpasta")
    os.makedirs(sub_dir, exist_ok=True)
    

    os.makedirs("test_other_dir", exist_ok=True)
    outside_file = os.path.join("test_other_dir", "nao_mexer.txt")
    with open(outside_file, "w") as f:
        f.write("Fica aqui")
        

    processor.process_existing_files()
    

    assert not os.path.exists(regular_file), "Ficheiro regular devia ter sido movido"
    assert os.path.exists(os.path.join("test_destination", "Documentos_Teste", "documento.pdf")), "Ficheiro devia estar no destino"
    
    assert os.path.exists(hidden_file), "Ficheiros ocultos nao devem ser tocados"
    assert os.path.exists(sub_dir), "Diretorios internos nao devem ser tocados"
    assert os.path.exists(outside_file), "Ficheiros fora do alvo nao devem ser tocados"
    

    shutil.rmtree("test_other_dir")