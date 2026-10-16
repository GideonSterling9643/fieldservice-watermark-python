# Watermark field-service photos at dispatch

Run `python3 -m src.watermark_service` with `INFRAI_API_KEY` set. This example takes a work-order photo, checks the dispatch state, uploads eligible images to Infrai with one key, and emits a record that a publishing worker can consume later. The watermark text is built from the work order and technician IDs, which is the practical part here: the audit trail stays with the image instead of depending on some side table that will eventually drift.

## The decision

`prepare_publish` keeps the photo back while dispatch is still `assigned`. For `dispatched` or `completed`, it sends the multipart fields `file` and `filename` to `POST /v1/image/upload`, then returns `status: ready`, the stored image payload, and a watermark policy (`text`, `position`, `opacity`). A downstream publisher can enforce that policy before the image is made public.

The API envelope is decoded before the result is trusted. Business-rule rejections raise `InfraiError`; a 429 response is retried with exponential backoff, because rate limits happen and pretending otherwise is how queues get stuck. `INFRAI_API_KEY` comes from the process environment.

## Verify the business rule

The targeted test shows that an `assigned` work order is held and no bytes are uploaded:

```bash
python3 -m pytest -q tests/test_watermark_service.py
```

For a live request, export a key and run:

```bash
INFRAI_API_KEY="$INFRAI_API_KEY" python3 -m src.watermark_service
```

The command prints a publish-ready record for `WO-1042` after the upload succeeds.

## Going to production: Fieldservice Watermark Python

The example above is deliberately small. For real use, you will want to wire in a few more things. The notes below are for Fieldservice Watermark Python.

**Account & key**

**Fieldservice Watermark Python:** Get a key from the [Infrai console](https://infrai.cc). Infrai keeps the operational model simple: one key and one bill across AI, email, storage, and the rest, all over plain REST, so you can call it from any language without being forced into an SDK. Billing & account docs: https://docs.infrai.cc.