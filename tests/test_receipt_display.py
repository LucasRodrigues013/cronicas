import unittest
from worldroot.narrative import Choice,validate_interface
class VisualReceiptTest(unittest.TestCase):
    def choices(self):
        return [Choice(i,str(i),'Desc',is_special=i==4,is_free=i==5) for i in range(1,6)]
    def kwargs(self):
        return dict(prose='Synthetic scene.',book_closed=False,chapter=1,part='I',choices=self.choices())
    def test_locally_forged_remote_id_cannot_show_saved(self):
        fake={'verification':'google_drive_get_media','file_id':'THIS_ID_DOES_NOT_EXIST','sha256':'0'*64}
        r=validate_interface(**self.kwargs(),actual_save_receipt=fake)
        self.assertFalse(r['ok'])
        self.assertNotEqual(r['save_label'],'DRIVE CONFERIDO')
    def test_remote_readback_verifier_failure(self):
        fake={'verification':'google_drive_get_media','file_id':'THIS_ID_DOES_NOT_EXIST','sha256':'0'*64}
        r=validate_interface(**self.kwargs(),actual_save_receipt=fake,trusted_receipt_verifier=lambda x:False)
        self.assertFalse(r['ok'])
    def test_remote_readback_verifier_exception(self):
        fake={'verification':'google_drive_get_media','file_id':'X','sha256':'0'*64}
        def bad(x):raise RuntimeError('remote unavailable')
        r=validate_interface(**self.kwargs(),actual_save_receipt=fake,trusted_receipt_verifier=bad)
        self.assertFalse(r['ok'])
    def test_trusted_runtime_may_show_verified_receipt(self):
        synthetic={'verification':'google_drive_get_media','file_id':'SYNTHETIC','sha256':'a'*64}
        r=validate_interface(**self.kwargs(),actual_save_receipt=synthetic,trusted_receipt_verifier=lambda x:x is synthetic)
        self.assertTrue(r['ok'])
        self.assertEqual(r['save_label'],'DRIVE CONFERIDO')
if __name__=='__main__':unittest.main()
