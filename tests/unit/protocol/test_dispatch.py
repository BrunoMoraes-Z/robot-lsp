from robot_lsp.protocol.dispatch import MethodDispatcher
from robot_lsp.protocol.jsonrpc import METHOD_NOT_FOUND, create_notification, create_request


class TestMethodDispatcher:
    def test_request_returns_response(self):
        dispatcher = MethodDispatcher()

        def handler(params, token):
            assert params == {"x": 1}
            assert not token.is_canceled()
            return {"ok": True}

        dispatcher.register("test/echo", handler)

        response = dispatcher.dispatch(create_request("test/echo", id=1, params={"x": 1}))

        assert response is not None
        assert response.id == 1
        assert response.result == {"ok": True}

    def test_notification_returns_none(self):
        dispatcher = MethodDispatcher()
        calls = []

        def handler(params, token):
            calls.append(params)
            return {"ignored": True}

        dispatcher.register("test/notify", handler)

        response = dispatcher.dispatch(create_notification("test/notify", params={"x": 1}))

        assert response is None
        assert calls == [{"x": 1}]

    def test_json_rpc_method_not_found(self):
        dispatcher = MethodDispatcher()

        response = dispatcher.dispatch(create_request("missing", id=1))

        assert response is not None
        assert response.error is not None
        assert response.error.code == METHOD_NOT_FOUND
        assert response.error.message == "Method not found: missing"

    def test_unknown_notification_returns_none(self):
        dispatcher = MethodDispatcher()

        response = dispatcher.dispatch(create_notification("missing"))

        assert response is None

    def test_cancel_request(self):
        dispatcher = MethodDispatcher()
        observed_cancel = []

        def handler(params, token):
            dispatcher.dispatch(create_notification("$/cancelRequest", params={"id": 1}))
            observed_cancel.append(token.is_canceled())
            return "ignored"

        dispatcher.register("test/cancelable", handler)

        response = dispatcher.dispatch(create_request("test/cancelable", id=1))

        assert response is None
        assert observed_cancel == [True]

    def test_handler_exception_returns_internal_error(self):
        dispatcher = MethodDispatcher()

        def handler(params, token):
            raise RuntimeError("boom")

        dispatcher.register("test/error", handler)

        response = dispatcher.dispatch(create_request("test/error", id=1))

        assert response is not None
        assert response.error is not None
        assert response.error.message == "Internal error"
        assert response.error.data == "boom"
