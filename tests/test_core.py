import tempfile, unittest
from pathlib import Path
from matrix.mission_chain import MissionChain, order_agents
from matrix.model_router import recommend

class CoreTests(unittest.TestCase):
    def test_chain_assignment_and_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            chain=MissionChain('demo','Review source',['first','second'],Path(temp),Path(temp)/'chains')
            chain.start('first')
            chain.finish('first','TACHE_AGENT: second | Check the output')
            self.assertEqual(chain.data['tasks']['second']['assignment'],'Check the output')
            self.assertTrue((chain.path/'etat.json').is_file())
            chain.close()
    def test_invalid_identifier(self):
        with self.assertRaises(ValueError): MissionChain('../escape','brief',[],'.')
    def test_routing_is_available_only(self):
        self.assertEqual(recommend('corriger code',['aws-qwen-coder'])[0],'aws-qwen-coder')
        self.assertEqual(recommend('design',['offline'])[0],'offline')
        with self.assertRaises(ValueError): recommend('design',[])
    def test_order_deduplicates(self):
        self.assertEqual(order_agents(['a','a','b']),['a','b'])
