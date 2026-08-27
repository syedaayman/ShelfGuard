import unittest

from pricing_model import predict_discount


class TestPricingModel(unittest.TestCase):
    def test_predict_discount_returns_valid_fraction(self):
        discount = predict_discount(
            days_to_expiry=2,
            stock_level=20,
            remaining_shelf_life_pct=25.0,
            supplier_score=8,
            is_promoted=0,
        )

        self.assertIsInstance(discount, (int, float))
        self.assertGreaterEqual(discount, 0)
        self.assertLessEqual(discount, 1)

    def test_predict_discount_rejects_invalid_supplier_score(self):
        with self.assertRaises(ValueError):
            predict_discount(2, 20, 25.0, 80, 0)

    def test_predict_discount_rejects_invalid_shelf_life(self):
        with self.assertRaises(ValueError):
            predict_discount(2, 20, 125.0, 8, 0)


if __name__ == "__main__":
    unittest.main()