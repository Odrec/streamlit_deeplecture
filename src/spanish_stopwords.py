import nltk
from nltk.corpus import stopwords
import src.data_utils as data_utils


class StopWords:

    def __init__(self):
        self.stop_words = None

    def set_stopwords(self):
        nltk.download('stopwords')
        stop_words = set(stopwords.words('spanish'))
        stop_words.add("mas")
        stop_words.add("alli")
        stop_words.add("sino")
        stop_words.add("todas")
        stop_words.add("pues")
        stop_words.add("puede")
        stop_words.add("tan")
        stop_words.add("misma")
        stop_words.add("mismo")
        stop_words.add("solo")
        stop_words.add("tal")
        stop_words.add("debe")
        stop_words.add("segun")
        stop_words.add("dos")
        stop_words.add("asi")
        stop_words.add("siempre")
        stop_words.add("menos")
        stop_words.add("toda")
        stop_words.add("parte")
        stop_words.add("quando")
        stop_words.add("hace")
        stop_words.add("aun")
        stop_words.add("hacer")
        stop_words.add("cosas")
        stop_words.add("parece")
        stop_words.add("fin")
        stop_words.add("qual")
        stop_words.add("pueden")
        stop_words.add("igual")
        stop_words.add("partes")
        stop_words.add("aunque")
        stop_words.add("demas")
        stop_words.add("quanto")
        stop_words.add("veces")
        stop_words.add("aquel")
        stop_words.add("cosa")
        stop_words.add("decir")
        stop_words.add("dice")
        stop_words.add("conocer")
        stop_words.add("efectos")
        stop_words.add("toda")
        stop_words.add("deben")
        stop_words.add("tambien")
        stop_words.add("esta")
        stop_words.add("muchas")
        stop_words.add("alguna")
        stop_words.add("despues")
        stop_words.add("aquellos")
        stop_words.add("dar")
        stop_words.add("cuya")
        stop_words.add("cuyo")
        stop_words.add("mejor")
        stop_words.add("toda")
        stop_words.add("cada")
        stop_words.add("dela")
        stop_words.add("tres")
        stop_words.add("gran")
        stop_words.add("siendo")
        stop_words.add("aqui")
        stop_words.add("habia")
        stop_words.add("aquella")
        stop_words.add("sido")
        stop_words.add("algun")
        stop_words.add("ver")
        stop_words.add("comun")
        stop_words.add("biblioteca")
        stop_words.add("haber")
        stop_words.add("tener")
        stop_words.add("dicho")
        stop_words.add("baxo")
        stop_words.add("cerca")
        stop_words.add("hacia")
        stop_words.add("casi")
        stop_words.add("grande")
        stop_words.add("llaman")
        stop_words.add("llamado")
        stop_words.add("aquellas")
        stop_words.add("pide")
        stop_words.add("fon")
        stop_words.add("alguno")
        stop_words.add("sola")
        stop_words.add("qualquiera")
        stop_words.add("digo")
        stop_words.add("cuales")
        stop_words.add("dijo")
        stop_words.add("siete")
        stop_words.add("hacen")
        stop_words.add("varias")
        stop_words.add("vifto")
        stop_words.add("mucha")
        stop_words.add("eftaba")
        stop_words.add("varios")
        stop_words.add("iba")
        stop_words.add("adentro")
        stop_words.add("nacional")
        stop_words.add("mui")
        stop_words.add("habian")
        stop_words.add("caso")
        stop_words.add("vez")
        stop_words.add("bajar")
        stop_words.add("salieron")
        stop_words.add("dan")
        stop_words.add("apenas")
        stop_words.add("luego")
        stop_words.add("efte")
        stop_words.add("junto")
        stop_words.add("enel")
        stop_words.add("dio")
        stop_words.add("dentro")
        stop_words.add("lado")
        stop_words.add("mil")
        stop_words.add("cuyos")
        stop_words.add("abaxo")
        stop_words.add("mrs")
        stop_words.add("arriba")
        stop_words.add("cuatro")
        stop_words.add("ultimo")
        stop_words.add("cabida")
        stop_words.add("art")
        stop_words.add("efta")
        stop_words.add("ningun")
        stop_words.add("mejoran")
        stop_words.add("folo")
        stop_words.add("primero")
        stop_words.add("significa")
        stop_words.add("fus")
        stop_words.add("fino")
        stop_words.add("cap")
        stop_words.add("primera")
        stop_words.add("existe")
        stop_words.add("solamente")
        stop_words.add("ahora")
        stop_words.add("grandes")
        stop_words.add("cualquiera")
        stop_words.add("per")
        stop_words.add("dexado")
        stop_words.add("hafta")
        stop_words.add("havia")
        stop_words.add("nueftra")
        stop_words.add("quatro")
        stop_words.add("daran")
        stop_words.add("assi")
        stop_words.add("halla")
        stop_words.add("fobre")
        stop_words.add("quales")
        stop_words.add("enla")
        stop_words.add("dara")
        stop_words.add("des")
        stop_words.add("ademas")
        stop_words.add("dado")
        stop_words.add("jos")
        stop_words.add("jas")
        stop_words.add("hizo")
        stop_words.add("cuanto")
        stop_words.add("entonces")
        stop_words.add("cion")
        stop_words.add("pre")
        stop_words.add("com")
        stop_words.add("lus")
        stop_words.add("dad")
        stop_words.add("hallan")
        stop_words.add("efto")
        stop_words.add("delos")
        stop_words.add("ele")
        stop_words.add("aca")
        stop_words.add("dicen")
        stop_words.add("cinco")
        stop_words.add("unas")
        stop_words.add("acia")
        stop_words.add("abaxo")
        stop_words.add("abajo")
        stop_words.add("debaxo")
        stop_words.add("debajo")
        stop_words.add("ello")
        stop_words.add("vna")
        stop_words.add("afsi")
        stop_words.add("fido")
        stop_words.add("ocho")
        stop_words.add("unas")
        stop_words.add("seis")
        stop_words.add("pag")
        stop_words.add("est")
        stop_words.add("num")
        stop_words.add("diez")
        stop_words.add("queda")
        stop_words.add("cel")
        self.stop_words = stop_words

    def get_stopwords(self):
        if not self.stop_words:
            self.set_stopwords()
        return self.stop_words

    def remove_stopwords(self, text):
        # Tokenize the text
        words = data_utils.tokenize(text)

        # Get the stopwords
        stop_words = self.get_stopwords()

        # Remove stopwords
        filtered_words = [word for word in words if word.lower() not in stop_words]

        # Join the filtered words back into a string
        filtered_text = ' '.join(filtered_words)

        return filtered_text