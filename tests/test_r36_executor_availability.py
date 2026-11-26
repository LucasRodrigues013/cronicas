import unittest
from worldroot.semantic_local import availability,revision
class ExecutorAvailabilityTests(unittest.TestCase):
    def test_unavailable(self):
        def fail(*args):raise ConnectionRefusedError()
        self.assertEqual(availability(fail)["status"],"UNAVAILABLE")
    def test_same_digest_not_two_models(self):
        def fake(*args):return {"models":[{"name":"a","digest":"a"*64},{"name":"b","digest":"sha256:"+"a"*64}]}
        self.assertEqual(availability(fake)["distinct_local_digests"],1)
    def test_distinct_and_remote_rejected(self):
        def fake(*args):return {"models":[{"name":"a","digest":"a"*64},{"name":"b","digest":"b"*64},{"name":"remote","digest":"c"*64,"remote_model":"remote"}]}
        self.assertEqual(availability(fake)["distinct_local_digests"],2)
        self.assertFalse(availability(fake)["inference_executed"])
