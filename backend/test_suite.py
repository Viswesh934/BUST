import unittest
import logging
from fastapi.testclient import TestClient
from app.main import app
from app.tools.cfo import get_cfo_financial_context
from app.services.grounding import ingest_grounding_source, get_all_grounded_sources, delete_grounding_source
from app.services.crustdata import get_crustdata_deep_research

logging.basicConfig(level=logging.INFO)

class TestBUSTEnterpriseFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_check(self):
        """Verify API health check endpoint."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "healthy")

    def test_02_no_hardcoded_150k_arr(self):
        """Verify deal_size defaults to clean empty fields without hardcoded $150,000 ARR."""
        # Unspecified deal size
        ctx_empty = get_cfo_financial_context(account_name="TestCorp", deal_size="")
        self.assertEqual(ctx_empty.get("status"), "pending_deal_size")
        self.assertEqual(ctx_empty.get("deal_arr"), "")
        self.assertEqual(ctx_empty.get("annual_projected_savings"), "")

        # Explicit deal size should calculate accurately
        ctx_filled = get_cfo_financial_context(account_name="TestCorp", deal_size="$300,000 ARR")
        self.assertEqual(ctx_filled.get("status"), "connected")
        self.assertEqual(ctx_filled.get("deal_arr"), "$300,000")
        self.assertIn("$", ctx_filled.get("annual_projected_savings"))
        self.assertIn("days", ctx_filled.get("payback_period_days"))

    def test_03_grounding_source_addition_and_removal(self):
        """Verify technical grounding sources can be ingested and deleted."""
        # 1. Ingest test source
        ingest_res = self.client.post("/api/sources/ingest", json={
            "source_type": "website",
            "url_or_path": "https://specs.internal.test/architecture",
            "raw_content": "Zero data retention architecture with customer VPC peering."
        })
        self.assertEqual(ingest_res.status_code, 200)
        source_data = ingest_res.json()
        source_id = source_data["source"]["id"]
        self.assertTrue(source_id)

        # 2. Verify source appears in active sources
        list_res = self.client.get("/api/sources")
        self.assertEqual(list_res.status_code, 200)
        sources = list_res.json()
        self.assertTrue(any(s["id"] == source_id for s in sources))

        # 3. Delete source
        del_res = self.client.delete(f"/api/sources/{source_id}")
        self.assertEqual(del_res.status_code, 200)
        del_data = del_res.json()
        self.assertEqual(del_data.get("status"), "deleted")

        # 4. Confirm source is gone
        list_res_after = self.client.get("/api/sources")
        sources_after = list_res_after.json()
        self.assertFalse(any(s["id"] == source_id for s in sources_after))

    def test_04_competitor_public_revenue_intelligence(self):
        """Verify public competitor (Datadog) discovers online public revenue."""
        res = self.client.post("/api/competitor/analyze", json={
            "competitor": "Datadog",
            "account_name": "ACME Cloud",
            "deal_size": ""
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        art = data.get("artifact", {})
        content = art.get("content", {})
        
        self.assertEqual(content.get("competitor_name"), "Datadog")
        rev = content.get("revenue_intelligence", {})
        self.assertTrue(rev.get("has_public_revenue"))
        self.assertIn("$", rev.get("revenue_estimate"))
        self.assertTrue(len(content.get("pricing_vulnerabilities", [])) > 0)
        self.assertTrue(len(content.get("head_to_head_matrix", [])) > 0)
        self.assertTrue(len(content.get("landmine_traps", [])) > 0)

    def test_05_competitor_private_undisclosed_revenue(self):
        """Verify private competitor gracefully reports undisclosed revenue without failing."""
        res = self.client.post("/api/competitor/analyze", json={
            "competitor": "StealthPrivateStartupXYZ",
            "account_name": "ACME Cloud",
            "deal_size": ""
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        art = data.get("artifact", {})
        content = art.get("content", {})
        rev = content.get("revenue_intelligence", {})
        
        self.assertFalse(rev.get("has_public_revenue"))
        self.assertIn("Not publicly disclosed", rev.get("revenue_estimate"))

    def test_06_crustdata_deep_sales_research(self):
        """Verify Crustdata deep sales research generates rich firmographics, headcount, and hiring signals."""
        res = self.client.post("/api/competitor/deep-research", json={
            "competitor": "Datadog",
            "account_name": "Stripe"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        art = data.get("artifact", {})
        content = art.get("content", {})
        
        self.assertIn(content.get("status"), ["connected", "api_key_ready"])
        self.assertEqual(content.get("api_endpoint"), "https://api.crustdata.com")
        self.assertTrue(content.get("has_api_key_configured"))
        research = content.get("research", {})
        
        self.assertTrue(research.get("headcount", {}).get("total_employees"))
        self.assertTrue(research.get("financials_and_funding", {}).get("stage_or_status"))
        self.assertTrue(len(research.get("hiring_signals", {}).get("critical_focus_areas", [])) > 0)
        self.assertTrue(len(research.get("tech_stack_footprint", [])) > 0)

    def test_07_agent_conversational_turn_with_competitor(self):
        """Verify agent autonomously selects analyze_competitor tool with decision rationale."""
        res = self.client.post("/api/agent/chat", json={
            "message": "Analyze competitor Datadog and check online revenue and hiring velocity",
            "deal_context": {
                "account_name": "Stripe",
                "competitor": "Datadog",
                "deal_size": ""
            }
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("analyze_competitor", data.get("actions_taken", []))
        self.assertIn("competitor", data.get("artifacts", {}))
        self.assertTrue(data.get("decision_rationale"))
        self.assertTrue(len(data.get("follow_ups", [])) > 0)

if __name__ == "__main__":
    unittest.main()
