from src.watermark_service import WorkOrderPhoto, prepare_publish


class NoUpload:
    def upload(self, filename, content):
        raise AssertionError("held work orders must not upload")


def test_dispatch_pending_holds_photo_before_publish():
    photo = WorkOrderPhoto("WO-9", "T-2", "site.jpg", b"x", "assigned", "call customer")
    assert prepare_publish(photo, NoUpload()) == {"status": "held", "reason": "dispatch_pending", "work_order_id": "WO-9"}
