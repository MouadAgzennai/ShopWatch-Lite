import unittest
from src.contrat import Diagnostic, Signal
from src.notification import (approuver, choisir_canal, composer,
                              consigner, diffuser)


def exemple(critique=True, niveau="BLOQUANT",
            action="Isoler le service paiement", origines=None):
    s = Signal("SH-0125", "2026-11-27T17:02:11Z", "PAIEMENT", "paiement",
               "production", "JOURNAL", "MAJEUR", "timeout passerelle apres 30s")
    d = Diagnostic("SH-0125", niveau, "Passerelle lente",
                   action, critique, origines or ["PAIEMENT"])
    return s, d


class TestNotification(unittest.TestCase):
    def test_canaux(self):
        self.assertEqual(choisir_canal("BLOQUANT"), "SLACK")
        self.assertEqual(choisir_canal("MAJEUR"), "TEAMS")
        self.assertEqual(choisir_canal("MODERE"), "EMAIL")
        self.assertEqual(choisir_canal("MINEUR"), "TABLEAU")

    def test_canal_invalide(self):
        with self.assertRaises(ValueError):
            choisir_canal("INCONNU")

    def test_composer(self):
        s, d = exemple()
        attendu = ("*** BLOQUANT *** Service : paiement\n"
                   "Constat : timeout passerelle apres 30s\n"
                   "Cause : Passerelle lente\n"
                   "A faire : Isoler le service paiement\n"
                   "Origines : PAIEMENT")
        self.assertEqual(composer(s, d), attendu)

    def test_composer_plusieurs_origines(self):
        s, d = exemple(origines=["PAIEMENT", "SCANNER"])
        self.assertTrue(composer(s, d).endswith("Origines : PAIEMENT + SCANNER"))

    def test_diffuser(self):
        s, d = exemple()
        registre = []
        msg = diffuser(s, d, registre)
        self.assertEqual(msg.canal, "SLACK")
        self.assertEqual(msg.destinataire, "astreinte-shop")
        self.assertEqual(msg.signal_ref, "SH-0125")
        self.assertEqual(registre, [msg])
        self.assertEqual(s.etat, "DIFFUSE")

    def test_approbation(self):
        _, d = exemple()
        for rep in ("o", "oui", "ok", "yes", " OUI ", "Yes"):
            self.assertTrue(approuver(d, rep))
        for rep in ("n", "non", "", "peut-etre"):
            self.assertFalse(approuver(d, rep))

    def test_approbation_non_critique(self):
        _, d = exemple(critique=False, niveau="MINEUR", action="Observer")
        self.assertTrue(approuver(d, "n"))

    def test_consigner(self):
        _, d = exemple()
        carnet = []
        entree = consigner(d, True, "astreinte-shop", carnet, "2026-11-27T17:10:00Z")
        self.assertEqual(entree, {
            "ref": "SH-0125",
            "action": "Isoler le service paiement",
            "accord": True,
            "responsable": "astreinte-shop",
            "instant": "2026-11-27T17:10:00Z",
        })
        self.assertEqual(carnet, [entree])


if __name__ == "__main__":
    unittest.main()