import unittest
from dataclasses import replace
from fgmapping.ai.gateway import Preview,ReplayConsent,OfflineReplayGateway
from fgmapping.integrations.proposals import parse_synthetic_pid
class Gateway(unittest.TestCase):
    def preview(self):return Preview('SYN-JOB','OFFLINE_REPLAY','offline://replay','SYNTHETIC_MODEL','TEST','text-only','SYN-A','0'*64,'SYNTHETIC','Synthetic check','0','0')
    def result(self,p):return {'suggestions':[{'text':'Check synthetic source','source_hash':p.source_hash,'source_revision':p.source_revision,'status':'CANDIDATE'}]}
    def test_replay_and_one_use(self):
        p=self.preview();g=OfflineReplayGateway();c=ReplayConsent(p.sha256,'TEST_ENGINE')
        self.assertEqual(g.execute(p,c,self.result(p)),self.result(p))
        self.assertNotIn('Synthetic check',str(g.audit));self.assertNotIn('Check synthetic source',str(g.audit))
        with self.assertRaises(ValueError):g.execute(p,c,self.result(p))
    def test_live_disabled(self):
        p=self.preview()
        with self.assertRaises(ValueError):OfflineReplayGateway().execute(p,ReplayConsent(p.sha256,'TEST_ENGINE'),self.result(p),live=True)
    def test_changed_preview_and_external_endpoint(self):
        p=self.preview();c=ReplayConsent(p.sha256,'TEST_ENGINE')
        for q in (replace(p,outbound_text='Changed'),replace(p,endpoint='https://example.invalid'),replace(p,data_class='PROJECT_BASIS'),replace(p,estimated_cost='1')):
            with self.assertRaises(ValueError):OfflineReplayGateway().execute(q,c,self.result(q))
    def test_budget_exact_consent(self):
        p=replace(self.preview(),estimated_cost='1',maximum_cost='0')
        with self.assertRaises(ValueError):OfflineReplayGateway().execute(p,ReplayConsent(p.sha256,'TEST_ENGINE'),self.result(p))
    def test_response_cannot_accept_or_write_geometry(self):
        p=self.preview()
        for result in ({'suggestions':[],'approved':True},{'suggestions':[{'text':'x','source_hash':p.source_hash,'source_revision':p.source_revision,'status':'APPROVED'}]}):
            with self.assertRaises(ValueError):OfflineReplayGateway().execute(p,ReplayConsent(p.sha256,'TEST_ENGINE'),result)
class Interfaces(unittest.TestCase):
    def payload(self):return {'schema_version':'fg-pid-proposal/1','data_class':'SYNTHETIC','source_hash':'0'*64,'source_revision':'SYN-A','equipment':[{'tag':'SYN-V101','class':'VESSEL','evidence_locator':'SYN page 1'}],'connections':[]}
    def test_proposal_only(self):
        r=parse_synthetic_pid(self.payload());self.assertEqual(r['equipment_proposals'][0]['position'],'NOT SUPPLIED');self.assertFalse(r['external_writes'])
    def test_coordinate_inference_forbidden(self):
        p=self.payload();p['equipment'][0]['xyz']=[1,2,3]
        with self.assertRaises(ValueError):parse_synthetic_pid(p)
    def test_unknown_endpoint_and_version(self):
        p=self.payload();p['connections']=[{'from':'SYN-V101','to':'MISSING','evidence_locator':'SYN'}]
        with self.assertRaises(ValueError):parse_synthetic_pid(p)
        p=self.payload();p['schema_version']='2'
        with self.assertRaises(ValueError):parse_synthetic_pid(p)
