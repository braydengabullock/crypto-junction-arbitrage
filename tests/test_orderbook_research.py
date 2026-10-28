import unittest
from decimal import Decimal
from orderbook_research import kalshi_buy_levels,polymarket_buy_levels,depth_cost

class OrderbookTests(unittest.TestCase):
    def test_kalshi_complementary_ask_from_opposing_bid(self):
        book={"orderbook_fp":{"yes_dollars":[["0.40","3"]],"no_dollars":[["0.62","4"],["0.60","5"]]}}
        self.assertEqual(kalshi_buy_levels(book,"YES")[0],(Decimal("0.38"),Decimal("4")))
        self.assertEqual(kalshi_buy_levels(book,"NO")[0],(Decimal("0.60"),Decimal("3")))
    def test_polymarket_asks_are_direct(self):
        book={"asks":[{"price":"0.42","size":"2"},{"price":"0.40","size":"3"}]}
        self.assertEqual(polymarket_buy_levels(book)[0][0],Decimal("0.40"))
    def test_walk_multiple_levels(self):
        r=depth_cost([(Decimal(".40"),Decimal("2")),(Decimal(".45"),Decimal("3"))],4)
        self.assertTrue(r["depth_sufficient"])
        self.assertEqual(r["displayed_cost_usd"],"1.70")
    def test_missing_liquidity_cannot_be_priced(self):
        r=depth_cost([(Decimal(".40"),Decimal("2"))],5)
        self.assertFalse(r["depth_sufficient"])
        self.assertIsNone(r["displayed_cost_usd"])
    def test_invalid_book_rejected(self):
        with self.assertRaises(ValueError):
            kalshi_buy_levels({}, "YES")
        with self.assertRaises(ValueError):
            polymarket_buy_levels({"asks":[{"price":"1.25","size":"4"}]})
if __name__=="__main__":
    unittest.main()
