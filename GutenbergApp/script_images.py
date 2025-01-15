import os
import xml.etree.ElementTree as ET
import requests


def get_book_cover_url(rdf_file):
    """Extrait l'URL de la couverture du fichier RDF."""
    try:
        tree = ET.parse(rdf_file)
        root = tree.getroot()

        namespaces = {
            'dcterms': 'http://purl.org/dc/terms/',
            'pgterms': 'http://www.gutenberg.org/2009/pgterms/',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
        }

        for file_node in root.findall(".//pgterms:file", namespaces):
            about = file_node.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", "")
            format_node = file_node.find(".//dcterms:format//rdf:value", namespaces)
            if format_node is not None and format_node.text == "image/jpeg":
                return about
        return None
    except Exception as e:
        print(f"Erreur lors de l'analyse du fichier RDF {rdf_file} : {e}")
        return None


def download_cover_image(url, save_path):
    """Télécharge l'image de couverture depuis une URL."""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Image téléchargée avec succès : {save_path}")
        else:
            print(f"Échec du téléchargement de l'image : {response.status_code}")
    except Exception as e:
        print(f"Erreur lors du téléchargement de l'image : {e}")


def process_covers(rdf_root_dir, covers_dir="covers"):
    """Parcourt les fichiers RDF et télécharge les images de couverture."""
    if not os.path.exists(covers_dir):
        os.makedirs(covers_dir)

    for folder_number in range(1, 1666):  # Parcourir les dossiers 1 à 1665
        subdir_path = os.path.join(rdf_root_dir, str(folder_number))
        if os.path.isdir(subdir_path):
            rdf_file = next((f for f in os.listdir(subdir_path) if f.endswith(".rdf")), None)
            if rdf_file:
                rdf_path = os.path.join(subdir_path, rdf_file)
                cover_url = get_book_cover_url(rdf_path)
                if cover_url:
                    save_path = os.path.join(covers_dir, f"{folder_number}.jpg")
                    download_cover_image(cover_url, save_path)


if __name__ == "__main__":
    rdf_root_dir = "books"  # Répertoire contenant les fichiers RDF
    process_covers(rdf_root_dir, covers_dir="covers")
