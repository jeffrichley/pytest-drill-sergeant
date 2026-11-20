"""Base test classes the tests beside them inherit, as pandas' extension tests do.
Analysed, never run."""


class BaseOrderTests:
    def check_order(self, order):
        assert order["id"] == 1

    def test_order_has_an_id(self, order):
        assert "id" in order

    def build(self):
        return {"id": 1}

    def test_order_builds(self):
        self.build()
