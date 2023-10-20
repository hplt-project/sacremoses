from normalize import MosesPunctNormalizer
import sys

def test(fileName):
    a = MosesPunctNormalizer(perl_parity = True)
    file_path = fileName

    with open(file_path, "r") as file:
        text = file.read()
    print(a.normalize(text))

test(sys.argv[1])