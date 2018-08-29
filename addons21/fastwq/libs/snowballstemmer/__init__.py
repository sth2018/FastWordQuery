__all__ = ('language', 'stemmer')

from .english_stemmer import EnglishStemmer

language = {
    'english': EnglishStemmer,
}

try:
    import Stemmer
    cext_available = True
except ImportError:
    cext_available = False

def algorithms():
    if cext_available:
        return Stemmer.language()
    else:
        return list(language.keys())

def stemmer(lang):
    if cext_available:
        return Stemmer.Stemmer(lang)
    if lang.lower() in language:
        return language[lang.lower()]()
    else:
        raise KeyError("Stemming algorithm '%s' not found" % lang)
