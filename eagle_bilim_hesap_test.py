import unittest
from eagle_bilim_hesap import bilim_hesapla
from eagle_merkez_motoru import EagleMerkezMotoru

class BilimTest(unittest.TestCase):
    def test_square(self): self.assertIn('25 cm²', bilim_hesapla('Kenarı 5 cm olan karenin alanı kaç?'))
    def test_circle(self): self.assertIn('12,566', bilim_hesapla('Yarıçapı 2 m olan dairenin alanı kaç?'))
    def test_cube(self): self.assertIn('27 m³', bilim_hesapla('Kenarı 3 m olan küpün hacmi kaç?'))
    def test_mixed_units(self): self.assertIn('1 m²', bilim_hesapla('Kenarları 50 cm ve 2 m olan dikdörtgenin alanı kaç?'))
    def test_force(self): self.assertIn('-6 N', bilim_hesapla('Kütlesi 2 kg ve ivmesi -3 m/s² olan cismin kuvveti kaç?'))
    def test_invalid(self): self.assertIn('büyük', bilim_hesapla('Kenarı -5 cm olan karenin alanı kaç?'))
    def test_unrelated(self): self.assertIsNone(bilim_hesapla('Kare hakkında bilgi'))
    def test_relativity_negative(self): self.assertIsNone(EagleMerkezMotoru.bilimsel_model_cevabi('Özel görelilik -5 yıl ışık hızının %99'))
