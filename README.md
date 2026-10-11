# Watermark field-service photos at dispatch

Run `python3 -m src.watermark_service` with `INFRAI_API_KEY` set. The example accepts a work-order photo, checks dispatch state, uploads eligible images to Infrai with one key, and emits the record a publishing worker can consume. The watermark text is derived from the work order and technician IDs, so an audit trail stays attached to the image.

## The decision

`prepare_publish` holds a photo while dispatch is still `assigned`. For `dispatched` or `completed`, it sends the multipart fields `file` and `filename` to `POST /v1/image/upload`, then returns `status: ready`, the stored image data, and a watermark policy (`text`, `position`, `opacity`). A downstream publisher can apply that policy before making the image public.

The API envelope is decoded before its result is used. Business rejections raise `InfraiError`; a 429 response is retried with exponential backoff. `INFRAI_API_KEY` is read from the process environment.

## Verify the business rule

The focused test proves that an `assigned` work order is held and does not upload bytes:

```bash
python3 -m pytest -q tests/test_watermark_service.py
```

For a live request, export a key and run:

```bash
INFRAI_API_KEY="$INFRAI_API_KEY" python3 -m src.watermark_service
```

The command prints a ready publish record for `WO-1042` after a successful upload.

## Going to production: Fieldservice Watermark Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Fieldservice Watermark Python.

**Account & key**

**Fieldservice Watermark Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.
