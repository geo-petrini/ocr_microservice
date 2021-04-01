import argparse, pytesseract, logging, sys, os.path
from pathlib import Path
from os import path
try:
    from PIL import Image
except ImportError:
    import Image

"""
Lettura immaggine e scrittura del output nel file.

author: Viktorija Tilevska, Thaisa De Torre
version: 11.02.2012
last change: 01.04.2021
"""

# -----------------------------------------------------------------------
# Fa lo scan di tutti i file validi. Se non ci sono file validi il programma finisce
#
# args: dizionario di argomenti da controllare
# -----------------------------------------------------------------------
def scan(args):
    valid_files = validate_source(args.source)
    files_text = {}

    if len(valid_files) != 0:
        for f in valid_files:
            files_text[f] = {}
            files_text[f]['txt'] = get_text(f, args.lang)

        return files_text
    else:
        logging.error("Program stopped. No valid files were inserted.")
        sys.exit(1)
    
# -----------------------------------------------------------------------
# Fa tutti i controlli e i cambiamenti in modo da avere una lista con solamente
# i file validi da scannerizzare.
#
# source: lista con i percorsi sorgente
# return: una lista con tutti i percorsi validi per l'ocr
# -----------------------------------------------------------------------
def validate_source(source):
    valid_files = [] #contiene tutti i file validi (jpg, png)
    file_list = len(source)
    logging.info(f"Number of files inserted: {file_list}")

    for img in source:
        if check_permission(img):   #per vedere se funziona quando metto check_permission qua     
            if path.isfile(img):
                if is_valid(img):
                    valid_files.append(img)
                else:
                    logging.debug(f"file {img} not valid")
                    sys.exit(1)
            elif path.isdir(img):
                dir_list = get_dir_content(img)
                logging.debug(f"dir list: {dir_list}")

                for f in dir_list:
                    if is_valid(f):
                        valid_files.append(img)

    # controllare se è una mask

    logging.debug(f"List of valid files ({len(valid_files)}): {valid_files}")
    return valid_files

# -----------------------------------------------------------------------
# Controlla se il formato del file al percorso path sia accettato dall'ocr (png o jpg o jpeg). 
#
# src: percorso del file da controllare
# return: true se il formato è accettato, altrimenti false
# -----------------------------------------------------------------------            
def is_valid(src):
    valid = False
    valid_extensions = ['.png', '.jpg', '.jpeg']
    file_ext = os.path.splitext(src)[-1]
    #if file_ext in valid_extensions and check_permission(src):
    if file_ext in valid_extensions:
        valid = True
        logging.debug(f"File {src} is valid")
    else:       
        logging.error("Error: A file has non been accepted. Please insert PNG and/or JPG/JPEG files")
        #sys.exit(1) #per il TC-001.bat
    return valid

# --------------------------------------------------
# Controlla se il file è accessibile in lettura
#
# path: il percorso del file da controllare 
# returns: true se il file è accessibile, altrimenti ritorna false
# -------------------------------------------------
def check_permission(path):
    valid = False
    try:
        with open(path, 'r') as outfile:
            valid = True
    except OSError:
        logging.warning(f"File {path} is not readable")
   
    # if os.access(path, os.R_OK):
    #     valid = True
    # else:
    #     logging.warning(f"File {path} is not readable")

    return valid

# ------------------------------------------------------------
# Prende e ritorna il contenuto della cartella nel percorso path.
#
# path: percorso della cartella
# returns: una lista con i file contenuti nella cartella
# ------------------------------------------------------------
def get_dir_content(path):
    if len(os.listdir(path)) != 0:
        return os.listdir(path)
    else:
        logging.debug(f"The directory {path} is empty")
        return None

# -----------------------------------------------------------------------
# Legge il contenuto di una immagine 
#
# f: il percorso del file
# lang: la lingua
# return: una stringa con il contenuto dell'immagine
# ----------------------------------------------------------------------- 
def get_text(f, lang):
    logging.info("scanning file")
    try:
        text = pytesseract.image_to_string(Image.open(f), lang)
        return text
    except FileNotFoundError as fnf_error:
        logging.exception(f"Error: file {f} not found")
        return None

#https://docs.python.org/3/library/os.path.html link utile per lavorare con i percorsi
# ----------------------------------------------------------------------- 
# riceve l'output da scrivere
#
# funzionamento:
#    ricevo output da scrivere
#    controllo dest
#       esiste? 
#           posso scrivere? 
#    altrimenti creo dir/file
#    
#    controllo prefix
#       è valido per nome file?
#   --------------------------------
# descrizione metodo [...]
#
# output: è un dizionario contente l'associazione tra immagine e testo
#   scannerizzato insieme ad altre info.
# dest: la destinazione in cui scrivere l'output. Se è un file scrive tutto li,
#    se è una cartella salverà le scansioni in quella dir.
# prefix: il prefisso che avrà il file di output per evitare duplicati
#    nella stessa cartella.
# ----------------------------------------------------------------------- 
def write_output(output, dest, prefix):
    if path.exists(dest):
        if os.access(dest, os.W_OK):
            logging.debug("dest exists and is writable")
            
            if path.isdir(dest):
                logging.debug("dest is dir")
                check_prefix(output, dest, prefix)
                

            elif path.isfile(dest):
                # sovrascrive il file ---> ??? richiedere consenso a user ???
                logging.debug("dest is file")
                with open(dest, 'w') as f:
                    first_value = next(iter(output.values()))
                    f.write(first_value["txt"])

                logging.warning("dest file overwrote")
    else:
        create_directory(dest)
        check_prefix(output, dest, prefix)


# riceve il dizionario e ritorna il testo
def get_output(output):
    logging.debug("getting text from dict output")
    text = ""
    for key, value in output.items():
        text += f"\n\nfile {key}\n" + value["txt"]

    return text


def create_directory(path):
    try:
        os.mkdir(path)
    except OSError:
        logging.exception(f"Directory {path} already exists")
    else:
        logging.info(f"Created directory {path}")

# -------------------------------
# gestisce il prefisso del file di destinazione per non avere duplicati
#
# -------------------------------
def check_prefix(output, dest, prefix):
    output_file_name = prefix + ".txt"
    dest_file = f"{dest}\{output_file_name}"
    logging.debug(f"path dest file: {dest_file}")

    if path.exists(dest_file):
        logging.debug("dest file exists, check prefix")
        dir_content =  get_dir_content(dest)
        logging.debug(f"get dir content: {dir_content}")
        id = 1
        # output_file_name = f"{prefix}_{id}.txt"

        logging.debug(f"len dir content: {len(dir_content)}")
        for file in dir_content:
            logging.debug(f"file: {file}; out name: {output_file_name}; id: {id}")
            if file == output_file_name:
                id = id +1
                logging.debug(f"incremented id: {id}")
            output_file_name = f"{prefix}_{id}.txt"
                
        dest_file = f"{dest}\{output_file_name}"
        logging.debug(f"out file name: {output_file_name}")
        logging.debug(f"dest file: {dest_file}")
    else:
        logging.debug("dest file not exists, lets write")

    with open(dest_file, "w") as f:
        f.write(get_output(output))
